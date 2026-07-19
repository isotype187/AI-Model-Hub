"""Nexus98 Workspace Continuity Foundation.

Extends the existing lightweight resume helper (``core.resume``) into a
structured continuity + recovery store. It records:

  * Active task tracking (what is in flight, by whom, and its state).
  * Workspace state snapshots (files touched, phase, open context).
  * Recovery information (last good checkpoint, how to resume).
  * Development context preservation across interruptions.

Persistence is a single JSON document under ``data/continuity.json`` by
default. The module is fully standalone and makes NO autonomy-state changes;
it only records state so a future session can understand where work stopped.

Legacy ``core.resume.save_state / load_state`` are preserved for backward
compatibility and are layered on top of the new store.
"""
from __future__ import annotations

import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(r"D:\Nexus98")
DEFAULT_PATH = ROOT / "data" / "continuity.json"
# Backwards-compatible legacy resume path.
LEGACY_PATH = ROOT / "data" / "resume.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkspaceContinuity:
    """Structured continuity + recovery store for a Nexus98 session."""

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else DEFAULT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._state: Dict[str, Any] = self._load()

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return self._empty()
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.setdefault("active_tasks", {})
            data.setdefault("workspace_state", {})
            data.setdefault("recovery", {})
            data.setdefault("context", {})
            return data
        except (json.JSONDecodeError, OSError):
            # Corrupt store: keep a backup and start fresh so we never crash.
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup = self.path.with_suffix(f".corrupt_{ts}.json")
            try:
                shutil.copy2(self.path, backup)
            except OSError:
                pass
            return self._empty()

    def _empty(self) -> Dict[str, Any]:
        return {
            "version": 1,
            "updated_at": _now(),
            "active_tasks": {},
            "workspace_state": {},
            "recovery": {},
            "context": {},
        }

    def save(self) -> None:
        self._state["updated_at"] = _now()
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._state, f, indent=2)
        # Atomic replace.
        shutil.move(str(tmp), str(self.path))

    # ------------------------------------------------------------------
    # Active task tracking
    # ------------------------------------------------------------------

    def start_task(
        self,
        title: str,
        *,
        owner: str = "agent",
        kind: str = "task",
        detail: str = "",
    ) -> str:
        """Register a new in-flight task. Returns its task id."""
        tid = uuid.uuid4().hex[:12]
        self._state["active_tasks"][tid] = {
            "task_id": tid,
            "title": title,
            "owner": owner,
            "kind": kind,
            "detail": detail,
            "status": "in_progress",
            "started_at": _now(),
            "updated_at": _now(),
            "completed_at": None,
        }
        self.save()
        return tid

    def update_task(self, task_id: str, *, status: Optional[str] = None,
                    detail: Optional[str] = None) -> bool:
        task = self._state["active_tasks"].get(task_id)
        if not task:
            return False
        if status is not None:
            task["status"] = status
            if status in ("completed", "done", "failed"):
                task["completed_at"] = _now()
        if detail is not None:
            task["detail"] = detail
        task["updated_at"] = _now()
        self.save()
        return True

    def complete_task(self, task_id: str, *, outcome: str = "completed") -> bool:
        return self.update_task(task_id, status=outcome)

    def active_tasks(self) -> List[dict]:
        """Return tasks that are not yet completed/failed."""
        return [
            t for t in self._state["active_tasks"].values()
            if t.get("status") not in ("completed", "done", "failed")
        ]

    def get_task(self, task_id: str) -> Optional[dict]:
        return self._state["active_tasks"].get(task_id)

    # ------------------------------------------------------------------
    # Workspace state
    # ------------------------------------------------------------------

    def set_workspace_state(self, **fields) -> None:
        self._state["workspace_state"].update(fields)
        self.save()

    def get_workspace_state(self) -> dict:
        return dict(self._state["workspace_state"])

    # ------------------------------------------------------------------
    # Development context
    # ------------------------------------------------------------------

    def set_context(self, **fields) -> None:
        self._state["context"].update(fields)
        self.save()

    def get_context(self) -> dict:
        return dict(self._state["context"])

    # ------------------------------------------------------------------
    # Recovery information
    # ------------------------------------------------------------------

    def set_recovery(self, *, checkpoint: Optional[str] = None,
                     resume_hint: Optional[str] = None,
                     last_good_phase: Optional[str] = None) -> None:
        rec = self._state["recovery"]
        if checkpoint is not None:
            rec["last_checkpoint"] = checkpoint
        if resume_hint is not None:
            rec["resume_hint"] = resume_hint
        if last_good_phase is not None:
            rec["last_good_phase"] = last_good_phase
        rec["recorded_at"] = _now()
        self.save()

    def get_recovery(self) -> dict:
        return dict(self._state["recovery"])

    # ------------------------------------------------------------------
    # Summary for resume
    # ------------------------------------------------------------------

    def snapshot(self) -> dict:
        """A concise resume-oriented view of where work stopped."""
        return {
            "updated_at": self._state.get("updated_at"),
            "active_tasks": self.active_tasks(),
            "workspace_state": self.get_workspace_state(),
            "recovery": self.get_recovery(),
            "context": self.get_context(),
        }

    def close(self) -> None:
        self.save()


# ----------------------------------------------------------------------
# Backwards-compatible legacy resume API (delegates to the store)
# ----------------------------------------------------------------------

_legacy_store = WorkspaceContinuity(LEGACY_PATH)


def save_state(model_id, progress):
    """Legacy shim: record model progress under workspace_state."""
    _legacy_store._state.setdefault("workspace_state", {})["model_progress"] = {
        model_id: progress
    }
    _legacy_store.save()
    return True


def load_state():
    """Legacy shim: return recorded model progress (or empty dict)."""
    return (
        _legacy_store._state.get("workspace_state", {}).get("model_progress", {})
    )


# Convenience singleton for the default continuity store.
default_continuity = WorkspaceContinuity()
