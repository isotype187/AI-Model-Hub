"""
Nexus98 Mouse Agent - Tests.

Validates the programmatic MouseControl API (core/mouse_control.py) and the
agent-facing wrappers. All tests use dry_run=True so NO real cursor movement or
clicks occur - safe for CI/sandbox. Covers movement, clicking, invalid input
handling, safety limits, and error recovery.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from core.mouse_control import (
    MouseControl,
    ScreenBounds,
    load_config,
    DEFAULT_CONFIG,
)
from core import mouse_control as mc_module


def _mc(**over):
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    cfg.setdefault("logging", {})["enabled"] = False
    cfg["safety"]["boundary_margin"] = 0
    cfg["safety"]["use_virtual_desktop"] = False
    for k, v in over.items():
        cfg[k] = v
    m = MouseControl(config=cfg, dry_run=True)
    # Force deterministic bounds regardless of host screen.
    m.bounds.left, m.bounds.top = 0, 0
    m.bounds.width, m.bounds.height = 1920, 1080
    m.bounds.available = True
    return m


# ---------------------------------------------------------------- movement

def test_move_valid():
    m = _mc()
    r = m.move(100, 200)
    assert r["ok"] is True
    assert r["result"] == {"x": 100, "y": 200}


def test_move_out_of_bounds_fails_safely():
    m = _mc()
    r = m.move(999999, 5)
    assert r["ok"] is False
    assert "outside bounds" in r["error"]


def test_move_negative_fails():
    m = _mc()
    r = m.move(-10, -10)
    assert r["ok"] is False


def test_move_non_integer_fails():
    m = _mc()
    r = m.move("abc", 10)
    assert r["ok"] is False
    assert "integers" in r["error"]


# ---------------------------------------------------------------- clicking

def test_click_default_left():
    m = _mc()
    r = m.click(10, 10)
    assert r["ok"] is True
    assert r["result"]["button"] == "left"
    assert r["result"]["count"] == 1


def test_double_click():
    m = _mc()
    r = m.double_click(10, 10)
    assert r["ok"] is True
    assert r["action"] == "double_click"
    assert r["result"]["count"] == 2


def test_right_and_middle_click():
    m = _mc()
    assert m.right_click(10, 10)["result"]["button"] == "right"
    assert m.middle_click(10, 10)["result"]["button"] == "middle"


def test_click_invalid_button():
    m = _mc()
    r = m.click(10, 10, button="purple")
    assert r["ok"] is False
    assert "invalid button" in r["error"]


def test_click_invalid_count():
    m = _mc()
    assert m.click(10, 10, count=0)["ok"] is False
    assert m.click(10, 10, count="x")["ok"] is False


def test_click_partial_coordinates_fail():
    m = _mc()
    r = m.click(x=10)  # y missing
    assert r["ok"] is False


def test_click_out_of_bounds_fails():
    m = _mc()
    r = m.click(999999, 5)
    assert r["ok"] is False


# ---------------------------------------------------------------- drag/scroll

def test_drag_valid():
    m = _mc()
    r = m.drag(10, 10, 100, 100)
    assert r["ok"] is True
    assert r["result"]["from"] == {"x": 10, "y": 10}
    assert r["result"]["to"] == {"x": 100, "y": 100}


def test_drag_out_of_bounds_fails():
    m = _mc()
    assert m.drag(10, 10, 999999, 10)["ok"] is False


def test_scroll_directions():
    m = _mc()
    assert m.scroll("up", 3)["result"]["dy"] == 3
    assert m.scroll("down", 3)["result"]["dy"] == -3
    assert m.scroll("left", 2)["result"]["dx"] == -2
    assert m.scroll("right", 2)["result"]["dx"] == 2


def test_scroll_invalid_direction():
    m = _mc()
    assert m.scroll("sideways")["ok"] is False


def test_scroll_negative_amount_fails():
    m = _mc()
    assert m.scroll("down", -5)["ok"] is False


# ------------------------------------------------------------ safety limits

def test_emergency_stop_blocks_actions():
    m = _mc()
    m.emergency_stop()
    r = m.move(10, 10)
    assert r["ok"] is False
    assert "emergency stop" in r["error"]


def test_emergency_stop_reset_recovers():
    m = _mc()
    m.emergency_stop()
    assert m.move(10, 10)["ok"] is False
    m.reset_emergency_stop()
    assert m.move(10, 10)["ok"] is True


def test_max_actions_limit():
    m = _mc()
    m.config["safety"]["max_actions_per_session"] = 2
    assert m.move(1, 1)["ok"] is True
    assert m.move(2, 2)["ok"] is True
    r = m.move(3, 3)
    assert r["ok"] is False
    assert "max_actions_per_session" in r["error"]


def test_bounds_disabled_allows_out_of_range():
    m = _mc()
    m.config["safety"]["enforce_bounds"] = False
    r = m.move(999999, 5)
    assert r["ok"] is True  # clamped, not rejected


# --------------------------------------------------------- introspection

def test_status_and_history():
    m = _mc()
    m.move(10, 10)
    st = m.status()
    assert st["ok"] is True
    assert st["result"]["action_count"] >= 1
    hist = m.history()
    assert isinstance(hist, list) and len(hist) >= 1


def test_screen_bounds_report():
    m = _mc()
    b = m.get_screen_bounds()
    assert b["ok"] is True
    assert b["result"]["width"] == 1920


def test_screenshot_dry_run_no_capture():
    m = _mc()
    r = m.screenshot()
    assert r["ok"] is True
    assert r["result"]["captured"] is False


# --------------------------------------------------- config / error recovery

def test_load_config_missing_returns_defaults():
    cfg = load_config(Path(tempfile.mkdtemp()) / "nope.json")
    assert cfg["move_steps"] == DEFAULT_CONFIG["move_steps"]


def test_load_config_bad_json_returns_defaults():
    p = Path(tempfile.mkdtemp()) / "bad.json"
    p.write_text("{ not json", encoding="utf-8")
    cfg = load_config(p)
    assert cfg["scroll_amount"] == DEFAULT_CONFIG["scroll_amount"]


def test_screenbounds_fallback_is_deterministic():
    b = ScreenBounds(use_virtual_desktop=False)
    assert b.width > 0 and b.height > 0


# --------------------------------------------------- module-level wrappers

def test_module_level_wrappers():
    assert mc_module.move(5, 5, dry_run=True)["ok"] is True
    assert mc_module.click(5, 5, dry_run=True)["ok"] is True
    assert mc_module.scroll("down", dry_run=True)["ok"] is True
    assert mc_module.control_status(dry_run=True)["result"]["dry_run"] is True