"""Nexus98 Goal Management Framework.

Long-term goal management: goals, subgoals, milestones, dependencies,
priorities, progress tracking, and interruption/resume support. Integrates
with the Continuity store (recovery), the Planning framework (task breakdown),
and Code Memory (rationale/decisions) — it does not replace any of them.

Advisory/representational. No autonomy-state mutation. Goals are persisted as
JSON under ``data/goals.json`` (temp-path safe for tests).
"""
from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(r"D:\Nexus98")
DEFAULT_PATH = ROOT / "data" / "goals.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Goal:
    """A goal with optional subgoals, milestones, and dependencies."""

    goal_id: str
    title: str
    description: str = ""
    parent_id: Optional[str] = None
    priority: int = 3           # 1 (low) .. 5 (high)
    status: str = "active"      # active | paused | completed | archived
    milestones: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    progress_pct: float = 0.0
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "goal_id": self.goal_id, "title": self.title,
            "description": self.description, "parent_id": self.parent_id,
            "priority": self.priority, "status": self.status,
            "milestones": list(self.milestones),
            "depends_on": list(self.depends_on),
            "progress_pct": self.progress_pct,
            "created_at": self.created_at, "updated_at": self.updated_at,
        }


class GoalManager:
    """Manages the goal hierarchy and persistence."""

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else DEFAULT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._goals: Dict[str, Goal] = self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> Dict[str, Goal]:
        if not self.path.exists():
            return {}
        try:
            rows = json.loads(self.path.read_text(encoding="utf-8"))
            return {gid: Goal(**g) for gid, g in rows.items()}
        except (json.JSONDecodeError, OSError, TypeError):
            return {}

    def save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({gid: g.to_dict() for gid, g in self._goals.items()}, f, indent=2)
        shutil.move(str(tmp), str(self.path))

    # ------------------------------------------------------------------
    # Goal lifecycle
    # ------------------------------------------------------------------

    def add_goal(self, title: str, *, description: str = "", parent_id: Optional[str] = None,
                 priority: int = 3, milestones: Optional[List[str]] = None,
                 depends_on: Optional[List[str]] = None) -> Goal:
        gid = uuid.uuid4().hex[:12]
        goal = Goal(
            goal_id=gid, title=title, description=description, parent_id=parent_id,
            priority=priority, milestones=list(milestones or []),
            depends_on=list(depends_on or []),
        )
        self._goals[gid] = goal
        self.save()
        return goal

    def get(self, goal_id: str) -> Optional[Goal]:
        return self._goals.get(goal_id)

    def list_goals(self, status: Optional[str] = None, parent_id: Optional[str] = None) -> List[Goal]:
        out = list(self._goals.values())
        if status:
            out = [g for g in out if g.status == status]
        if parent_id is not None:
            out = [g for g in out if g.parent_id == parent_id]
        return out

    def update_status(self, goal_id: str, status: str) -> bool:
        g = self._goals.get(goal_id)
        if not g:
            return False
        g.status = status
        g.updated_at = _now()
        self.save()
        return True

    def add_milestone(self, goal_id: str, milestone: str) -> bool:
        g = self._goals.get(goal_id)
        if not g:
            return False
        if milestone not in g.milestones:
            g.milestones.append(milestone)
        g.updated_at = _now()
        self.save()
        return True

    def set_dependency(self, goal_id: str, depends_on: str) -> bool:
        g = self._goals.get(goal_id)
        if not g or depends_on not in self._goals:
            return False
        if depends_on not in g.depends_on:
            g.depends_on.append(depends_on)
        g.updated_at = _now()
        self.save()
        return True

    # ------------------------------------------------------------------
    # Progress + interruption/resume
    # ------------------------------------------------------------------

    def set_progress(self, goal_id: str, pct: float) -> bool:
        g = self._goals.get(goal_id)
        if not g:
            return False
        g.progress_pct = round(max(0.0, min(100.0, pct)), 1)
        g.updated_at = _now()
        self.save()
        return True

    def active_goals(self) -> List[Goal]:
        return sorted(
            [g for g in self._goals.values() if g.status == "active"],
            key=lambda g: g.priority, reverse=True,
        )

    def resume_context(self) -> dict:
        """A concise resume view for interruption recovery."""
        active = self.active_goals()
        return {
            "updated_at": _now(),
            "active_count": len(active),
            "active_goals": [
                {"goal_id": g.goal_id, "title": g.title, "progress": g.progress_pct}
                for g in active
            ],
        }

    def close(self) -> None:
        self.save()
