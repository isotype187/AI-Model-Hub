# Phase 5 - Supervisor / ProjectEngine Integration

Status: IMPLEMENTED (2026-07-17)
Scope: Wire the existing ProjectEngine proposal / checkpoint / approval
machinery into the live `supervisor.run_task` path for **action intents**.
Change type: ADDITIVE ONLY. No existing systems removed or rewritten.

## Goal

Convert Nexus98 from "agent validation only" toward "controlled autonomous
workflow execution" by routing file/code action intents through the
already-present (but previously unwired) ProjectEngine pipeline.

## What changed (core/supervisor.py)

1. **Safety gate added** (module scope, non-destructive):
   `auto_execute = False`
   Action intents never auto-execute. They always create a proposal +
   checkpoint request and wait for approval.

2. **New helper `request_file_operation_blocking(...)`**:
   Always creates the engine request (proposal + checkpoint record on disk).
   Only calls `approve_engine_request` + `execute_engine_request` when
   `auto_execute` is explicitly `True`. When `False`, the request is held
   with `status = "awaiting_approval"`.

3. **New function `run_action_task(task, status)`**:
   - `build_task_plan(task, [step])`
   - `convert_plan_to_action_proposals(plan, agent="supervisor")`
   - for each proposal: `approve_agent_proposal(proposal)` (this writes the
     engine request / checkpoint record via `ProjectEngine.create_request`)
   - `request_file_operation_blocking(...)` routes each request through the
     safety gate.
   - Returns a structured result: `awaiting_approval` (default) or
     `executed` (only when `auto_execute=True`).

4. **`run_task` action branch wired**:
   When `detect_intent(task) == "action"`, `run_task` now calls
   `run_action_task(...)` and returns its result BEFORE reaching the Ollama /
   agent path. Non-action ("information") intents continue unchanged through
   the existing router -> orchestrator -> agent -> Ollama path.

## Safety invariants

- `supervisor.auto_execute` remains `False` by default. No file is written
  for an action intent unless a caller explicitly enables autonomous
  execution.
- Proposal + checkpoint records are persisted to the ProjectEngine history
  directory for every action intent, regardless of approval outcome.
- The existing `approve_engine_request` / `execute_engine_request` functions
  are untouched; the gate is applied in the new additive helper.

## Flow diagram

```
run_task(task)
  -> detect_intent(task)
       == "action"  --> run_action_task(task, status)
                          -> build_task_plan
                          -> convert_plan_to_action_proposals   (proposals)
                          -> approve_agent_proposal  (creates engine request / checkpoint)
                          -> request_file_operation_blocking
                               auto_execute=False -> awaiting_approval (no write)
                               auto_execute=True  -> approve + execute (writes file)
       == "information" --> router -> orchestrator -> agent -> Ollama (UNCHANGED)
```

## Validation

- Tests: `tests/test_supervisor_phase5.py` (dependency-aware; skips when the
  autogen runtime is unavailable).
- Environment note: the project venv (`D:\Nexus98\.venv`) references a removed
  Python 3.14 base and no system `python`/`py` is on PATH, so live test
  execution could not run in this session. Static structural validation was
  performed instead (see reports/PHASE5_IMPLEMENTATION_COMPLETE.md).

## Next steps (deferred, approval-gated)

- Install a working Python + `autogen-ext` / `flask` to enable live import and
  end-to-end `run_task` execution.
- Add a human approval UI hook reading `awaiting_approval` results.
- Consolidate config authority (system_config.json) and remove stale
  supervisor snapshots once the live path is verified.
