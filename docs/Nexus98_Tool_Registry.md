# Nexus98 Tool Registry

> Inventory of tools, integrations, and core services available to autonomous
> operation. Extracted from the current repository layout (`tools/`,
> `integrations/`, `core/`, `api/`, `bridge/`). This is a catalog, not an
> authorization list — access is further constrained by the safety gate in
> `core/supervisor.py` and `core/project_engine.py`.

## 1. Local File Tools (`tools/file_tools.py`)
- `list_files() -> str` — inventory of important project files.
- `read_file(path: str) -> str` — read a file's contents.
- **Safety:** read-only. No mutation.

## 2. Git Tools (`tools/git_tools.py`)
- `git_status() -> str` — current working-tree status.
- **Safety:** read-only by default. Commits/branches are not created by the
  agent unless explicitly directed.

## 3. Model / Agent Tools
- `tools/agent_runner.py`: `load_models()`, `select_model(task)`, `log(entry)`,
  `run()` — load and run local models.
- `tools/agent_selector.py`: `load()`, `choose(task)` — pick an agent for a task.
- `tools/model_router.py`: `ollama_models()`, `load()`, `scan()` — discover and
  route to Ollama models.
- `tools/continue_sync.py` — resume/sync continuation state.
- `tools/health_check.py`: `result(name, ok, detail="")` — structured health
  reporting.

## 4. Ollama Management (`tools/ollama_manager/`, `tools/ollama-startup.ps1`)
- Model management, startup, and health for the local Ollama runtime
  (`http://localhost:11434`).
- **Safety:** model lifecycle operations are infrastructure-level; require
  human/Level2+ authorization.

## 5. VS Code Integration (`integrations/vscode_connector.py`, `api/vscode_bridge.py`)
- `vscode_connector.log(message)`, `vscode_connector.status()`,
  `vscode_connector.send_task(task, mode="hybrid")` — drive VS Code tasks and
  query bridge status.
- `api/vscode_bridge.py`: Flask app exposing `/status`, `/task`, etc.
- `bridge/vscode_listener.py`, `bridge/worker.py` — local bridge listener and
  worker.
- `vscode_extension/extension.js + package.json`: the client-side VS Code
  extension (front-end to the bridge). It sends tasks to `api/vscode_bridge.py`
  and renders status. Not an autonomous action surface; manual/user-driven.

## 6. Core Services (`core/`)
- **Supervisor** (`core/supervisor.py`, package `core/supervisor/`): intent
  detection, action routing, approval gate, Project Engine wiring.
- **Project Engine** (`core/project_engine.py`): the only authorized file
  mutator. Provides `write_file`, `backup_file`, `validate_file`,
  `execute_operation`, `create_request`, `approve_request`, `log_operation`,
  and `history/` recording.
- **Memory** (`core/memory.py`, `core/memory_service.py`): agent memory store.
- **Orchestrator** (`core/orchestrator.py`): agent team loading/routing.
- **Config** (`core/config.py`, `core/config_manager/`): system configuration.
- **State/Events/Rules** (`core/state_manager/`, `core/event_bus/`,
  `core/rule_engine/`): runtime state, event propagation, rule evaluation.
- **Installer/Bootstrap** (`core/installer.py`, `core/boot.py`,
  `core/autostart.py`): setup and startup.
- **Discovery/Catalog** (`core/discovery.py`, `core/catalog.py`,
  `core/categories.py`): model/resource discovery.
- **Downloaders** (`core/downloader.py`, `core/huggingface.py`,
  `core/github.py`, `core/gguf.py`): external resource acquisition
  (network/infra; Level2+).

### 6b. Supporting Core Services (not in the primary list above)
- `core/agent_factory.py` — builds AutoGen agents from a config path (`AgentFactory`).
- `core/agent_registry.py` — in-process agent catalog (`AGENTS`: Supervisor, Coding Agent, etc.).
- `core/identity.py` — agent identity/persona text (see consistency note: still branded
  "AI Model Hub Agent"; Operating Rules refer to "Nexus98 Agent" — branding to unify later).
- `core/ollama.py` — Ollama provider client (read-only model inventory; never downloads/removes).
- `core/hardware.py`, `core/tray.py`, `core/recommender.py`, `core/search.py`,
  `core/pipeline.py`, `core/queue.py`, `core/workers.py`, `core/display.py`,
  `core/command.py`, `core/manager.py`, `core/cache.py`, `core/updater.py`,
  `core/db.py`, `core/resume.py`, `core/router.py`, `core/server.py`,
  `core/status.py`, `core/favorites.py`, `core/logs.py`, `core/bridge.py` —
  supporting services (catalog, queue, bridge controller, DB, router, server,
  status, logging, etc.). Not autonomous action surfaces.

## 7. Mouse Agent (`tools/mouse_agent/`, `core/mouse_agent.py`,
`core/mouse_control.py`)
- GUI/input automation. High-risk surface; must remain at Level 0/1 unless
  explicitly authorized.

## 8. UI / Launcher (`ui/main_window.py`)
- `launch_ui()` — Tkinter "Command Center" window (model catalog, queue, favorites,
  agent list, bridge status). Entry point imported by `main.py`.
- **Safety:** manual/user-driven UI only. Not an autonomous action surface; remains
  Level 0/1 unless explicitly authorized.

## 9. Autonomy Levels vs Tool Access

| Level | Allowed tools |
|-------|--------------|
| 0 Supervised | read-only: `list_files`, `read_file`, `git_status`, `status` queries |
| 1 Assisted | + create proposals/checkpoints (no execution) |
| 2 Semi-Auto | + Project Engine writes (approved actions), VS Code task send |
| 3 Autonomous | + model/agent lifecycle, downloads (trusted workflows only) |

## 10. Configuration Surface (authoritative map)
See `docs/CONFIG_AUTHORITY.md` for the full configuration authority map
(sources, authoritative files, generated/derived config, override precedence,
do-not-edit files, and recovery when configs disagree).

## 11. Integration Status
- **Ollama:** local runtime at `localhost:11434`; models available (verified at
  milestone time: 16 models).
- **VS Code Bridge:** Flask API + listener; status queryable.
- **HY3 / Codex:** integration present (see `checkpoints/HARD_BACKUP_BEFORE_HY3_INTEGRATION_*`).
