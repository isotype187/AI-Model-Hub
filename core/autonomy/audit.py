"""Phase 8 - Autonomy Governor: append-only audit log.

Reuses the existing history/ trail (history/autonomy/). Every request,
decision, level transition, and checkpoint reference is recorded here.
This module performs NO autonomy-state mutation; it only appends.
"""
from __future__ import annotations
import json
import os
import time
from typing import Any, Dict, Optional

# Audit log lives under history/ (consistent with history/operations).
AUDIT_DIR = os.path.join("history", "autonomy")
AUDIT_FILE = os.path.join(AUDIT_DIR, "audit.log")


def _ensure_dir() -> None:
    os.makedirs(AUDIT_DIR, exist_ok=True)


def record(event: str, **fields: Any) -> Dict[str, Any]:
    """Append one structured audit record; return it. Does not mutate state."""
    _ensure_dir()
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "event": event,
    }
    for k, v in fields.items():
        entry[k] = v
    line = json.dumps(entry, ensure_ascii=False)
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    return entry


def requests() -> list:
    """Return all audit records (read-only)."""
    if not os.path.exists(AUDIT_FILE):
        return []
    out = []
    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if ln:
                out.append(json.loads(ln))
    return out


def last_request(request_id: str) -> Optional[Dict[str, Any]]:
    for r in reversed(requests()):
        if r.get("request_id") == request_id:
            return r
    return None
