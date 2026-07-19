# Phase 7 — Level 2 Promotion Procedure

> **Procedure document only.** This file defines *how* to promote the single
> trusted workflow (`vscode_task_send`) to Level 2. It does **not** enable
> Level 2, does **not** change `supervisor.auto_execute`, and makes no code,
> config, or autonomy changes. `supervisor.auto_execute` stays `False` until the
> explicit final human approval in the checklist (Section 5) is granted and the
> approved promotion step is executed separately.

## 1. Promotion Preconditions

Verify **all** of the following before any promotion action:

- **78/78 test baseline** — `tests/test_supervisor_phase5.py` (and the full
  suite) must report 78 passed / 0 failed. Re-run the suite to confirm the
  current state matches the Phase 5 stable baseline
  (`checkpoints/NEXUS98_PHASE5_STABLE_BEFORE_AUTONOMY_20260717/`).
- **Checkpoint exists** — a pre-promotion checkpoint directory must already exist:
  `checkpoints/NEXUS98_BEFORE_PHASE7_VSCODE_WF_<YYYYMMDD_HHMMSS>/`
  containing a copy of `config/system_context.json` and `config/system_config.json`
  plus a `MANIFEST.txt`. (The pre-alignment checkpoint
  `checkpoints/NEXUS98_BEFORE_PHASE7_CONFIG_ALIGNMENT/` is also on hand.)
- **`supervisor.auto_execute` remains `False`** until final approval — confirmed by
  reading `core/supervisor.py`; the promotion step that sets it `True` is the very
  last action and only runs after human sign-off.
- **`autonomy_level` is `"controlled"`** — confirmed in
  `config/system_config.json` (`autonomy_level`, `mode: "development"`).
- **Approval gates enabled** — `safety.require_approval_for_risky_actions`,
  `safety.require_snapshots`, and `safety.require_validation` are all `true`.
- **Rollback path verified** — `ProjectEngine.restore_backup()` (auto on
  `validate_file` failure), `git checkout` of affected files, and the
  `checkpoints/` tree are all confirmed reachable (see Section 4).

## 2. Trusted Workflow Definition

**Workflow:** `vscode_task_send` (the Level 2 workflow named in
`docs/Nexus98_Tool_Registry.md` §9).

- **Accepted task types** (constrained vocabulary — no arbitrary command/shell
  execution):
  - Open / focus a *specified* file in the VS Code editor.
  - Inspect / lint / format a *specified* file via the bridge.
  - Query bridge status (`vscode_connector.status()`).
  - Dispatch a pre-approved, well-formed task string to
    `vscode_connector.send_task(task, mode="hybrid")`.
- **Allowed file scope:**
  - Read-only queries anywhere (`list_files`, `read_file`, bridge `status()`).
  - Project Engine file writes **only** for files explicitly named by the task,
    routed through `create_request → approve_request → execute_operation →
    write_file` (with automatic `backup_file` + `validate_file`).
- **Forbidden operations** (stay Level 0/1 or blocked entirely):
  - Any write outside the Project Engine gated path.
  - Enabling `supervisor.auto_execute = True` without the Section 5 approval.
  - Model/agent lifecycle changes, downloads, or dependency installs (Level 3+).
  - Mouse-agent GUI automation (`tools/mouse_agent/`) — high-risk; stays Level 0/1.
  - Editing `config/`, `core/supervisor.py` `auto_execute`, or unrelated files.
  - Broad/unspecified task strings ("do whatever", shell execution, deletes).
- **Maximum change scope:** one trusted workflow, one operation at a time; total
  blast radius limited to the specific files named by the current task. No bulk or
  cross-module changes.
- **Required validation:**
  - **Pytest temp directory (required):** any validation run that invokes pytest
    MUST use the approved workspace `TMPDIR` redirect documented in
    `PROJECT_STATE.md` (e.g. `TMPDIR=D:\Nexus98\.pytest_temp_alt` or another
    writable workspace root). Set it as an environment variable before the pytest
    invocation: `TMPDIR=<writable-workspace-root> python -m pytest ...`.
    This avoids stale locked system temp artifacts (the system
    `Temp/pytest-of-isoty` root can lock after an interrupted session and cause
    collection/setup ERRORs that are environmental, not code failures). Redirecting
    `TMPDIR` to a writable workspace root yields a reproducible green run.
  1. `python -m pytest tests/test_import_smoke.py` — imports intact.
  2. `python -m pytest tests/test_vscode_bridge.py tests/test_vscode_workflow_config.py tests/test_vscode_connection.py` — bridge/config/connection green.
  3. Confirm `supervisor.auto_execute == False` and `autonomy_level == "controlled"` still hold post-run.
  4. Confirm each `write_file` produced a `backup_file` and passed `validate_file`.
  5. Confirm a `history/operations/<operation_id>` record exists and is auditable.
- **Required checkpoint behavior:** a `checkpoints/NEXUS98_PHASE7_<WF>_<YYYYMMDD_HHMMSS>/`
  snapshot (with `MANIFEST.txt`) is **mandatory before every mutation**, in addition
  to the per-operation `history/operations/<operation_id>` record.

## 3. First Promotion Run Procedure

### Before
- Create the pre-promotion checkpoint
  `checkpoints/NEXUS98_BEFORE_PHASE7_VSCODE_WF_<YYYYMMDD_HHMMSS>/` (copy
  `config/system_context.json`, `config/system_config.json`; write `MANIFEST.txt`).
- Record current state: capture `git status --short`, the current
  `autonomy_level`, and `supervisor.auto_execute` value for later comparison.

### During
- Monitor execution live (logs, bridge status, `history/operations`).
- Stop immediately on **any** unexpected behavior: unexpected file write,
  autonomy flag change, test failure, external-process error, or task outside the
  accepted vocabulary.
- On stop: re-engage Level 1 (proposals + checkpoint; human approves before
  execution) and proceed to Section 4 rollback if state diverged.

### After
- Run the Section 2 validation steps; all must pass.
- Compare changes: `git diff` (and `checkpoints/` comparison) must show only the
  intended, task-scoped file writes — nothing outside the allowed scope.
- Preserve rollback: keep the pre-promotion checkpoint and the
  `history/operations/<operation_id>` records; do not delete them.

## 4. Emergency Rollback Procedure

- **Disable Level 2:** immediately set the workflow back to Level 1/assisted
  (proposals + checkpoint; human approves before execution). If `auto_execute`
  was enabled during the run, revert it to `False` via the approved path and
  confirm `supervisor.auto_execute == False`.
- **Restore checkpoint:** copy the matching
  `checkpoints/NEXUS98_BEFORE_PHASE7_VSCODE_WF_<...>/` (or
  `checkpoints/NEXUS98_PHASE5_STABLE_BEFORE_AUTONOMY_20260717/`) tree back over
  the working files, or `git checkout -- <affected files>`.
- **Auto-restore on validation failure:** `ProjectEngine.write_file` already
  backs up the target before overwriting and calls `restore_backup()` if
  `validate_file` fails — no manual step needed for a single failed write.
- **Identify unintended changes:** diff the working tree against the pre-promotion
  checkpoint and against `git` HEAD; any file not in the accepted task scope is an
  unintended change and must be restored from the checkpoint / `git checkout`.
- After rollback: re-run `tests/test_import_smoke.py` + the vscode bridge tests,
  confirm `supervisor.auto_execute == False`, and report to the human.

## 5. Promotion Approval Checklist

Explicit human approval points (each requires a human sign-off; document the
approver and timestamp):

- [ ] **A1 — Preconditions verified:** 78/78 baseline confirmed, checkpoint
      exists, `auto_execute == False`, `autonomy_level == "controlled"`,
      approval gates enabled, rollback path verified.
- [ ] **A2 — Workflow scope approved:** the `vscode_task_send` accepted task
      types, allowed file scope, and forbidden operations (Section 2) are accepted
      as the trusted boundary.
- [ ] **A3 — Pre-promotion checkpoint created and recorded** (`NEXUS98_BEFORE_PHASE7_VSCODE_WF_*`).
- [ ] **A4 — Human approves enabling Level 2 for this single workflow**, including
      the explicit, checkpointed, logged change that sets
      `supervisor.auto_execute = True` via the approved procedure (the hard safety
      floor; config alone cannot override it).
- [ ] **A5 — First promotion run monitored**; stop-on-anomaly honored.
- [ ] **A6 — Post-run validation passed** (Section 2 steps 1–5) and change
      comparison shows only intended, task-scoped writes.
- [ ] **A7 — Rollback rehearsed/verified** and checkpoint + `history/` records
      preserved.

> Promotion is authorized **only** after A1–A4 are signed. A5–A7 are performed
> during/after the first run. Until A4 is granted, `supervisor.auto_execute`
> remains `False` and the workflow stays at Level 1.

---

### Readiness assessment
The project is **documentation- and config-consistent and procedurally ready** for a
single-workflow Level 2 promotion: the trusted workflow is identified
(`vscode_task_send`), the promotion plan and this procedure exist, the safety floor
(`auto_execute = False`), `autonomy_level = "controlled"`, and all approval gates
are confirmed enabled, and a verified rollback path (Project Engine auto-restore +
`checkpoints/` + `git`) is in place.

### Exact remaining action required before enabling Level 2
Execute the **human approval steps A1–A4** in Section 5 (this is the only thing
that promotes the workflow), which includes creating the pre-promotion checkpoint
`NEXUS98_BEFORE_PHASE7_VSCODE_WF_<YYYYMMDD_HHMMSS>/` and — as the final,
separately-executed step — setting `supervisor.auto_execute = True` through the
approved procedure. **No code, config, or autonomy change is made by this
document.** Until those approvals are granted and executed, Level 2 stays disabled.
