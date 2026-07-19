# Phase 8 — Autonomy Governor Implementation Plan

> **Implementation plan only.** No source, config, test, or autonomy changes are
> made here. `supervisor.auto_execute` remains `False`. This plan sequences the
> build of the Autonomy Governor (`core/autonomy/`) and its UI panel, per the
> accepted designs `docs/PHASE8_AUTONOMY_GOVERNOR_DESIGN.md` and
> `docs/PHASE7_5_AUTONOMY_CONTROL_INTERFACE_DESIGN.md`, and the gate in
> `docs/PHASE7_TO_PHASE8_TRANSITION_PLAN.md`.

## 1. Implementation Order

1. **`core/autonomy/levels.py`** — declaritive L0–L4 definitions, permission
   sets, and trusted-workflow allow-lists (seed with `vscode_task_send`).
   Pure data + helpers; no I/O side effects.
2. **`core/autonomy/audit.py`** — append-only audit log reusing `history/`
   (and `history/autonomy/` if separated); one record per request/decision/
   transition/checkpoint reference.
3. **`core/autonomy/pollicies.py`** — approval + scope engine; port the Phase 7
   promotion checklist into the L1→L2 rule; maps a request to the concrete
   gated action and enforces per-workflow allow/deny.
4. **`core/autonomy/governor.py`** — the authority; the **sole** writer of
   `supervisor.auto_execute` + `system_config.json` intent; validates requests
   via `pollicies`, applies level changes, emits audit events.
5. **UI autonomy panel** — request-only interface in `ui/main_window.py`
   (level dial, current state, requested promotion, approval, checkpoint status,
   rollback availability, audit history). No direct grant.
6. **Phase 7 workflow migration** — move the live `vscode_task_send` L2
   promotion under the Governor; expand to L3 one at a time; add L4 as an
   explicit experimental toggle.

## 2. Existing Code Integration Points

- **`supervisor.auto_execute`** — the **hard safety floor** and the only
  sanctioned write target. `governor.apply()` is the sole path that flips it;
  config alone cannot override (per `docs/CONFIG_AUTHORITY.md` §4).
- **`system_config.json`** — authoritative runtime config (`autonomy_level`,
  `mode`, safety gates). Governor reads gates and writes the *intent* level; the
  actual execution enablement still requires `auto_execute`.
- **`system_context.json`** — project/phase narrative. Governor may record the
  active autonomy posture but must not be the source of truth for the safety floor.
- **Project Engine approval flow** — `create_request` → `approve_request` →
  `execute_operation` → `write_file` (with `backup_file` + `validate_file`)
  stays the file-mutation authority. Governor governs the *autonomy level*;
  Project Engine governs the *file writes*; they compose.
- **`checkpoints/`** — Governor requires a `checkpoints/NEXUS98_BEFORE_PHASE*_*`
  snapshot + `MANIFEST.txt` before any promotion (reuse Phase 7 convention).
- **`history/operations`** — every Governor decision references/extends this
  audit trail; `audit.py` appends to it.

## 3. Migration Strategy

- **Preserve Phase 7 manual activation:** the existing human-signed procedure
  (`docs/PHASE7_LEVEL2_ACTIVATION_CHECKLIST.md`) stays valid as the fallback
  path; the Governor does **not** alter `supervisor.auto_execute` semantics.
- **Introduce Governor as a wrapper:** it wraps `auto_execute` + `system_config`
  so that no other component can change them except via `governor.apply()`;
  the hard floor is unchanged.
- **Migrate `vscode_task_send` as first governed workflow:** port its scope +
  approval into `levels.py` / `pollicies.py`; the live L2 promotion becomes the
  Governor's first governed workflow with **no behavioral regression**.
- **No data migration:** `history/operations/` and `checkpoints/` are reused as
  the Governor's audit/rollback backing; `audit.py` appends to the same trail.

## 4. Testing Strategy

- **Unit tests:** `levels.py` (L0–L4 resolution, allow-list lookup),
  `pollicies.py` (approval/scope decisions, reject-on-missing-checkpoint),
  `governor.py` (apply/downgrade/emergency_stop transitions, sole-writer
  invariant), `audit.py` (append-only record shape).
- **Permission boundary tests:** assert the UI/agent request path **cannot**
  write `auto_execute` or `system_config.json` directly; assert every L(n)→L(n+1)
  without a recorded approval is rejected; assert stricter-value-wins on config
  read conflict (per `docs/CONFIG_AUTHORITY.md` §6).
- **Rollback tests:** `restore_backup()` auto on `validate_file` failure;
  checkpoint-restore + `git checkout` bring state back; `emergency_stop()`
  forces `auto_execute = False` and downgrades to L0/L1.
- **UI request-only tests:** the panel emits `request_level_change(...)` and has
  **no** code path that flips `auto_execute`; simulate an approval to confirm the
  Governor (not the UI) applies the change.
- **Migration test:** reproduce the Phase 7 `vscode_task_send` L2 promotion
  through the Governor (checkpoint + approval + monitored run) with identical
  observable behavior to the manual procedure.

## 5. Rollback Strategy

- **Remove the Governor safely:** because it only *wraps* existing
  `auto_execute`/`system_config` writes and the manual Phase 7 procedure
  remains documented, removing `core/autonomy/` (or disabling it) leaves the
  system exactly where Phase 7 left it — manual, checkpointed, human-approved
  promotion. No orphaned state.
- **Return to Phase 7 manual procedure:** flip the control surface back to the
  `docs/PHASE7_LEVEL2_ACTIVATION_CHECKLIST.md` path; the UI panel can be
  hidden/disabled while `governor.py` is bypassed. The hard floor
  (`auto_execute`) is untouched by this switch.
- **Verification after rollback:** re-run the Phase 7 validation suite (with the
  approved `TMPDIR` redirect) and confirm `auto_execute = False` (or the
  intended manual level) and all safety gates `true`.

## 6. First Implementation Milestone

**"Autonomy Governor Foundation"**

- Stand up `core/autonomy/` with `levels.py` + `audit.py` + `pollicies.py` +
  `governor.py` per the accepted Phase 8 design.
- Governor wraps `supervisor.auto_execute` + `system_config.json` and is the
  **sole** sanctioned writer of autonomy state.
- The live Phase 7 `vscode_task_send` L2 workflow is migrated in as the first
  governed workflow (no behavioral regression).
- A request-only UI autonomy panel is added; no component other than the
  Governor can change `auto_execute`.
- All Phase 7 safety invariants preserved (human approval, checkpoints, rollback,
  validation, audit logging).
- **Exit criterion:** the Governor can reproduce the exact Phase 7 L2 promotion
  (same checkpoint + approval + monitored run) for the trusted workflow, and no
  new autonomy surface exists beyond what Phase 7 already authorized.

> This milestone changes no autonomy level by itself. Promotions still require
> explicit human approval via the Governor/approval flow, exactly as in Phase 7.
