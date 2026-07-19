# Nexus98 - Extension Point Map

Status: READ-ONLY ANALYSIS (no code changes, no implementation)
Purpose: identify WHERE future systems should integrate, using existing seams.
Design source: docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md.

Each entry lists: the target capability, the best existing seam(s) today, the
proposed home, and the governing constraint. Nothing here is implemented.

---

## 1. Model / Provider Router
- Existing seams: `core/router.py` (keyword TaskRouter), `core/agent_factory.py`
  (Ollama client construction), `tools/model_router.py` (helper),
  `core/catalog.py` (model metadata).
- Proposed home: new `core/model_router/` exposing select(provider, model,
  strategy, override) with a metadata catalog feeding UI dropdowns.
- Constraint: user override must be first-class; selection is non-mutating to
  autonomy state.

## 2. Local / Cloud Model Switching
- Existing seams: Ollama-only access points (agent_factory, api/vscode_bridge,
  core/pipeline), `config/providers.json`.
- Proposed home: `core/providers/` with a common adapter interface
  (ollama, cloud_*), selected by the Model Router.
- Constraint: local-first default; cloud is opt-in and configuration-driven.

## 3. Agent Orchestration
- Existing seams: `core/orchestrator.py` (team load), `core/agent_registry.py`
  (status), `core/manager.py`, `core/pipeline.py`, `core/supervisor.py` (routes
  information tasks to orchestrator).
- Proposed home: extend orchestrator + fill empty `core/supervisor/` package;
  add strategy-aware team selection via the Model Router.
- Constraint: execution remains gated by the Governor/auto_execute floor.

## 4. Tool Discovery
- Existing seams: `tools/` (file_tools, git_tools, model_router, agent_runner),
  `docs/Nexus98_Tool_Registry.md`, tool bindings in `core/agent_factory.py`.
- Proposed home: `core/tools_registry/` (discovery + capability metadata),
  registered into agent tool sets.
- Constraint: discovered tools are declared, not auto-granted; risky tools gated.

## 5. Custom Tool Generation
- Existing seams: Project Engine (`core/project_engine.py`) for governed file
  writes; supervisor action path for proposals.
- Proposed home: `core/tool_gen/` producing tool code via Project Engine
  proposals (checkpoint -> write -> validate).
- Constraint: Medium/High risk - requires approval; never bypass Project Engine
  or the Governor.

## 6. Memory Database
- Existing seams: `core/memory_service.py` (SQLite data/db/memory.db) with
  store/query/verify/forget; `core/memory_migration.py`.
- Proposed home: memory_service is the canonical DB; add indexes/categories per
  docs/MEMORY_ARCHITECTURE_DESIGN.md (Active/Knowledge/Code/Recovery/Archive/Cache).
- Constraint: retire legacy `core/memory.py`; align with handoff #16 (DB over
  file sprawl).

## 7. Code Memory
- Existing seams: none dedicated; memory_service can store records; tools/
  file_tools can read modules.
- Proposed home: `core/code_memory/` - AST parse of Python/JSON/YAML tracking
  functions/classes/deps/hashes/summaries; persisted in the memory DB.
- Constraint: source files remain authoritative; code memory is derived/index.

## 8. Guardian Communication Layer
- Existing seams: `core/bridge_controller.py` (external companion process pattern
  under D:\AI\Nexus98_Bridge) is the closest analogue; git_tools (read/inspect).
- Proposed home: `core/guardian/` - a CLIENT to the separate Guardian project
  for health/recovery/git/memory-maintenance requests over controlled interfaces.
- Constraint: Guardian owns Git and recovery; Nexus98 requests, never assumes,
  those responsibilities. No merge.

## 9. Voice Integration
- Existing seams: none (no audio modules today).
- Proposed home: `core/voice/` (STT/TTS adapters) + a UI control in the future
  toolbar/control panel; routed like any other input to the supervisor.
- Constraint: local-first preferred; opt-in; no dependency additions without
  approval.

## 10. VS Code Integration
- Existing seams: `api/vscode_bridge.py`, `bridge/vscode_listener.py`,
  `bridge/worker.py`, `integrations/vscode_connector.py`,
  `vscode_extension/extension.js`; governed workflow vscode_task_send (L2).
- Proposed home: consolidate the bridge/API/connector roles behind one
  documented interface; extend via new governed workflows (not new permissions).
- Constraint: any new VS Code action becomes a governed workflow; preserve L2
  vscode_task_send.

## 11. Internal Shell / Editor
- Existing seams: Project Engine (governed writes), supervisor action path;
  no shell/editor surface exists.
- Proposed home: `core/dev_surface/` (shell exec + self-edit) + a future
  `ui/views/editor_view.py`.
- Constraint: HIGHEST risk tier (handoff High Risk / Guardian-protected). Shell
  and self-edit must be approval-gated, checkpointed, and Governor-authorized;
  implement last.

---

## Cross-Cutting Integration Rules
- All state-changing capabilities route through the Governor; observability stays
  read-only via `ui.autonomy_dashboard.snapshot()`.
- Prefer configuration-driven design; resolve paths via a future config_manager
  rather than hardcoding.
- Fill the reserved empty packages (event_bus, rule_engine, state_manager,
  config_manager, supervisor) as the natural homes for cross-cutting concerns.
- Every integration follows: checkpoint -> analyze -> document -> approve ->
  implement -> validate.
