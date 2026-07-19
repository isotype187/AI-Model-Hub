# Nexus98 — Milestone 2: Task Workflow Design

# Implementation Divergence Notice

**Historical design specification; superseded by implementation reality.**

This document describes the originally intended Milestone 2 design. The actual
implementation diverged from this design:

- The design described a `plans.json` task-lifecycle system (task CRUD, milestone
  progress, state-machine transitions) owned by a new `workflow.py`.
- The implemented system became the `core/workflow.py` advisory execution pipeline
  (intake -> planning -> assigning -> tracking -> reviewing -> updating -> done), which
  delegates execution to `supervisor.run_task` and is in-memory/record-keeping only.
- The implemented UI became the Operations tab through `ui/views/operations_view.py`,
  a read-only live-operations view.
- `ui/views/tasks_view.py` (the "Tasks" tab described below) was not created.
- Supervisor gating changes occurred despite the original non-goal ("no changes to
  supervisor.py gating"): `core/supervisor.py` now sets `auto_execute = True` and
  wires `run_action_task` -> `request_file_operation_blocking`.


Status: DESIGN DOCUMENT ONLY (documentation only; no code changes; no new
runtime files; existing architecture files are NOT modified).

Source of truth + supporting design:
- `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md`
- `docs/CURRENT_ARCHITECTURE_MAP.md`
- `docs/PHASE8_AUTONOMY_GOVERNOR_DESIGN.md`
- `docs/NEXUS98_UI_DESIGN_SPECIFICATION.md`
- `docs/PHASE9_GUI_BEHAVIOR_SPEC.md`
- `docs/EXTENSION_POINT_MAP.md`

This document proposes a `workflow.py` module that owns the *task lifecycle* for
Nexus98 plans. It is deliberately scoped beneath the Autonomy Governor and the
Project Engine: it orchestrates state, never grants permissions or performs file
mutations on its own.

---

## 1. Executive Summary

Milestone 2 introduces a first-class **task workflow** layer that turns the
existing plan shell in `data/plans.json` into a trackable, auditable, and
UI-visible work unit. Today each plan has only `goal`, `milestones: []`, and an
empty `tasks: {}` map, with a single `status: "draft"`. There is no notion of an
individual task, no lifecycle, and no surfacing in the UI.

This milestone adds:

- A new module `workflow.py` that owns task creation, state transitions, and the
  relationship between a plan, its milestones, and its tasks.
- An expanded `plans.json` data model that nests a typed `tasks` collection and
  richer `milestones` under each plan.
- Clear boundaries with the **Autonomy Governor** (`core/autonomy/*`) and the
  **Project Engine** (`core/project_engine.py`): `workflow.py` may *request*
  actions through those authorities but never bypass them.
- A new **Tasks** UI tab (read-mostly, request-only) that renders plans/tasks and
  submits Governor-gated requests.

Non-goals for Milestone 2: no new autonomy levels, no new trusted workflows, no
direct file writes from `workflow.py`, no changes to `supervisor.py` gating.

---

## 2. Current Architecture References

The design reuses (does not replace) existing seams documented in
`docs/CURRENT_ARCHITECTURE_MAP.md` and `docs/PHASE8_AUTONOMY_GOVERNOR_DESIGN.md`.

- **Plan store:** `data/plans.json` — a JSON object keyed by `plan_id`. Current
  per-plan shape:
  - `plan_id`, `goal`, `milestones: []`, `tasks: {}`, `status`, `created_at`,
    `updated_at`.
- **Autonomy Governor** (`core/autonomy/governor.py`): the *sole* writer of
  autonomy state. Clients only `request_level_change(...)`. A `snapshot()`
  read API exists for observability.
- **Autonomy levels** (`core/autonomy/levels.py`): L0 (manual) … L4 (experimental).
  L2 `TRUSTED_WORKFLOWS` = `{vscode_task_send}`. No task-workflow is trusted yet.
- **Policies** (`core/autonomy/policies.py`): approval/scope engine (decides
  only).
- **Audit** (`core/autonomy/audit.py`): append-only log of every request,
  decision, and level transition.
- **Project Engine** (`core/project_engine.py`): the file-mutation authority via
  `create_request -> approve_request -> execute_operation`. Every write routes
  through it (L1 requires human approval).
- **Supervisor** (`core/supervisor.py`): owns `auto_execute` hard floor; exposes
  `build_task_plan`, `validate_task_plan`, `convert_plan_to_proposals`,
  `create_vscode_task`, `run_action_task`. This is the closest existing analogue
  to "plan -> proposal" translation, and `workflow.py` should reuse (not fork) it.
- **VS Code bridge** (`api/vscode_bridge.py`, `bridge/vscode_listener.py`,
  `integrations/vscode_connector.py`): the proven request-only client / server
  authority split that the Governor and (proposed) `workflow.py` should mirror.
- **UI shell** (`ui/main_window.py`): tabbed Tkinter shell with `add_tab(title)`
  and per-view `build(...)` functions under `ui/views/`. The Autonomy tab is
  *strictly read-only* and calls only `ui.autonomy_dashboard.snapshot()`.

---

## 3. Proposed `workflow.py` Responsibilities

`workflow.py` is a **state + orchestration** module. It must not write files,
flip `auto_execute`, or call the Governor's apply path directly.

Responsibilities:
- **Plan access (read/write of `plans.json` only via a persistence helper):**
  load plans, get a plan, list plans, save a plan. All writes are to
  `data/plans.json`; no other filesystem mutation.
- **Task CRUD:** create, update, close, and reassign tasks inside a plan's
  `tasks` map; maintain `updated_at` on the parent plan.
- **Milestone management:** add/reorder/complete milestones; derive milestone
  progress from its member tasks.
- **State machine enforcement:** validate and apply task lifecycle transitions
  (see Section 4); reject illegal transitions.
- **Proposal translation (delegated):** when a task is ready to execute, call
  `supervisor.build_task_plan` / `convert_plan_to_proposals` to produce
  Governor/Project-Engine-shaped requests. `workflow.py` does not execute them.
- **Governor requests (delegated):** for any action that needs elevated
  autonomy, emit a `governor.request_level_change(...)` request with scope +
  justification; never apply the change itself.
- **Audit emission:** append structured events to `core/autonomy/audit.py` for
  every transition it performs (mirroring the Governor's audit discipline).
- **Read APIs for UI:** `get_task_board(plan_id)`, `list_active_tasks()`,
  `get_plan_summary(plan_id)` returning plain serializable dicts.

Anti-responsibilities (explicitly NOT in `workflow.py`):
- Does not set `supervisor.auto_execute` or `autonomy_level`.
- Does not call `project_engine.execute_operation` directly (it builds requests
  that the Project Engine approves/executes).
- Does not own autonomy promotion policy (that is `policies.py`).
- Does not perform Git operations or recovery (external Guardian seam).

---

## 4. Task Lifecycle States

A task lives inside a plan's `tasks` map. Proposed state enum:

| State | Meaning | Allowed next |
|-------|---------|--------------|
| `backlog` | Created, not yet scheduled | `ready`, `cancelled` |
| `ready` | Eligible to start (deps met) | `in_progress`, `cancelled` |
| `in_progress` | Actively being worked / proposed | `blocked`, `review`, `cancelled` |
| `blocked` | Waiting on dependency / external | `ready`, `cancelled` |
| `review` | Work proposed; awaiting Governor/Project-Engine approval | `in_progress`, `done`, `cancelled` |
| `done` | Verified complete | (terminal) |
| `cancelled` | Abandoned; terminal | (terminal) |

Transition rules:
- Transitions are validated by `workflow.py`; illegal moves raise/return an error
  without mutating state.
- Moving `in_progress -> review` constructs a proposal via the supervisor and
  submits it, but does NOT flip `done`.
- `done` is only reachable from `review` after the Project Engine reports a
  successful, approved execution and (optionally) a verification step passes.
- A milestone is `complete` when all member tasks are `done`.

---

## 5. Data Model Changes for `plans.json`

Backward-compatible extension. Existing keys (`plan_id`, `goal`, `status`,
`created_at`, `updated_at`) are preserved. `milestones` and `tasks` gain richer
shapes.

Plan-level additions:
- `status` gains values beyond `draft`: `active`, `on_hold`, `completed`,
  `archived`. (Existing `draft` plans remain valid.)
- `owner`, `tags`, `priority` (optional, UI hints only).

`milestones` (was `[]`): array of objects:
```
{
  "milestone_id": "m_01",
  "title": "Scaffold workflow module",
  "description": "...",
  "task_ids": ["t_abc"],
  "status": "open|in_progress|complete",
  "target_date": "2026-08-01"
}
```

`tasks` (was `{}`): map keyed by `task_id`:
```
{
  "t_abc": {
    "task_id": "t_abc",
    "title": "Add task state machine to workflow.py",
    "description": "...",
    "state": "ready",            # one of Section 4
    "priority": "high|med|low",
    "milestone_id": "m_01",      # optional
    "depends_on": ["t_xyz"],     # task_ids; gates ready
    "assigned_to": "vscode_task_send",  # trusted workflow hint
    "created_at": "...",
    "updated_at": "...",
    "completed_at": null,
    "proposal_ref": null,        # id from supervisor/Project Engine
    "audit_refs": []             # autonomy audit log ids
  }
}
```

Migration notes:
- Old `status: "draft"` plans with empty `tasks` keep working; `get_task_board`
  treats an empty `tasks` map as zero tasks.
- No rename of top-level keys. No removal of fields. This keeps the change
  non-breaking for any reader that currently only inspects `goal`/`status`.

---

## 6. Supervisor / Governor Integration Boundaries

`workflow.py` sits *beneath* both authorities and composes with them:

- **Governor boundary (request-only):**
  - `workflow.py` calls `governor.request_level_change(target, scope,
    justification)` when a task needs more autonomy than the current level grants.
  - It reads live posture only via `governor`/snapshot read APIs (same pattern as
    `autonomy_view.build` -> `ui.autonomy_dashboard.snapshot()`).
  - It NEVER imports or mutates `supervisor.auto_execute` or
    `system_config.json`'s `autonomy_level`.
  - Any new task workflow (e.g. a future `task_execute` trusted workflow) must be
    added to `levels.py` `TRUSTED_WORKFLOWS` through a separate, Governor-owned
    promotion — not hardcoded in `workflow.py`.

- **Supervisor boundary (translate-only):**
  - Reuse `supervisor.build_task_plan` / `validate_task_plan` /
    `convert_plan_to_proposals` to turn a task into a proposal. Do not reimplement
    plan parsing.
  - `create_vscode_task` remains the model for how a task hands off to the trusted
    `vscode_task_send` workflow.

- **Project Engine boundary (delegate writes):**
  - Execution of any file mutation goes through
    `project_engine.create_request -> approve_request -> execute_operation`.
  - At L1 these require human approval; `workflow.py` surfaces the pending request
    but does not approve it.

- **Audit boundary:** every transition and request from `workflow.py` is recorded
  via `core/autonomy/audit.py`, referencing the resulting proposal/request id so
  the Tasks UI and audit view stay consistent.

Invariant (mirrors the Governor UI rule): *`workflow.py` requests, authorities
act.* No code path in `workflow.py` flips `auto_execute`, writes
`system_config.json`, or calls `project_engine.execute_operation` directly.

---

## 7. Tasks UI Tab Design

A new tab registered in `ui/main_window.py` via `add_tab("Tasks")` and a new
`ui/views/tasks_view.py` `build(...)`. It follows the established read-mostly,
request-only discipline of `autonomy_view.py`.

Layout:
- **Left pane — Plan list:** selectable plans (goal + status badge), with
  create/duplicate/archive actions that call `workflow.py` persistence helpers.
- **Center pane — Task board:** columns per state (`backlog`, `ready`,
  `in_progress`, `blocked`, `review`, `done`). Each card shows title, priority,
  milestone, assignee, dependency indicators.
- **Right pane — Detail/inspector:** selected task's description, deps,
  proposal_ref, audit refs, and a state-transition control.
- **Bottom strip — Autonomy posture:** read-only snapshot of current level +
  `auto_execute` (reuses `ui.autonomy_dashboard.snapshot()`), plus a disabled
  "Request elevation" button that becomes enabled only when the selected task
  needs a higher level and the user supplies justification.

Behavior rules:
- The tab reads via `workflow.py` read APIs; it performs no writes to
  `plans.json`, `system_config.json`, or `supervisor.py`.
- State transitions in the UI call `workflow.py` transition functions, which
  enforce Section 4 and emit audit events.
- "Request elevation" submits a `governor.request_level_change(...)`; the button
  reflects pending/approved state but never applies a change.
- "Execute task" (when `in_progress -> review`) builds a proposal via the
  supervisor and submits it through the Project Engine request flow; at L1 it
  shows "awaiting approval."
- Semantic status colors follow the UI spec: OK green / warn amber / error-stop
  red.

---

## 8. Implementation Phases

Phase 0 — Checkpoint (per handoff Development Rule): snapshot
`checkpoints/NEXUS98_BEFORE_MILESTONE2_TASKWORKFLOW_*` + `MANIFEST.txt`.

Phase 1 — Data model: extend `plans.json` reader/writer in `workflow.py` to
support the richer `milestones`/`tasks` shapes; add a tolerant loader that keeps
legacy `draft` plans valid. No UI yet.

Phase 2 — State machine: implement task CRUD + transition validation (Section 4)
with audit emission to `core/autonomy/audit.py`.

Phase 3 — Supervisor integration: wire `build_task_plan` /
`convert_plan_to_proposals` so a task can produce a Project-Engine-shaped
request; keep it request-only.

Phase 4 — Governor seam: add `request_level_change` calls for tasks needing
elevation; read posture via snapshot only.

Phase 5 — Tasks UI tab: add `ui/views/tasks_view.py` and register the tab in
`ui/main_window.py`; read-mostly, request-only, matching `autonomy_view` style.

Phase 6 — Validate: import smoke + workflow unit tests (transition legality,
backward-compatible load) under the approved `TMPDIR` redirect; manual click-through
of the Tasks tab at L1 and L2.

---

## 9. Risks and Rollback Considerations

Risks:
- **`plans.json` corruption:** richer schema written by a partial run could
  break existing readers. Mitigation: atomic write (temp file + rename) and a
  pre-write backup under `backups/`; loader tolerates legacy shape.
- **Authority creep:** `workflow.py` accidentally calling `execute_operation` or
  flipping `auto_execute`. Mitigation: code review gate + the Section 6 invariant;
  keep `workflow.py` free of `supervisor.auto_execute` writes and
  `project_engine.execute_operation` calls.
- **UI over-privilege:** Tasks tab performing writes. Mitigation: mirror the
  `autonomy_view` strictly-read-only contract for all authority interactions.
- **Governor bypass:** hardcoding a trusted workflow in `workflow.py`. Mitigation:
  trusted-workflow membership stays owned by `levels.py` via separate promotion.

Rollback:
- Dependency: pre-promotion checkpoint from Phase 0.
- `plans.json` rollback: restore from `backups/` snapshot; legacy `draft` plans
  are unaffected by the schema addition, so a partial rollback only loses new
  task/milestone detail, never existing plan goals/status.
- UI rollback: remove the Tasks tab registration from `ui/main_window.py` and the
  `tasks_view.py` module; does not affect other tabs.
- Autonomy rollback: any elevation request tied to a task is itself a Governor
  request; rejecting/cancelling it reverts posture with no `auto_execute` change,
  consistent with the Governor's soft-stop behavior.
- Trigger: if validation fails, an audit rule trips, or the checkpoint write
  fails, follow the Governor auto-downgrade pattern (fall back to L1 propose +
  human approve) and open a rollback record.

---

## Appendix A — Proposed File/Module Additions (design only)

- `workflow.py` (new module; state + orchestration only)
- `ui/views/tasks_view.py` (new; read-mostly UI)
- `ui/main_window.py` tab registration for "Tasks" (additive)

No existing architecture files are modified by this milestone's design.

