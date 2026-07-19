# Nexus98 Phase 6 — Documentation Review & Consistency Audit

> Planning/validation milestone only. No code, tests, dependencies, config,
> or commits changed. Produced 2026-07-17 (America/Chicago).
> Reader: this report audits the three Phase 6 docs against the live repo and
> proposes a prioritized roadmap plus relaxable Codex restrictions.

## A. Audit Scope & Method
- Reviewed: `docs/Nexus98_Autonomous_Operating_Rules.md`,
  `docs/Nexus98_Vision_Architecture.md`, `docs/Nexus98_Tool_Registry.md`.
- Method: read each doc in full; cross-checked every named component, function,
  intent keyword, and autonomy level against the actual repository source and
  directory layout.
- Cross-checks performed:
  - `core/supervisor.py` defs vs documented functions/keywords -> MATCH.
  - `core/project_engine.py` methods (`write_file`, `backup_file`,
    `validate_file`, `create_request`, `approve_request`, `log_operation`,
    `execute_operation`) -> all PRESENT.
  - `detect_intent` keywords (`create file`, `write file`, `modify file`,
    `edit file`, `build app`, `make script`) -> MATCH code exactly.
  - All `core/` subpackages and `tools/` modules named in docs -> PRESENT.
  - Ollama 16-model claim -> VERIFIED live (localhost:11434).

## B. Internal Consistency Verdict
- No contradictions between the three docs (autonomy levels, safety gate,
  checkpoint convention, stop conditions all align).
- No duplicate rules across docs.
- No outdated claims (test count 78/78, `auto_execute=False`, Phase 5 status
  all current).
- No references to non-existent components in the three target docs.
- Architecture described matches the real `core/supervisor.py` +
  `core/project_engine.py` routing.

## C. Gap Analysis (repo vs documentation)

### G1 — `ui/main_window.py` (real GUI launcher) undocumented
- Severity: Medium
- Description: `main.py` imports `from ui.main_window import launch_ui`; an 8.5 KB
  PySide/Qt-style window exists but is absent from the Tool Registry and Vision
  doc. This is a real entry surface, not a stub.
- Recommended action: add a "UI / Launcher" section to the Tool Registry noting
  `ui/main_window.py: launch_ui()` and its Level 0/1 constraint (manual launch
  only; not an autonomous action surface).
- Effort: Low (doc edit).
- Before autonomy: No (doc completeness only).

### G2 — `vscode_extension/` (real VS Code extension) undocumented
- Severity: Medium
- Description: `vscode_extension/extension.js` + package.json form a working
  extension, but the registry only mentions `integrations/vscode_connector.py`
  and `api/vscode_bridge.py`. The client-side extension is a distinct component.
- Recommended action: document the extension as part of the VS Code integration
  (client side) in the Tool Registry; note it is the UI front-end to the bridge.
- Effort: Low.
- Before autonomy: No.

### G3 — Real `core/` service modules undocumented
- Severity: Low
- Description: `core/agent_factory.py`, `core/agent_registry.py`,
  `core/identity.py`, `core/ollama.py`, `core/hardware.py`, `core/tray.py`,
  `core/recommender.py`, `core/search.py`, `core/pipeline.py`, `core/queue.py`,
  `core/workers.py`, `core/display.py`, `core/command.py`, `core/manager.py`,
  `core/cache.py`, `core/updater.py`, `core/db.py`, `core/resume.py`,
  `core/router.py`, `core/server.py`, `core/status.py`, `core/favorites.py`,
  `core/logs.py`, `core/bridge.py` exist but are not in the registry. Many are
  supporting services; a few are notable: `agent_factory`/`agent_registry`
  (agent lifecycle), `identity` (the "never pretend identity" rule's backing
  module), `ollama` (Ollama client distinct from `tools/ollama_manager`).
- Recommended action: add a "Supporting Core Services" subsection listing the
  notable modules (`agent_factory`, `agent_registry`, `identity`, `ollama`)
  with one-line purpose + safety note; the remainder can be a summarized list.
- Effort: Low-Medium.
- Before autonomy: No.

### G4 — Empty/artifact directories mislead the layout
- Severity: Low
- Description: `agents/`, `autogen/`, `agent_logs/`, `.tmp_dl/` are empty or
  transient. `build/`, `dist/` are packaging artifacts. Presenting the raw
  top-level listing as "architecture" would confuse.
- Recommended action: in the Vision doc, clarify which top-level dirs are
  source vs build/transient vs archive (`archive/`, `AI_Model_Hub_archive/`,
  `backups/`, `snapshots/`, `checkpoints/`, `history/`, `reports/`, `logs/`).
- Effort: Low.
- Before autonomy: No.

### G5 — Obsolete / cleanup documentation not flagged
- Severity: Low
- Description: `docs/vscode_workflow_setup.md` and `docs/README.md` coexist with
  archived source (`archive/cleanup_20260717/`, `AI_Model_Hub_archive/`,
  `AI_Model_Hub_LEFTOVER_INVENTORY.md`, `AI_Model_Hub_path_references.txt`).
  The AI_Model_Hub namespace was superseded by Nexus98; leftover inventory docs
  could be mistaken for current architecture.
- Recommended action: add a one-line "Obsolete / superseded" note at the top of
  the AI_Model_Hub_* docs (or move them under `archive/`), and mark
  `vscode_workflow_setup.md` as legacy vs the current bridge integration.
- Effort: Low.
- Before autonomy: No.

### G6 — Config authority not fully mapped
- Severity: Medium
- Description: `config/` holds `system_config.json`, `system_context.json`,
  `vscode_workflow.json`, `models.json`, `models.yaml`, `providers.json`,
  `settings.json`, `mouse_agent.json`. The Phase 5 review doc itself flagged the
  need to consolidate config authority, but the registry/vision docs do not map
  which config file is authoritative for what.
- Recommended action: add a "Configuration Surface" section to the Tool Registry
  (or a short config map doc) listing each config file's purpose and the
  authoritative source.
- Effort: Medium.
- Before autonomy: Recommended (autonomy decisions read config; ambiguity is a
  risk).

### G7 — `history/` and `checkpoints/` lifecycle undocumented for operators
- Severity: Low
- Description: docs reference `history/operations/<operation_id>` and
  `checkpoints/<NAME>_<TIMESTAMP>/` but do not define retention, location, or
  how an operator locates the right rollback snapshot (many now exist:
  HARD_BACKUP_BEFORE_HY3_INTEGRATION_*, HARD_BACKUP_BEFORE_PATH_MIGRATION_*,
  snapshots/, etc.).
- Recommended action: add a "Recovery Inventory" subsection listing the existing
  checkpoint/backup roots and when each was taken.
- Effort: Low.
- Before autonomy: No (but helps recovery confidence).

## D. Prioritized Roadmap

### Phase 6.5 — Immediate improvements (doc + safety hardening)
1. Close G1, G2, G3 (document UI, vscode_extension, supporting core modules).
2. Close G4, G5 (mark obsolete/superseded docs; clarify dir layout).
3. Close G7 (recovery inventory).
4. Add a one-paragraph "Config authority" note addressing G6-lite.
- Effort: ~1 short doc-pass. No code.

### Phase 7 — High-value capabilities (autonomy enablement)
1. Formalize a Level 1->2 promotion procedure (explicit, checkpointed, logged)
   behind the `auto_execute` gate, scoped to a single trusted workflow.
2. Config authority consolidation (G6 full) — pick single source per setting.
3. Add an autonomous-operation audit dashboard reading `history/operations`.
- Effort: Medium (mostly docs + config; optional minimal glue).

### Phase 8 — Major feature expansion
1. Agent lifecycle automation via `core/agent_factory` + `core/agent_registry`
   (spawn/retire agents under supervision).
2. Memory-driven personalization via `core/memory_service` + `core/identity`.
3. Multi-agent coordination (AutoGen teams) gated by the supervisor.
- Effort: High (code + tests).

### Phase 9 — Long-term improvements
1. Self-healing recovery (auto-restore from `checkpoints/` on detected breakage).
2. Telemetry/observability across `event_bus` + `rule_engine`.
3. Model/provider abstraction via `core/providers` + `core/huggingface`/`github`
   downloaders with sandboxing.
- Effort: High.

### Phase 10 — Deployment, launcher, recovery USB, installer
1. `ui/main_window.py` launcher polish + `tools/*-DesktopShortcut.ps1` flow.
2. `core/installer.py` + `core/boot.py` + `core/autostart.py` packaging.
3. Recovery USB / portable runtime build (currently `build/`, `dist/` artifacts).
4. Explicit go/no-go gate: only after Phases 7-9 validated and autonomy proven
   at Level 2 on trusted workflows.
- Effort: High (deferred per Non-Goals).

## E. Relaxable Codex Workflow Restrictions (recommendation)

| # | Current rule | Proposed rule | Reason | Risk | Rollback |
|---|--------------|---------------|--------|------|----------|
| C1 | Halt & confirm before any repo file read/inspection | Allow read-only inspection (`list_files`, `read_file`, `git_status`, status queries) without per-step approval | Phase 5 gate only triggers on action intents; reads are Level 0 safe | Very low (no mutation possible) | Re-engage strict on any write/action intent |
| C2 | Halt & confirm on every new untracked file | Allow doc/checkpoint artifacts (`.md`, checkpoint dirs) without confirmation | Reversible, non-production; git + checkpoints give full rollback | Low (stray files possible) | `git clean` / delete untracked; checkpoints are self-contained |
| C3 | Re-verify environment before each sub-step | Re-verify only on test failure or import error | Env stable (venv, pytest 9.1.1, Ollama up); per-step checks waste time | Low (env drift undetected between steps) | Run full env check on any anomaly |
| C4 | Smoke-test every import | Smoke-test only when `core/` or `tools/` Python changes | Import integrity validated at milestone (18 passed); doc-only work can't break imports | Low (doc edit won't import-break) | Re-run `test_import_smoke.py` if Python changes |
| C5 | Treat legacy/archive dirs as in-scope | Exclude `archive/`, `AI_Model_Hub_archive/`, `backups/`, `snapshots/`, `checkpoints/`, `history/`, `*.backup*` from active review scope | These are frozen/obsolete; reviewing them wastes effort and risks confusion | Low (genuine change elsewhere missed) | Re-include if a task explicitly targets them |

### Rules that MUST stay strict (do not relax)
- No `auto_execute=True` flip without explicit human-approved, checkpointed decision.
- No production code mutation outside the Project Engine gated path.
- No dependency install / environment change without sign-off.
- No launcher/deployment work until Phase 10.
- No destructive action, credential use, or admin elevation without approval.
- Stop-and-report on any production behavior defect.

### Relaxation boundary (automatic re-engagement)
All relaxed rules re-engage the moment `supervisor.auto_execute` is enabled, a
dependency is installed, or production code is touched.

## F. Conclusion
The three Phase 6 documents are internally consistent and accurately reflect the
verified Phase 5 implementation. All gaps identified are documentation/completeness
issues (none are safety defects). Recommended pre-autonomy action: complete
Phase 6.5 (G1-G7 doc fixes) and resolve G6 config-authority mapping. Autonomy may
then be raised to Level 2 for a single trusted, checkpointed workflow.
