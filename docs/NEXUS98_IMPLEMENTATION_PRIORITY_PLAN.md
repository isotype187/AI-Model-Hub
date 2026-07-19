# Nexus98 Implementation Priority Plan

> **Author:** Nexus98 Implementation Engineer (Codex)
> **Date:** 2026-07-18 (America/Chicago)
> **Scope:** Documentation only. No source, config, test, Guardian, or dependency files modified.
> **Sources:** `docs/NEXUS98_ENGINEERING_READINESS_REPORT.md`; `docs/tasks/*.md`; `docs/NEXUS98_CONSTITUTION.md`; `docs/codex_handoff/01_FOUNDATION_AND_RULES.md`.
> **Governance baseline:** Constitution development rule — before any production modification:
> 1) Inspect, 2) Checkpoint, 3) Explain, 4) Apply controlled modification, 5) Test, 6) Validate, 7) Report.
> Guardian owns Git/recovery/integrity; the Governor (`core/autonomy/governor.py`) is the sole writer of autonomy state. Nexus98 must not bypass safety systems or modify Guardian ownership.

---

## Guiding Principles for Ordering

1. **Safety before autonomy.** Any task that touches the `auto_execute` floor or autonomy level is strictly first and blocks all later autonomy phases.
2. **Stabilize before expand.** Hygiene/enabler tasks (source-of-truth clarity, config drift, cross-machine paths) precede feature work so later edits target authoritative, correct files.
3. **Every production edit is checkpointed + human-approved.** No task below may be applied without a Guardian checkpoint and explicit approval, per the Constitution.
4. **Rollback is always available.** Guardian known-good snapshots make every change reversible; tasks are scoped to minimize blast radius.

---

## Task Registry (priority-ordered)

| Rank | Task | Severity | Task Doc |
|------|------|----------|----------|
| P1 | auto_execute Safety Alignment | CRITICAL | `docs/tasks/TASK_AUTO_EXECUTE_SAFETY_ALIGNMENT.md` |
| P2 | Bridge Cross-Machine Path | HIGH | `docs/tasks/TASK_BRIDGE_CROSS_MACHINE_PATH.md` |
| P3 | Config / System State Drift | MEDIUM (enabler) | `docs/tasks/TASK_CONFIG_SYSTEM_DRIFT.md` |
| P4 | Legacy File / Source-of-Truth Ambiguity | MEDIUM (enabler) | `docs/tasks/TASK_LEGACY_FILE_AMBIGUITY.md` |

> Note: The readiness report's §5.3/§5.4 were MEDIUM, not HIGH/CRITICAL. They are
> included here because they are direct enablers for safe engineering (clear
> authority + consistent config), but their true severity is preserved honestly.
> §5.5 (LOW test-temp lock) is intentionally out of scope for this priority plan;
> it is a test-hygiene item tracked separately in the report's T5.

---

## P1 — auto_execute Safety Alignment

1. **Priority ranking:** P1 (highest). CRITICAL, safety-gating.
2. **Reason for placement:** The Constitution mandates `auto_execute = False` at rest. The live `core/supervisor.py:28` is `True`, so the Governor reports an autonomous-capable level and trusted workflows could execute without a gated Phase 7 promotion. This inverts the core safety model and therefore blocks every later autonomy phase (report §6, step 1: "Blocking for all later autonomy phases").
3. **Dependencies:** None (hard floor; everything else depends on it being correct). Downstream: P2–P4 and all Phase 7+ autonomy work.
4. **Required checkpoint:** Guardian checkpoint/snapshot of `core/supervisor.py` and `config/system_config.json`; human-approved proposal to set `auto_execute = False` and reconcile `autonomy_level` intent; edit only after approval (Constitution steps 2–4).
5. **Expected validation:** `auto_execute = False`; `governor.current_level()` returns 0; dashboard snapshot reports "Manual only"; sample action intent yields `awaiting_approval`; full `pytest -q` (TMPDIR redirected) green; no new warnings.
6. **Rollback considerations:** Single-constant change with existing gating logic already in place — revert flag to `True` (or restore Guardian snapshot) restores prior state. Guardian checkpoint guarantees recoverability. Minimal blast radius (Supervisor execution path only).

---

## P2 — Bridge Cross-Machine Path

1. **Priority ranking:** P2 (HIGH).
2. **Reason for placement:** A core integration (VS Code bridge / continuity) is broken on this machine because `core/bridge_controller.py` hardcodes `D:\AI\Nexus98_Bridge\...` instead of the live `D:\Nexus98` root. It does not affect the safety floor, so it sits just below P1, but it must be fixed before any workflow relies on the bridge. Independent of P1.
3. **Dependencies:** None hard; can run in parallel with P1. Benefits from the P3/P4 config-root work if a shared `ROOT` constant is introduced (coordinate to avoid duplicate path constants).
4. **Required checkpoint:** Guardian checkpoint of `core/bridge_controller.py` (and any bridge config); human-approved proposal to replace hardcoded foreign paths with a root-derived path; edit only after approval.
5. **Expected validation:** No `D:\AI\Nexus98_Bridge` references remain; paths resolve to `D:\Nexus98` by default; `bridge_controller.get_status()` / `find_bridge_processes()` operate against the local bridge; bridge tests pass (`test_vscode_bridge.py`, `test_vscode_connection.py`, `test_vscode_workflow_config.py`) with TMPDIR redirected.
6. **Rollback considerations:** Path-constant change only; restoring the Guardian snapshot or re-pointing the root constant reverts behavior. Risk is low; ensure the launch `cwd` is preserved so the bridge still starts correctly.

---

## P3 — Config / System State Drift

1. **Priority ranking:** P3 (MEDIUM, enabler).
2. **Reason for placement:** Branding inconsistency ("AI Model Hub" vs "Nexus98"), a declared-but-stubbed `auto_update: true`, and stray pre-migration `AI_Model_Hub_*` artifacts erode config authority and operator trust. Not a runtime defect, but it should be resolved before feature/autonomy work so future edits target a consistent, authoritative config. Sits after P1/P2 because it is non-blocking and partly needs its own config change window (cannot be done in the documentation-only pass).
3. **Dependencies:** Independent of P1/P2 technically, but should follow them so branding/config cleanup does not collide with the P1 autonomy-config reconciliation or the P2 path root. Corroborates P4 (legacy artifact relocation).
4. **Required checkpoint:** Guardian checkpoint of any touched config/source (`settings.json`, `identity.py`, `tray.py`, `launcher.py`, `system_context.json`); human-approved proposal; keep `auto_execute` strictly untouched (that is P1's remit).
5. **Expected validation:** `identity.py`/`tray.py` report "Nexus98"; `auto_update` implemented or explicitly reserved/off; `system_context.json` phase consistent with `PROJECT_STATE.md`; `AI_Model_Hub_*` artifacts relocated; import-smoke + full `pytest -q` green; no `SyntaxWarning` regression.
6. **Rollback considerations:** Mostly string/config edits; Guardian snapshot makes revert trivial. Explicit guard: must not alter the `auto_execute` floor (revert scope to P1 if it does).

---

## P4 — Legacy File / Source-of-Truth Ambiguity

1. **Priority ranking:** P4 (MEDIUM, enabler).
2. **Reason for placement:** ≥368 `.backup`/`.bak`/`before` copies across the tree create ambiguity about which file is authoritative, risking edits to stale copies. It is non-runtime and fully non-destructive (relocation + manifest only), so it is last among the four but valuable as a precondition for safe future engineering. Can begin immediately as it requires no source/config edit.
3. **Dependencies:** None on P1–P3. Should be completed before broad feature work so the active tree contains only live files. Complements P3 (both tidy pre-migration/legacy artifacts).
4. **Required checkpoint:** Guardian checkpoint/snapshot of the repo before relocation; human-approved scope (move only dead copies, never live modules or Guardian recovery artifacts; do not delete).
5. **Expected validation:** No `*_before_*`/`.backup`/`.bak` copies remain alongside live modules; `archive/legacy_inventory/MANIFEST.csv` indexes each relocated file; `git status` (via Guardian) shows only archive additions; import-smoke still green.
6. **Rollback considerations:** Pure relocation with a manifest — reverse the move from the manifest to restore. Zero runtime impact; Guardian checkpoint guarantees reversibility. Must exclude Guardian-owned recovery artifacts from the move scope.

---

## Execution Cadence

- **Phase A (safety + integration):** P1, then P2 (may overlap; P2 independent of the autonomy floor).
- **Phase B (stabilization/enablers):** P3, then P4 (P4 can start earlier as non-destructive).
- **Gate:** No Phase 7 (Level 2 autonomy promotion) or later feature work begins until P1 is validated and the autonomy floor is confirmed Level 0 at rest, per the Constitution's "Stability before Autonomy" rule and the report's blocking note.

## Non-Negotiables (from Constitution / Handoff 01)

- Governor remains the **sole** writer of autonomy state; Nexus98 never flips `auto_execute` or autonomy level outside the Governor.
- Guardian owns Git/recovery/integrity; Nexus98 requests, never bypasses.
- No production modification without Inspect -> Checkpoint -> Explain -> Apply -> Test -> Validate -> Report.
- Never blindly replace architecture, create duplicate authority, bypass validation, modify Guardian ownership, or add uncontrolled autonomy.

---

*End of plan. No files outside `docs/` were modified.*
