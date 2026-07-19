# Nexus98 Mouse Agent System

Status: COMPLETE
Last updated: 2026-07-17 02:39:49

## 1. Overview

The Mouse Agent subsystem gives Nexus98 agents a reliable, safe computer
interaction capability. It has two distinct, non-overlapping parts:

- Agent control API (new): `core/mouse_control.py` - programmatic, bounds-checked,
  logged mouse control that agents call. This is the primary interface.
- Human-assistive tray tool (preserved): `tools/mouse_agent/ai_mouse_mode.py`,
  managed by `core/mouse_agent.py`. A hold-drag-to-copy / middle-click-to-paste
  macro with a tray icon. Unchanged by this work and independent of the API.

## 2. Architecture

```
Nexus98 agent
    |
    v
core/mouse_control.py                 core/mouse_agent.py
  MouseControl (class)                   start_mouse_mode()
  get_mouse_control() (singleton)        stop_mouse_mode()
  module-level wrappers                   mouse_status()
    move/click/double/right/middle             |
    drag/scroll/screenshot                     v
    get_position/get_screen_bounds       tools/mouse_agent/ai_mouse_mode.py
    emergency_stop/reset/status            (human tray macro; separate)
    |
    +-- pynput.mouse.Controller  (input events)
    +-- ctypes user32            (screen metrics / bounds)
    +-- PIL.ImageGrab            (screenshots)
```

Backends require no new installs: `pynput` 1.8.2, `Pillow` 12.3.0, and stdlib
`ctypes` are already present in `.venv`.

## 3. Capabilities

Input control (all return a structured dict):
- `move(x, y)`
- `click(x, y, button, count)`
- `double_click(x, y, button)`
- `right_click(x, y)`, `middle_click(x, y)`
- `drag(x1, y1, x2, y2, button)` - stepwise interpolation
- `scroll(direction, amount, x, y)` - up/down/left/right

Coordinate management:
- Screen detection via ctypes (primary or full virtual desktop).
- Boundary checking (`enforce_bounds`), invalid-coordinate rejection, integer
  validation, clamping when bounds enforcement is disabled.
- Deterministic 1920x1080 fallback if metrics are unavailable (headless/CI).

Screen awareness:
- `screenshot(path)` via `PIL.ImageGrab` (all screens). `get_screen_bounds()`,
  `get_position()`.

## 4. Response Format

Every action returns:

```json
{
  "ts": "<iso-utc>",
  "action": "<name>",
  "ok": true,
  "result": { ... },
  "error": null,
  "dry_run": false
}
```

Agents branch on `ok`; failures never raise for normal control flow.

## 5. Safety Systems

- Action validation: type/range checks on coordinates, buttons, counts, amounts.
- Bounds enforcement: off-screen / invalid coordinates rejected (configurable).
- Emergency stop: `emergency_stop()` blocks all actions until
  `reset_emergency_stop()`; state visible via `status()`.
- Session limit: `max_actions_per_session` caps total actions.
- Timeouts: each real action runs in a worker thread with `action_timeout`;
  hung backend calls fail safely with a clear error.
- Logging: JSONL to `logs/mouse_agent.log` plus in-memory ring buffer
  (`history()`), bounded by `logging.max_history`. Logging never breaks actions.
- Dry run: `dry_run=True` validates + logs but emits no real input - used by all
  tests so the physical cursor is never touched. If `pynput` is missing at
  runtime, the controller auto-degrades to dry_run instead of crashing.

## 6. Configuration

File: `config/mouse_agent.json` (merged over built-in defaults; bad/missing file
falls back to defaults). Keys:

- `move_steps`, `move_duration`, `drag_duration` - motion smoothing.
- `click_delay`, `double_click_interval`, `inter_action_delay` - timing.
- `scroll_amount` - default scroll magnitude.
- `action_timeout` - per-action timeout (seconds).
- `safety`: `enforce_bounds`, `boundary_margin`, `use_virtual_desktop`,
  `fail_on_out_of_bounds`, `max_actions_per_session`, `emergency_stop_default`.
- `logging`: `enabled`, `path`, `max_history`.
- `screenshot`: `dir`.

## 7. Usage

```python
from core import mouse_control as mouse

r = mouse.move(500, 300)
if r["ok"]:
    mouse.click(500, 300, button="left")

mouse.drag(100, 100, 400, 400)
mouse.scroll("down", amount=5)
shot = mouse.screenshot()          # -> {"ok": True, "result": {"path": ...}}

# Or hold a controller instance:
from core.mouse_control import get_mouse_control
mc = get_mouse_control()
mc.emergency_stop()                 # halt everything
mc.reset_emergency_stop()
```

## 8. Testing

- `tests/test_mouse_agent.py` - 27 tests (all dry_run): movement, clicking,
  invalid input handling, drag/scroll, safety limits (emergency stop, session
  cap, bounds toggle), introspection, config fallback, error recovery, wrappers.
- Run: `.\.venv\Scripts\python.exe -m pytest tests/test_mouse_agent.py -v`
- Result: 27 passed. Memory suite still 10/10 (no regression).

## 9. Future Improvements

- Optional real-input integration test (opt-in, not in default CI).
- Target detection / template matching on top of `screenshot()` (would need a
  vision lib; deferred, out of current scope).
- Multi-monitor per-display addressing helpers.
- Wire convenience wrappers into `core/mouse_agent.py` once that file is writable
  (currently locked by the environment; see final report).