# Nexus98 Phase 5 Integration Review - Analysis

Generated: 2026-07-17
Mode: READ-ONLY analysis (per handoff restrictions: recommend before
implementation; do not rewrite architecture, remove systems, or rename
core components). Builds on the completed architecture audit.

## 1. Current Architecture (as-built)

Entry / glue:
- core/supervisor.py::run_task(task) is the live end-to-end entry point.
  Flow today: detect_intent(task) -> route(task) via TaskRouter ->
  orchestrator.get_agent(decision) -> agent.on_messages(Ollama) ->
  clean_output. This is AGENT VALIDATION only.

Agent layer:
- core/agent_factory.py::AgentFactory(config_path) -> create_agent(name)
  builds AutoGen AssistantAgent with an OllamaChatCompletionClient.
- core/orchestrator.py::Orchestrator.load_agents() instantiates the team
  from factory.config["agents"]; get_agent/list_agents/describe_team.
- tools/agent_runner.py, tools/agent_selector.py: model selection + run
  helpers (standalone CLI helpers, not yet consumed by the live path).

Supervisor proposal engine (PRESENT but UNWIRED):
- build_task_plan, validate_task_plan, convert_plan_to_proposals,
  build_agent_proposal, approve_agent_proposal, approve_engine_request,
  execute_engine_request, create_engine_request exist in supervisor.py.
- core/project_engine.py::ProjectEngine implements the checkpoint/backup/
  execute/restore flow (create_request, approve_request, backup_file,
  write_file, execute_operation, restore_backup, history).

Intent routing:
- detect_intent(task) returns "action" for file/code/fs operations.
  run_task logs "Action request routed through Project Engine" but does
  NOT actually call ProjectEngine for those intents.

Config:
- Authoritative source is config/system_config.json (system_config.json +
  system_context.json + vscode_workflow.json are secondary/derived).
  models.json / models.yaml existence to be confirmed; risk of duplicate
  model settings if both are read.

## 2. Working Capabilities (verified by prior sessions)

- Ollama backend responds; AgentFactory loads; Orchestrator loads;
  7 agents configurable; agent creation + tool use tested; supervisor
  intent framework present; Project Engine framework present.

## 3. Remaining Gaps (Agent Validation -> Controlled Autonomous Execution)

G1 (HIGHEST): Live run path bypasses Project Engine. Action intents are
    detected but never converted to proposals/checkpoints/executions.
    The entire supervisor proposal/approval machinery is dead code in the
    live flow. This is the core Phase 5 gap.
G2: No approval gate in run_task. Even non-action intents run without a
    checkpoint; safe-by-default execution requires routing action intents
    through approve_engine_request before execute_engine_request.
G3: Config authority unclear. Multiple config files may define models;
    risk of drift. Need one authoritative source + migration.
G4 (env): autogen-ext + flask still not installed (manifest now declares
    them post-audit). Agent runtime + servers can't import until installed.
G5: No tests for agent runtime / supervisor / project_engine (test suite
    only covers memory + mouse + bridge).

## 4. Recommended Next Milestone

"Wire the Project Engine into the live Supervisor run path for action
intents" - the minimal, non-destructive change that converts Nexus98 from
Agent Validation to Controlled Autonomous Workflow Execution.

## 5. Exact Files Requiring Modification (minimal, additive)

- core/supervisor.py: in run_task, when intent == "action", call
  build_task_plan -> convert_plan_to_proposals -> approve_agent_proposal
  -> approve_engine_request -> execute_engine_request (using the already
  imported ProjectEngine `engine` instance at module scope). Keep the
  existing router/agent path for non-action intents. No new modules.
  (Do NOT rewrite the existing proposal functions; call them.)
- config/system_config.json: designate as authoritative; document which
  keys win. (Decision needed before editing - see G3/Risk.)
- tests/test_supervisor_phase5.py (NEW): dependency-aware (skip when
  autogen-ext missing) tests for run_task action routing + approval gate.

## 6. Risk Assessment

- Low risk: the proposal/approval functions already exist and are imported;
  wiring them is additive. The live agent path is unchanged for non-action.
- Medium: approval policy (auto-approve vs. require human) must be decided
  to avoid silent autonomous file writes. Default: require explicit approval
  or a config flag `supervisor.auto_execute` (safe default false).
- Medium: config consolidation could break running setups if both files are
  read; align on one source first.
- Env-blocked: G4 install is approval-gated; cannot validate import here.

## 7. Implementation Order (recommended, after approval)

1. Decide approval policy + designate authoritative config (config change).
2. Wire ProjectEngine into run_task for action intents (supervisor.py).
3. Add dependency-aware smoke/unit tests for the new path.
4. Update docs (handoffs / reports) with the standard execution flow.
5. (Deferred, approval-gated) install autogen-ext/flask to enable live import
   and end-to-end manual run; remove stale supervisor snapshots + root scratch.

## 8. Status

Read-only Phase 5 analysis COMPLETE. No files modified. Ready to implement
milestone (section 4/5) on approval, per handoff restrictions.
