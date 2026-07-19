# Nexus98 - Codebase Intelligence Report

Status: READ-ONLY REPOSITORY INTELLIGENCE ANALYSIS (documentation only; no source/config/test/Guardian/dependency modifications)
Source of truth: docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md (v2) and the seven companion architecture docs.
Generated: 2026-07-18. Repo root: D:\Nexus98.

This report inventories the live repository as it exists today. It does not change any file. Every
recommended implementation step should still follow the handoff Development Rule:
checkpoint -> analyze -> document -> approve -> implement -> validate.

## 1. Repository Structure

### 1.1 Active (source-relevant) folders
- core/           - backend (64 *.py files incl. autonomy/, scaffolds). Primary engine.
- ui/             - Tkinter/ttk Command Center shell + view builders + read-only dashboard.
- api/            - Flask VS Code bridge entry (vscode_bridge.py) + backups.
- bridge/         - file-drop listener/worker (vscode_listener.py, worker.py) + responses/.
- integrations/   - vscode_connector.py (HTTP client to the bridge API).
- tools/          - file_tools, git_tools, model_router, agent_runner, agent_selector,
                    continue_sync, health_check, mouse_agent/, ollama_manager/.
- runtime/        - generate_models.py + run-ai.ps1 (catalog generation).
- scripts/        - PowerShell launch/setup for the VS Code workflow.
- vscode_extension/ - JS extension (extension.js) + package.json + node_modules.
- config/         - JSON/YAML system config + model/provider/workflow definitions.
- tests/          - 13 pytest modules / 9 active test files; 96 tests passing.
- docs/ handoffs/ - design + handoff documentation (authoritative intent).

### 1.2 State / history (recoverable, NOT source)
- history/, checkpoints/ (54 dirs), snapshots/ (4), backups/, agent_logs/,
  logs/, reports/, data/ (SQLite DBs + system_state.json).

### 1.3 Superseded / archive (excluded from architecture)
- archive/, AI_Model_Hub_archive/, diagnostic_parts/, ollama_cleanup_backups/,
  .venv_broken_*, build/, dist/, plus many *.pre_nexus98_migration_backup files
  and *.backup* snapshots.

### 1.4 Entry points
- main.py -> from ui.main_window import launch_ui (crash-logged to D:\Nexus98\logs\startup_crash.log). PRIMARY GUI.
- debug_launch.py -> launch_ui() (dev harness).
- api/vscode_bridge.py -> Flask app on 127.0.0.1:8000 (health, /v1/models, /v1/chat/completions).
- bridge/vscode_listener.py + bridge/worker.py -> file-drop task processors (via core.bridge).
- core/api_server.py, core/server.py -> additional server entry points (127.0.0.1).
- runtime/generate_models.py -> model catalog generation.
- launcher.py -> stub only ('AI Model Hub launcher ready'); not a real entry point.

## 2. Python Module Map

### 2.1 Core backend (purpose / imports / relationships)
- core/supervisor.py (706 lines) - intent detection + task routing. Imports router, identity,
  orchestrator, vscode_bridge, project_engine. Two paths: run_task (info) -> orchestrator/agents;
  run_action_task -> proposals -> Project Engine. auto_execute is the code-level safety floor.
- core/project_engine.py (345) - SOLE file-mutation authority. backup -> write -> validate,
  request/approve lifecycle, operation logging to history/, restore_backup. No imports of other core.
- core/router.py (85) - TaskRouter.route() keyword rule mapping. Standalone; ROOT hardcoded.
- core/orchestrator.py (29) - builds the agent team via AgentFactory(config/models.yaml).
- core/agent_factory.py (53) - AutoGen AssistantAgents (autogen_agentchat/autogen_ext) + Ollama
  client (localhost:11434); binds tools.file_tools, tools.git_tools. Import-time dep on AutoGen.
- core/agent_registry.py (66) - static AGENTS dict + list_agents; drives the Agents view.
- core/manager.py (11) - thin wrapper over AgentFactory.
- core/pipeline.py (94) - AgentPipeline with direct HTTP to Ollama generate (no provider abstraction).
- core/bridge.py (74) - file-drop bridge: imports supervisor.run_task + core.command.Command.
- core/bridge_controller.py (87) - enable/disable/start bridge; get_status()->{online,enabled} via
  HTTP to D:\AI\Nexus98_Bridge external venv; safe fallback.
- core/vscode_bridge.py (106; NOTE: also duplicated under api/) - Flask bridge surface.
- core/memory_service.py (383) - SQLite-backed MemoryService (data/db/memory.db).
- core/memory.py (55) - legacy Memory class; wraps memory_service.
- core/memory_migration.py (142) - migrate/rollback legacy JSON -> DB.
- core/catalog.py (90) - model catalog; imports discovery + db.
- core/discovery.py (50) - imports ollama.get_installed_models.
- core/inspector.py (37) - imports hardware + categories.
- core/recommender.py (18) - imports hardware.
- core/display.py (91) - model formatting.
- core/db.py (125) - SQLite models.db access; DB_PATH hardcoded.
- core/ollama.py (51), core/huggingface.py (19), core/github.py (19), core/gguf.py (19),
  core/downloader.py (19) - provider/discovery helpers.
- core/config.py (21) - points at D:\Nexus98\config.json (DIFFERENT file from system_config.json).
- core/queue.py (48) - imports installer + logs.
- core/favorites.py (21), core/status.py (20), core/resume.py (14), core/logs.py (14),
  core/cache.py (13), core/identity.py (12), core/boot.py (12), core/hardware.py (39),
  core/categories.py (9), core/search.py (17), core/command.py (44), core/workers.py (25),
  core/tray.py (24), core/autostart.py (17), core/installer.py (40), core/updater.py (1),
  core/logger.py (1) - supporting modules.
- core/api_server.py (52), core/server.py (56) - secondary HTTP servers; both import core.bridge.execute.

### 2.2 Autonomy stack (core/autonomy/)
- governor.py (167) - SOLE writer of autonomy state (supervisor.auto_execute + system_config intent).
  Methods: current_level, request_level_change (policies-gated), emergency_stop. Imports audit/levels/policies.
- levels.py (48) - PURE DATA (L0-L4), TRUSTED_WORKFLOWS_L2={vscode_task_send}, L3/L4 empty.
- policies.py (62) - approval/scope engine (DECIDES only; no writes).
- audit.py (44) - append-only history/autonomy/audit.log. NO mutation.

### 2.3 UI (ui/)
- main_window.py (72) - composition/entry only; builds ttk.Notebook (7 tabs). Imports theme + ui.views.*.
- theme.py (49) - centralized clam dark palette/fonts/styles.
- autonomy_dashboard.py (166) - read-only snapshot() consumed by Autonomy + Dashboard views.
  Imports core.autonomy.{governor,levels,audit}. NO mutation.
- autonomy_panel.py (83) - request-capable (submit_level_request -> governor) but UNWIRED in shell.
- views/ - dashboard_view, models_view, supervisor_view, agents_view, bridge_view, autonomy_view,
  system_view. Each imports a narrow core slice (catalog, agent_registry, bridge_controller, supervisor,
  autonomy_dashboard). No Governor mutation in views.
- main_window_BEFORE_STATUS.py (198) - STALE sibling (not used by launch_ui).

### 2.4 Tools / integrations (tools/, integrations/)
- tools/file_tools.py, tools/git_tools.py, tools/model_router.py, tools/agent_runner.py,
  tools/agent_selector.py, tools/continue_sync.py, tools/health_check.py - each hardcodes D:\Nexus98.
- integrations/vscode_connector.py - HTTP client to 127.0.0.1:8000.

### 2.5 Relationship summary
supervisor ~> router + orchestrator + agent_factory + vscode_bridge + project_engine
project_engine (standalone, writes) ~> history/ + backups/
governor (standalone writer) ~> supervisor.auto_execute + system_config.json
ui (read-only) ~> autonomy_dashboard.snapshot() ~> governor/levels/audit
api/vscode_bridge ~> supervisor.run_task ~> orchestrator/agents
bridge/* ~> core.bridge ~> supervisor.run_task

## 3. Configuration Map

| File | Format | Owner | Purpose |
|------|--------|-------|---------|
| config/system_config.json | JSON | Autonomy authority | project/version/mode/autonomy_level/ safety gates. GOVERNS autonomy. |
| config/providers.json | JSON | Provider flags | ollama/huggingface/github booleans. |
| config/settings.json | JSON | UI/settings | theme=dark, auto_update=true. |
| config/models.yaml | YAML | Agent->model map | 7 agents (architect/coder/researcher/reviewer/tester/documentation/vision) -> Ollama models. |
| config/models.json | JSON | Model catalog | 6 models w/ category, priority, context, tags, roles. |
| config/system_context.json | JSON | Phase/context | completed milestones, agent assignments, next_phase. |
| config/mouse_agent.json | JSON | Mouse tool | timings, safety bounds, logging, screenshot dirs. |
| config/vscode_workflow.json | JSON | VS Code bridge | desktop/laptop roles, extensions, workspace, tunnel. |
| config/vscode.json | JSON | Bridge metadata | 'AI Hub VS Code Bridge', endpoint 127.0.0.1:8000. |
| tools/ollama_manager/config.json | JSON | Ollama manager | internal to ollama_manager. |

Ownership notes / conflicts:
- Split authority: system_config.json is the autonomy authority, but core/config.py points at a
  DIFFERENT file (D:\Nexus98\config.json) and auto-writes it on first load. Unresolved.
- Duplicate context files: system_context.json vs system_context_before_autogen.json.
- Duplicate model files: models.yaml (agents) vs models.json (catalog) - two sources of model truth.
- Legacy backups in config/: models_before_small_test_models.yaml, system_context_before_autogen.json.

## 4. UI Architecture

### 4.1 Shell (ui/main_window.py)
- launch_ui(): tk.Tk() titled 'Nexus98 Command Center', geometry 1600x950, theme.apply_theme.
- Title bar + ttk.Notebook with 7 tabs: Dashboard, Models, Supervisor, Agents, Bridge, Autonomy, Logs/System.
- Each tab hosts one view builder from ui.views/. Coordinated refresh() (models + agents) on search trace.
- Composition only; no backend/autonomy logic. Preserves launch_ui() contract.

### 4.2 Views
- dashboard_view - read-only overview; imports autonomy_dashboard, bridge_controller, agent_registry, catalog.
- models_view - left search/list + center inspector; imports catalog, inspector, recommender, display.
- supervisor_view - task console; imports supervisor.run_task + tray.
- agents_view - imports agent_registry.list_agents.
- bridge_view - imports bridge_controller get/enable/disable.
- autonomy_view - STRICTLY READ-ONLY via autonomy_dashboard.snapshot() only.
- system_view - read-only logs/system.

### 4.3 Panels
- autonomy_dashboard.py - read-only snapshot() (8 fields: level, workflows, pending, approvals, audit,
  checkpoint, rollback, emergency-stop). Single observability surface.
- autonomy_panel.py - request-capable but NOT wired into main_window (observability still read-only).

### 4.4 Data flow
UI views -> read via core slice calls + autonomy_dashboard.snapshot() (Governor read-only).
State-changing requests (autonomy_panel.submit_level_request) -> governor.request_level_change
(policies-gated, human approval + checkpoint) -> governor writes supervisor.auto_execute + system_config.
UI NEVER writes autonomy state directly. Governor is the sole authority/writer.

## 5. Backend Architecture

- Supervisor: info path -> orchestrator/agents; action path -> proposals -> Project Engine.
  auto_execute = code safety floor. detect_intent, run_task, run_action_task, approve*, execute*.
- Project Engine: file-mutation authority. Request -> approve -> validate -> write; backup before write;
  restore_backup for recovery. Logs to history/.
- Router: keyword rule-based TaskRouter.route() (no strategy/provider abstraction).
- Agents: AgentFactory (AutoGen) + Orchestrator (team) + agent_registry (status) + manager + pipeline.
  Hard import-time dependency on autogen_agentchat/autogen_ext; Ollama host hardcoded localhost:11434.
- Memory: memory_service (SQLite, canonical) + legacy memory.py + memory_migration. Generic records;
  no code-memory index. Category/confidence/importance/verification_status fields exist.
- Bridge: bridge_controller (external venv under D:\AI\Nexus98_Bridge) + api/vscode_bridge (Flask 8000)
  + bridge/* (file-drop) + integrations/vscode_connector (client). Governed workflow: vscode_task_send (L2).
- Autonomy: Governor (sole writer), levels (data), policies (decides), audit (append-only).
  Live state: autonomy_level='trusted' (L2), auto_execute=True; all safety gates True.

## 6. Duplicate & Legacy Detection

### 6.1 Live stale / legacy modules (NOT in archive/snapshots/backups)
- core/supervisor_before_final_autogen_fix.py - stale supervisor copy (unimported).
- ui/main_window_BEFORE_STATUS.py - stale UI shell (unimported).
- core/orchestrator.py.backup_20260709_192725 - stale backup.
- api/vscode_bridge.backup.py, api/vscode_bridge.pre_ollama_fix.backup.py,
  api/vscode_bridge.py.backup_before_chat_fix, api/vscode_bridge.py.backup_before_chat_fix2 - API backups.
- tools/*.pre_nexus98_migration_backup (agent_runner, agent_selector, continue_sync, file_tools,
  git_tools, model_router, ollama_manager/migrate_execute, ollama-startup.ps1).
- scripts/launch_vscode_laptop.ps1.pre_nexus98_migration_backup, scripts/setup_vscode_workflow.ps1.*.
- data/db/models.db.backup_20260707_042435 - DB backup beside live DB.
- docs/NEXUS98_Tool_Registry.md.bak, tests/test_vscode_workflow_config.py.bak.

### 6.2 Root-level one-off patch scripts (brittle; should be retired)
bridge_toggle_patch.py, bridge_ui_patch.py, clean_bridge_toggle_patch.py, fast_vertical_switch_patch.py,
fix_switch_logic.py, patch_scanner.py, real_toggle_patch.py, vertical_bridge_switch_patch.py,
vertical_rect_switch.py - mutate ui/main_window.py by string patching. Risk of editing wrong file.

### 6.3 Duplicate logic
- ollama_models() defined twice: tools/model_router.py:11 AND api/vscode_bridge.py:80
  (plus copies in api backups). Two model listers, divergent.
- vscode_bridge duplicated: core/vscode_bridge.py AND api/vscode_bridge.py (Flask surface).
- Duplicate memory backends: core/memory.py + core/memory_service.py.

## 7. Dependency Map

### 7.1 Third-party (external) packages observed
- autogen_agentchat, autogen_core, autogen_ext - agent runtime (import-time; tests skip if missing).
- flask - VS Code bridge HTTP server.
- requests - HTTP client (bridge connector, bridge_controller, vscode_bridge).
- psutil - bridge process status.
- pystray, pynput (+pynput.keyboard/mouse) - system tray + mouse agent.
- PIL (Pillow) - image/vision handling.
- huggingface_hub - HuggingFace discovery.
- sqlite3 (stdlib) - memory + model DBs.
- yaml (PyYAML) - config parsing.
- tkinter/ttk (stdlib) - UI toolkit. No other UI deps (handoff constraint: Tkinter only, no new deps).

### 7.2 Internal dependency direction
- UI -> core (read-only) and never the reverse.
- supervisor -> router, orchestrator, agent_factory, vscode_bridge, project_engine.
- governor -> supervisor.auto_execute (text rewrite) + system_config.json.
- Empty scaffold packages (no public API yet): core/event_bus/, core/rule_engine/,
  core/state_manager/, core/config_manager/, core/supervisor/.

### 7.3 Environment coupling
- Hardcoded D:\Nexus98 in 25 places across core/; D:\AI\Nexus98_Bridge in bridge_controller (2 refs).
- External tool subprocess: ollama (11434), git (cwd D:/Nexus98), python/pip.
- C:\Users\isoty\.continue, %USERPROFILE% references in tools/continue_sync.py, tools/health_check.py.

## 8. Code Memory Foundation

The handoff (#16-17) requires DB-backed memory and a code-understanding index. memory_service.py is the
canonical SQLite store; there is currently NO code-memory index. Recommendation (build on memory_service,
source files remain authoritative):

### 8.1 Database structure
- Extend the existing memories table model (or add a dedicated code_index table) rather than a new DB, to
  preserve the single-SQLite mandate and migration tooling.
- Proposed table code_index:
  CREATE TABLE code_index (
    symbol_id TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    file_path TEXT NOT NULL,
    language TEXT NOT NULL,            -- python/json/yaml/config
    symbol_type TEXT NOT NULL,         -- module/function/class/method/config_key
    name TEXT NOT NULL,
    qualified_name TEXT NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    parent_symbol TEXT,                -- for nesting (class->method)
    source_hash TEXT NOT NULL,         -- sha256 of file at index time
    code_hash TEXT NOT NULL,           -- sha256 of the symbol body (change detection)
    summary TEXT,                      -- LLM/static summary
    dependencies TEXT,                 -- JSON list of imported/referenced symbols
    docstring TEXT,
    last_indexed TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    importance INTEGER DEFAULT 3
  );
- Join to memories via source/path; keep code_index as derived/index (rebuildable), source files authoritative.

### 8.2 Indexing approach
- AST parse Python via ast module (stdlib); JSON/YAML via json/PyYAML; walk config/ + core/ + ui/ + tools/.
- Incremental indexing keyed on source_hash + code_hash: skip unchanged files/symbols; re-index only deltas.
- Store dependencies as resolved symbol references where possible, else raw import strings.
- Trigger: on Project Engine write (post-validate) and on explicit 'reindex' action (governed, not automatic).
- Avoid file sprawl: index lives in data/db/memory.db (or a sibling code_memory.db), never thousands of files.

### 8.3 Metadata fields (per symbol)
- Identity: symbol_id, project, file_path, language, symbol_type, name, qualified_name, parent_symbol.
- Location: start_line, end_line.
- Integrity: source_hash, code_hash, last_indexed.
- Understanding: summary, docstring, dependencies (JSON), confidence, importance.
- Indexes: code_index(file_path), code_index(language), code_index(symbol_type),
  code_index(source_hash), code_index(qualified_name).

## 9. Technical Debt Ranking

Ranked by risk to portability, safety, and maintenance (HIGH -> MEDIUM -> LOW).

HIGH
1. Hardcoded absolute paths (25 in core/, D:\AI in bridge_controller, C:\Users\isoty in tools/) -
   blocks Docker/multi-node/relocation. No path/config abstraction.
2. Split config authority (system_config.json vs core/config.py's D:\Nexus98\config.json auto-write) -
   ambiguity over the real autonomy/config source of truth.
3. Stale/duplicate supervisor + UI shells (supervisor_before_final_autogen_fix.py,
   main_window_BEFORE_STATUS.py) - risk of editing/importing the wrong module.
4. Duplicate ollama_models() + dual vscode_bridge (core/ vs api/) - divergent logic, port confusion.

MEDIUM
5. Root-level one-off patch scripts string-patching ui/main_window.py - brittle, should be retired.
6. Dual memory backends (memory.py + memory_service.py) with unclear migration retirement.
7. Four overlapping server entry points (api/vscode_bridge, core/api_server, core/server, bridge/*) -
   port/role confusion.
8. Checkpoint sprawl (54 checkpoints/, snapshots/, backups/) contradicts handoff #16 DB-forward mandate.
9. Duplicate model/context configs (models.yaml vs models.json; system_context vs *_before_autogen).

LOW
10. Legacy 'AI Model Hub' strings in main.py ('Starting AI Model Hub...'), launcher.py, api/vscode_bridge
    health ('AI Hub Bridge'), config/vscode.json ('AI Hub VS Code Bridge'), tools/health_check.py banner.
11. Empty scaffold packages (event_bus/rule_engine/state_manager/config_manager/supervisor) declare intent
    but expose no API.
12. core/config.py DEFAULT auto-writes a config file on first load (implicit side effect).
13. UI untested (no GUI harness); agent/orchestrator tests skipped without AutoGen runtime.

## 10. Recommended Implementation Order

Follow the handoff Development Rule for every step. Sequences infrastructure before UX/Guardian work.

1. Foundation hardening (low UX risk, unblocks everything)
   - Centralize path/config resolution via config_manager (remove hardcoded D:\ paths).
   - Resolve the split config authority: pick system_config.json (or a new canonical) and retire core/config.py's auto-write.
   - Retire/relocate stale legacy modules + root patch scripts (with checkpoints).
   - Consolidate server/entry roles; document ports.
2. Model Router + Providers (handoff #7)
   - Unified select(provider, model, strategy, override) + metadata catalog; user override first-class.
   - Collapse duplicate ollama_models()/vscode_bridge into the router/provider seam.
3. Strategy System (#8) composed with the router.
4. Memory maturation (#16-17)
   - Implement code_index on top of memory_service; AST-based incremental indexing.
   - Consolidate checkpoint/DB storage; align with MEMORY_ARCHITECTURE_DESIGN.md; retire legacy memory.py.
5. Guardian communication layer (#4-5)
   - Nexus98 Guardian CLIENT only (read-only status first). No merge, no Git ownership transfer.
   - Requires the Guardian request/response contract (see GUARDIAN_DEVELOPMENT_ROADMAP Phase A).
6. Context continuity: WWW + Don't Forget (#14-15) on top of memory + Guardian client.
7. UI evolution (#9-13)
   - Conversation system + chat-first shell, toolbar, consolidated control panel - ONLY after the frozen
     GUI behavior spec is finalized/approved. Wire autonomy_panel through the Governor.
8. Internal development surface (#11) + tool discovery/generation - LAST, High Risk / Guardian-protected.

Sequencing rationale: paths/router/memory unblock the UI and Guardian integration; the chat-first pivot and
self-editing are deferred until foundations and the frozen GUI spec are approved. Guardian client work (step 5)
is gated by Guardian's own Phase A contract definition (separate project).

*End of report. No production files were modified.*
