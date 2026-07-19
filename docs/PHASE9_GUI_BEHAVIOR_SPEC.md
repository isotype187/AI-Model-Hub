# Phase 9 - Nexus98 GUI Behavior Specification (DESIGN FREEZE)

Status: DESIGN FREEZE / SPECIFICATION (no implementation)
Purpose: Capture the owner's desired Nexus98 GUI design and behavior before any
further UI implementation. This document is the reference contract for future
Phase 9+ UI work. It changes no source, config, or tests.

Baseline: The current implementation (Phase 9 Step 2 "Command Center shell")
already provides a themed ttk.Notebook with tabs Dashboard, Models, Supervisor,
Agents, Bridge, Autonomy, Logs/System. This spec formalizes intended behavior;
where the spec exceeds today's build, those items are FUTURE and must follow the
usual checkpoint -> implement -> validate -> test flow.

---

## 1. Overall Application Identity

### 1.1 What Nexus98 should feel like
- A calm, professional "command center" for an autonomy-governed AI workstation.
- Trustworthy and legible: the operator should always know the current autonomy
  posture, what is running, and what is safe to do.
- Fast and quiet: no gratuitous motion, no surprising state changes. The UI
  observes and requests; it never silently mutates governed state.
- Dense but not cluttered: information-rich panels with clear hierarchy.

### 1.2 Intended user experience
- Single operator ("owner") on a local Windows machine.
- Open the app, land on an overview, glance at health + autonomy, then drill into
  a specific area (Models, Supervisor, Bridge, Autonomy).
- Every state-changing action is explicit, confirmed where risky, and audited.
- The UI degrades gracefully when a backend (bridge/Ollama) is offline.

### 1.3 Primary use cases
- Observe system health and autonomy level at a glance (Dashboard).
- Browse/inspect available models (Models).
- Run and monitor supervisor tasks (Supervisor).
- View registered agents and their status (Agents).
- Control the VSCode bridge on/off and see connectivity (Bridge).
- Observe autonomy state read-only; request governed changes only via approved,
  human-in-the-loop flows (Autonomy).
- Review logs and environment/system diagnostics (Logs/System).

---

## 2. Main Window Behavior

### 2.1 Startup behavior
- Launch via `main.py` -> `ui.main_window.launch_ui()` (stable entry contract).
- Apply the Command Center ttk theme immediately; window titled
  "Nexus98 Command Center".
- Build the navigation shell, then perform an initial read-only refresh of the
  landing view. No autonomy mutation occurs at startup.
- Crash safety: startup errors are logged (logs/startup_crash.log) and surfaced.

### 2.2 Default landing page
- Dashboard is the default tab on launch.
- Dashboard shows an at-a-glance, read-only overview (see 3.1).

### 2.3 Navigation style
- Top tabbed navigation (ttk.Notebook) with 7 tabs in fixed order:
  Dashboard, Models, Supervisor, Agents, Bridge, Autonomy, Logs/System.
- Tabs are always visible; selecting a tab reveals its panel. No hidden routes.
- FUTURE (optional): a left sidebar variant may replace top tabs, but tab order
  and names must be preserved.

### 2.4 Window resizing behavior
- Default geometry 1600x950; window is resizable.
- Content areas expand/fill; primary text/list panels grow with the window,
  fixed-width controls (e.g., bridge toggle) keep their size.
- Minimum usable size should keep the active panel's primary content visible.

### 2.5 Panels, tabs, sidebars, status areas
- Title bar: app name + short subtitle ("Autonomy-governed workstation").
- Tab strip: the primary navigation.
- Per-tab content region.
- Status area (FUTURE): a persistent bottom strip showing autonomy level, bridge
  online/enabled, and last-refresh time. Until then, per-tab summaries carry this.

---

## 3. Major UI Areas

For each area: Purpose, Information displayed, User actions, Refresh behavior,
Error states.

### 3.1 Dashboard
- Purpose: read-only situational overview / landing.
- Information: autonomy level + name, active workflows, emergency-stop engaged
  flag, pending-request count (all via `autonomy_dashboard.snapshot()`); bridge
  online/enabled; agent count; catalog (model) count.
- User actions: "Refresh Overview" (read-only). No mutation.
- Refresh: manual on demand; FUTURE optional timed auto-refresh (read-only poll).
- Error states: any failing source degrades to a placeholder value; the panel
  never crashes. Show "(unavailable)" rather than raising.

### 3.2 Models
- Purpose: browse, search, and inspect models.
- Information: searchable model list (from catalog + recommender), and a detail
  inspector for the selected model (via inspector + display formatting).
- User actions: type to search/filter; select a model to inspect; Refresh to
  re-sync the catalog.
- Refresh: search box triggers a coordinated refresh; explicit Refresh button
  re-syncs catalog and repopulates the list.
- Error states: empty/failed catalog shows an empty list and a neutral message;
  inspection failure shows a readable error in the inspector rather than crashing.

### 3.3 Supervisor
- Purpose: submit and monitor supervisor tasks.
- Information: task input box; streaming status/output log ("[STATUS] ..." then
  "RESULT: ...").
- User actions: enter a task; "Run Supervisor Task"; Refresh; Tray Mode.
- Refresh: task execution runs on a background thread and marshals UI updates via
  `app.after(0, ...)`; the console remains responsive.
- Error states: run failures are printed to the output log; the UI thread is
  never blocked. Preserve the existing threaded behavior exactly.

### 3.4 Agents
- Purpose: view registered agents and their status.
- Information: per-agent name, type, status, description (from agent registry).
- User actions: read-only view; refreshed as part of the coordinated refresh.
- Refresh: repopulated on global Refresh and on search-driven refresh.
- Error states: empty registry shows an empty panel; lookup failure shows a
  neutral message.

### 3.5 Bridge
- Purpose: control and observe the VSCode bridge.
- Information: online/enabled status text; a vertical toggle indicator
  (green=ON/top, red=OFF/bottom).
- User actions: click the toggle to enable/disable the bridge.
- Refresh: toggling runs enable/disable on a background thread, then re-polls
  status via `app.after(500, ...)`; status also polled on load.
- Error states: unreachable bridge falls back to online=False/enabled=False (safe
  default) without error dialogs.

### 3.6 Autonomy (STRICTLY READ-ONLY)
- Purpose: observe autonomy posture. This tab NEVER mutates governed state.
- Information (from `autonomy_dashboard.snapshot()` only): current level + name,
  auto_execute + config intent, active workflows, pending requests, approval
  history, recent audit events (newest first), last checkpoint, rollback
  availability, emergency-stop status.
- User actions: "Refresh Autonomy Dashboard" (read-only) only.
- Refresh: manual on demand; FUTURE optional timed read-only poll of snapshot().
- Error states: if snapshot() fails, show
  "Autonomy dashboard unavailable (read-only): <error>"; never raise, never
  fall back to a mutating path.
- Hard rule: no Governor imports, no request_level_change(), no emergency_stop(),
  no writes to config/system_config.json or core/supervisor.py from this tab.

### 3.7 Logs/System
- Purpose: read-only diagnostics.
- Information: environment summary (python version, platform, cwd) and a tail of
  the startup log.
- User actions: Refresh (read-only).
- Refresh: manual re-read on demand.
- Error states: missing/unreadable log shows a neutral placeholder; files are
  opened read-only.

---

## 4. Visual Design

### 4.1 Theme
- Dark "command-center" aesthetic, built on ttk (clam base) for cross-platform
  color control. No external UI toolkits or dependencies.

### 4.2 Colors (palette reference; may be refined, not expanded arbitrarily)
- Background: #1e1e2e; alt/card: #26263a.
- Foreground text: #e6e6f0; muted: #9aa0b5.
- Accent (primary): #5b8def.
- Semantic: OK #3ecf8e, Warn #e5c07b, Error #e06c75.

### 4.3 Density
- Comfortable-dense: generous tab padding, moderate control padding (~6px),
  16px content margins. Prioritize scanability over maximal compactness.

### 4.4 Icons
- Minimal. Text-first labels for clarity. FUTURE: small monochrome glyphs for
  tab affordances and status; icons must never be the sole status signal (pair
  with text/color).

### 4.5 Typography
- UI: Segoe UI (10pt); titles Segoe UI Semibold (18pt); headers (12pt).
- Monospace for logs/audit/inspector: Consolas (10pt).

### 4.6 Status indicators
- Autonomy level, bridge state, and emergency-stop shown as text + color.
- Use semantic colors consistently (green OK, amber warn, red error/stop).
- Emergency-stop engaged must be unmistakable (red + explicit label).

### 4.7 Animations
- None required. Motion, if ever added, is limited to subtle state transitions
  (e.g., toggle slider) and must be non-blocking and disable-able. No spinners
  that imply background mutation of governed state.

---

## 5. Interaction Rules

### 5.1 Buttons
- Clear verb labels ("Refresh", "Run Supervisor Task"). Primary actions may use
  the accent style; destructive/governed actions are visually distinct.
- Read-only refresh buttons never imply mutation.

### 5.2 Toggles
- Bridge toggle is a direct on/off control with immediate visual feedback and a
  background status re-poll. State reflects the backend after confirmation.

### 5.3 Sliders
- Not used for autonomy level selection in passive views. Any future autonomy
  level selector is a discrete, labeled control behind an approval flow (never a
  free-drag slider that could imply instant promotion).

### 5.4 Notifications
- Inline, non-modal status text is preferred (e.g., supervisor output log,
  bridge status line). Avoid intrusive popups for routine events.

### 5.5 Confirmations
- Required for any state-changing or potentially disruptive action (e.g., bridge
  disable while in use, and all autonomy changes). Confirmations state exactly
  what will change.

### 5.6 Approval dialogs
- Any autonomy promotion/change requires an explicit human approval dialog that:
  captures approver identity/intent, shows current -> target level and the
  requested workflow set, and confirms a pre-promotion checkpoint exists.
- Approval dialogs submit through the Governor's request path only; they never
  write autonomy state directly.

---

## 6. Autonomy UI Rules (INVARIANTS - must be preserved)

### 6.1 Governor authority
- The Autonomy Governor (core.autonomy.governor) is the sole authority and sole
  writer of autonomy state (supervisor.auto_execute + config intent). The UI
  must never write these directly.

### 6.2 Read-only dashboard behavior
- All passive autonomy displays (Autonomy tab, Dashboard overview) read ONLY via
  `ui.autonomy_dashboard.snapshot()`. No Governor imports in observability views.
- No `request_level_change()`, no `emergency_stop()`, no `auto_execute =`
  assignment, and no write-mode file access in any observability view.

### 6.3 Approval boundaries
- Level changes require: human approval (identity/intent captured), a valid
  target within the allowed workflow set, and a pre-promotion checkpoint.
- Any control surface (FUTURE, separate tab) that can submit a request must route
  exclusively through the Governor and be gated by an explicit approval dialog.
- No new autonomy levels, no workflow expansion, and no new permissions may be
  introduced by the UI.

---

## 7. Scope Boundaries (for future implementation)

- Do not replace Tkinter or add dependencies.
- Do not change backend APIs.
- Do not modify config/system_config.json, core/supervisor.py, or
  core/autonomy/* from the UI.
- Preserve the launch_ui() entry contract and existing view behavior.
- Preserve vscode_task_send Level 2 state; do not add levels or workflows.

This specification is frozen as the design reference. Any deviation requires an
explicit owner decision and a new checkpointed, validated implementation step.
