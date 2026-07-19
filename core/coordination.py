"""Nexus98 Agent Coordination layer.

A thin orchestration facade that ties the major subsystems together with
clean, well-defined interfaces so the Supervisor, Router, Project Engine,
Strategy Engine, Code Memory, Continuity, and Tool Registry can exchange
information without tight coupling or duplicate authority.

This module is *coordination glue only*. It does not own any state of its
own beyond references to the subsystem singletons. It never changes autonomy
state, never flips ``auto_execute``, and never bypasses the Governor or
Guardian boundaries.

Coordination responsibilities:
  * Hand a task to the Strategy Engine for advisory guidance.
  * Translate that guidance into a Router role hint.
  * Give agents a single entry point to record/recall Code Memory.
  * Give agents a single entry point to track continuity + recovery.
  * Allow agents to discover tools via the Tool Registry.
  * Provide structured, explainable logging for task handoffs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional

from core.strategy import StrategyController, default_controller
from core.code_memory import CodeMemory, default_memory
from core.continuity import WorkspaceContinuity, default_continuity
from core.tool_registry import ToolRegistry, default_registry


@dataclass
class TaskHandoff:
    """A structured handoff passed between coordination participants."""

    task: str
    strategy: FrozenSet[str] = field(default_factory=frozenset)
    recommended_role: str = "researcher"
    safety_constrained: bool = False
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "task": self.task,
            "strategy": sorted(self.strategy),
            "recommended_role": self.recommended_role,
            "safety_constrained": self.safety_constrained,
            "notes": self.notes,
        }


class AgentCoordinator:
    """Facade coordinating strategy, memory, continuity, and tools.

    Construct with explicit subsystem instances for testing, or rely on the
    module-level defaults. All operations are advisory/record-keeping except
    memory/continuity writes, which are intentionally persistence actions the
    agent is authorized to perform.
    """

    def __init__(
        self,
        strategy: Optional[StrategyController] = None,
        memory: Optional[CodeMemory] = None,
        continuity: Optional[WorkspaceContinuity] = None,
        registry: Optional[ToolRegistry] = None,
    ):
        self.strategy = strategy or default_controller
        self.memory = memory or default_memory
        self.continuity = continuity or default_continuity
        self.registry = registry or default_registry
        self._handoff_log: List[dict] = []

    # ------------------------------------------------------------------
    # Strategy -> routing handoff
    # ------------------------------------------------------------------

    def plan_handoff(
        self,
        task: str,
        strategy: Optional[FrozenSet[str]] = None,
        *,
        autonomous: bool = False,
    ) -> TaskHandoff:
        """Produce an advisory handoff for a task.

        Combines strategy evaluation with a router role hint. Does not route;
        the Router remains the authority for final role selection.
        """
        decision = self.strategy.evaluate(
            task=task, active=strategy, autonomous=autonomous
        )
        handoff = TaskHandoff(
            task=task,
            strategy=decision.active,
            recommended_role=decision.recommended_role,
            safety_constrained=decision.safety_constrained,
            notes=decision.explanation,
        )
        self._handoff_log.append(handoff.to_dict())
        return handoff

    def last_handoffs(self) -> List[dict]:
        return list(self._handoff_log)

    # ------------------------------------------------------------------
    # Memory delegation
    # ------------------------------------------------------------------

    def remember(self, category: str, content: str, **kwargs) -> str:
        return self.memory.record_knowledge(category, content, **kwargs)

    def recall(self, category: Optional[str] = None, **kwargs) -> List[dict]:
        return self.memory.recall(category, **kwargs)

    # ------------------------------------------------------------------
    # Continuity delegation
    # ------------------------------------------------------------------

    def track_task(self, title: str, **kwargs) -> str:
        return self.continuity.start_task(title, **kwargs)

    def complete_tracked(self, task_id: str, **kwargs) -> bool:
        return self.continuity.complete_task(task_id, **kwargs)

    def record_recovery(self, **kwargs) -> None:
        self.continuity.set_recovery(**kwargs)

    # ------------------------------------------------------------------
    # Tool discovery delegation
    # ------------------------------------------------------------------

    def discover_tools(self, query: str) -> List[dict]:
        return [t.to_dict() for t in self.registry.search(query)]

    def capabilities(self) -> dict:
        return self.registry.capability_summary()


# Convenience singleton wiring the defaults together.
default_coordinator = AgentCoordinator()
