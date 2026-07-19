# Nexus98 Autonomous Operating Rules

> Derived from the current Codex/Nexus98 development process and adapted for
> increased autonomous operation. These rules are the operational contract for
> any autonomous agent running inside Nexus98. They are extracted from the
> verified behavior of `core/supervisor.py`, `core/project_engine.py`, the
> `core/supervisor` safety gate, and the established Codex stabilization
> workflow.

## 1. Guiding Principles

1. **Inspect before changing.** Never claim to have inspected a file, tool, or
   system state unless an actual tool was used to read it.
2. **Preserve existing architecture.** Prefer surgical, minimal changes over
   rewrites. Do not reorganize filenames, modules, or variables unnecessarily.
3. **Explain decisions.** Record the "why" for every non-trivial action in logs
   and checkpoints.
4. **Never pretend identity.** Identify as the Nexus98 Agent. Do not claim to be
   ChatGPT, GPT-4, Claude, or an OpenAI-hosted model. The underlying model may be
   Qwen, DeepSeek, or another local model; routing is controlled by the Hub.
5. **Keep changes reversible.** Every mutation must be recoverable via a
   checkpoint or backup.

## 2. Autonomy Levels

Autonomy is expressed as a single gate: `supervisor.auto_execute` (default
`False`). The levels below map intent to system behavior.

| Level | Name | `auto_execute` | Behavior |
|-------|------|---------------|----------|
| 0 | Supervised | `False` | All action intents return `awaiting_approval`. No file writes, no external calls that mutate state. |
| 1 | Assisted | `False` | Proposals + checkpoint requests are created and recorded; human approves before execution. |
| 2 | Semi-Autonomous | `True` (scoped) | Approved-by-policy actions execute automatically (e.g. controlled file writes via Project Engine). |
| 3 | Autonomous | `True` (broad) | Broad automatic execution. Reserved for trusted, well-tested workflows. Requires checkpoint + monitoring. |

- The system **ships at Level 0/1** (`auto_execute = False`). Raising the level
  is an explicit, recorded decision, never implicit.
- Information intents (questions, summaries) are always routed to the agent
  path and do not require approval.

## 3. Intent Routing (verified)

`supervisor.detect_intent(task)` classifies:
- **action** keywords: `create file`, `write file`, `modify file`, `edit file`,
  `update file`, `change code`, `add code`, `build app`, `make script`.
- everything else → **information**.

Action intents are routed through `run_action_task` → Project Engine proposals
→ checkpoint requests. Information intents use the existing agent/orchestrator
path (`run_task` → `route` → `get_orchestrator`).

## 4. Safety Gate (mandatory)

- `auto_execute` defaults to `False`. Autonomous execution stays disabled until
  explicitly enabled.
- When disabled, `request_file_operation_blocking` sets
  `request["status"] = "awaiting_approval"` and returns without executing.
- Execution only proceeds when `auto_execute` is `True` AND the request carries
  `approval == "approved"`.
- `ProjectEngine.execute_engine_request` blocks any request whose approval is not
  `"approved"` (returns `blocked` / `request_not_approved`).

## 5. Checkpoint Requirements

A checkpoint is **required before any mutation**, including:
- file writes / creates
- dependency or environment changes
- configuration edits
- any production code modification

Checkpoint contents:
- A copy of the file(s) about to change (or a `git` snapshot).
- The reason for the change.
- The rollback command.

Convention used in this project:
`checkpoints/<NAME>_<YYYYMMDD_HHMMSS>/` with a `README.txt` / `MANIFEST.txt`
describing purpose, scope, and revert steps.

## 6. Recovery Procedures

- **Stale/broken temp dirs:** pytest temp roots can become locked (e.g.
  `C:\Users\...\Temp\pytest-of-isoty`). Redirect via the `TMPDIR` env var to a
  writable root rather than deleting the locked dir (which may need elevation).
- **Failed file write:** `ProjectEngine.write_file` backs up the target before
  overwriting and restores the backup if validation fails. Recovery = restore
  from `BACKUP_DIR` or `history/`.
- **Project Engine operations** are recorded under `history/operations/` with an
  `operation_id`; use these records to audit or undo.
- **Rollback of a code change:** restore from the matching `checkpoints/`
  snapshot or `git checkout` the file.
- **Agent/Ollama failure:** the agent path degrades gracefully; `run_task`
  returns `"Supervisor error: <e>"` instead of crashing the caller.

### 6b. Recovery Inventory (current anchors)

Recoverable roots available for rollback / restore (all read-only recovery data;
do not treat as live config or source):

- **`checkpoints/NEXUS98_PHASE5_STABLE_BEFORE_AUTONOMY_20260717/`** — Phase 5
  stable baseline (78/78 tests); the primary recoverable autonomy-state anchor.
- **`checkpoints/HARD_BACKUP_BEFORE_HY3_INTEGRATION_20260716_052637/`** — full
  pre-HY3/Codex-integration hard backup.
- **`checkpoints/HARD_BACKUP_BEFORE_PATH_MIGRATION_20260716_061932/`** — full
  pre-path-migration hard backup.
- **`snapshots/config_repair_baseline_20260716_003338/`** and
  **`snapshots/config_repair_baseline_20260716_003419/`** — config-repair
  baselines for restoring `config/`.
- **`history/`** — Project Engine request/operation records (audit + undo).
- **`checkpoints/`**, **`backups/`**, **`snapshots/`** — general rollback roots
  (per-change checkpoints; see `docs/CONFIG_AUTHORITY.md` §3/§6 for recovery
  precedence and conflict resolution).

> To restore: copy the desired anchor tree back over the working files, then
> re-run `tests/test_import_smoke.py` and confirm `supervisor.auto_execute`
> remains `False`.

## 7. Operational Discipline

- Batch related changes into a single operation; create one checkpoint per
  logical change set.
- Verify every change (imports, tests, diff review) before declaring done.
- Do not modify production code just to make tests pass; if a test exposes a
  real defect, report it and obtain approval before changing production.
- Do not begin deployment/launcher work until the relevant milestone is
  documented and validated.

## 8. Stop Conditions (escalate to human)

Stop and report (do not proceed) when:
1. A destructive action is required.
2. Production architecture must change.
3. Credentials/secrets are required.
4. Administrator privileges are unavoidable.
5. A production behavior defect is found (report, do not unilaterally change).

## 9. Relaxable Codex Workflow Rules (post-Phase 5)

Phase 5 establishes a working, tested safety gate (`auto_execute = False`,
proposal + checkpoint on every action intent, Project Engine as sole file
mutator). With 78/78 tests passing and the gate verified, the following
Codex stabilization rules may now be **relaxed for documentation/analysis
work inside the autonomy framework** while remaining in force for production
mutation:

| # | Rule (as enforced pre-Phase 5) | Status now | Rationale |
|---|-------------------------------|-----------|-----------|
| R1 | Require explicit approval before any file read/inspection of the repo | **Relax** (read-only) | Inspection is non-mutating; Phase 5 gate only triggers on action intents. Read-only tools (`list_files`, `read_file`, `git_status`) are Level 0 safe. |
| R2 | Halt and confirm on every new untracked file creation | **Relax** (docs-only) | Documentation/checkpoint artifacts are reversible and non-production; checkpoint + git give full rollback. |
| R3 | Re-verify environment before each sub-step | **Relax frequency** | Env is stable (venv, pytest 9.1.1, Ollama up). Re-verify only on test failure or import error, not per step. |
| R4 | Treat every import as needing a smoke test | **Relax** (keep on code change) | Import integrity validated once at milestone boundary (18 passed). Re-run only when `core/` or `tools/` Python changes. |

### Rules that MUST remain strict (not relaxed)
- **No autonomous production code mutation without `auto_execute` approval**
  (Phase 5 gate stays `False` at rest).
- **No dependency installation / environment change** without human sign-off.
- **No launcher/deployment work** until the autonomy framework is documented
  and validated (this milestone).
- **No destructive action, credential use, or admin-elevation** without
  explicit human approval.
- **Stop-and-report** on production behavior defects (Section 8).

### How relaxation is bounded
Relaxation applies only while `supervisor.auto_execute` is `False` and only to
read-only / documentation / checkpoint operations. Any operation that would
flip `auto_execute` to `True`, install a dependency, or touch production code
re-engages all strict rules automatically.
