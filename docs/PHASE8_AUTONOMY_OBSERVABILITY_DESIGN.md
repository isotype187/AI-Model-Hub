# Phase 8 - Autonomy Observability Dashboard (Design Summary)

Status: DESIGN / PENDING APPROVAL (no source changes yet)
Milestone: Phase 8 - Autonomy Observability
Checkpoint: checkpoints/NEXUS98_BEFORE_PHASE8_OBSERVABILITY_20260717_225554

## 1. Objective

Provide a strictly READ-ONLY observability surface over the Autonomy Governor
so an operator can see the complete live autonomy posture at a glance, without
any ability to mutate autonomy state from this surface.

This milestone adds *observation*, not *control*. The existing request-only
control panel (ui/autonomy_panel.py) is untouched. The new surface never
promotes, never writes supervisor.auto_execute, never writes system_config,
and never triggers emergency_stop.

## 2. Hard Invariants (carried from Governor design)

- Read-only UI surface only. No mutation entry points on this surface.
- No new permissions. No L3 expansion. No workflow-set changes.
- No direct writes to autonomy state (no `auto_execute =`, no config writes).
- Governor remains the sole authority and sole writer of autonomy state.
- All safety gates in system_config.json remain as-is.

## 3. Exposed Fields (dashboard contract)

The dashboard renders a single read-only snapshot dict with these keys:

| Field                  | Source (read-only)                                             |
|------------------------|----------------------------------------------------------------|
| current_level          | governor.current_level() (+ levels.level_name)                 |
| active_workflows       | levels.allowed_workflows(current_level) (auto-exec eligible)   |
| pending_requests       | audit.requests() filtered to request_level_change w/o apply    |
| approval_history       | audit.requests() filtered to approved/rejected decisions       |
| audit_events           | audit.requests() (most-recent-N, newest first)                 |
| last_checkpoint        | newest dir under checkpoints/ (name + mtime, read-only scan)   |
| rollback_available     | derived: a checkpoint exists AND supervisor/config readable    |
| emergency_stop_status  | derived from audit (last emergency_stop) + live consistency    |

Notes on derivations (all read-only, no state change):
- pending vs. resolved is computed by correlating request_id across
  `request_level_change` and `apply_level_change` / `apply_level_change_failed`
  / rejected records already present in the audit log.
- emergency_stop_status reports: last emergency_stop event (if any), whether
  auto_execute is currently False, and whether current_level()==0 is
  consistent. It NEVER invokes emergency_stop.

## 4. Placement / Module Plan (proposed, not yet implemented)

- New module: `ui/autonomy_dashboard.py`
  - Pure read + assemble. Imports core.autonomy.{governor,levels,audit}.
  - Public: `snapshot() -> dict`, plus small read helpers per field.
  - Contains NO `auto_execute =`, NO `open(CONFIG_PATH, "w")`, NO governor
    mutation calls (request_level_change / emergency_stop are NOT called).
  - `__main__` demo prints the snapshot only.
- No changes to governor.py, levels.py, policies.py, audit.py.
- No changes to ui/autonomy_panel.py (control panel stays separate).
- Optional (deferred, only if approved): a read-only tab wired into
  ui/main_window.py. Not part of this milestone's core scope.

## 5. Architecture Fit

- Reuses existing read-only accessors: governor.current_level(),
  levels.allowed_workflows(), audit.requests(). No new I/O patterns.
- Mirrors the read-only discipline already proven in ui/autonomy_panel.py
  (which separates read accessors from the single request entry point); the
  dashboard simply drops the request entry point entirely.
- Checkpoint discovery uses the existing checkpoints/ convention
  (NEXUS98_BEFORE_<PHASE>_<desc>_<timestamp>) via a read-only directory scan.
- Audit correlation uses request_id fields the Governor already writes.

## 6. Explicit Non-Goals

- No promotion / demotion controls.
- No emergency-stop trigger control.
- No L3/L4 workflow additions.
- No changes to safety gates or permissions.
- No background writers, schedulers, or daemons.

## 7. Validation Plan (post-approval)

1. Static guard: assert the new module contains no `auto_execute =`,
   no config write, and no governor mutation calls.
2. Functional: snapshot() returns all 8 required keys with correct types.
3. Non-mutation: run snapshot() and confirm supervisor.py + system_config.json
   byte-for-byte unchanged.
4. Safety gates unchanged after render.

## 8. Approval Gate

Implementation of ui/autonomy_dashboard.py will NOT begin until explicit
approval is given. This document + the checkpoint + the architecture-fit
check constitute the pre-implementation deliverables.
