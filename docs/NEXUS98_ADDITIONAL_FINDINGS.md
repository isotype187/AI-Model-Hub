# Nexus98 Additional Findings (Documentation-Only)

> **Author:** Nexus98 Implementation Engineer (Codex)
> **Date:** 2026-07-18 (America/Chicago)
> **Mode:** Analysis only. No source/config/test/Guardian/dependency modifications.
> **Companion docs:** `docs/NEXUS98_ENGINEERING_READINESS_REPORT.md`, `docs/NEXUS98_OVERNIGHT_ANALYSIS_REPORT.md`, `docs/checkpoints/P2_PRECHANGE_INSPECTION.md`.

This document records architecture risks discovered during a documentation-only
review that are NOT already covered (or are under-weighted) in the readiness
report. Each is a finding only — no remediation applied.

---

## F1 — Split Config Authority (HIGH, newly discovered)

- **Evidence:** `core/config.py:4` sets `CONFIG_PATH = r'D:\Nexus98\config.json'`. The file `D:\Nexus98\config.json` **does not exist** (confirmed: `Test-Path` returns False). The repository instead uses the `config/` directory, and `docs/NEXUS98_CONSTITUTION.md` (line 887) states `config/system_config.json` is the autonomy authority while `core/config.py` points at a *different* file — explicitly calling this "split config authority."
- **Behavior:** `config.load_config()` will, on first call, **create** `D:\Nexus98\config.json` from `DEFAULT` (base_path, hf_dir, gguf_dir, max_workers, ui_mode, cache_ttl) because the path is missing. This means a second, divergent config file can be silently auto-created, fragmenting configuration state.
- **Impact:** Two competing config sources (`config.json` vs `config/system_config.json` + `config/*.json`). Operators may edit the wrong file; the autonomy authority and the runtime `config.py` authority disagree. Latent misconfiguration risk.
- **Why not fixed:** Requires a config/source change + Guardian checkpoint + human approval (out of scope for this pass). Recommendation: reconcile `core/config.py` to the `config/` directory (or `config_manager`) under a dedicated checkpointed task (candidate P3 sub-task).
- **Constitution guidance:** "do NOT change in the analysis phase."

## F2 — Hardcoded Absolute `D:\Nexus98` Paths (MEDIUM, pervasive)

- **Evidence:** ≥25 literals across `core/` — `config.py`, `db.py`, `memory_service.py`, `supervisor.py`, `router.py`, `server.py`, `project_engine.py`, `resume.py`, `favorites.py`, `installer.py`, `logs.py`, `status.py`, `mouse_agent.py`, `mouse_control.py`, `memory_migration.py`, plus root patch scripts; also `C:\Users\isoty\.continue` in `tools/continue_sync.py` and `tools/health_check.py`.
- **Impact:** Zero portability; any machine/path change breaks the app. All paths are environment-coupled.
- **Recommendation (from Constitution):** centralize via `config_manager` + environment/base-path resolution. Do NOT change in analysis phase.

## F3 — Multiple Server Entry Points / Port Confusion (MEDIUM)

- **Evidence:** At least two HTTP surfaces — `bridge_controller.py` -> external `D:\AI\Nexus98_Bridge` on **8765**; `api/vscode_bridge.py` Flask app on **8000**; plus `core/api_server.py`, `core/server.py`. `config/vscode.json` endpoint is `http://127.0.0.1:8000/v1`.
- **Impact:** Role/port ambiguity; risk of connecting to the wrong service. The Constitution (line 873) flags "multiple server entry points risk port/role confusion."
- **Recommendation:** Document a single service/topology map; no change this pass.

## F4 — Stub / Dead Modules (MEDIUM)

- **Evidence:** `core/updater.py` = `# updater`; `core/logger.py` = `# logger`; `launcher.py` = `print('AI Model Hub launcher ready')`. `config/settings.json` sets `auto_update: true` with no functioning updater.
- **Impact:** Declared capabilities (auto-update, logging) are non-functional; branding still "AI Model Hub".
- **Recommendation:** Implement or explicitly mark reserved (P3 scope).

## F5 — Branding Inconsistency (MEDIUM)

- **Evidence:** `core/identity.py` ("AI Model Hub Agent"), `core/tray.py`, `launcher.py`, `ui/main_window_BEFORE_STATUS.py`, and root `.py` files print "AI Model Hub"; Constitution/Operating Rules say "Nexus98 Agent". `config/vscode.json` name is "AI Hub VS Code Bridge".
- **Impact:** Operator confusion; undermines config/identity authority.
- **Recommendation:** Unify to "Nexus98" (P3 scope).

## F6 — Legacy / Duplicate Module Proliferation (MEDIUM)

- **Evidence:** `core/supervisor_before_final_autogen_fix.py`, `core/supervisor_STATUS_BEFORE.py`, `core/orchestrator.py.backup_20260709_192725`, and ≥368 `.backup`/`.bak`/`before` files repo-wide (see P4 task).
- **Impact:** Source-of-truth ambiguity; risk of editing a stale copy.
- **Recommendation:** Quarantine into `archive/legacy_inventory/` with manifest (P4 scope).

## F7 — Memory Checkpoint Clutter vs DB-Forward Mandate (LOW/MEDIUM)

- **Evidence:** Constitution (line 873) notes "memory clutter (54 checkpoint dirs) vs DB-forward mandate." `core/memory_service.py` is SQLite-only (Phase 1); many `checkpoints/`, `snapshots/`, `backups/` dirs exist.
- **Impact:** Storage growth, potential duplicate history; opposes the "database storage, lifecycle management" memory mandate.
- **Recommendation:** Lifecycle/cleanup policy; no change this pass.

## F8 — Cosmetic Syntax Warning (LOW)

- **Evidence:** `core/supervisor/__init__.py:3` invalid escape sequence -> `SyntaxWarning` (non-fatal, per PROJECT_STATE.md).
- **Impact:** Noise only.
- **Recommendation:** Fix escape in a low-risk edit window; out of scope here.

## F9 — Locked Pytest Temp (LOW, operational)

- **Evidence:** System `Temp/pytest-of-isoty` locks after interrupted sessions; tests must run with `TMPDIR` redirected to a writable root.
- **Impact:** Routine validation friction; not a product defect.
- **Recommendation:** Document one-line run instruction (already noted in report T5).

---

## Summary Table

| ID | Finding | Severity | Covered elsewhere? | Action owner |
|----|---------|----------|-------------------|--------------|
| F1 | Split config authority (`config.py` -> missing `config.json`) | HIGH | New (Constitution mentions) | New checkpointed task (P3-adjacent) |
| F2 | 25+ hardcoded `D:\Nexus98` + `C:\Users\isoty` paths | MEDIUM | Readiness debt #7 | P3 (root constant) |
| F3 | Multiple server entry points / port confusion | MEDIUM | Constitution | Document topology |
| F4 | Stub/dead modules (`updater`, `logger`, `launcher`) | MEDIUM | Readiness debt #1 | P3 |
| F5 | Branding mismatch | MEDIUM | Readiness debt #1 | P3 |
| F6 | Legacy/duplicate module proliferation | MEDIUM | P4 task | P4 |
| F7 | Memory checkpoint clutter vs DB mandate | LOW/MED | Constitution | Lifecycle policy |
| F8 | `supervisor/__init__.py` SyntaxWarning | LOW | PROJECT_STATE | Low-risk edit |
| F9 | Locked pytest temp | LOW | Report T5 | Doc only |

> No files were modified. F1 is the most notable new finding and should be triaged
> alongside P3 (config authority consolidation) before any autonomy promotion.

*End of additional findings. Documentation only.*
