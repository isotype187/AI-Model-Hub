"""Nexus98 Project Intelligence framework.

Extends (does NOT replace) the Project Engine with higher-level awareness:
project understanding, state awareness, dependency awareness, change planning,
checkpoint awareness, and progress tracking.

This framework is a *read/plan* layer. It records intelligence records to the
Workspace Reality store and the Continuity store, and it asks the Project
Engine to perform the actual file mutations (Project Engine stays the only
authorized file mutator). It performs no autonomy-state mutation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from core.frameworks.workspace import WorkspaceReality


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ChangePlan:
    """A planned, reviewable change (not yet executed)."""

    change_id: str
    title: str
    target: str            # file / component path
    rationale: str
    steps: List[str] = field(default_factory=list)
    status: str = "planned"  # planned | approved | in_progress | done | cancelled
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "change_id": self.change_id, "title": self.title, "target": self.target,
            "rationale": self.rationale, "steps": list(self.steps),
            "status": self.status, "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class ProjectIntelligence:
    """Project-level awareness built on WorkspaceReality + Continuity."""

    def __init__(self, reality: Optional[WorkspaceReality] = None,
                 path: Optional[Path] = None):
        self.reality = reality or WorkspaceReality(path)
        self._intel: Dict[str, dict] = self._load_intel()

    # ------------------------------------------------------------------
    # Intelligence storage (lives beside reality under a sibling key)
    # ------------------------------------------------------------------

    def _intel_path(self) -> Path:
        return self.reality.path.with_name("project_intelligence.json")

    def _load_intel(self) -> Dict[str, dict]:
        p = self._intel_path()
        if not p.exists():
            return {"projects": {}, "change_plans": {}, "dependencies": {}}
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.setdefault("projects", {})
            data.setdefault("change_plans", {})
            data.setdefault("dependencies", {})
            return data
        except (json.JSONDecodeError, OSError):
            return {"projects": {}, "change_plans": {}, "dependencies": {}}

    def _save_intel(self) -> None:
        p = self._intel_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._intel, f, indent=2)
        # atomic replace
        import shutil
        shutil.move(str(tmp), str(p))

    # ------------------------------------------------------------------
    # Project understanding / state awareness
    # ------------------------------------------------------------------

    def understand_project(self, project_id: str, *, summary: str = "",
                           state: str = "unknown", health: str = "unknown") -> dict:
        """Record/refresh an understanding record for a project."""
        rec = self._intel["projects"].get(project_id, {"project_id": project_id})
        rec.update({
            "summary": summary, "state": state, "health": health,
            "understood_at": _now(),
        })
        self._intel["projects"][project_id] = rec
        self._save_intel()
        return rec

    def project_state(self, project_id: str) -> Optional[dict]:
        return self._intel["projects"].get(project_id)

    # ------------------------------------------------------------------
    # Dependency awareness
    # ------------------------------------------------------------------

    def record_dependency(self, project_id: str, depends_on: str,
                          relation: str = "depends_on") -> dict:
        deps = self._intel["dependencies"].setdefault(project_id, [])
        entry = {"depends_on": depends_on, "relation": relation, "recorded_at": _now()}
        if entry not in deps:
            deps.append(entry)
        self._save_intel()
        return entry

    def dependencies_of(self, project_id: str) -> List[dict]:
        return list(self._intel["dependencies"].get(project_id, []))

    # ------------------------------------------------------------------
    # Change planning (separate from execution)
    # ------------------------------------------------------------------

    def plan_change(self, title: str, target: str, rationale: str,
                    steps: Optional[List[str]] = None) -> ChangePlan:
        import uuid
        cid = uuid.uuid4().hex[:12]
        plan = ChangePlan(
            change_id=cid, title=title, target=target,
            rationale=rationale, steps=list(steps or []),
        )
        self._intel["change_plans"][cid] = plan.to_dict()
        self._save_intel()
        return plan

    def update_change_status(self, change_id: str, status: str) -> bool:
        plan = self._intel["change_plans"].get(change_id)
        if not plan:
            return False
        plan["status"] = status
        plan["updated_at"] = _now()
        self._save_intel()
        return True

    def list_change_plans(self, status: Optional[str] = None) -> List[dict]:
        plans = list(self._intel["change_plans"].values())
        if status:
            plans = [p for p in plans if p.get("status") == status]
        return plans

    # ------------------------------------------------------------------
    # Checkpoint / progress awareness
    # ------------------------------------------------------------------

    def note_checkpoint(self, project_id: str, checkpoint: str,
                        note: str = "") -> dict:
        rec = self._intel["projects"].get(project_id, {"project_id": project_id})
        rec.setdefault("checkpoints", []).append({
            "checkpoint": checkpoint, "note": note, "at": _now(),
        })
        rec["last_checkpoint"] = checkpoint
        self._intel["projects"][project_id] = rec
        self._save_intel()
        return rec

    def track_progress(self, project_id: str, milestone: str,
                       done: bool = False) -> dict:
        rec = self._intel["projects"].get(project_id, {"project_id": project_id})
        milestones = rec.setdefault("milestones", [])
        m = next((x for x in milestones if x["name"] == milestone), None)
        if m is None:
            m = {"name": milestone, "done": done, "at": _now()}
            milestones.append(m)
        else:
            m["done"] = done
            m["at"] = _now()
        rec["progress_pct"] = round(
            100 * sum(1 for x in milestones if x["done"]) / max(1, len(milestones)), 1
        )
        self._intel["projects"][project_id] = rec
        self._save_intel()
        return rec

    def summary(self) -> dict:
        return {
            "projects_understood": len(self._intel["projects"]),
            "change_plans": len(self._intel["change_plans"]),
            "dependencies": sum(len(v) for v in self._intel["dependencies"].values()),
        }

    def close(self) -> None:
        self._save_intel()
