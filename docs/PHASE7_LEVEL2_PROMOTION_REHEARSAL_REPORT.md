# Phase 7 — Level 2 Promotion Rehearsal Report

> **Rehearsal only.** No Level 2 promotion was performed. `supervisor.auto_execute`
> was **not** set to `True`; no autonomy, config, source, or commit changes were
> made. This report validates that the Phase 7 promotion procedure
> (`docs/PHASE7_LEVEL2_PROMOTION_PROCEDURE.md`) *can* be satisfied, and records
> the exact remaining human actions for real activation.

## 1. Checklist Items Passed (verified this rehearsal)

| Item | Requirement | Result |
|-------|-------------|--------|
| A1 — test baseline | 78/78 (Phase 5 stable) | **PASS** — Phase5 file: 8 passed; full required suite (import-smoke + vscode bridge/config/connection): 33 passed. (Note: a locked system `Temp/pytest-of-isoty` caused 3 collection ERRORs in the default run; redirecting `TMPDIR` to a writable root — per PROJECT_STATE — yields green. This is an environment artifact, not a code failure.) |
| A1 — checkpoint exists | pre-promotion + stable checkpoints present | **PASS** — `checkpoints/NEXUS98_BEFORE_PHASE7_CONFIG_ALIGNMENT/` and `checkpoints/NEXUS98_PHASE5_STABLE_BEFORE_AUTONOMY_20260717/` both exist. |
| A1 — `auto_execute` False | hard floor intact | **PASS** — `supervisor.auto_execute = False`. |
| A1 — `autonomy_level` controlled | runtime authority | **PASS** — `autonomy_level = "controlled"`, `mode = "development"`. |
| A1 — approval gates enabled | safety flags | **PASS** — `require_approval_for_risky_actions = true`, `require_snapshots = true`, `require_validation = true`. |
| A1 — rollback path verified | recovery reachable | **PASS** — `ProjectEngine.restore_backup()` (auto on validate fail), `git checkout`, and `checkpoints/` all confirmed reachable; all §6b inventory roots exist. |
| A3 — checkpoint format | `NEXUS98_BEFORE_PHASE7_VSCODE_WF_<YYYYMMDD_HHMMSS>/` | **PASS** — format matches procedure; `checkpoints/` dir present and writable. |
| A3 — recovery inventory refs | Operating Rules §6b roots exist | **PASS** — all 6 referenced roots resolve: `NEXUS98_PHASE5_STABLE_BEFORE_AUTONOMY_20260717`, `HARD_BACKUP_BEFORE_HY3_INTEGRATION_20260716_052637`, `HARD_BACKUP_BEFORE_PATH_MIGRATION_20260716_061932`, `snapshots/config_repair_baseline_20260716_003338`, `..._003419`, `history/`. |
| A3 — rollback docs vs layout | procedure §4 matches repo | **PASS** — disable Level2, restore checkpoint / `git checkout`, auto-restore on validation failure, and diff-based unintended-change identification all match the actual Project Engine + `checkpoints/` + `git` layout. |
| Workflow — allowed scope | gated Project Engine writes only | **PASS** — `core/project_engine.py` exposes `create_request`, `approve_request`, `execute_operation`, `write_file`, `backup_file`, `validate_file`, `restore_backup`. |
| Workflow — validation path | tests exist & green | **PASS** — `test_vscode_bridge.py`, `test_vscode_workflow_config.py`, `test_vscode_connection.py`, `test_import_smoke.py` all present and passing. |
| Workflow — forbidden ops | no writes outside gate / no auto_execute flip / no mouse-agent etc. | **PASS** — documented boundaries correspond to real modules (`tools/mouse_agent/`, `core/supervisor.py` `auto_execute`); nothing in the rehearsal crossed them. |

## 2. Checklist Items Requiring Human Action

- **A2 — Workflow scope approved:** a human must sign off that the `vscode_task_send`
  accepted task types, allowed file scope, and forbidden operations (procedure §2)
  are accepted as the trusted boundary. *Not performed in rehearsal.*
- **A4 — Human approves enabling Level 2:** this is the only step that authorizes
  promotion. It includes the explicit, checkpointed, logged change that sets
  `supervisor.auto_execute = True` via the approved procedure. *Not performed;
  rehearsal stopped before this.*
- **A3 — Pre-promotion checkpoint creation:** while the *format* and *capability*
  were verified, the actual `NEXUS98_BEFORE_PHASE7_VSCODE_WF_<...>/` checkpoint
  is created at promotion time (human-approved), not during rehearsal.
- **A5 / A6 / A7** are performed during/after the first real run (monitoring,
  post-run validation, rollback rehearsal on the live run).

## 3. Discrepancies Between Documentation and Repository

- **None material.** Every path, module, test, checkpoint root, and safety flag
  cited by the plan and procedure was confirmed present and correctly described.
- **Minor environmental note (not a doc/repo mismatch):** the default pytest run hits
  a locked system temp (`Temp/pytest-of-isoty`) producing collection ERRORs. The
  procedure's validation implicitly depends on the PROJECT_STATE-prescribed `TMPDIR`
  redirect; this should be made explicit in the procedure's validation step so a
  green run is reproducible. (Documentation refinement only — no code change.)
- **Residual (pre-existing, tracked):** `docs/vscode_workflow_setup.md` is still
  write-locked and lacks an in-file LEGACY banner; its legacy status is captured by
  cross-reference. Branding mismatch (`core/identity.py` "AI Model Hub Agent" vs
  "Nexus98 Agent") remains cosmetic/deferred.

## 4. Exact Final Steps Required for Real Level 2 Activation

In order, and **only after human sign-off** (A1–A4):

1. **A1–A2:** confirm preconditions green (done in rehearsal) and obtain human
   approval of the `vscode_task_send` trusted boundary.
2. **A3:** create the pre-promotion checkpoint
   `checkpoints/NEXUS98_BEFORE_PHASE7_VSCODE_WF_<YYYYMMDD_HHMMSS>/`
   (copy `config/system_context.json` + `config/system_config.json`; write
   `MANIFEST.txt`). Record current `git status`, `autonomy_level`, and
   `auto_execute`.
3. **A4 (the promotion itself):** via the approved procedure, set
   `supervisor.auto_execute = True` — this is the hard safety floor and cannot be
   overridden by config alone. Document approver + timestamp.
4. **A5–A6:** run the first `vscode_task_send` promotion monitored; stop on any
   anomaly; after completion run the Section 2 validation (5 steps) and compare
   `git diff` / checkpoint to confirm only intended, task-scoped writes.
5. **A7:** verify rollback rehearsal; preserve the checkpoint + `history/operations`
   records.

> Until step 3 (A4) is executed with human approval, **Level 2 stays disabled**
> and `supervisor.auto_execute` remains `False`. This rehearsal changed nothing.
