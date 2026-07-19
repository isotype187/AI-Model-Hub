# Nexus98 - Current Architecture Map

Status: READ-ONLY ARCHITECTURE AUDIT (analysis only; no code changes)
Design source of truth: docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md
Supporting design: docs/Nexus98_Vision_Architecture.md,
docs/MEMORY_ARCHITECTURE_DESIGN.md, docs/PHASE5_SUPERVISOR_PROJECTENGINE.md,
docs/PHASE8_AUTONOMY_GOVERNOR_DESIGN.md, handoffs/*.

This map reflects the repository as it exists now. It does not modify the
handoff, production code, config, or tests.

---

## 1. Current Folder Structure (source-relevant)

Source:
- `main.py` - launcher/entry wrapper.
- `core/` - backend (60 py files): supervisor, project_engine, router,
  orchestrator, agent_factory/registry, memory/memory_service, ollama, catalog,
  bridge_controller, autonomy/ (governor stack), plus scaffold packages
  (event_bus/, rule_engine/, state_manager/, config_manager/, supervisor/).
- `ui/` - Tkinter Command Center: main_window.py (shell), theme.py,
  autonomy_dashboard.py (read-only), autonomy_panel.py (request-capable),
  views/ (dashboard, models, supervisor, agents, bridge, autonomy, system).
- `api/` - Flask VSCode bridge (vscode_bridge.py) + backups.
- `bridge/` - file-drop listener/worker (vscode_listener.py, worker.py).
- `integrations/` - vscode_connector.py (HTTP client to bridge/API).
- `tools/` - file/git/model tools, agent runner/selector, model_router,
  continue_sync, ollama_manager.
- `runtime/` - generate_models.py (+ run-ai.ps1).
- `config/` - system_config.json (autonomy authority), models.yaml/json,
  providers.json, settings.json, system_context.json, mouse_agent.json,
  vscode_workflow.json.
- `vscode_extension/` - JS extension (extension.js).
- `tests/` - 9 pytest modules (96 tests).
- `scripts/` - PowerShell launch/setup.

State / history (recoverable, not source):
- `history/`, `checkpoints/` (54 dirs), `snapshots/` (4), `backups/`,
  `agent_logs/`, `logs/`, `reports/`, `data/` (db + system_state.json).

Superseded / archive (NOT current architecture):
- `AI_Model_Hub_archive/`, `archive/`, `diagnostic_parts/`,
  `ollama_cleanup_backups/`, `.venv_broken_*`, and various
  `AI_Model_Hub_*` inventory files.

---

## 2. Entry Points

- `main.py` -> `from ui.main_window import launch_ui; launch_ui()` (crash-logged
  to logs/startup_crash.log). Primary GUI entry.
- `debug_launch.py` -> `launch_ui()` (dev harness).
- `api/vscode_bridge.py` - Flask app (`health`, `models`, `chat`); the bridge
  HTTP surface (127.0.0.1:8765 per bridge_controller; API 127.0.0.1:8000 per
  connector).
- `bridge/vscode_listener.py`, `bridge/worker.py` - file-drop task processors.
- `core/api_server.py`, `core/server.py` - additional server entry points
  (127.0.0.1) present in tree.
- `runtime/generate_models.py` - model catalog generation.

---

## 3. main.py Execution Flow

1. Define crash log path (hardcoded `D:\Nexus98\logs\startup_crash.log`).
2. `main()` prints startup banner.
3. Import `launch_ui` from `ui.main_window`.
4. `launch_ui()`:
   - `tk.Tk()`, title "Nexus98 Command Center", geometry 1600x950.
   - `theme.apply_theme(app)` (ttk clam dark theme).
   - Build title bar + `ttk.Notebook` with 7 tabs (Dashboard, Models,
     Supervisor, Agents, Bridge, Autonomy, Logs/System).
   - Each tab hosts a view builder from `ui/views/`.
   - Wire coordinated `refresh()` (models + agents), search trace, footer
     buttons; run initial `refresh()`; enter `app.mainloop()`.
5. Any exception is printed and appended to the crash log; user is prompted.

---

## 4. UI Architecture

- Framework: Tkinter + ttk (clam theme). No external UI toolkit; no deps.
- Shell: `ui/main_window.py` is composition/entry only (Phase 9 Step 1-2
  refactor). View builders live in `ui/views/` (one class + `build()` each):
  models_view, supervisor_view, agents_view, bridge_view, autonomy_view,
  dashboard_view, system_view.
- Theming: `ui/theme.py` centralizes palette/fonts/styles.
- Autonomy observability: `ui/autonomy_dashboard.py` exposes read-only
  `snapshot()` + field helpers; the Autonomy and Dashboard views consume it and
  never mutate governed state.
- Request-capable panel: `ui/autonomy_panel.py` exists (submit_level_request ->
  governor) but is NOT wired into the current shell (observability is read-only).
- Legacy: `ui/main_window_BEFORE_STATUS.py` remains as a stale sibling.

---

## 5. Backend Architecture

- Supervisor (`core/supervisor.py`): intent detection (`detect_intent`),
  `run_task` (information path -> orchestrator/agents) and `run_action_task`
  (action path -> proposals -> Project Engine). `auto_execute` is the code-level
  safety floor.
- Project Engine (`core/project_engine.py`): file-mutation authority -
  backup -> write -> validate, request/approve lifecycle, operation logging to
  history/, restore_backup for recovery.
- Router (`core/router.py`): keyword rule-based `TaskRouter.route()` mapping
  tasks to roles (architect/coder/reviewer/...); logs to logs/routing.log.
- Orchestrator (`core/orchestrator.py`): loads an agent team from
  config/models.yaml via AgentFactory; get/list agents.
- Bridge control (`core/bridge_controller.py`): enable/disable/start bridge,
  `get_status()` -> {online, enabled} (HTTP, safe fallback).
- Catalog/models pipeline (`core/catalog.py`, `core/discovery.py`,
  `core/recommender.py`, `core/inspector.py`, `core/display.py`, `core/db.py`).
- Additional servers/APIs: `core/api_server.py`, `core/server.py`,
  `core/pipeline.py` (AgentPipeline with direct Ollama generate calls).
- Scaffold packages (present but empty of public API): `core/event_bus/`,
  `core/rule_engine/`, `core/state_manager/`, `core/config_manager/`,
  `core/supervisor/` - reserved extension points.

---

## 6. Agent Systems

- AgentFactory (`core/agent_factory.py`): builds AutoGen AssistantAgents from
  config/models.yaml, using OllamaChatCompletionClient
  (host http://localhost:11434) and tool bindings (file_tools, git_tools).
- Orchestrator (`core/orchestrator.py`): registers the configured agent team.
- Agent registry (`core/agent_registry.py`): get_agents/list_agents +
  status tracking (drives the Agents view).
- Manager agent (`core/manager.py`), pipeline (`core/pipeline.py`), and
  tools/agent_runner.py / agent_selector.py provide execution helpers.
- Mouse agent (`core/mouse_agent.py`, `core/mouse_control.py`): start/stop/status
  for the desktop mouse tool (see docs/MOUSE_AGENT_SYSTEM.md).

---

## 7. Model Systems

- Providers: Ollama (primary, local), HuggingFace, GitHub discovery
  (`core/discovery.py`, `core/ollama.py`, `core/huggingface.py`,
  `core/github.py`, `core/gguf.py`).
- Catalog: build/sync/get catalog (`core/catalog.py`) backed by
  `data/db/models.db` (`core/db.py`); recommendations via `core/recommender.py`.
- Config: `config/models.yaml` (agent->model mapping), `config/models.json`,
  `config/providers.json`.
- Model access at runtime: AutoGen client in agent_factory; direct HTTP to
  Ollama in api/vscode_bridge.py and core/pipeline.py.
- No unified provider/model router abstraction yet (tools/model_router.py is a
  helper, not the handoff's "Model Router").

---

## 8. Memory Systems

- MemoryService (`core/memory_service.py`): SQLite-backed store
  (data/db/memory.db) with store/update/query/get/verify/delete/forget/export/
  import + integrity_check. This is the modern memory layer aligned with
  docs/MEMORY_ARCHITECTURE_DESIGN.md.
- Legacy Memory (`core/memory.py`): simple `Memory` class (save/load/close).
- Migration (`core/memory_migration.py`): migrate/rollback from legacy
  agent_memory.json to the DB, with logging.
- Recovery/continuity surfaces today are file-based: history/, checkpoints/,
  snapshots/, backups/, plus data/system_state.json.

---

## 9. Autonomy / Governor Architecture

- Governor (`core/autonomy/governor.py`): SOLE writer of autonomy state -
  supervisor.auto_execute (code floor) + config autonomy_level intent.
  `request_level_change` (policies-gated, human-approval + checkpoint required),
  `emergency_stop`, `current_level`.
- Levels (`core/autonomy/levels.py`): L0-L4, TRUSTED_WORKFLOWS_L2 =
  {vscode_task_send}; L3/L4 seed empty.
- Policies (`core/autonomy/policies.py`): approval/scope engine (decides only).
- Audit (`core/autonomy/audit.py`): append-only history/autonomy/audit.log.
- Observability: `ui/autonomy_dashboard.snapshot()` (read-only) surfaces level,
  workflows, pending/approval/audit, checkpoint, rollback, emergency-stop.
- Current live state: autonomy_level "trusted" (L2), auto_execute True; safety
  gates all True in config/system_config.json.

---

## 10. Existing Guardian Relationship

- Per the handoff, Guardian is a SEPARATE project, NOT merged into Nexus98.
- No `guardian/` module or Guardian client exists in the repo today.
- Guardian-owned responsibilities (Git operations, recovery points, health,
  memory maintenance) are currently either handled ad hoc inside Nexus98
  (checkpoints/, history/, backups/, git_tools) or not yet implemented.
- A `core/bridge_controller.py` references an external bridge venv/script under
  `D:\AI\Nexus98_Bridge\...`, indicating an external companion process pattern -
  the closest existing analogue to an "external Guardian" integration seam.
- No dedicated Guardian communication layer exists yet.

---

## 11. External Integrations

- VS Code: `api/vscode_bridge.py` (Flask), `bridge/vscode_listener.py` +
  `bridge/worker.py` (file-drop), `integrations/vscode_connector.py` (HTTP
  client), and `vscode_extension/extension.js`. Governed workflow:
  vscode_task_send (L2 trusted).
- Ollama: local model runtime at 127.0.0.1:11434 (agent_factory, vscode_bridge,
  pipeline, ollama.py).
- HuggingFace / GitHub: discovery + download tooling (read/inspect per handoff;
  Nexus98 does not own Git operations).
- Continue: tools/continue_sync.py writes Continue config pointing at Ollama.
- Mouse/desktop automation: tools/mouse_agent (external tool invoked by
  core/mouse_agent.py).
