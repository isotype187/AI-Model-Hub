"""
Nexus98 Mouse Agent - Programmatic Control API.

Agent-callable computer-interaction surface for Nexus98. Provides reliable,
bounds-checked, logged mouse control (move / click / double / right / middle /
drag / scroll), screen-coordinate management, on-demand screenshots, and safety
controls (action validation, timeouts, emergency stop, structured failure
reporting).

Design notes:
  - Backend: pynput (input) + ctypes user32 (screen metrics) + PIL.ImageGrab
    (screenshots). No pyautogui/mss/screeninfo dependency.
  - Every public action returns a structured dict:
        {"ok": bool, "action": str, "result": <any>, "error": <str|None>, ...}
  - dry_run=True validates + logs WITHOUT emitting real input events.
  - Emergency stop: once tripped, all further actions fail safely until reset.

This module is the agent-facing control API. It is separate from and does not
import the human-assistive tray tool (tools/mouse_agent/ai_mouse_mode.py).
"""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


DEFAULT_CONFIG_PATH = Path(r"D:\Nexus98\config\mouse_agent.json")

VALID_BUTTONS = ("left", "right", "middle")
VALID_SCROLL_DIRECTIONS = ("up", "down", "left", "right")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


DEFAULT_CONFIG: dict[str, Any] = {
    "move_duration": 0.0,
    "move_steps": 20,
    "click_delay": 0.05,
    "double_click_interval": 0.12,
    "drag_duration": 0.3,
    "scroll_amount": 3,
    "action_timeout": 5.0,
    "inter_action_delay": 0.02,
    "safety": {
        "enforce_bounds": True,
        "boundary_margin": 0,
        "use_virtual_desktop": True,
        "fail_on_out_of_bounds": True,
        "max_actions_per_session": 100000,
        "emergency_stop_default": False,
    },
    "logging": {
        "enabled": True,
        "path": r"D:\Nexus98\logs\mouse_agent.log",
        "max_history": 500,
    },
    "screenshot": {"dir": r"D:\Nexus98\logs\mouse_screenshots"},
}


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path: Optional[Path] = None) -> dict:
    """Load mouse config merged over defaults. Never raises on bad/missing file."""
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    try:
        raw = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
        if isinstance(raw, dict):
            return _deep_merge(DEFAULT_CONFIG, raw)
    except Exception:
        pass
    return dict(DEFAULT_CONFIG)


class ScreenBounds:
    """Resolves screen extents via ctypes user32, with a safe fallback."""

    def __init__(self, use_virtual_desktop: bool = True, margin: int = 0):
        self.use_virtual_desktop = use_virtual_desktop
        self.margin = max(0, int(margin))
        self.left = 0
        self.top = 0
        self.width = 0
        self.height = 0
        self.available = False
        self.refresh()

    def refresh(self) -> None:
        try:
            import ctypes

            user32 = ctypes.windll.user32
            try:
                user32.SetProcessDPIAware()
            except Exception:
                pass
            if self.use_virtual_desktop:
                self.left = int(user32.GetSystemMetrics(76))
                self.top = int(user32.GetSystemMetrics(77))
                self.width = int(user32.GetSystemMetrics(78))
                self.height = int(user32.GetSystemMetrics(79))
            if not self.use_virtual_desktop or self.width <= 0 or self.height <= 0:
                self.left = 0
                self.top = 0
                self.width = int(user32.GetSystemMetrics(0))
                self.height = int(user32.GetSystemMetrics(1))
            self.available = self.width > 0 and self.height > 0
        except Exception:
            self.left, self.top, self.width, self.height = 0, 0, 1920, 1080
            self.available = False

    @property
    def right(self) -> int:
        return self.left + self.width - 1

    @property
    def bottom(self) -> int:
        return self.top + self.height - 1

    def contains(self, x: int, y: int) -> bool:
        m = self.margin
        return (self.left + m) <= x <= (self.right - m) and (
            self.top + m
        ) <= y <= (self.bottom - m)

    def as_dict(self) -> dict:
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
            "right": self.right,
            "bottom": self.bottom,
            "detected": self.available,
        }


class MouseControlError(Exception):
    """Raised only for programmer errors; normal failures return dicts."""


class MouseControl:
    """Reliable, bounds-checked, logged mouse controller for Nexus98 agents."""

    def __init__(self, config: Optional[dict] = None,
                 config_path: Optional[Path] = None, dry_run: bool = False):
        self.config = config if config is not None else load_config(config_path)
        self.dry_run = bool(dry_run)
        self._lock = threading.RLock()
        self._emergency_stop = bool(
            self.config.get("safety", {}).get("emergency_stop_default", False)
        )
        self._action_count = 0
        self._history: deque = deque(
            maxlen=int(self.config.get("logging", {}).get("max_history", 500))
        )
        safety = self.config.get("safety", {})
        self.bounds = ScreenBounds(
            use_virtual_desktop=bool(safety.get("use_virtual_desktop", True)),
            margin=int(safety.get("boundary_margin", 0)),
        )
        self._controller = None
        self._button_enum = None
        if not self.dry_run:
            self._init_backend()

    def _init_backend(self) -> None:
        try:
            from pynput.mouse import Button, Controller

            self._controller = Controller()
            self._button_enum = Button
        except Exception as exc:
            self._controller = None
            self._button_enum = None
            self.dry_run = True
            self._record("backend_init", ok=False,
                         error=f"pynput unavailable, forced dry_run: {exc!r}")

    def _button(self, name: str):
        if self._button_enum is None:
            return None
        return {
            "left": self._button_enum.left,
            "right": self._button_enum.right,
            "middle": self._button_enum.middle,
        }[name]

    def emergency_stop(self) -> dict:
        with self._lock:
            self._emergency_stop = True
        return self._record("emergency_stop", ok=True, result="engaged")

    def reset_emergency_stop(self) -> dict:
        with self._lock:
            self._emergency_stop = False
        return self._record("reset_emergency_stop", ok=True, result="cleared")

    @property
    def stopped(self) -> bool:
        return self._emergency_stop

    def _precheck(self, action: str) -> Optional[dict]:
        if self._emergency_stop:
            return self._fail(action, "emergency stop engaged")
        limit = int(self.config.get("safety", {}).get("max_actions_per_session", 0))
        if limit and self._action_count >= limit:
            return self._fail(action, f"max_actions_per_session ({limit}) reached")
        return None

    def _validate_point(self, action: str, x: Any, y: Any) -> Optional[dict]:
        try:
            xi, yi = int(x), int(y)
        except (TypeError, ValueError):
            return self._fail(action,
                              f"coordinates must be integers, got ({x!r}, {y!r})")
        safety = self.config.get("safety", {})
        if safety.get("enforce_bounds", True) and not self.bounds.contains(xi, yi):
            if safety.get("fail_on_out_of_bounds", True):
                return self._fail(action,
                                  f"({xi}, {yi}) outside bounds {self.bounds.as_dict()}")
        return None

    def _clamp(self, x: int, y: int) -> tuple[int, int]:
        m = self.bounds.margin
        cx = min(max(int(x), self.bounds.left + m), self.bounds.right - m)
        cy = min(max(int(y), self.bounds.top + m), self.bounds.bottom - m)
        return cx, cy

    def _record(self, action: str, ok: bool, result: Any = None,
                error: Optional[str] = None, **extra) -> dict:
        entry = {"ts": _now(), "action": action, "ok": ok, "result": result,
                 "error": error, "dry_run": self.dry_run}
        entry.update(extra)
        with self._lock:
            self._history.append(entry)
        self._write_log(entry)
        return entry

    def _write_log(self, entry: dict) -> None:
        log_cfg = self.config.get("logging", {})
        if not log_cfg.get("enabled", True):
            return
        try:
            path = Path(log_cfg.get("path", DEFAULT_CONFIG["logging"]["path"]))
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    def _fail(self, action: str, error: str, **extra) -> dict:
        return self._record(action, ok=False, error=error, **extra)

    def _ok(self, action: str, result: Any = None, **extra) -> dict:
        with self._lock:
            self._action_count += 1
        return self._record(action, ok=True, result=result, **extra)

    def _sleep_inter(self) -> None:
        d = float(self.config.get("inter_action_delay", 0.0))
        if d > 0 and not self.dry_run:
            time.sleep(d)

    def _run_with_timeout(self, action: str, fn) -> Optional[dict]:
        timeout = float(self.config.get("action_timeout", 5.0))
        result_box: dict[str, Any] = {}

        def _target():
            try:
                fn()
                result_box["done"] = True
            except Exception as exc:
                result_box["exc"] = exc

        if self.dry_run:
            return None
        t = threading.Thread(target=_target, daemon=True)
        t.start()
        t.join(timeout)
        if t.is_alive():
            return self._fail(action, f"action timed out after {timeout}s")
        if "exc" in result_box:
            return self._fail(action, f"backend error: {result_box['exc']!r}")
        return None

    def get_position(self) -> dict:
        if self.dry_run or self._controller is None:
            return self._ok("get_position", result=None,
                            note="dry_run/no-backend; position unavailable")
        try:
            pos = tuple(int(v) for v in self._controller.position)
        except Exception as exc:
            return self._fail("get_position", f"backend error: {exc!r}")
        return self._ok("get_position", result={"x": pos[0], "y": pos[1]})

    def get_screen_bounds(self) -> dict:
        return self._ok("get_screen_bounds", result=self.bounds.as_dict())

    def move(self, x: int, y: int) -> dict:
        action = "move"
        pre = self._precheck(action)
        if pre:
            return pre
        bad = self._validate_point(action, x, y)
        if bad:
            return bad
        xi, yi = self._clamp(int(x), int(y))

        def _do():
            self._controller.position = (xi, yi)

        err = self._run_with_timeout(action, _do)
        if err:
            return err
        self._sleep_inter()
        return self._ok(action, result={"x": xi, "y": yi})

    def click(self, x: Optional[int] = None, y: Optional[int] = None,
              button: str = "left", count: int = 1) -> dict:
        action = "click"
        pre = self._precheck(action)
        if pre:
            return pre
        if button not in VALID_BUTTONS:
            return self._fail(action,
                              f"invalid button {button!r}; expected {VALID_BUTTONS}")
        try:
            count = int(count)
        except (TypeError, ValueError):
            return self._fail(action, f"count must be int, got {count!r}")
        if count < 1:
            return self._fail(action, "count must be >= 1")
        if x is not None or y is not None:
            if x is None or y is None:
                return self._fail(action, "both x and y required when positioning")
            moved = self.move(x, y)
            if not moved["ok"]:
                return moved

        def _do():
            self._controller.click(self._button(button), count)

        err = self._run_with_timeout(action, _do)
        if err:
            return err
        if not self.dry_run:
            time.sleep(float(self.config.get("click_delay", 0.0)))
        self._sleep_inter()
        return self._ok(action, result={"button": button, "count": count,
                                        "x": x, "y": y})

    def double_click(self, x: Optional[int] = None, y: Optional[int] = None,
                     button: str = "left") -> dict:
        res = self.click(x=x, y=y, button=button, count=2)
        res["action"] = "double_click"
        return res

    def right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> dict:
        res = self.click(x=x, y=y, button="right", count=1)
        res["action"] = "right_click"
        return res

    def middle_click(self, x: Optional[int] = None, y: Optional[int] = None) -> dict:
        res = self.click(x=x, y=y, button="middle", count=1)
        res["action"] = "middle_click"
        return res

    def drag(self, x1: int, y1: int, x2: int, y2: int, button: str = "left") -> dict:
        action = "drag"
        pre = self._precheck(action)
        if pre:
            return pre
        if button not in VALID_BUTTONS:
            return self._fail(action,
                              f"invalid button {button!r}; expected {VALID_BUTTONS}")
        bad = self._validate_point(action, x1, y1) or self._validate_point(action, x2, y2)
        if bad:
            return bad
        sx, sy = self._clamp(int(x1), int(y1))
        ex, ey = self._clamp(int(x2), int(y2))

        def _do():
            self._controller.position = (sx, sy)
            self._controller.press(self._button(button))
            steps = max(1, int(self.config.get("move_steps", 20)))
            dur = float(self.config.get("drag_duration", 0.0))
            for i in range(1, steps + 1):
                ix = int(sx + (ex - sx) * i / steps)
                iy = int(sy + (ey - sy) * i / steps)
                self._controller.position = (ix, iy)
                if dur > 0:
                    time.sleep(dur / steps)
            self._controller.release(self._button(button))

        err = self._run_with_timeout(action, _do)
        if err:
            return err
        self._sleep_inter()
        return self._ok(action, result={"from": {"x": sx, "y": sy},
                                        "to": {"x": ex, "y": ey}, "button": button})

    def scroll(self, direction: str = "down", amount: Optional[int] = None,
               x: Optional[int] = None, y: Optional[int] = None) -> dict:
        action = "scroll"
        pre = self._precheck(action)
        if pre:
            return pre
        if direction not in VALID_SCROLL_DIRECTIONS:
            return self._fail(action, f"invalid direction {direction!r}; "
                                      f"expected {VALID_SCROLL_DIRECTIONS}")
        if amount is None:
            amount = int(self.config.get("scroll_amount", 3))
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            return self._fail(action, f"amount must be int, got {amount!r}")
        if amount < 0:
            return self._fail(action, "amount must be >= 0")
        if x is not None and y is not None:
            moved = self.move(x, y)
            if not moved["ok"]:
                return moved
        dx, dy = 0, 0
        if direction == "up":
            dy = amount
        elif direction == "down":
            dy = -amount
        elif direction == "right":
            dx = amount
        elif direction == "left":
            dx = -amount

        def _do():
            self._controller.scroll(dx, dy)

        err = self._run_with_timeout(action, _do)
        if err:
            return err
        self._sleep_inter()
        return self._ok(action, result={"direction": direction, "amount": amount,
                                        "dx": dx, "dy": dy})

    def screenshot(self, path: Optional[str] = None) -> dict:
        action = "screenshot"
        pre = self._precheck(action)
        if pre:
            return pre
        try:
            from PIL import ImageGrab
        except Exception as exc:
            return self._fail(action, f"PIL.ImageGrab unavailable: {exc!r}")
        if path is None:
            sdir = Path(self.config.get("screenshot", {}).get(
                "dir", DEFAULT_CONFIG["screenshot"]["dir"]))
            sdir.mkdir(parents=True, exist_ok=True)
            path = str(sdir / f"screenshot_{int(time.time() * 1000)}.png")
        if self.dry_run:
            return self._ok(action, result={"path": path, "captured": False},
                            note="dry_run; no capture performed")
        try:
            img = ImageGrab.grab(all_screens=True)
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            img.save(path)
        except Exception as exc:
            return self._fail(action, f"capture failed: {exc!r}")
        return self._ok(action, result={"path": path, "captured": True,
                                        "size": list(img.size)})

    def status(self) -> dict:
        return {
            "ok": True,
            "action": "status",
            "result": {
                "dry_run": self.dry_run,
                "backend": "pynput" if self._controller is not None else None,
                "emergency_stop": self._emergency_stop,
                "action_count": self._action_count,
                "bounds": self.bounds.as_dict(),
                "history_len": len(self._history),
            },
            "error": None,
        }

    def history(self, limit: Optional[int] = None) -> list[dict]:
        items = list(self._history)
        if limit is not None:
            items = items[-int(limit):]
        return items


_default_control: Optional[MouseControl] = None


def get_mouse_control(dry_run: bool = False,
                      config_path: Optional[Path] = None) -> MouseControl:
    """Return a process-wide MouseControl instance (created on first call)."""
    global _default_control
    if _default_control is None:
        _default_control = MouseControl(dry_run=dry_run, config_path=config_path)
    return _default_control


# ----------------------------------------------------------------------
# Module-level convenience API (functional interface for agents).
# These delegate to the shared MouseControl instance so callers can use a
# simple import without managing an object. Each returns a structured dict.
# ----------------------------------------------------------------------


def move(x, y, dry_run: bool = False) -> dict:
    return get_mouse_control(dry_run=dry_run).move(x, y)


def click(x=None, y=None, button: str = "left", count: int = 1,
          dry_run: bool = False) -> dict:
    return get_mouse_control(dry_run=dry_run).click(x=x, y=y, button=button, count=count)


def double_click(x=None, y=None, button: str = "left", dry_run: bool = False) -> dict:
    return get_mouse_control(dry_run=dry_run).double_click(x=x, y=y, button=button)


def right_click(x=None, y=None, dry_run: bool = False) -> dict:
    return get_mouse_control(dry_run=dry_run).right_click(x=x, y=y)


def middle_click(x=None, y=None, dry_run: bool = False) -> dict:
    return get_mouse_control(dry_run=dry_run).middle_click(x=x, y=y)


def drag(x1, y1, x2, y2, button: str = "left", dry_run: bool = False) -> dict:
    return get_mouse_control(dry_run=dry_run).drag(x1, y1, x2, y2, button=button)


def scroll(direction: str = "down", amount=None, x=None, y=None,
           dry_run: bool = False) -> dict:
    return get_mouse_control(dry_run=dry_run).scroll(
        direction=direction, amount=amount, x=x, y=y)


def screenshot(path=None, dry_run: bool = False) -> dict:
    return get_mouse_control(dry_run=dry_run).screenshot(path=path)


def get_position(dry_run: bool = False) -> dict:
    return get_mouse_control(dry_run=dry_run).get_position()


def get_screen_bounds(dry_run: bool = False) -> dict:
    return get_mouse_control(dry_run=dry_run).get_screen_bounds()


def emergency_stop(dry_run: bool = False) -> dict:
    return get_mouse_control(dry_run=dry_run).emergency_stop()


def reset_emergency_stop(dry_run: bool = False) -> dict:
    return get_mouse_control(dry_run=dry_run).reset_emergency_stop()


def control_status(dry_run: bool = False) -> dict:
    return get_mouse_control(dry_run=dry_run).status()

if __name__ == "__main__":
    mc = MouseControl(dry_run=True)
    print(json.dumps(mc.status(), indent=2))
    print(json.dumps(mc.move(100, 100), indent=2))
    print(json.dumps(mc.move(-5, -5), indent=2))