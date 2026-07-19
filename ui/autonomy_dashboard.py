"""Phase 8 - Autonomy Observability Dashboard (STRICTLY READ-ONLY).

DESIGN INVARIANT (hard): this module NEVER mutates autonomy state. It performs
NO file writes, NO config writes, and NO supervisor.auto_execute changes. It
calls NO Governor mutation entry points (request_level_change / emergency_stop
are NOT invoked here). It only OBSERVES.

The Governor (core.autonomy.governor) remains the sole authority and sole
writer of autonomy state. This dashboard reads:
  - core.autonomy.governor.current_level()  (read-only)
  - core.autonomy.levels                     (pure data)
  - core.autonomy.audit.requests()           (read-only append-log reader)
  - the checkpoints/ directory                (read-only scandir)
  - core/supervisor.py + config/system_config.json (read-only, for status only)

Public surface:
  - snapshot() -> dict            full read-only view (all 8 approved fields)
  - individual read helpers per field (all read-only)
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

import core.autonomy.audit as _audit
import core.autonomy.governor as _governor
import core.autonomy.levels as _levels

# Read-only path references (opened with mode "r" only, never "w"/"a").
SUPERVISOR_PATH = os.path.join("core", "supervisor.py")
CONFIG_PATH = os.path.join("config", "system_config.json")
CHECKPOINTS_DIR = "checkpoints"

# Governor event names this dashboard correlates (read-only interpretation).
_REQUEST_EVENT = "request_level_change"
_APPLY_EVENTS = ("apply_level_change", "apply_level_change_failed")
_EMERGENCY_EVENT = "emergency_stop"


# ---------------------------------------------------------------------------
# Low-level read-only readers (no mutation, no writes)
# ---------------------------------------------------------------------------

def _read_text(path: str) -> str:
    """Read a file as text (read-only). Never opens for writing."""
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


def _auto_execute_on() -> bool:
    """Read supervisor.auto_execute without modifying it."""
    m = re.search(r"auto_execute\s*=\s*(True|False)", _read_text(SUPERVISOR_PATH))
    return m.group(1) == "True" if m else False


def _config_intent() -> str:
    """Read the autonomy_level intent string (read-only)."""
    try:
        cfg = json.loads(_read_text(CONFIG_PATH))
    except (OSError, ValueError):
        return "unknown"
    return cfg.get("autonomy_level", "controlled")


def _all_events() -> List[Dict[str, Any]]:
    """Return the full audit trail, oldest-first (read-only)."""
    return _audit.requests()


# ---------------------------------------------------------------------------
# Field helpers (each maps to one approved dashboard field)
# ---------------------------------------------------------------------------

def current_autonomy_level() -> Dict[str, Any]:
    """Field 1: current autonomy level (via Governor, read-only)."""
    lvl = _governor.current_level()
    return {
        "level": lvl,
        "name": _levels.level_name(lvl),
        "auto_execute": _auto_execute_on(),
        "config_intent": _config_intent(),
    }


def active_workflows() -> List[str]:
    """Field 2: workflows eligible to auto-execute at the current level."""
    return sorted(_levels.allowed_workflows(_governor.current_level()))


def pending_requests() -> List[Dict[str, Any]]:
    """Field 3: approved level-change requests not yet applied (read-only).

    Correlates request_id across request/apply events already written by the
    Governor. Rejected requests are terminal and excluded from 'pending'.
    """
    events = _all_events()
    applied_ids = {
        e.get("request_id") for e in events if e.get("event") in _APPLY_EVENTS
    }
    out: List[Dict[str, Any]] = []
    for e in events:
        if e.get("event") != _REQUEST_EVENT:
            continue
        if e.get("decision") != "approved":
            continue
        if e.get("request_id") in applied_ids:
            continue
        out.append(e)
    return out


def approval_history() -> List[Dict[str, Any]]:
    """Field 4: all approved/rejected level-change decisions (read-only)."""
    return [
        e for e in _all_events()
        if e.get("event") == _REQUEST_EVENT
        and e.get("decision") in ("approved", "rejected")
    ]


def audit_events(limit: int = 50) -> List[Dict[str, Any]]:
    """Field 5: most recent audit events, newest-first (read-only)."""
    events = _all_events()
    recent = events[-limit:] if limit and limit > 0 else events
    return list(reversed(recent))


def last_checkpoint() -> Optional[Dict[str, Any]]:
    """Field 6: newest directory under checkpoints/ (read-only scan)."""
    if not os.path.isdir(CHECKPOINTS_DIR):
        return None
    newest: Optional[os.DirEntry] = None
    try:
        for entry in os.scandir(CHECKPOINTS_DIR):
            if not entry.is_dir():
                continue
            if newest is None or entry.stat().st_mtime > newest.stat().st_mtime:
                newest = entry
    except OSError:
        return None
    if newest is None:
        return None
    return {"name": newest.name, "mtime": newest.stat().st_mtime}


def rollback_available() -> bool:
    """Field 7: whether a rollback target exists (derived, read-only).

    True when at least one checkpoint exists AND the autonomy-state files the
    Governor would restore are present and readable. This never performs a
    rollback; it only reports availability.
    """
    if last_checkpoint() is None:
        return False
    return os.path.isfile(SUPERVISOR_PATH) and os.path.isfile(CONFIG_PATH)


def emergency_stop_status() -> Dict[str, Any]:
    """Field 8: emergency-stop status (derived, read-only; NEVER triggers it).

    Reports the last recorded emergency_stop event (if any) and the live
    consistency of the kill-switch state. When auto_execute is off, the
    Governor's contract is that current_level() reports 0.
    """
    events = _all_events()
    last = None
    for e in reversed(events):
        if e.get("event") == _EMERGENCY_EVENT:
            last = e
            break
    ae_on = _auto_execute_on()
    consistent = True if ae_on else (_governor.current_level() == 0)
    return {
        "last_event": last,
        "engaged": bool(last) and not ae_on,
        "auto_execute_on": ae_on,
        "level_zero_consistent": consistent,
    }


# ---------------------------------------------------------------------------
# Full read-only snapshot
# ---------------------------------------------------------------------------

def snapshot(audit_limit: int = 50) -> Dict[str, Any]:
    """Assemble the complete read-only observability view (no mutation).

    Returns all 8 approved fields:
      current_level, active_workflows, pending_requests, approval_history,
      audit_events, last_checkpoint, rollback_available, emergency_stop_status
    """
    return {
        "current_level": current_autonomy_level(),
        "active_workflows": active_workflows(),
        "pending_requests": pending_requests(),
        "approval_history": approval_history(),
        "audit_events": audit_events(limit=audit_limit),
        "last_checkpoint": last_checkpoint(),
        "rollback_available": rollback_available(),
        "emergency_stop_status": emergency_stop_status(),
    }


if __name__ == "__main__":
    import pprint
    pprint.pprint(snapshot())
