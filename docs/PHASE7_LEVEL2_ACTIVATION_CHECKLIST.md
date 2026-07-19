# Phase 7 — Level 2 Activation Checklist

> **Activation package only.** This document is the final, human-executable
> checklist for promoting the single trusted workflow (`vscode_task_send`) to
> Level 2. It does **not** enable Level 2 and does **not** set
> `supervisor.auto_execute = True`. No code, config, autonomy, or commit changes
> are made here. Each section lists the exact action plus the confirmation; a human
> signs each item. Until Section 3 is executed with sign-off, Level 2 stays
> disabled and `supervisor.auto_execute` remains `False`.

## 1. Pre-Activation Verification

Confirm **all** before any activation action:

- **Current test status:** full required suite green — `tests/test_import_smoke.py`
  (passing), `tests/test_supervisor_phase5.py` (Phase 5 stable baseline, 78/78
  class), and `tests/test_vscode_bridge.py` + `tests/test_vscode_workflow_config.py`
  + `tests/test_vscode_connection.py` (passing). Run pytest with the approved
  `TMPDIR` redirect (see `docs/PHASE7_LEVEL2_PROMOTION_PROCEDURE.md` §2) to avoid
  stale locked system-temp ERRORs.
- **Current autonomy settings:** `supervisor.auto_execute = False`;
  `config/system_config.json` `autonomy_level = "controlled"`, `mode = "development"`;
  `safety.require_approval_for_risky_actions = true`,
  `safety.require_snapshots = true`, `safety.require_validation = true`.
- **Checkpoint readiness:** pre-alignment checkpoint
  `checkpoints/NEXUS98_BEFORE_PHASE7_CONFIG_ALIGNMENT/` and stable baseline
  `checkpoints/NEXUS98_PHASE5_STABLE_BEFORE_AUTONOMY_20260717/` both exist and are
  readable; `checkpoints/` is writable.
- **Trusted workflow scope:** `vscode_task_send` boundaries (procedure §2) are
  accepted — accepted task types, allowed file scope (gated Project Engine writes
  only), forbidden operations, and maximum change scope (one workflow / one
  operation at a time). Human sign-off on scope recorded.

## 2. Exact Checkpoint Creation Step

- **Required name format:**
  `checkpoints/NEXUS98_BEFORE_PHASE7_VSCODE_WF_<YYYYMMDD_HHMMSS>/`
  (e.g. `checkpoints/NEXUS98_BEFORE_PHASE7_VSCODE_WF_20260717_210000/`).
- **Required contents:**
  - A copy of `config/system_context.json`.
  - A copy of `config/system_config.json`.
  - `MANIFEST.txt` stating purpose (pre-Level-2 promotion snapshot for
    `vscode_task_send`), the exact timestamp, the intended single change
    (`supervisor.auto_execute: False -> True` via approved procedure), and that all
    other config/autonomy values are preserved.
- **Verification after creation:**
  - Directory exists and contains the two JSON copies + `MANIFEST.txt`.
  - The two JSON copies parse as valid JSON and match the live files byte-for-byte
    (BOM preserved).
  - Record current `git status --short`, `autonomy_level`, and `auto_execute`
    value for later comparison.

## 3. Exact Activation Step

- **The single setting change required:** set `supervisor.auto_execute = True`
  **only** via the approved procedure, executed as the final action after the
  Section 1–2 checks and explicit human sign-off. This is the hard safety floor;
  config alone cannot override it.
- **Confirmation that no other settings change:**
  - `autonomy_level` stays `"controlled"` (config may reflect intent but the gate
    does not enable execution without `auto_execute = True`).
  - `mode`, `require_approval_for_risky_actions`, `require_snapshots`,
    `require_validation`, `current_phase`, and all tool/model/provider config remain
    exactly as pre-activation.
  - Only `core/supervisor.py` `auto_execute` changes; nothing else in `config/`
    or elsewhere is modified by this step.
- Document the approver name + timestamp alongside the change.

## 4. First-Run Monitoring Procedure

- **What to watch:**
  - Live bridge status (`vscode_connector.status()`) and agent logs
    (`logs/supervisor.log`, `logs/vscode_bridge.log`).
  - `history/operations/<operation_id>` records for each dispatched task.
  - `checkpoints/` and `git status` for any file write outside the named task scope.
- **Stop conditions (halt immediately):**
  - Any write outside the Project Engine gated path.
  - `auto_execute` or `autonomy_level` changes unexpectedly.
  - A validation/test failure during the run.
  - A task string outside the accepted vocabulary (broad/unspecified/shell execution).
  - Any external-process or runtime error on the trusted path.
- **Rollback trigger:** if any stop condition fires, immediately disable Level 2
  (revert `auto_execute = False` via approved path) and execute the Emergency
  Rollback Procedure (`docs/PHASE7_LEVEL2_PROMOTION_PROCEDURE.md` §4).

## 5. Post-Activation Validation

- **Tests to run (procedure §2 validation steps 1–5):**
  1. `python -m pytest tests/test_import_smoke.py` — imports intact.
  2. `python -m pytest tests/test_vscode_bridge.py tests/test_vscode_workflow_config.py tests/test_vscode_connection.py` — bridge/config/connection green (with `TMPDIR` redirect).
  3. Confirm `supervisor.auto_execute == True` (expected post-activation) and
     `autonomy_level == "controlled"` still holds.
  4. Confirm each `write_file` produced a `backup_file` and passed `validate_file`.
  5. Confirm a `history/operations/<operation_id>` record exists and is auditable.
- **Logs to inspect:**
  - `logs/supervisor.log` — action routing / approval events.
  - `logs/vscode_bridge.log` — dispatched tasks and status.
  - `history/operations/<operation_id>.json` — per-operation record.
- **Change review:**
  - `git diff` and checkpoint comparison must show **only** the intended,
    task-scoped file writes for `vscode_task_send` — nothing outside the allowed
    scope.
  - Preserve the Section 2 checkpoint and all `history/operations/` records; do
    not delete them (rollback must remain available).

---

### Sign-off summary
- [ ] Section 1 pre-activation verification complete (tests green, autonomy
      settings confirmed, checkpoints ready, scope signed).
- [ ] Section 2 checkpoint created and verified.
- [ ] Section 3 activation executed with explicit human approval (single
      `auto_execute = True` change; all other settings unchanged).
- [ ] Section 4 first run monitored; no stop condition fired.
- [ ] Section 5 post-activation validation passed; change review clean.

> Until Section 3 is signed and executed, **Level 2 remains disabled** and
> `supervisor.auto_execute = False`. This document makes no change by itself.
