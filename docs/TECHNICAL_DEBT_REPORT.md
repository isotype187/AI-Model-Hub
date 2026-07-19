# Nexus98 - Technical Debt Report

Status: READ-ONLY ANALYSIS (no code changes, no refactoring)
Scope: current live source tree (excludes archive/, backups/, checkpoints/,
snapshots/, .venv*, build/, dist/).

---

## 1. Hardcoded Paths (HIGH priority)

Absolute `D:\Nexus98` (and external `D:\AI\Nexus98_Bridge`) paths are embedded
across core modules, blocking portability, Docker, and multi-node goals.

Representative (non-exhaustive):
- `core/config.py:4` CONFIG_PATH = D:\Nexus98\config.json (+ base_path, hf_dir,
  gguf_dir).
- `core/db.py:4` DB_PATH = D:\Nexus98\data\db\models.db.
- `core/memory_service.py:26` DEFAULT_DB_PATH = D:\Nexus98\data\db\memory.db.
- `core/memory_migration.py:25,155` legacy + log paths.
- `core/project_engine.py:9`, `core/supervisor.py:17`, `core/router.py:5`,
  `core/server.py:7`, `api/vscode_bridge.py:10`, `bridge/*` ROOT = D:\Nexus98.
- `core/bridge_controller.py:11,13` external bridge venv/script under D:\AI\...
- `core/mouse_agent.py:6`, `core/mouse_control.py:33,62,65`, `core/favorites.py`,
  `core/installer.py`, `core/logs.py`, `core/resume.py`, `core/status.py`.
- Root patch scripts (bridge_toggle_patch.py, real_toggle_patch.py, etc.) hardcode
  ui/main_window.py; one references a nonexistent D:\Nexus98_Recovery_System path.

Note: `config/system_config.json` is the autonomy authority, but `core/config.py`
points at a DIFFERENT file (D:\Nexus98\config.json) - split config authority.

Recommendation (future): centralize via config_manager + environment/base-path
resolution; do NOT change in this analysis phase.

## 2. Duplicate / Superseded Systems

- Supervisor: `core/supervisor.py` (live) vs `core/supervisor_STATUS_BEFORE.py`
  and `core/supervisor_before_final_autogen_fix.py` (stale) and an empty
  `core/supervisor/` package.
- Bridge API: `api/vscode_bridge.py` (live) vs `api/vscode_bridge.backup.py` and
  `api/vscode_bridge.pre_ollama_fix.backup.py`.
- UI: `ui/main_window.py` (live) vs `ui/main_window_BEFORE_STATUS.py` (stale).
- Config duplicates: `config/models_before_small_test_models.yaml`,
  `config/system_context_before_autogen.json`, `docs/Nexus98_Tool_Registry.md.bak`,
  `data/db/models.db.backup_*`.
- Two Ollama model listers: `api/vscode_bridge.ollama_models()` and
  `tools/model_router.ollama_models()`.
- Multiple server entry points: `core/api_server.py`, `core/server.py`,
  `api/vscode_bridge.py`, `bridge/*` - overlapping roles/ports.

Risk: accidental edit/import of the wrong (stale) module.

## 3. Fragile Modules

- `core/agent_factory.py` / `core/orchestrator.py`: hard dependency on
  autogen_agentchat/autogen_ext at import time; tests skip when unavailable.
  Ollama host hardcoded (localhost:11434).
- `core/pipeline.py`, `core/supervisor_before_final_autogen_fix.py`: direct HTTP
  to Ollama generate with fixed URLs; no provider abstraction.
- Bridge stack: file-drop + HTTP + external venv (D:\AI\Nexus98_Bridge) - many
  moving parts, environment-specific.
- Root-level one-off patch scripts (bridge_*_patch.py, vertical_*_switch.py,
  fix_switch_logic.py): mutate ui/main_window.py by string patching - brittle,
  should be retired.
- `core/config.py` DEFAULT auto-writes a config file on first load - implicit
  side effect.

## 4. Missing Abstractions

- No provider/model router interface (handoff #7); model access is ad hoc.
- No strategy layer (#8).
- No unified config/path resolver (paths hardcoded per-module).
- No conversation/session abstraction (#9).
- No code-memory index (#17); memory_service is generic key/value-ish records.
- No Guardian client interface (#4-5).
- Empty scaffold packages (event_bus, rule_engine, state_manager, config_manager,
  supervisor) declare intent but provide no API yet.

## 5. Testing Limitations

- 96 tests pass, but coverage is uneven: strong on vscode bridge, mouse agent,
  memory phase1, supervisor phase5; UI is largely untested (no GUI harness).
- Agent/orchestrator tests are skipped without the AutoGen runtime.
- No tests for router strategy selection, catalog/discovery, or the new UI view
  builders (only import-smoke + autonomy_dashboard logic).
- Pytest requires a TMPDIR workaround on this environment (documented) - a sign
  of environment fragility rather than code.

## 6. UI Limitations

- Tkinter-only; dense text panels; limited widgets (no tables/rich charts).
- Command Center is tab-based, not the handoff's chat-first vision.
- No toolbar, no consolidated control panel, no Documents/Chat views, no WWW.
- `ui/autonomy_panel.py` (request-capable) is unused/unwired.
- Window still branded "AI Model Hub" in the legacy sibling; title corrected in
  the live shell but legacy strings remain in tree.
- No hover explanations / accessibility affordances yet (handoff #13).

## 7. Storage / Memory Concerns

- Checkpoint sprawl: 54 checkpoints/ dirs + 4 snapshots/ + backups/ conflict with
  handoff #16 ("avoid thousands of checkpoint files; use databases/indexes").
- Two memory backends coexist: legacy `core/memory.py` + modern
  `core/memory_service.py` (SQLite) with a migration path not clearly retired.
- Split state: data/system_state.json, config/system_context.json, history/,
  and DBs - no single source of continuity state.
- DB backups stored alongside live DB (data/db/models.db.backup_*).
- No compression/cleanup/dedup policy (handoff assigns this to Guardian).
