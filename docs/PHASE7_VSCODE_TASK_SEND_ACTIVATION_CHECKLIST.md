# Phase 7 — Final Level 2 Activation Checklist: `vscode_task_send`

> **Checklist only.** Stop **before** changing `supervisor.auto_execute`. No
> implementation, config, source, test, or autonomy changes are made here.
> `supervisor.auto_execute` remains `False` until the explicit, human-signed
> step below is executed. This checklist is the last gate before the single
> approved promotion of the trusted `vscode_task_send` workflow to Level 2.

## Pre-Activation Gates (verified this pass)

- [x] **Checkpoint confirmed:** `checkpoints/NEXUS98_BEFORE_PHASE7_VSCODE_WF_20260717_210538/`
  exists with `MANIFEST.txt`, `system_config.json`, `system_context.json`,
  `_git_status_snapshot.txt`. Rollback roots all resolve:
  `NEXUS98_PHASE5_STABLE_BEFORE_AUTONOMY_20260717/`,
  `NEXUS98_BEFORE_PHASE7_CONFIG_ALIGNMENT/`,
  `HARD_BACKUP_BEFORE_HY3_INTEGRATION_20260716_052637/`,
  `snapshots/config_repair_baseline_20260716_003338/`, `history/`.
- [x] **Tests confirmed:** required suite present and green — **33 passed**
  (import-smoke + vscode bridge/config/connection) via the approved `TMPDIR`
  redirect; `tests/test_supervisor_phase5.py` (Phase 5 78/78 baseline) passes
  with the same redirect. TMPDIR procedure documented in
  `docs/PHASE7_LEVEL2_PROMOTION_PROCEDURE.md` §2.
- [x] **Safety gates confirmed:** `supervisor.auto_execute = False` (hard floor
  intact pre-activation); `autonomy_level = "controlled"`; `mode = "development"`;
  `require_approval_for_risky_actions = true`; `require_snapshots = true`;
  `require_validation = true`.
- [x] **Rollback path confirmed:** `ProjectEngine.restore_backup()` present
  (auto on `validate_file` failure); `checkpoints/` + `history/` + `git checkout`
  all reachable.

## Activation Steps (execute only with explicit human sign-off)

- [ ] **A1 — Human confirms** the four pre-activation gates above (checkpoint,
  tests, safety gates, rollback) are satisfied. Record approver + timestamp.
- [ ] **A2 — Human approves** the `vscode_task_send` trusted-workflow scope
  (accepted task types, allowed file scope, forbidden operations per
  `docs/PHASE7_LEVEL2_PROMOTION_PROCEDURE.md` §2).
- [ ] **A3 — Confirm pre-promotion checkpoint** present:
  `checkpoints/NEXUS98_BEFORE_PHASE7_VSCODE_WF_20260717_210538/`.
  (Already created and verified this pass; no new action required unless state
  changed since.)
- [ ] **A4 — EXECUTE THE SINGLE PROMOTION (requires human sign-off):** set
  `supervisor.auto_execute = True` **only** via the approved procedure, for the
  `vscode_task_send` workflow set. This is the hard safety floor and cannot be
  overridden by config alone. Record approver + timestamp.
  > STOP: do **not** change `autonomy_level`, `mode`, or any safety gate.
  > Do **not** enable any workflow beyond `vscode_task_send`.

## Post-Activation Verification (after A4)

- [ ] **Monitored first run:** watch `logs/supervisor.log`, `logs/vscode_bridge.log`,
  `history/operations/<operation_id>`; stop immediately on any anomaly
  (out-of-gate write, unexpected flag change, test failure, out-of-vocabulary
  task, runtime error).
- [ ] **Validation:** re-run the Section "Tests confirmed" suite (with `TMPDIR`
  redirect) — must be green; confirm each `write_file` produced a `backup_file`
  and passed `validate_file`; confirm a `history/operations/<operation_id>` record
  exists and is auditable.
- [ ] **Change review:** `git diff` / checkpoint comparison shows **only** the
  intended, task-scoped file writes for `vscode_task_send`.
- [ ] **Rollback preserved:** keep the A3 checkpoint + `history/operations/` records;
  do not delete them.

## Stop Condition (this checklist)

**Do NOT proceed past the pre-activation gates without human sign-off on A1–A4.**
Until A4 is executed, `supervisor.auto_execute` remains `False` and Level 2 stays
disabled. This document performs no activation by itself.
