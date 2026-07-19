"""Nexus98 Execution Intelligence Framework.

Creates the *execution preparation* architecture: sequencing, batching, retry
policies, validation checkpoints, stopping conditions, and execution metadata.
Crucially, Execution Intelligence does NOT execute — it prepares an
``ExecutionPlan`` that the (authoritative) Supervisor / Project Engine may
later consume under the Governor's safety gate.

Advisory/representational. No autonomy-state mutation. The Supervisor remains
the execution authority.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class RetryPolicy:
    """A reusable retry policy."""

    max_attempts: int = 1
    backoff_seconds: float = 0.0
    retry_on: str = "any"   # "any" | "transient" | "never"

    def to_dict(self) -> dict:
        return {
            "max_attempts": self.max_attempts,
            "backoff_seconds": self.backoff_seconds,
            "retry_on": self.retry_on,
        }


@dataclass
class ExecutionStep:
    """A single prepared (not executed) step."""

    step_id: str
    title: str
    depends_on: List[str] = field(default_factory=list)
    batch: Optional[str] = None
    validation: Optional[str] = None   # validation checkpoint description
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id, "title": self.title,
            "depends_on": list(self.depends_on), "batch": self.batch,
            "validation": self.validation,
            "retry": self.retry.to_dict(), "metadata": self.metadata,
        }


@dataclass
class ExecutionPlan:
    """A fully prepared execution plan (no execution performed)."""

    plan_id: str
    goal: str
    steps: Dict[str, ExecutionStep] = field(default_factory=dict)
    stopping_conditions: List[str] = field(default_factory=list)
    sequence: List[str] = field(default_factory=list)  # topological order

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id, "goal": self.goal,
            "steps": {k: v.to_dict() for k, v in self.steps.items()},
            "stopping_conditions": self.stopping_conditions,
            "sequence": self.sequence,
        }


class ExecutionIntelligence:
    """Prepares execution plans; never runs them."""

    def __init__(self):
        self._plans: Dict[str, ExecutionPlan] = {}

    def prepare(self, goal: str, steps: List[dict],
                *, stopping_conditions: Optional[List[str]] = None,
                default_retry: Optional[RetryPolicy] = None) -> ExecutionPlan:
        """Build an ExecutionPlan from step specs.

        ``steps`` is a list of dicts: {title, depends_on?, batch?, validation?,
        retry?, metadata?}. Returns the prepared plan with a computed sequence.
        """
        pid = uuid.uuid4().hex[:12]
        plan = ExecutionPlan(plan_id=pid, goal=goal,
                             stopping_conditions=list(stopping_conditions or []))
        for spec in steps:
            sid = uuid.uuid4().hex[:12]
            retry = spec.get("retry") or default_retry or RetryPolicy()
            if isinstance(retry, dict):
                retry = RetryPolicy(**retry)
            plan.steps[sid] = ExecutionStep(
                step_id=sid, title=spec["title"],
                depends_on=list(spec.get("depends_on", [])),
                batch=spec.get("batch"),
                validation=spec.get("validation"),
                retry=retry, metadata=spec.get("metadata", {}),
            )
        plan.sequence = self._toposort(plan)
        self._plans[pid] = plan
        return plan

    def batch_steps(self, plan_id: str, batch_key: str = "batch") -> Dict[str, List[str]]:
        plan = self._plans.get(plan_id)
        if not plan:
            return {}
        out: Dict[str, List[str]] = {}
        for sid, step in plan.steps.items():
            key = getattr(step, batch_key) or "default"
            out.setdefault(key, []).append(sid)
        return out

    def ready_steps(self, plan_id: str,
                    completed: Optional[List[str]] = None) -> List[str]:
        plan = self._plans.get(plan_id)
        if not plan:
            return []
        done = set(completed or [])
        return [sid for sid, s in plan.steps.items()
                if set(s.depends_on) <= done]

    def should_stop(self, plan_id: str, *, completed: Optional[List[str]] = None,
                    conditions_met: Optional[List[str]] = None) -> bool:
        plan = self._plans.get(plan_id)
        if not plan:
            return True
        done = set(completed or [])
        if set(plan.steps.keys()) <= done:
            return True
        return bool(set(conditions_met or []) & set(plan.stopping_conditions))

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _toposort(self, plan: ExecutionPlan) -> List[str]:
        """Kahn-style topological order over step dependencies."""
        indeg = {sid: 0 for sid in plan.steps}
        adj: Dict[str, List[str]] = {sid: [] for sid in plan.steps}
        for sid, step in plan.steps.items():
            for dep in step.depends_on:
                if dep in plan.steps:
                    indeg[sid] += 1
                    adj[dep].append(sid)
        queue = sorted([s for s, d in indeg.items() if d == 0])
        order: List[str] = []
        while queue:
            cur = queue.pop(0)
            order.append(cur)
            for nxt in sorted(adj[cur]):
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    queue.append(nxt)
        # If a cycle remains, append the rest to keep a complete plan.
        if len(order) < len(plan.steps):
            order += [s for s in plan.steps if s not in order]
        return order

    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        return self._plans.get(plan_id)
