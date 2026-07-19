"""Nexus98 Planning framework.

The foundation for Nexus98 planning capabilities: task decomposition, goal
tracking, milestone planning, dependency tracking, and execution plans.

Critical boundary: **planning is strictly separate from execution authority.**
This framework produces plans and tracks their state; it never executes
actions, never mutates autonomy state, and never invokes the Project Engine to
write files. Execution remains the responsibility of the Supervisor / Project
Engine under the Governor's safety gate.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(r"D:\Nexus98")
DEFAULT_PATH = ROOT / "data" / "plans.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TaskNode:
    """A single decomposed task within a plan."""

    task_id: str
    title: str
    parent_id: Optional[str] = None
    status: str = "planned"   # planned | ready | in_progress | done | blocked
    depends_on: List[str] = field(default_factory=list)
    owner: str = "unassigned"
    detail: str = ""
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id, "title": self.title,
            "parent_id": self.parent_id, "status": self.status,
            "depends_on": list(self.depends_on), "owner": self.owner,
            "detail": self.detail, "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Plan:
    """A goal-oriented plan with milestones and a task tree."""

    plan_id: str
    goal: str
    milestones: List[str] = field(default_factory=list)
    tasks: Dict[str, TaskNode] = field(default_factory=dict)
    status: str = "draft"   # draft | active | paused | completed | cancelled
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id, "goal": self.goal,
            "milestones": list(self.milestones),
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "status": self.status, "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class PlanningEngine:
    """Creates and tracks plans; never executes them."""

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else DEFAULT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._plans: Dict[str, Plan] = self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> Dict[str, Plan]:
        if not self.path.exists():
            return {}
        try:
            rows = json.loads(self.path.read_text(encoding="utf-8"))
            out = {}
            for pid, p in rows.items():
                tasks = {tid: TaskNode(**t) for tid, t in p.get("tasks", {}).items()}
                out[pid] = Plan(
                    plan_id=p["plan_id"], goal=p["goal"],
                    milestones=list(p.get("milestones", [])),
                    tasks=tasks, status=p.get("status", "draft"),
                    created_at=p.get("created_at", _now()),
                    updated_at=p.get("updated_at", _now()),
                )
            return out
        except (json.JSONDecodeError, OSError, KeyError, TypeError):
            return {}

    def save(self) -> None:
        payload = {pid: p.to_dict() for pid, p in self._plans.items()}
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        import shutil
        shutil.move(str(tmp), str(self.path))

    # ------------------------------------------------------------------
    # Plan lifecycle
    # ------------------------------------------------------------------

    def create_plan(self, goal: str, milestones: Optional[List[str]] = None) -> Plan:
        pid = uuid.uuid4().hex[:12]
        plan = Plan(plan_id=pid, goal=goal, milestones=list(milestones or []),
                    status="draft")
        self._plans[pid] = plan
        self.save()
        return plan

    def get_plan(self, plan_id: str) -> Optional[Plan]:
        return self._plans.get(plan_id)

    def list_plans(self, status: Optional[str] = None) -> List[Plan]:
        plans = list(self._plans.values())
        if status:
            plans = [p for p in plans if p.status == status]
        return plans

    def set_plan_status(self, plan_id: str, status: str) -> bool:
        plan = self._plans.get(plan_id)
        if not plan:
            return False
        plan.status = status
        plan.updated_at = _now()
        self.save()
        return True

    # ------------------------------------------------------------------
    # Task decomposition + dependencies
    # ------------------------------------------------------------------

    def add_task(self, plan_id: str, title: str, *,
                 parent_id: Optional[str] = None,
                 depends_on: Optional[List[str]] = None,
                 owner: str = "unassigned", detail: str = "") -> Optional[TaskNode]:
        plan = self._plans.get(plan_id)
        if not plan:
            return None
        tid = uuid.uuid4().hex[:12]
        node = TaskNode(
            task_id=tid, title=title, parent_id=parent_id,
            depends_on=list(depends_on or []), owner=owner, detail=detail,
        )
        plan.tasks[tid] = node
        plan.updated_at = _now()
        self.save()
        return node

    def decompose(self, plan_id: str, title: str, subtasks: List[str],
                 owner: str = "unassigned") -> Optional[str]:
        """Create a parent task and its child subtasks in one call."""
        parent = self.add_task(plan_id, title, owner=owner)
        if not parent:
            return None
        for sub in subtasks:
            self.add_task(plan_id, sub, parent_id=parent.task_id, owner=owner)
        return parent.task_id

    def update_task_status(self, plan_id: str, task_id: str, status: str) -> bool:
        plan = self._plans.get(plan_id)
        if not plan or task_id not in plan.tasks:
            return False
        plan.tasks[task_id].status = status
        plan.tasks[task_id].updated_at = _now()
        plan.updated_at = _now()
        self.save()
        return True

    def ready_tasks(self, plan_id: str) -> List[TaskNode]:
        """Tasks whose dependencies are all 'done' and are not yet started."""
        plan = self._plans.get(plan_id)
        if not plan:
            return []
        done = {t.task_id for t in plan.tasks.values() if t.status == "done"}
        out = []
        for t in plan.tasks.values():
            if t.status in ("planned", "ready") and set(t.depends_on) <= done:
                out.append(t)
        return out

    def progress(self, plan_id: str) -> dict:
        plan = self._plans.get(plan_id)
        if not plan or not plan.tasks:
            return {"plan_id": plan_id, "tasks": 0, "done": 0, "pct": 0.0}
        done = sum(1 for t in plan.tasks.values() if t.status == "done")
        return {
            "plan_id": plan_id, "tasks": len(plan.tasks), "done": done,
            "pct": round(100 * done / len(plan.tasks), 1),
        }

    def close(self) -> None:
        self.save()
