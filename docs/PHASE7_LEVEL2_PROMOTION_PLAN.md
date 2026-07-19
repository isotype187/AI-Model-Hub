# Phase 7 — Level 2 Autonomy Promotion Plan (One Trusted Workflow)

> **Planning document only.** No Level 2 autonomy is enabled by this file.
> This plan defines the single trusted workflow proposed for promotion to Level 2,
> the safety controls that must remain in force, and the approval/rollback boundary.
> Per the task rules: documentation only — no code, config, autonomy, or commit
> changes are made here. `supervisor.auto_execute` stays `False` until the
> explicit, human-approved promotion in the "Approval boundary" section is executed.

## 1. Selected Workflow Candidate

**Workflow: "VS Code Task Send" (trusted, read-mostly → approved-write)**

This is the workflow already named at Level 2 in `docs/Nexus98_Tool_Registry.md`
(§9 Autonomy table: Level 2 = "+ Project Engine writes (approved actions),
VS Code task send"). It reuses existing, tested components only.

- **Existing components:**
  - `integrations/vscode_connector.py` — `send_task(task, mode="hybrid")`,
    `status()`, `log()` drive a VS Code task and query bridge status.
  - `api/vscode_bridge.py` — Flask app exposing `/status`, `/task`, etc.
  - `bridge/vscode_listener.py`, `bridge/worker.py` — local bridge listener/worker.
  - `core/project_engine.py` — the only authorized file mutator; all writes go
    through `create_request` → `approve_request` → `execute_operation` →
    `write_file` (with `backup_file` + `validate_file`), recorded under
    `history/operations/`.
- **Why it is the safest candidate:**
  - Already exists and is wired end-to-end.
  - Has dedicated test coverage: `tests/test_vscode_bridge.py`,
    `tests/test_vscode_workflow_config.py`, `tests/test_vscode_connection.py`.
  - Clear inputs/outputs: input = a task string (e.g. "open file X in editor",
    "run lint on Y"); output = task dispatched to the bridge + status rendered in
    the VS Code extension. No arbitrary code execution.
  - Checkpoint/recovery capability: every mutation is pre-backed-up by
    `ProjectEngine.backup_file` and logged in `history/`; `checkpoints/` and
    `git` provide rollback.
  - No new dependencies required.
  - No admin privileges required (local loopback `localhost:11434`/bridge only).
  - Scoped to a single integration surface; does not modify unrelated files.

## 2. Workflow Definition

- **Workflow name:** `vscode_task_send` (Level 2 trusted workflow)
- **Purpose:** Allow the agent, at Level 2, to dispatch a well-formed task to the
  VS Code bridge (via `vscode_connector.send_task`) and perform only the
  Project-Engine-approved file writes that the task implies — without per-step
  human confirmation for each individual action, while remaining inside the
  approval gate and checkpoint system.
- **Allowed actions:**
  - Call `vscode_connector.status()` / `log()` (read-only bridge queries).
  - Call `vscode_connector.send_task(task, mode="hybrid")` for a pre-approved,
    constrained task vocabulary (open/inspect/lint/format a *specified* file;
    never "execute arbitrary command").
  - Perform Project Engine file writes **only** through the gated path:
    `create_request` → human/Policy-approved `approve_request` →
    `execute_operation` → `write_file` (auto `backup_file` + `validate_file`).
  - Create a `checkpoints/` snapshot before any mutation.
- **Forbidden actions (must stay Level 0/1 or blocked):**
  - Any write outside the Project Engine gated path.
  - Enabling `supervisor.auto_execute = True` without the explicit promotion step.
  - Model/agent lifecycle changes, downloads, or dependency installs (Level 3+).
  - Mouse-agent GUI automation (`tools/mouse_agent/`) — high-risk; stays Level 0/1.
  - Editing `config/`, `core/supervisor.py` `auto_execute`, or unrelated files.
  - Broad/unspecified task strings ("do whatever", shell execution, deletes).
- **Required checkpoint:** A `checkpoints/NEXUS98_PHASE7_<WF>_<YYYYMMDD_HHMMSS>/`
  snapshot (with `MANIFEST.txt`) is **mandatory before every mutation**, plus a
  `history/operations/<operation_id>` record per `execute_operation`.
- **Validation steps (gate before/after each run):**
  1. `python -m pytest tests/test_import_smoke.py` — imports intact.
  2. `python -m pytest tests/test_vscode_bridge.py tests/test_vscode_workflow_config.py tests/test_vscode_connection.py` — bridge/config/connection green.
  3. Confirm `supervisor.auto_execute == False` and
     `system_config.json` `autonomy_level == "controlled"` still hold post-run.
  4. Confirm each `write_file` produced a `backup_file` and passed `validate_file`.
  5. Confirm `history/operations/<operation_id>` record exists and is auditable.
- **Rollback procedure:**
  - On any failed `validate_file`: `ProjectEngine.restore_backup()` auto-restores
    the pre-write backup.
  - On broader breakage: restore the matching `checkpoints/NEXUS98_PHASE7_*` tree
    (or `git checkout` the affected files) and re-run the import + bridge tests.
  - Re-engage strict Level 0/1 behavior immediately (set the workflow back to
    assisted) and report to human.
- **Approval boundary (the ONLY thing that promotes this workflow to Level 2):**
  - This document does **not** perform the promotion.
  - Promotion requires, in order, and only after this plan is reviewed:
    1. Human approval of this plan (explicit sign-off).
    2. A pre-promotion checkpoint:
       `checkpoints/NEXUS98_BEFORE_PHASE7_VSCODE_WF_<YYYYMMDD_HHMMSS>/`.
    3. An explicit, checkpointed, logged change that raises the workflow's
       autonomy scope — and **only** if `supervisor.auto_execute` is also set to
       `True` via the approved procedure (it is the hard safety floor and cannot be
       overridden by config alone).
    4. A monitored first run on the single trusted workflow, with stop-and-report
       on any anomaly.
  - Until steps 1–4 are completed by a human, the workflow remains at Level 1
    (proposals + checkpoints; human approves before execution).

## 3. Current Safety Controls (reviewed, must remain in force)

| Control | Current value | Status |
|----------|--------------|--------|
| `supervisor.auto_execute` (`core/supervisor.py`) | `False` | Hard safety floor; unchanged. |
| `autonomy_level` (`config/system_config.json`) | `"controlled"` | Unchanged. |
| `mode` (`config/system_config.json`) | `"development"` | Unchanged. |
| `safety.require_approval_for_risky_actions` | `true` | Unchanged. |
| `safety.require_snapshots` | `true` | Unchanged. |
| `safety.require_validation` | `true` | Unchanged. |
| Checkpoint system | `ProjectEngine.backup_file` + `history/` + `checkpoints/` | Available; mandatory for this WF. |
| Existing tests | `test_import_smoke`, `test_supervisor_phase5`, `test_vscode_bridge`, `test_vscode_workflow_config`, `test_vscode_connection`, `test_memory_phase1`, `test_mouse_agent` | Green baseline to re-run. |

> Note: `config/system_context.json.current_phase` was aligned to
> `"Phase 6.5 — Documentation Audit Remediation"` in the pre-Phase-7 config
> cleanup, satisfying the earlier stale-state blocker.

## 4. Suitability Recommendation

**Recommendation: SUITABLE for Level 2 — conditionally, and only via the
approval boundary above.**

Rationale:
- The `vscode_task_send` workflow meets every selection criterion: it already
  exists, has test coverage, has clear inputs/outputs, has checkpoint/recovery
  via the Project Engine + `history/` + `checkpoints/`, needs no new
  dependencies, needs no admin privileges, and does not modify unrelated files.
- It is the least-blast-radius candidate: it reuses an existing, already-tested
  integration and keeps all writes inside the gated Project Engine path.
- All safety controls reviewed above remain at their safe defaults; the promotion
  does **not** relax them — it only widens the approved-action scope for this one
  workflow, and only after explicit human sign-off plus a pre-promotion
  checkpoint.

**Conditions / residual cautions before promotion:**
- The promotion must keep `supervisor.auto_execute` as the hard floor: Level 2 is
  authorized only when `auto_execute` is explicitly set `True` through the
  approved procedure — not by config alone.
- Constrain the task vocabulary (no arbitrary shell/command execution) to preserve
  the "trusted workflow" boundary.
- Keep `docs/vscode_workflow_setup.md` flagged LEGACY (currently write-locked;
  flagged by cross-reference) so operators do not confuse the legacy setup doc
  with the active bridge integration.
- First production run must be monitored; stop-and-report on any anomaly.

**Out of scope for this document:** any actual change to code, config, autonomy
level, or `auto_execute`. This is the plan only.
