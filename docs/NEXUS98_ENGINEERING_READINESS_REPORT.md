# Nexus98 Engineering Readiness Report

> **Author:** Nexus98 Implementation Engineer (Codex)
> **Date:** 2026-07-18 (America/Chicago)
> **Scope:** Read-only assessment. No source, config, test, Guardian, or dependency file was modified.
> **Basis:** `docs/NEXUS98_CONSTITUTION.md`; `docs/codex_handoff/01..05`; `PROJECT_STATE.md`; direct repository inspection.

---

## 0. Executive Summary

The repository is a large, multi-phase local-first AI workbench. Documentation,
architecture intent, and safety governance are well-defined. The *code* is broad
but uneven: several systems are real and tested (Supervisor, Project Engine,
Memory Service, Autonomy Governor, VS Code bridge), while others are stubs,
brand-mismatched, or reference paths from a prior machine/install.

**One confirmed safety-critical conflict exists** and must be treated as the
highest-priority risk before any autonomy work proceeds (see section 5).

---

## 1. Current Architecture State

- **Entry points:** `main.py` (Tkinter "Command Center" via `ui.main_window.launch_ui`), `launcher.py` (trivial stub), `api/api_server.py`, `core/api_server.py`, `core/server.py`.
- **Layered core (`core/`):** ~60 Python modules covering orchestration, routing, supervisor, project engine, memory, autonomy, bridge, model discovery/download, UI views, and tooling.
- **Autonomy Governor (`core/autonomy/`):** `governor.py`, `levels.py`, `policies.py`, `audit.py` — the *sole writer* of autonomy state by design.
- **UI (`ui/`):** Tkinter `main_window.py` + `views/` (agents, autonomy, bridge, dashboard, models, supervisor, system) + `autonomy_dashboard.py` / `autonomy_panel.py` (read-only observability).
- **Bridge (`bridge/`, `api/`):** VS Code bridge + worker listener; external `Nexus98_Bridge` process referenced.
- **Config (`config/`):** JSON/YAML authority files (`system_config.json`, `models.json/yaml`, `providers.json`, `settings.json`, `vscode*.json`, `mouse_agent.json`, `system_context.json`).
- **Tests (`tests/`):** 9 test modules; `PROJECT_STATE.md` reports 78 passed (Supervisor/ProjectEngine Phase 5), plus import-smoke and memory tests.
- **Docs (`docs/`):** Extensive constitution, handoff, phase, and design specs.

**Governance posture (intended):** auto-execute disabled at rest; autonomy gated; Guardian (separate) owns Git/recovery/integrity; Governor owns autonomy writes.

---

## 2. Implemented Systems

| System | Status | Evidence |
|--------|--------|----------|
| Supervisor | Implemented + tested | `core/supervisor.py` (gated `run_action_task`, `create_engine_request`) |
| Project Engine | Implemented + tested | `core/project_engine.py` (7.9 KB), Phase 5 78/78 tests |
| Autonomy Governor | Implemented (design-complete) | `core/autonomy/{governor,levels,policies,audit}.py` |
| Autonomy Dashboard/Panel | Implemented (read-only) | `ui/autonomy_dashboard.py`, `ui/autonomy_panel.py` |
| Memory Service | Implemented (Phase 1, SQLite) | `core/memory_service.py` (16 KB), `core/memory.py`, `core/memory_migration.py` |
| VS Code Bridge | Implemented + tested | `core/vscode_bridge.py`, `api/vscode_bridge.py`, 3+ test modules |
| Model Discovery / Catalog | Implemented | `core/catalog.py`, `core/discovery.py`, `core/ollama.py`, `core/huggingface.py`, `core/github.py` |
| Mouse Agent | Implemented (subprocess wrapper) | `core/mouse_agent.py`, `core/mouse_control.py` (21 KB) |
| Router / Orchestrator | Implemented | `core/router.py`, `core/orchestrator.py` |
| Agent Registry / Factory | Implemented | `core/agent_registry.py`, `core/agent_factory.py` |
| Tray / Identity / Status | Implemented (partial) | `core/tray.py`, `core/identity.py`, `core/status.py` |
| UI Views | Implemented (Tkinter) | `ui/views/*` |

---

## 3. Missing / Incomplete Systems

- **Stubs with no real behavior:** `core/updater.py` (`# updater`), `core/logger.py` (`# logger`), `launcher.py` (`print('AI Model Hub launcher ready')`).
- **Internal Development Environment (Phase 10):** spec exists; no implementation.
- **Self-Healing Recovery / Observability maturity (Phase 9):** `event_bus`, `rule_engine` exist as packages but are not yet wired into a recovery loop.
- **Memory personalization & multi-agent coordination (Phase 8):** `core/identity.py`, `core/agent_factory.py` present but personalization/coordination not matured.
- **Strategy system (Phase 5 roadmap item):** referenced in handoff 03; no dedicated `core/strategy*` module observed.
- **WWW / Don't Forget continuity UI (handoff 04):** design present; no dedicated implemented module found under `core/` or `ui/`.
- **Code Memory engine:** spec exists (`NEXUS98_CODE_MEMORY_SPECIFICATION.md`); no dedicated `core/code_memory*` module observed.
- **Provider abstraction robustness:** `providers.json` present; `downloader.py`, `github.py`, `huggingface.py` are thin (approx 390-540 bytes).

---

## 4. Technical Debt

1. **Branding mismatch:** `core/identity.py` declares "AI Model Hub Agent"; Constitution/Operating Rules say "Nexus98 Agent". Also `tray.py`, `main_window_BEFORE_STATUS.py`, `launcher.py`, and several root-level `.py` files still print "AI Model Hub".
2. **Proliferation of backup/legacy files:** >=368 files across repo matching `.backup`/`.bak`/`before`/`STATUS_BEFORE`, plus `archive/`, `snapshots/`, `backups/`, `checkpoints/`, and `AI_Model_Hub_*` inventory files. Risk of confusion about source of truth.
3. **Stale `current_phase` config:** `config/system_context.json.current_phase` still reads "AutoGen Multi-Agent Foundation" — does not reflect Phase 5/6.5 (documented, but uncorrected).
4. **Cosmetic `SyntaxWarning`:** `core/supervisor/__init__.py:3` invalid escape sequence.
5. **Duplicate/competing bridge paths:** `core/bridge_controller.py` hardcodes `D:\AI\Nexus98_Bridge\...`; repo root is `D:\Nexus98`. The bridge target appears to be from a different machine/install.
6. **Locked test temp:** `TMPDIR`/`pytest-of-isoty` lock from a prior interrupted session requires redirecting `TMPDIR` to run tests (see `PROJECT_STATE.md`).
7. **Hardcoded absolute `ROOT` paths:** multiple modules use `Path(r"D:\Nexus98")` and `Path(r"D:\Nexus98\...")` (e.g., `supervisor.py`, `memory_service.py`, `mouse_agent.py`), reducing portability.
8. **Inconsistent `auto_execute` documentation:** comments say "default False" but the live constant is `True` (see section 5, critical).
9. **Pre-migration `AI_Model_Hub_*` artifacts** left in repo root (`AI_Model_Hub_LEFTOVER_INVENTORY.md`, `AI_Model_Hub_path_references.txt`, `core_audit_*.txt`, `nexus98_path_inventory.txt`) — migration cleanup incomplete.

---

## 5. Conflicts and Risks

### 5.1 CRITICAL - `auto_execute` safety gate inverted (resolve before autonomy work)
- `core/supervisor.py:28` defines `auto_execute = True`.
- The Governor (`core/autonomy/governor.py`) derives level from this constant: `L0 if not ae_on`. With `True`, the Governor reads the system as **Level 1+ (autonomous-capable)** even though `system_config.json` + Constitution intend `auto_execute = False` at rest.
- `config/system_config.json` sets `"autonomy_level": "trusted"` — i.e., Level 2 intent — combined with `auto_execute = True` this implies **trusted workflows would auto-execute without an explicit, gated Level 2 promotion**.
- Comments throughout `supervisor.py` claim "default False" / "Execution is gated ... (default False)" — the live code contradicts its own comments.
- The Autonomy Dashboard is correctly read-only, so it will *report* this elevated state but cannot fix it.
- **Risk:** Violates the Constitution's "Safety by default: `auto_execute = False` at rest" tenet and the Phase 5/7 safety gate. This is the single highest-priority item.

### 5.2 HIGH - Cross-machine path references
- `core/bridge_controller.py` points at `D:\AI\Nexus98_Bridge\...` (different install root). The bridge subsystem may fail or operate against the wrong target on this machine.

### 5.3 MEDIUM - Config/system state drift
- `system_context.json.current_phase` stale; branding strings inconsistent; `settings.json` `auto_update: true` with a non-functional `updater.py`.

### 5.4 MEDIUM - Authority/source-of-truth ambiguity
- Hundreds of `.backup`/`.bak`/`before` files plus parallel `archive/`, `snapshots/`, `backups/`, `checkpoints/` trees. A future engineer could edit a non-authoritative copy. Guardian remains the intended authority for recovery/Git.

### 5.5 LOW - Test-environment fragility
- Locked pytest temp; test suite must be run with redirected `TMPDIR`. Not a product defect but blocks routine validation.

---

## 6. Recommended Implementation Order

Aligned with `codex_handoff/05` phase order and the Constitution's "Stability before Autonomy" rule:

1. **Resolve the `auto_execute` safety conflict (section 5.1)** and reconcile `system_config.json` autonomy intent. *Blocking for all later autonomy phases.*
2. **Configuration cleanup & consolidation** (`codex_handoff/05` step 2): fix stale `current_phase`, unify branding, correct cross-machine bridge path, centralize config authority (`docs/CONFIG_AUTHORITY.md`).
3. **Architecture stabilization** (step 3): replace absolute `D:\Nexus98` paths with a single configurable root; remove/relocate dead stubs (`updater.py`, `logger.py`, `launcher.py`); quarantine legacy `.backup`/`.bak` files.
4. **Model/provider systems** (step 4): harden `downloader.py`, `github.py`, `huggingface.py`, `providers.json` wiring.
5. **Strategy system** (step 5): introduce the strategy selector referenced in handoff 03.
6. **Memory maturation** (step 6): personalization (`identity.py`), lifecycle, code-memory engine.
7. **Guardian integration** (step 7): ensure Nexus98 to Guardian recovery/integrity handshake (Guardian stays separate; do not merge).
8. **Continuity systems** (step 8): WWW + Don't Forget UI/`core` modules.
9. **UI expansion** (step 9 / Phase 9): self-healing + observability wiring (`event_bus`, `rule_engine`).
10. **Internal dev environment** (step 10 / Phase 10): launcher/installer/recovery USB — gated behind phases 7-9 validation.

---

## 7. First Safe Engineering Tasks

All of the following are **non-destructive, reversible, and do not alter production autonomy behavior** (consistent with the Constitution's read-only/safe-change rules and the "do not modify Guardian/source/configs" constraint for this pass):

- **T1 (Documentation/risk):** Open a tracked issue for the `auto_execute = True` conflict (section 5.1); document the exact diff needed (`core/supervisor.py:28` to `False` + reconcile `system_config.json`) so it can be applied under a checkpoint + human approval before any autonomy phase.
- **T2 (Documentation):** Draft a `config/system_context.json.current_phase` correction note and a branding-unification checklist (Nexus98 vs "AI Model Hub").
- **T3 (Repo hygiene, non-source):** Inventory and quarantine the >=368 `.backup`/`.bak`/`before` files into a single `archive/legacy_inventory/` index (move only; no source edit) to remove source-of-truth ambiguity.
- **T4 (Path audit, documentation):** Catalog every hardcoded `D:\Nexus98` / `D:\AI\Nexus98_Bridge` absolute path into a migration table; propose a single `ROOT` config constant.
- **T5 (Test hygiene):** Document the `TMPDIR` redirect procedure so the suite runs deterministically on this machine; capture as a one-line run instruction.
- **T6 (Stub triage):** List dead stubs (`updater.py`, `logger.py`, `launcher.py`) with a recommendation (implement, or mark explicitly reserved) — decision deferred to a config-permitted change window.
- **T7 (Bridge risk):** Flag `core/bridge_controller.py` cross-machine path as a runtime defect to verify before relying on the bridge subsystem.

> None of T1-T7 modifies source, config, tests, Guardian, or dependencies. They are inspection/documentation/quarantine actions only, per the task constraints.

---

## Appendix A - Inspection Evidence (key paths)

- `core/supervisor.py:28` -> `auto_execute = True`
- `config/system_config.json` -> `"autonomy_level": "trusted"`, `require_approval_for_risky_actions: true`
- `core/autonomy/governor.py` -> derives level from `auto_execute` (L0 if False)
- `core/bridge_controller.py` -> `D:\AI\Nexus98_Bridge\...` (cross-machine)
- `core/identity.py` -> "AI Model Hub Agent"
- `core/memory_service.py` -> SQLite-only Phase 1 boundary
- `tests/` -> 9 modules; `PROJECT_STATE.md` reports 78 passed + import smoke
- `docs/` -> 40+ spec/handoff/phase documents present

*End of report.*
