# Task: auto_execute Safety Alignment

> **Type:** Safety-critical configuration/source alignment
> **Status:** OPEN — blocked, awaiting checkpoint + human approval
> **Source report:** `docs/NEXUS98_ENGINEERING_READINESS_REPORT.md` (section 5.1)
> **Created:** 2026-07-18 (America/Chicago)
> **Constraint:** Documentation only in this pass. No source, config, test, Guardian, or dependency files are modified here.

---

## 1. Problem Statement

The Nexus98 safety model requires autonomous execution to be **disabled at rest**
(`auto_execute = False`) so that no action can run without an explicit, gated,
human-approved promotion. The live code currently initializes `auto_execute = True`,
directly contradicting the Constitution's "Safety by default" tenet, the
`system_config.json` intent, and the module's own comments. This means the
Autonomy Governor reads the system as autonomous-capable instead of gated.

## 2. Current Behavior

- `core/supervisor.py:28` declares `auto_execute = True`.
- `core/autonomy/governor.py:current_level()` derives the live autonomy level as:
  `L0 if auto_execute is False, else mapped level from system_config.json`.
  With `auto_execute = True`, the Governor reports **Level 1+** regardless of the
  intended gate.
- `config/system_config.json` sets `"autonomy_level": "trusted"` (Level 2 intent)
  with `require_approval_for_risky_actions: true`.
- Net effect: `supervisor.py` comments say "Execution is gated … (default False)"
  and "Phase 5 safety gate … waits for approval", but the live constant enables
  execution immediately. The system presents as trusted/auto-executing rather than
  held-for-approval.
- The Autonomy Dashboard (`ui/autonomy_dashboard.py`) is correctly read-only and
  will surface this elevated state but cannot correct it.

## 3. Expected Behavior

- `core/supervisor.py` initializes `auto_execute = False` at rest.
- The Autonomy Governor therefore reports **Level 0 (Manual only)** until an
  explicit, checkpointed, human-approved promotion (Phase 7 procedure) flips it.
- `config/system_config.json` `autonomy_level` remains declarative intent only;
  the hard floor (`auto_execute`) stays the source of truth for safety.
- Action intents continue to create proposals/checkpoints and wait for approval
  (existing `supervisor.py` gating logic already supports this when the flag is False).

## 4. Files Involved

| File | Role | Change? |
|------|------|---------|
| `core/supervisor.py` | Defines `auto_execute` constant (line 28) | Proposed change (gated) |
| `core/autonomy/governor.py` | Reads `auto_execute` to derive level | No change (already correct) |
| `config/system_config.json` | Declares `autonomy_level: "trusted"`, risky-action gate | Reconcile intent only, under checkpoint |
| `ui/autonomy_dashboard.py` | Read-only observer | No change |
| `docs/NEXUS98_ENGINEERING_READINESS_REPORT.md` | Records the risk | Already documents it |

> Note: Guardian owns Git/recovery/integrity. Any modification must be requested
> through Guardian's known-good checkpoint flow; Nexus98 does not edit Git directly.

## 5. Risk Assessment

- **Severity:** CRITICAL. A `True` floor silently enables autonomous execution
  against the intended safety model.
- **Likelihood of harm if unchanged:** Medium-High — any workflow that reaches the
  execution branch would proceed without the intended approval hold.
- **Risk of the fix:** Low, provided the change is made under a checkpoint and
  validated. The surrounding gating logic (`if not auto_execute: … awaiting_approval`)
  is already in place, so flipping the flag to `False` restores intended behavior.
- **Blast radius:** Supervisor execution path; all downstream agents/Project Engine
  proposals. Contained by existing approval/checkpoint scaffolding.

## 6. Required Checkpoint Before Modification

Do NOT apply the change until all of the following are satisfied:

1. **Inspect** current implementation (done — see report §5.1).
2. **Create a Guardian checkpoint / known-good snapshot** of `core/supervisor.py`
   and `config/system_config.json` before any edit (Governor/Guardian authority).
3. **Explain intended change** in a human-visible proposal: set
   `core/supervisor.py:28` to `auto_execute = False`; reconcile
   `system_config.json` autonomy intent so it does not imply auto-execution at rest.
4. **Obtain human approval** (Constitution development rule step 4; Phase 5/7 safety gate).
5. **Apply controlled modification** only after approval.
6. **Validate** (section 7) and **report** results.

> This task document performs steps 1 and 3 (inspect + explain). Steps 2, 4, 5, 6
> require a config/source change window and human sign-off.

## 7. Validation Steps After Change

- [ ] `core/supervisor.py` line 28 reads `auto_execute = False`.
- [ ] `core/autonomy/governor.py:current_level()` returns `0` (Manual only) when run against current config.
- [ ] `ui/autonomy_dashboard.py:snapshot()` reports level `0` / "Manual only".
- [ ] A sample action intent produces `status: "awaiting_approval"` (no execution).
- [ ] Existing test suite passes: `pytest -q` (with `TMPDIR` redirected to a writable root to avoid the known pytest temp lock) — Supervisor/ProjectEngine 78/78 plus import-smoke and memory tests.
- [ ] No new `SyntaxWarning` introduced; existing `core/supervisor/__init__.py:3` escape warning tracked separately.
- [ ] Guardian checkpoint confirmed recoverable (known-good state retained).

---

*End of task document. No files outside `docs/tasks/` were modified.*
