# Phase 9 - Nexus98 UI Overhaul Plan

Status: ANALYSIS + PLAN (no source/config/test changes)
Scope: Read-only architectural analysis of the current UI, plus a proposed
Phase 9 overhaul. This document changes nothing at runtime.

---

## 1. Current UI Framework and Entry Points

- Framework: Tkinter (standard library) with a single `ttk` widget in use
  (`ttk.Notebook`, added in Phase 8). No external UI toolkit (no Qt, no web).
- System tray: `pystray` via `core/tray.py` (`run_tray`, background thread).
- Primary entry point: `main.py` -> `from ui.main_window import launch_ui;
  launch_ui()` (wrapped in a crash logger writing to `logs/startup_crash.log`).
- Secondary entry point: `debug_launch.py` -> `launch_ui()` (dev harness).
- The entire UI is constructed imperatively inside one function,
  `ui/main_window.py::launch_ui()`, which ends with `app.mainloop()`.

Observations:
- There is no window/class abstraction; all widgets and closures live in
  `launch_ui()`'s local scope (nonlocal state for `catalog_cache`,
  `selected_model`, `bridge_enabled`).
- Window title is still "AI Model Hub - Command Center", geometry 1600x950 -
  legacy branding from the pre-Nexus98 model hub.

---

## 2. Existing Tabs / Views / Widgets

Layout is a three-column `tk.Frame` split packed into a root `main` frame:

- Left column (`left`, width 300) - Model browser:
  - `search_label` + `search` (Entry, `search_var` with trace -> refresh)
  - `listbox` (Listbox of catalog model names; `<<ListboxSelect>>` -> `on_select`)
- Center column (`center`, expand) - Inspector + Supervisor console:
  - `status` (Label "Ready")
  - `inspector` (Text, height 25; shows `format_model(...)`)
  - `task_label` + `task_box` (Text; supervisor task input)
  - `output` (Text; run log)
  - Buttons: "Run Supervisor Task", "Refresh", "Tray Mode"
- Right column (`right`, width 500) - Agents, Bridge, Autonomy:
  - `agents` (Text; rendered from `list_agents()`)
  - `bridge_frame` (LabelFrame "Bridge Control") with a custom vertical
    `switch_canvas` toggle + `bridge_status` Label
  - Phase 8 addition: `autonomy_notebook` (`ttk.Notebook`) with a single
    read-only "Autonomy Dashboard" tab (`autonomy_view` Text, disabled) and a
    "Refresh Autonomy Dashboard" button.

Only one true tabbed surface exists today: the Phase 8 autonomy notebook. All
other views are directly packed frames.

---

## 3. main_window.py Structure

Single function `launch_ui()` (~590 lines) containing:

- Imports: `tkinter`, `ttk`, `threading`, plus `core.*` data providers and
  `ui.autonomy_dashboard` (read-only).
- Root/window setup + three-column frames.
- Left/center/right widget construction (inline).
- Nested closures (share `launch_ui` scope via `nonlocal`):
  - `execute_task` / `worker` / `status_update` - supervisor run (threaded)
  - `draw_toggle`, `refresh_bridge_status`, `bridge_toggle_worker`,
    `toggle_bridge` - bridge control
  - `_format_autonomy_snapshot`, `refresh_autonomy_dashboard` - Phase 8
    read-only dashboard rendering (calls only `autonomy_dashboard.snapshot()`)
  - `refresh_agents`, `refresh`, `on_select` - catalog/agents refresh + select
- Event wiring: listbox select, search trace, button commands.
- Terminates with `refresh()` then `app.mainloop()`.

Key structural risks:
- Monolithic function; no separation of view construction, state, and data
  access. Hard to test, extend, or theme.
- Threading uses `app.after(0, lambda: ...)` marshaling - correct pattern, but
  scattered and duplicated.
- Legacy `main_window_BEFORE_STATUS.py` remains as a stale sibling.

---

## 4. Available Backend Data Sources

### autonomy_dashboard (ui/autonomy_dashboard.py) - READ-ONLY
- `snapshot(audit_limit=50) -> dict` (the single integration surface used by UI)
- Field helpers: `current_autonomy_level`, `active_workflows`,
  `pending_requests`, `approval_history`, `audit_events`, `last_checkpoint`,
  `rollback_available`, `emergency_stop_status`.
- Contract: no writes, no Governor mutation. This is the correct source for all
  observability views.

### autonomy_panel (ui/autonomy_panel.py) - REQUEST-CAPABLE
- Read accessors: `current_level`, `current_auto_execute`,
  `config_intent_level`, `checkpoint_status`, `audit_history`, `render`.
- Mutation-capable: `submit_level_request(...)` -> `governor.request_level_change`.
- Use only behind explicit human-approval controls; NOT for passive display.

### governor (core/autonomy/governor.py) - SOLE AUTONOMY AUTHORITY
- `current_level()` (read), `request_level_change(...)` (mutating),
  `emergency_stop(...)` (mutating).
- UI must never call the mutating entries except through a governed,
  human-approved control path (currently none wired in the observability tab).

### system status (core/status.py)
- `is_installed(model)`, `mark_installed(model)` - model install-state tracking.
- Note: this is model-centric, not a general system health provider. A broader
  "system status" (CPU/GPU/uptime) does not yet exist as a module.

### Ollama
- Live model/tag + chat access lives in `api/vscode_bridge.py`
  (`ollama_models()`, `ollama_chat()`, endpoint `127.0.0.1:11434`).
- A second `ollama_models()` exists in `tools/model_router.py`.
- The catalog pipeline (`core/catalog.py`: `build_catalog`, `sync_catalog`,
  `get_catalog`) is the UI's current model list source (not a direct Ollama call).

### bridge (core/bridge_controller.py)
- `get_status()` -> `{"online": bool, "enabled": bool}` (HTTP to bridge, 3s
  timeout, safe fallback), `enable_bridge()`, `disable_bridge()`,
  `start_bridge()`, `find_bridge_processes()`.

### Supporting providers
- `core/catalog.py`, `core/recommender.py` (`recommend`),
  `core/inspector.py` (`inspect_model`), `core/display.py` (`format_model`),
  `core/agent_registry.py` (`list_agents`, `get_agent_status`),
  `core/tray.py` (`run_tray`).

---

## 5. UI Components That Should Be Preserved

- Entry contract: `ui.main_window.launch_ui()` (invoked by `main.py` and
  `debug_launch.py`). Keep this callable name/signature stable.
- Supervisor task console (input + threaded run + status callback marshaling).
  The `app.after(0, ...)` threading pattern is correct and must be preserved.
- Bridge control (status polling + enable/disable) and its safe-fallback
  status contract.
- Model browser: search -> catalog -> listbox -> inspector via
  `format_model` + `inspect_model`.
- Agents panel from `list_agents()`.
- Phase 8 read-only Autonomy Dashboard integration and its hard invariant:
  observability calls ONLY `autonomy_dashboard.snapshot()`; no Governor
  mutation, no `request_level_change`, no `emergency_stop`, no writes to
  `config/system_config.json` or `core/supervisor.py`.
- Tray mode via `run_tray` on a daemon thread.

---

## 6. Proposed Phase 9 UI Overhaul Plan

Goal: modernize and modularize the UI into a coherent, themeable, tabbed
"Nexus98 Command Center" while strictly preserving autonomy safety invariants.

### 6.1 Guiding constraints (non-negotiable)
- Keep `launch_ui()` as the stable entry point (delegate internally).
- Autonomy remains observe-only in passive views; any control action must route
  through the Governor with explicit human approval (opt-in, separate tab).
- No new permissions, no workflow expansion, no writes to supervisor/config
  from the UI. Preserve `vscode_task_send` L2 state.

### 6.2 Target architecture
- Adopt a single top-level `ttk.Notebook` "Command Center" with dedicated tabs:
  1. Models - browser + inspector + recommendations (left/center merged).
  2. Supervisor - task console + run log (threaded, unchanged behavior).
  3. Agents - `list_agents()` view + status.
  4. Bridge - status + enable/disable toggle.
  5. Autonomy (read-only) - the Phase 8 dashboard, promoted to a first-class tab
     using `autonomy_dashboard.snapshot()`.
  6. System (new, optional) - health/status surface (see 6.5).
- Refactor `main_window.py` from one function into small view builders
  (e.g., `build_models_tab(parent)`, `build_bridge_tab(parent)`,
  `build_autonomy_tab(parent)`), each returning its frame + a `refresh()`
  callback. `launch_ui()` wires them into the notebook. This is a structural
  refactor with identical behavior per view.
- Introduce a light theming layer (ttk styles) and correct the window title to
  "Nexus98 Command Center".

### 6.3 Autonomy tab (Phase 9 refinement, still read-only)
- Replace the single Text blob with structured, labeled sub-panels:
  current level, active workflows, pending requests (table), approval history
  (table), audit events (scrolling list, newest-first), last checkpoint,
  rollback availability, emergency-stop status.
- Add a manual "Refresh" and optional timed auto-refresh (read-only poll of
  `snapshot()` only). No mutation controls in this tab.
- Optional, separately gated "Autonomy Control" tab (future): surfaces
  `autonomy_panel.submit_level_request` behind an explicit approval dialog.
  This is out of scope for the read-only overhaul and requires its own
  approval + checkpoint.

### 6.4 Threading + responsiveness
- Standardize a single `run_in_thread(fn, on_done)` helper that marshals back
  via `app.after`, replacing the duplicated inline patterns.
- Ensure all network calls (bridge status, Ollama) run off the UI thread.

### 6.5 New "System" tab (optional, additive)
- Aggregate read-only signals: bridge `get_status()`, Ollama reachability via a
  read-only `ollama_models()` probe, catalog counts, agent counts, and the
  autonomy level from `snapshot()`. No new writers; purely display.

### 6.6 Cleanup (non-behavioral)
- Remove/retire stale `ui/main_window_BEFORE_STATUS.py` (after confirming no
  references) in a dedicated cleanup step with a checkpoint.
- Consolidate duplicate `ollama_models()` definitions behind one read-only
  helper if a shared client is introduced.

### 6.7 Phased rollout (each step: checkpoint -> implement -> validate -> test)
1. Refactor to notebook + view-builder modules (behavior-preserving).
2. Promote Autonomy Dashboard to a first-class read-only tab (structured panels).
3. Add standardized threading helper.
4. Add optional System tab.
5. Theming + rebrand title.
6. Stale-file cleanup.

### 6.8 Validation strategy (per step)
- `launch_ui` import/compile check; static scan proving no autonomy mutation
  calls and no supervisor/config writes from the UI.
- Hash checks on `core/supervisor.py` and `config/system_config.json` before
  and after (must be unchanged).
- Full pytest suite green; add UI-logic unit tests where feasible (formatters,
  view-builder pure functions) without introducing a GUI test harness if the
  repo has none.
- Confirm `vscode_task_send` L2 state preserved after every step.

### 6.9 Risks / mitigations
- Monolith refactor risk -> do it behavior-preserving first, one view at a time.
- Accidental mutation surface creep -> keep observability tabs on
  `snapshot()` only; isolate any control surface behind a separate,
  approval-gated tab.
- Legacy branding/coupling -> rebrand and decouple `core.*` providers via view
  builders without changing their contracts.

---

## 7. Summary

The current UI is a single-function Tkinter app with a three-column layout and
one Phase 8 read-only autonomy notebook. Backend data is well-factored across
`core.*` providers, with `autonomy_dashboard.snapshot()` as the correct
read-only observability source and the Governor as the sole autonomy authority.
Phase 9 should modularize `main_window.py` into notebook tabs and view builders,
promote the autonomy dashboard to a structured first-class read-only tab, and
add optional system observability - all while preserving the entry point,
supervisor/bridge behavior, and every autonomy safety invariant.
