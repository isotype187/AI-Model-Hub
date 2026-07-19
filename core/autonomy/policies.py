"""Phase 8 - Autonomy Governor: approval + scope engine (DECIDES only).

policies.py NEVER writes supervisor.auto_execute or config. It returns an
approval decision for a level-change request, enforcing:
  - valid level range (0-L4)
  - target level >= current level (no downgrade via promotion request)
  - if target > current: human sign-off required
  - if target > 1: a fresh pre-promotion checkpoint must exist
  - the requested workflow set must be within the allowed set for the target
The Governor (governor.py) applies the change ONLY after approve()==True.
"""
from __future__ import annotations
import re
from typing import Dict, List, Tuple

from . import levels as _levels

# Human sign-off is modeled as a passed-in flag/identity, not auto-granted.
# This keeps the UI/agent from self-approving risky promotions.


def _parse_current_auto_execute(source: str) -> bool:
    m = re.search(r"auto_execute\s*=\s*(True|False)", source)
    return m.group(1) == "True" if m else False


def evaluate(current_level: int, target_level: int,
            requested_workflows: List[str],
            human_approved: bool,
            checkpoint_present: bool,
            supervisor_source: str,
            config_level: str) -> Tuple[bool, str, Dict[str, object]]:
    """Return (approved, reason, decision_dict).

    Does NOT mutate anything.
    """
    reasons: List[str] = []
    ok = True

    if not _levels.valid_level(target_level):
        return False, f"invalid target level {target_level}", {}

    if target_level < current_level:
        # Downgrade path is handled by governor emergency_stop, not promotion.
        return False, "downgrade not permitted via promotion request", {}

    if target_level > _levels.max_level():
        return False, "target exceeds max level", {}

    allowed = _levels.allowed_workflows(target_level)
    bad = [w for w in requested_workflows if w not in allowed]
    if bad:
        ok = False
        reasons.append(f"workflows not in allowed set for L{target_level}: {bad}")

    if target_level > current_level:
        if not human_approved:
            ok = False
            reasons.append("human sign-off required for promotion")
        if not checkpoint_present:
            ok = False
            reasons.append("pre-promotion checkpoint missing")

    decision = {
        "current_level": current_level,
        "target_level": target_level,
        "requested_workflows": list(requested_workflows),
        "allowed_workflows": sorted(allowed),
        "auto_execute_current": _parse_current_auto_execute(supervisor_source),
        "config_level": config_level,
        "human_approved": human_approved,
        "checkpoint_present": checkpoint_present,
    }
    if ok:
        return True, "approved", decision
    return False, "; ".join(reasons), decision
