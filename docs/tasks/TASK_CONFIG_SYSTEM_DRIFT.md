# Task: Config / System State Drift

> **Type:** Configuration consistency
> **Severity:** MEDIUM (enabler for safe autonomy work)
> **Status:** OPEN — partially blocked (some items need a config change window + Guardian checkpoint)
> **Source report:** `docs/NEXUS98_ENGINEERING_READINESS_REPORT.md` (section 5.3 / Technical Debt 3, 7, 9)
> **Created:** 2026-07-18 (America/Chicago)
> **Constraint:** Documentation only. No source, config, test, Guardian, or dependency files modified here.

---

## 1. Problem Statement

Several configuration and identity values have drifted from the intended Nexus98
state. This creates ambiguity about the system's true phase, brand, and runtime
behavior, and undermines trust in the safety/config authority layer.

> **Correction (verified 2026-07-18):** The report's claim that
> `config/system_context.json.current_phase` reads "AutoGen Multi-Agent Foundation"
> is **inaccurate** — the live file now reads `"current_phase": "Phase 6.5 — Documentation Audit Remediation"`.
> The drift item is therefore downgraded to: ensure the phase value stays consistent
> with `PROJECT_STATE.md` and is not silently reverted; the stronger issue is branding
> and the non-functional `auto_update` flag.

## 2. Current Behavior

- `config/settings.json` sets `"auto_update": true`, but `core/updater.py` is a stub (`# updater`) — auto-update is declared but cannot execute.
- Branding is inconsistent: `core/identity.py` declares "AI Model Hub Agent"; Constitution/Operating Rules say "Nexus98 Agent". `tray.py`, `launcher.py`, `main_window_BEFORE_STATUS.py`, and several root `.py` files still print "AI Model Hub".
- `config/system_context.json` phase value is now Phase 6.5 (consistent), but should be guarded against silent regression.
- Pre-migration `AI_Model_Hub_*` artifacts remain in repo root (`AI_Model_Hub_LEFTOVER_INVENTORY.md`, `AI_Model_Hub_path_references.txt`, `core_audit_*.txt`, `nexus98_path_inventory.txt`).
- Absolute paths hardcoded in modules (e.g., `core/supervisor.py`, `core/memory_service.py`, `core/mouse_agent.py` use `Path(r"D:\Nexus98")`).

## 3. Expected Behavior

- `auto_update` either points to a real implementation or is explicitly documented as reserved/off.
- Branding unified to "Nexus98" across `identity.py`, `tray.py`, launcher, and UI labels.
- `system_context.json` phase value remains the authoritative Phase 6.5/7 marker and is not silently regressed.
- Pre-migration `AI_Model_Hub_*` artifacts relocated to an archive index (non-source move).
- Absolute paths replaced by a single configurable `ROOT` (see bridge task and §6).

## 4. Files Involved

| File | Role | Change? |
|------|------|---------|
| `config/settings.json` | `auto_update: true` vs stub updater | Reconcile (gated) |
| `core/identity.py`, `core/tray.py`, `launcher.py`, `ui/main_window_BEFORE_STATUS.py` | Branding strings | Proposed change (gated) |
| `config/system_context.json` | Phase value guard | Verify/reconcile (gated) |
| `AI_Model_Hub_*` root artifacts | Pre-migration leftovers | Move to archive index (non-source) |
| `core/*.py` with `D:\Nexus98` literals | Portability | Proposed change (gated, see bridge task) |

## 5. Risk Assessment

- **Severity:** MEDIUM. No direct safety violation, but erodes config authority and
  can mislead operators about phase/brand/behavior.
- **Likelihood of harm if unchanged:** Low for runtime; Medium for governance/trust.
- **Risk of the fix:** Low. Mostly string/config edits; must avoid touching the
  `auto_execute` safety floor (handled by the separate CRITICAL task).
- **Blast radius:** Config + a few modules; contained.

## 6. Required Checkpoint Before Modification

1. **Inspect** current implementation (done).
2. **Create a Guardian checkpoint / known-good snapshot** of any config or source to be edited.
3. **Explain intended change** per item above; keep `auto_execute` untouched.
4. **Obtain human approval.**
5. **Apply controlled modification** (config edits + branding string updates; archive moves are non-source).
6. **Validate** (section 7) and **report**.

## 7. Validation Steps After Change

- [ ] `core/identity.py` and `core/tray.py` report "Nexus98" branding.
- [ ] `config/settings.json` `auto_update` either implemented or explicitly reserved/off with a comment.
- [ ] `config/system_context.json` phase value consistent with `PROJECT_STATE.md`.
- [ ] `AI_Model_Hub_*` artifacts relocated; repo root no longer mixes old/new branding.
- [ ] No `SyntaxWarning` or import regression introduced (run import-smoke `tests/test_import_smoke.py`).
- [ ] Full `pytest -q` (with `TMPDIR` redirected) still green.
- [ ] Guardian checkpoint confirmed recoverable.

---

*End of task document. No files outside `docs/tasks/` were modified.*
