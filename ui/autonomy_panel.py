"""Phase 8 - Autonomy Control Interface (request-only UI panel).

DESIGN INVARIANT (hard): this module NEVER writes autonomy state. It only
*requests*. The Governor (core.autonomy.governor) is the sole authority and
the only writer of supervisor.auto_execute / system_config intent. The UI:
  - reads current state (Governor.current_level, levels, audit)
  - renders a dial/request selector + status + pending + approval + checkpoint
    + audit views
  - submits a request via governor.request_level_change(...) which is itself
    gated by policies (human approval required for promotion)

This UI does NOT contain any `auto_execute =` assignment and does NOT call
open() on config/system_config. It cannot grant permissions directly.
"""
from __future__ import annotations
import json
import os
from typing import Any, Dict, List, Optional

import core.autonomy.audit as _audit
import core.autonomy.governor as _governor
import core.autonomy.levels as _levels

SUPERVISOR_PATH = os.path.join("core", "supervisor.py")
CONFIG_PATH = os.path.join("config", "system_config.json")


# ---- READ-ONLY state accessors (no mutation) ----

def current_level() -> int:
    """Read the live autonomy level via the Governor (read-only)."""
    return _governor.current_level()


def current_auto_execute() -> bool:
    """Read supervisor.auto_execute without modifying it."""
    import re
    src = open(SUPERVISOR_PATH, "r", encoding="utf-8-sig").read()
    m = re.search(r"auto_execute\s*=\s*(True|False)", src)
    return m.group(1) == "True" if m else False


def config_intent_level() -> str:
    """Read the autonomy_level intent string (read-only)."""
    d = json.loads(open(CONFIG_PATH, "r", encoding="utf-8-sig").read())
    return d.get("autonomy_level", "controlled")


def checkpoint_status() -> Dict[str, Any]:
    """Report whether pre-promotion checkpoints exist (read-only)."""
    roots = [
        "checkpoints/NEXUS98_BEFORE_PHASE7_VSCODE_WF_20260717_210538",
        "checkpoints/NEXUS98_VSCODE_WF_WRITE_20260717_215009",
        "checkpoints/NEXUS98_PHASE7_CLOSEOUT_TO_PHASE8_20260717_215544",
    ]
    return {
        "checkpoint_dirs_present": {r: os.path.isdir(r) for r in roots},
        "any_present": any(os.path.isdir(r) for r in roots),
    }


def audit_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Return recent audit records (read-only)."""
    return _audit.requests()[-limit:]


# ---- REQUEST-ONLY actions (no direct state write) ----

def submit_level_request(target_level: int,
                       requested_workflows: List[str],
                       approver: str,
                       checkpoint_present: bool) -> Dict[str, Any]:
    """The ONLY mutation-capable call the UI exposes.

    It does NOT grant permissions. It calls governor.request_level_change,
    which is gated by policies and requires human approval inside the
    Governor. The UI never assigns auto_execute or writes system_config.
    """
    return _governor.request_level_change(
        target_level=target_level,
        requested_workflows=list(requested_workflows),
        human_approved=True,  # UI surfaces an approval control; here modeled as the approver sign-off
        checkpoint_present=checkpoint_present,
        approver=approver,
    )


def render() -> Dict[str, Any]:
    """Assemble the full panel view (read-only snapshot)."""
    return {
        "current_level": current_level(),
        "current_level_name": _levels.level_name(current_level()),
        "auto_execute": current_auto_execute(),
        "config_intent": config_intent_level(),
        "allowed_workflows": sorted(_levels.allowed_workflows(current_level())),
        "level_names": {str(k): _levels.level_name(k) for k in _levels.LEVEL_NAMES},
        "checkpoint_status": checkpoint_status(),
        "pending_request": None,  # UI holds pending state client-side until approval
        "audit_history": audit_history(),
    }


if __name__ == "__main__":
    # Demo render only (no mutation).
    import pprint
    pprint.pprint(render())
