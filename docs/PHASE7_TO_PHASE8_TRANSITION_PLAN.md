# Phase 7 → Phase 8 Transition Plan

> **Transition plan only.** No Phase 8 implementation. No source, config, test,
> or autonomy changes. `supervisor.auto_execute` remains `False`. This document
> defines the gate between the completed Phase 7 Level 2 promotion of the
> `vscode_task_send` trusted workflow and the start of Phase 8 Autonomy Governor
> implementation (designed in `docs/PHASE8_AUTONOMY_GOVERNOR_DESIGN.md`).

## 1. Phase 7 Completion Criteria

Phase 7 is "complete" (and Phase 8 implementation may begin) only when **all**
of the following are true:

- **`vscode_task_send` successful activation:** the activation checklist
  (`docs/PHASE7_LEVEL2_ACTIVATION_CHECKLIST.md`) Section 3 executed with
  explicit human sign-off — `supervisor.auto_execute = True` set via the approved
  procedure, **only** for the trusted `vscode_task_send` workflow set.
- **Monitored first Level 2 execution:** the first run was monitored per
  checklist Section 4; **no** stop condition fired (no out-of-gate write, no
  unexpected flag change, no test failure, no out-of-vocabulary task, no runtime
  error).
- **Validation results:** checklist Section 5 passed — required suite green
  (import-smoke + vscode bridge/config/connection, via the approved `TMPDIR`
  redirect), each `write_file` produced a `backup_file` and passed
  `validate_file`, and a `history/operations/<operation_id>` record exists and is
  auditable.
- **Audit review:** the Section 5 change review confirmed `git diff` / checkpoint
  comparison shows **only** the intended, task-scoped file writes — nothing
  outside the allowed scope. Logs (`logs/supervisor.log`,
  `logs/vscode_bridge.log`, `history/operations/*.json`) inspected and clean.
- **Rollback verification:** the rollback path was confirmed reachable and retained
  — the pre-promotion checkpoint
  `checkpoints/NEXUS98_BEFORE_PHASE7_VSCODE_WF_<...>/` and all
  `history/operations/` records are preserved; a dry rollback (or rehearsal,
  per `docs/PHASE7_LEVEL2_PROMOTION_REHEARSAL_REPORT.md`) succeeded.

> Gate: if any criterion is unmet, stay in Phase 7; do **not** start Phase 8
> implementation.

## 2. Phase 8 Implementation Prerequisites

- **Lessons learned from the first Level 2 workflow:**
  - A single, constrained, already-tested workflow is the safest promotion unit.
  - The `TMPDIR` redirect (per `PROJECT_STATE.md`) is required for a
    reproducible green test run; bake it into every validation invocation.
  - Explicit human sign-off + pre-promotion checkpoint + monitored first run is a
    pattern worth reusing as code (the Governor's promotion rule).
  - `supervisor.auto_execute` as the hard floor worked; the Governor must keep
    this exact boundary.
- **Required changes before Autonomy Governor implementation:**
  - None to `supervisor` safety semantics — the Governor **wraps** `auto_execute`
    and `system_config.json`; it does not alter the floor.
  - No new dependencies; `core/autonomy/` is pure Python reusing `history/`,
    `checkpoints/`, and the existing logging pattern.
  - The UI must be extended request-only (no direct `auto_execute` write).
- **Migration considerations:**
  - The live Phase 7 `vscode_task_send` L2 promotion becomes the Governor's
    **first governed workflow** — port its scope + approval into `levels.py` /
    `policies.py`; do not regress it to L1.
  - Existing `history/operations/` and `checkpoints/` need **no data migration**;
    the Governor's `audit.py` appends to the same trail.
  - Keep `autonomy_level` in `system_config.json` as intent; runtime truth stays
    with the Governor (treat stricter value as correct on read, per
    `docs/CONFIG_AUTHORITY.md` §6).

## 3. Recommended Implementation Order

1. **`core/autonomy/levels.py`** — declaritive L0–L4 definitions, permission
   sets, and the trusted-workflow allow-lists (seed with `vscode_task_send`).
2. **`core/autonomy/audit.py`** — append-only audit log reusing `history/`.
3. **`core/autonomy/policies.py`** — approval + scope engine; port the Phase 7
   promotion checklist into the L1→L2 rule.
4. **`core/autonomy/governor.py`** — wraps `supervisor.auto_execute` +
   `system_config.json`; the **sole** writer of autonomy state.
5. **UI control panel** — request-only interface in `ui/main_window.py`
   (level dial, current state, requested promotion, approval, checkpoint status,
   rollback availability, audit history). No direct grant.
6. **Phase 7 workflow migration** — move the live `vscode_task_send` L2
   promotion under the Governor; then expand to L3 workflows one at a time; add
   L4 only as an explicit experimental toggle.

## 4. Explicit Non-Goals

- **No broad autonomy:** the Governor governs scoped, pre-approved workflows; it
  does not open unrestricted autonomous operation.
- **No unrestricted file access:** every write still routes through the Project
  Engine gated path (`create_request` → `approve_request` → `execute_operation`
  → `write_file` with `backup_file` + `validate_file`).
- **No automatic permission escalation:** every L(n)→L(n+1) requires explicit
  human sign-off captured as an approval record; the Governor enforces this.
- **No removal of approval gates:** `require_approval_for_risky_actions`,
  `require_snapshots`, and `require_validation` remain `true`; the safety floor
  (`auto_execute`) is never relaxed except through the approved promotion path.

## 5. First Phase 8 Milestone

**"Autonomy Governor Foundation"**

Scope (design-only now; implementation after Phase 7 gate passes):
- Stand up `core/autonomy/` with `levels.py` + `audit.py` + `policies.py` +
  `governor.py` as described in `docs/PHASE8_AUTONOMY_GOVERNOR_DESIGN.md`.
- Governor wraps `supervisor.auto_execute` + `system_config.json` and becomes the
  sole sanctioned writer of autonomy state.
- The live Phase 7 `vscode_task_send` L2 workflow is migrated in as the first
  governed workflow (no behavioral regression).
- A request-only UI control panel is added; no component other than the Governor
  can change `auto_execute`.
- All Phase 7 safety invariants preserved (human approval, checkpoints, rollback,
  validation, audit logging).
- Exit criterion: the Governor can reproduce the exact Phase 7 L2 promotion
  (same checkpoint + approval + monitored run) with the trusted workflow, and no
  new autonomy surface exists beyond what Phase 7 already authorized.

> This milestone changes no autonomy level by itself. It establishes the control
> plane; promotions still require explicit human approval per the Phase 7 pattern.
