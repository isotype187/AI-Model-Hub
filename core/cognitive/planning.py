"""Nexus98 Planning Intelligence Framework.

Expands planning into a production architecture: task decomposition, execution
graphs, dependency graphs, alternative plans, rollback plans, checkpoints,
estimated effort, and resource estimation. It wraps the existing
``core.frameworks.planning.PlanningEngine`` and adds intelligence on top.

Planning remains strictly **advisory**. This framework never executes actions
and never mutates autonomy state — it produces plans and analyses.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from core.frameworks.planning import PlanningEngine, Plan, TaskNode


@dataclass
class ExecutionEdge:
    """A directed edge in the execution/dependency graph."""

    from_id: str
    to_id: str
    kind: str  # sequence | dependency | rollback | alternative


@dataclass
class PlanAnalysis:
    """Intelligence attached to a plan."""

    plan_id: str
    alternatives: int = 0
    rollback_points: int = 0
    checkpoints: int = 0
    estimated_effort_hours: float = 0.0
    estimated_resources: Dict[str, float] = field(default_factory=dict)
    critical_path: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id, "alternatives": self.alternatives,
            "rollback_points": self.rollback_points, "checkpoints": self.checkpoints,
            "estimated_effort_hours": self.estimated_effort_hours,
            "estimated_resources": dict(self.estimated_resources),
            "critical_path": list(self.critical_path),
        }


class PlanningIntelligence:
    """Production planning intelligence over a PlanningEngine."""

    def __init__(self, engine: Optional[PlanningEngine] = None, path=None):
        self.engine = engine or PlanningEngine(path)

    # ------------------------------------------------------------------
    # Delegated planning
    # ------------------------------------------------------------------

    def create_plan(self, goal: str, milestones=None) -> Plan:
        return self.engine.create_plan(goal, milestones)

    def decompose(self, plan_id: str, title: str, subtasks: List[str], owner="unassigned"):
        return self.engine.decompose(plan_id, title, subtasks, owner=owner)

    # ------------------------------------------------------------------
    # Graphs
    # ------------------------------------------------------------------

    def execution_graph(self, plan_id: str) -> List[ExecutionEdge]:
        """Sequence edges derived from parent/child + dependency relations."""
        plan = self.engine.get_plan(plan_id)
        if not plan:
            return []
        edges: List[ExecutionEdge] = []
        for t in plan.tasks.values():
            if t.parent_id:
                edges.append(ExecutionEdge(t.parent_id, t.task_id, "sequence"))
            for dep in t.depends_on:
                edges.append(ExecutionEdge(dep, t.task_id, "dependency"))
        return edges

    def dependency_graph(self, plan_id: str) -> Dict[str, List[str]]:
        plan = self.engine.get_plan(plan_id)
        if not plan:
            return {}
        return {tid: list(t.depends_on) for tid, t in plan.tasks.items()}

    # ------------------------------------------------------------------
    # Alternatives / rollback / checkpoints
    # ------------------------------------------------------------------

    def add_alternative(self, plan_id: str, title: str, subtasks: List[str]) -> Optional[str]:
        """Register an alternative approach (a sibling branch)."""
        parent = self.engine.add_task(plan_id, title, detail="alternative-approach")
        for sub in subtasks:
            self.engine.add_task(plan_id, sub, parent_id=parent.task_id)
        return parent.task_id

    def mark_checkpoint(self, plan_id: str, task_id: str) -> bool:
        plan = self.engine.get_plan(plan_id)
        if not plan or task_id not in plan.tasks:
            return False
        plan.tasks[task_id].detail = (plan.tasks[task_id].detail + " [checkpoint]").strip()
        self.engine.save()
        return True

    def add_rollback_plan(self, plan_id: str, for_task: str, steps: List[str]) -> Optional[str]:
        """Attach a rollback branch that reverts `for_task`."""
        rb = self.engine.add_task(
            plan_id, f"rollback:{for_task}", detail="rollback-plan",
            depends_on=[for_task],
        )
        for step in steps:
            self.engine.add_task(plan_id, step, parent_id=rb.task_id)
        return rb.task_id

    # ------------------------------------------------------------------
    # Estimation
    # ------------------------------------------------------------------

    def estimate(self, plan_id: str, *, hours_per_task: float = 1.0,
                 resources: Optional[Dict[str, float]] = None) -> PlanAnalysis:
        plan = self.engine.get_plan(plan_id)
        if not plan:
            return PlanAnalysis(plan_id=plan_id)
        n = len(plan.tasks)
        analysis = PlanAnalysis(
            plan_id=plan_id,
            alternatives=sum(1 for t in plan.tasks.values()
                             if "alternative" in t.detail),
            rollback_points=sum(1 for t in plan.tasks.values()
                                if "rollback" in t.detail),
            checkpoints=sum(1 for t in plan.tasks.values()
                            if "checkpoint" in t.detail),
            estimated_effort_hours=round(n * hours_per_task, 2),
            estimated_resources=dict(resources or {}),
        )
        analysis.critical_path = self._critical_path(plan_id)
        return analysis

    def _critical_path(self, plan_id: str) -> List[str]:
        """Longest dependency chain (by task count) via DFS."""
        plan = self.engine.get_plan(plan_id)
        if not plan:
            return []
        memo: Dict[str, int] = {}

        def depth(tid: str) -> int:
            if tid in memo:
                return memo[tid]
            t = plan.tasks.get(tid)
            if not t or not t.depends_on:
                memo[tid] = 1
                return 1
            best = 1 + max(depth(d) for d in t.depends_on if d in plan.tasks)
            memo[tid] = best
            return best

        best_tid = max(plan.tasks, key=depth) if plan.tasks else None
        # reconstruct
        path: List[str] = []
        cur = best_tid
        while cur and cur in plan.tasks:
            path.append(cur)
            deps = plan.tasks[cur].depends_on
            cur = max(deps, key=depth) if deps else None
        return list(reversed(path))

    def close(self) -> None:
        self.engine.close()
