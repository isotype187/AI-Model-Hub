# Nexus98 Vision & Architecture

> High-level vision and system architecture for Nexus98, adapted for increased
> autonomous operation. Consistent with the verified Phase 5 implementation
> (`core/supervisor.py`, `core/project_engine.py`) and existing design docs
> (`docs/MOUSE_AGENT_SYSTEM.md`, `docs/MEMORY_ARCHITECTURE_DESIGN.md`,
> `docs/PHASE5_SUPERVISOR_PROJECTENGINE.md`).

## 1. Vision

Nexus98 is a local-first AI workstation hub that coordinates local models
(Ollama/AutoGen), project automation (Project Engine), and developer tooling
(VS Code bridge, git, file tools) under a single supervised agent runtime. The
goal of autonomy is to let the system **propose, checkpoint, and — when
authorized — execute** controlled operations without sacrificing safety or
reversibility.

## 2. Design Tenets

- **Local-first:** models and data stay on the workstation; no required cloud.
- **Safety by default:** execution is gated; `auto_execute = False` at rest.
- **Checkpoint everything:** every mutation is reversible.
- **Transparent routing:** intent is classified and routed explicitly.
- **Graceful degradation:** failures are caught and reported, never silent.

## 3. Component Architecture

```
User / Agent input
        |
        v
 +-------------------+   detect_intent()  +-----------------------+
 |  Supervisor        | -----------------> | action  | information |
 |  (core/supervisor) |                    +-----------+-----------+
 +-------------------+                                |
        | action                                     | information
        v                                            v
 +----------------------------+            +-------------------------+
 | run_action_task            |            | run_task -> route ->     |
 |  -> proposals              |            | get_orchestrator -> agent|
 |  -> Project Engine requests|            | (Ollama/AutoGen)         |
 +----------------------------+            +-------------------------+
        |
        v  (gated by auto_execute + approval)
 +----------------------------+
 | Project Engine             |
 |  backup -> write -> validate
 |  history/ operations log   |
 +----------------------------+
        |
        v
 +----------------------------+
 | Integrations               |
 |  VS Code bridge / connector|
 |  git / file / model tools  |
 +----------------------------+
```

## 4. Request Lifecycle (action intent)

1. `detect_intent` → `action`.
2. `run_action_task` builds a plan, then `convert_plan_to_action_proposals`.
3. Each proposal → `approve_agent_proposal` → Project Engine `create_request`
   (a checkpoint request record in `history/`).
4. If `auto_execute` is `False`: status `awaiting_approval`; return. No write.
5. If `auto_execute` is `True`: `approve_request` → `execute_engine_request`
   → `engine.execute_operation` → `write_file` (with backup + validate).
6. Operation logged under `history/operations/<operation_id>`.

## 5. Recovery & Audit Surfaces

- `ProjectEngine.backup_file` — pre-write backup; auto-restore on validation
  failure.
- `history/` — request and operation records for audit/undo.
- `checkpoints/` — human/agent-created rollback snapshots.
- `git` — source-of-truth versioning for code changes.

## 6. Autonomy Roadmap

| Milestone | State | Notes |
|-----------|-------|-------|
| Phase 5 Supervisor + Project Engine | **Complete** | 78/78 tests passing; safety model validated. |
| Autonomy documentation | **This milestone** | Operating rules, tool registry, vision/architecture. |
| Increased autonomous operation | Next | Raise autonomy level via explicit, checkpointed decision. |
| Deployment / launcher | Deferred | Not started until autonomy framework is documented & validated. |


## 6b. Repository Layout (source vs artifacts)
- **Source:** `core/`, `tools/`, `integrations/`, `api/`, `bridge/`, `runtime/`,
  `ui/`, `vscode_extension/`, `config/`, `scripts/`, `tests/`, `main.py`.
- **State/History (recoverable):** `history/`, `checkpoints/`, `snapshots/`,
  `backups/`, `agent_logs/`, `logs/`, `reports/`, `data/`.
- **Build/packaging artifacts:** `build/`, `dist/`, `.venv/`, `.pytest_cache/`,
  `.pytest_temp*/`, `.tmp_dl/`.
- **Superseded / archive (NOT current architecture):** `AI_Model_Hub_archive/`,
  `archive/`, `AI_Model_Hub_LEFTOVER_INVENTORY.md`, `AI_Model_Hub_path_references.txt`,
  `diagnostic_parts/`, `ollama_cleanup_backups/`. The `AI_Model_Hub` namespace was
  superseded by Nexus98; do not treat these as live components.
## 7. Non-Goals (current milestone)

- No launcher/shortcut/icon creation.
- No production code changes.
- No dependency installation.
- No deployment until the autonomy framework is documented and validated.

