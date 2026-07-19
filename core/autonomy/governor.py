"""Phase 8 - Autonomy Governor: the SOLE writer of autonomy state.

The Governor wraps (does NOT replace) the existing hard floor:
  - supervisor.auto_execute  (code constant; the safety floor)
  - config/system_config.json "autonomy_level" (intent)
It is the ONLY component permitted to change these. Project Engine remains
the file-mutation authority for workflow writes; the Governor governs the
*autonomy level*, not individual file edits.

Safety invariants preserved:
  - No promotion without an approved policies decision.
  - auto_execute is flipped only for the approved trusted-workflow set.
  - All safety gates in system_config.json stay as-is.
"""
from __future__ import annotations
import json
import os
import re

from . import audit as _audit
from . import levels as _levels
from . import policies as _policies

SUPERVISOR_PATH = os.path.join("core", "supervisor.py")
CONFIG_PATH = os.path.join("config", "system_config.json")
CONTEXT_PATH = os.path.join("config", "system_context.json")


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


def _write_text(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def current_level() -> int:
    """Derive the live level from config intent + auto_execute floor.

    L0 if auto_execute is False; otherwise the configured autonomy_level
    index (L1-L4). The Governor treats the stricter reading as truth.
    """
    src = _read_text(SUPERVISOR_PATH)
    ae_on = _parse_auto_execute(src)
    if not ae_on:
        return 0
    cfg = json.loads(_read_text(CONFIG_PATH))
    name = cfg.get("autonomy_level", "controlled")
    mapping = {
        "manual": 0, "controlled": 1, "assisted": 1,
        "trusted": 2, "expanded": 3, "experimental": 4,
    }
    return mapping.get(name, 1)


def scope_check(workflow: str) -> dict:
    """READ-ONLY runtime scope check for the execution gate.

    Returns a decision about whether ``workflow`` may auto-execute at the
    *current* autonomy level. This helper performs NO state mutation and
    emits NO audit events -- it is safe to call from the live execution path.

    The trusted-workflow set (e.g. ``vscode_task_send`` at L2) is the only
    set permitted to proceed without an explicit approval record. Anything
    outside that set must be held for review rather than auto-executed.

    Returns dict with keys:
      allowed (bool) - True if auto-execute is permitted at this level,
      held (bool)    - True if the workflow is outside the trusted set and
                       must wait for an approval/checkpoint (do NOT execute),
      reason (str)   - human-readable explanation,
      level (int)    - current autonomy level,
      known (bool)   - whether the workflow is in the allowed set.
    """
    level = current_level()
    known = _levels.is_workflow_allowed(workflow, level)
    if level <= 1:
        # Below L2 there is no trusted auto-execute set.
        return {
            "allowed": False,
            "held": True,
            "reason": "autonomy level below trusted (L%d); no auto-execute" % level,
            "level": level,
            "known": known,
        }
    if known:
        return {
            "allowed": True,
            "held": False,
            "reason": "workflow '%s' in trusted L%d set" % (workflow, level),
            "level": level,
            "known": True,
        }
    return {
        "allowed": False,
        "held": True,
        "reason": "workflow '%s' not in trusted set for L%d; hold for approval"
                  % (workflow, level),
        "level": level,
        "known": False,
    }


def _parse_auto_execute(src: str) -> bool:
    m = re.search(r"auto_execute\s*=\s*(True|False)", src)
    return m.group(1) == "True" if m else False

def _config_intent_level() -> int:
    """Read the autonomy_level INTENT from system_config.json (read-only)."""
    cfg = json.loads(_read_text(CONFIG_PATH))
    name = cfg.get("autonomy_level", "controlled")
    mapping = {"manual": 0, "controlled": 1, "assisted": 1,
               "trusted": 2, "expanded": 3, "experimental": 4}
    return mapping.get(name, 1)


def _state_consistent(src: str) -> bool:
    """Conflict handling: the STRICTER reading wins.

    If auto_execute is True but the config intent says L0/L1, that is an
    inconsistency -> treat as NOT-enabled (stricter value). Returns True only
    when both sources agree the floor is enabled.
    """
    ae_on = _parse_auto_execute(src)
    intent = _config_intent_level()
    if ae_on and intent <= 1:
        # conflict: floor says on, intent says off -> not consistent
        return False
    return True


def _verify_applied(target_level: int) -> bool:
    """Stricter-value-wins: after an apply, re-read and confirm the live
    state matches the requested intent. If not, it failed safe."""
    live = current_level()
    # auto_execute must reflect target >= 2
    ae_on = _parse_auto_execute(_read_text(SUPERVISOR_PATH))
    if target_level >= 2 and not ae_on:
        return False
    if target_level <= 1 and ae_on:
        return False
    return live == target_level



def _set_auto_execute(src: str, value: bool) -> str:
    new = "True" if value else "False"
    cnt = len(re.findall(r"auto_execute\s*=\s*(True|False)", src))
    if cnt != 1:
        raise RuntimeError("unexpected auto_execute occurrences: %d" % cnt)
    return re.sub(r"auto_execute\s*=\s*(True|False)",
                 "auto_execute = %s" % new, src, count=1)


def request_level_change(target_level: int, requested_workflows,
                        human_approved: bool, checkpoint_present: bool,
                        approver: str = "") -> dict:
    """The ONLY entry point. Returns a decision; applies ONLY if approved.

    Does not directly grant permissions. Requires an approved policies
    decision before flipping anything.
    """
    current = current_level()
    src = _read_text(SUPERVISOR_PATH)
    cfg = json.loads(_read_text(CONFIG_PATH))
    allowed = list(_levels.allowed_workflows(target_level))

    approved, reason, decision = _policies.evaluate(
        current_level=current,
        target_level=target_level,
        requested_workflows=list(requested_workflows),
        human_approved=human_approved,
        checkpoint_present=checkpoint_present,
        supervisor_source=src,
        config_level=cfg.get("autonomy_level", "controlled"),
    )

    req_id = _audit.record(
        "request_level_change",
        current_level=current, target_level=target_level,
        requested_workflows=list(requested_workflows),
        human_approved=human_approved, approver=approver,
        decision=("approved" if approved else "rejected"),
        reason=reason,
    ).get("ts")

    if not approved:
        return {"approved": False, "reason": reason, "decision": decision,
                "request_id": req_id}

    # Apply: the Governor is the sole writer.
    new_src = _set_auto_execute(src, target_level >= 2)
    _write_text(SUPERVISOR_PATH, new_src)
    _set_config_intent(target_level)
    applied_ok = _verify_applied(target_level)
    if not applied_ok:
        # Interrupted / inconsistent promotion: fail safe -> rollback to prior.
        _write_text(SUPERVISOR_PATH, src)          # restore supervisor
        _set_config_intent(current)                    # restore intent
        _audit.record(
            "apply_level_change_failed",
            request_id=req_id, expected_level=target_level,
            from_level=current, result="rolled_back",
        )
        return {"approved": True, "reason": "apply did not verify; rolled back",
                "decision": decision, "request_id": req_id,
                "applied_level": current, "rolled_back": True}
    _audit.record(
        "apply_level_change",
        request_id=req_id, from_level=current, to_level=target_level,
        auto_execute=new_src != src, approver=approver,
    )
    return {"approved": True, "reason": reason, "decision": decision,
            "request_id": req_id, "applied_level": target_level}


def _set_config_intent(level: int) -> None:
    """Write the autonomy_level INTENT only; never touch safety gates."""
    name = _levels.level_name(level).lower().split()[0]
    intent = {"manual": "manual", "assisted": "assisted",
              "trusted": "trusted", "expanded": "expanded",
              "experimental": "experimental"}.get(name, "controlled")
    cfg = json.loads(_read_text(CONFIG_PATH))
    cfg["autonomy_level"] = intent
    # safety gates explicitly preserved
    assert cfg["safety"]["require_approval_for_risky_actions"] is True
    assert cfg["safety"]["require_snapshots"] is True
    assert cfg["safety"]["require_validation"] is True
    _write_text(CONFIG_PATH, json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")


def emergency_stop(approver: str = "system") -> dict:
    """Kill-switch: force auto_execute=False and downgrade to L0/L1.

    Ensures the resulting state is CONSISTENT (stricter value wins): after
    this call, current_level() must report 0.
    """
    src = _read_text(SUPERVISOR_PATH)
    if _parse_auto_execute(src):
        _write_text(SUPERVISOR_PATH, _set_auto_execute(src, False))
    _set_config_intent(0)
    # Rollback consistency check
    consistent = _state_consistent(_read_text(SUPERVISOR_PATH))
    rec = _audit.record("emergency_stop", approver=approver,
                        result="auto_execute=False, level=0",
                        consistent=consistent)
    return rec
