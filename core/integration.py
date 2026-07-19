"""Nexus98 Framework Integration Facade.

The single internal coordination interface that lets the verified frameworks
cooperate. It extends (does NOT replace) :mod:`core.coordination` by wiring in
the additional architecture frameworks:

  * Strategy Engine      -> task guidance (advisory)
  * Model Intelligence    -> model recommendation (advisory)
  * Planning              -> task handoff / plan awareness
  * Workspace Continuity  -> context refresh (reality snapshot)
  * Code / Knowledge Mem  -> knowledge retrieval
  * Evaluation & Review   -> completion analysis

Design rules (enforced by structure, not just comments):
  * This layer ONLY coordinates. It owns no autonomy decisions.
  * It never flips ``auto_execute`` and never invokes the Governor/Guardian
    for state writes.
  * The Router remains authoritative for role selection; the Supervisor remains
    authoritative for execution; this facade merely supplies advisory context.
  * All framework writes it performs (memory, continuity, workspace reality,
    plans, reviews) are persistence/record-keeping actions the agent is
    already authorized to perform.

See docs/NEXUS98_FRAMEWORK_INTEGRATION_20260718.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional

from core.coordination import AgentCoordinator, TaskHandoff
from core.strategy import StrategyController, default_controller
from core.code_memory import CodeMemory, default_memory
from core.continuity import WorkspaceContinuity, default_continuity
from core.tool_registry import ToolRegistry, default_registry

# Framework imports are optional at import time so a missing/optional framework
# degrades gracefully rather than breaking the whole facade.
try:
    from core.frameworks.model import ModelIntelligence
except Exception:  # pragma: no cover - defensive
    ModelIntelligence = None

try:
    from core.frameworks.workspace import WorkspaceReality
except Exception:  # pragma: no cover
    WorkspaceReality = None

try:
    from core.frameworks.planning import PlanningEngine
except Exception:  # pragma: no cover
    PlanningEngine = None

try:
    from core.frameworks.knowledge import KnowledgeArchitecture
except Exception:  # pragma: no cover
    KnowledgeArchitecture = None

try:
    from core.frameworks.review import ReviewSystem
except Exception:  # pragma: no cover
    ReviewSystem = None

try:
    # Cognitive orchestrator (advisory composition of cognitive frameworks).
    from core.cognitive.orchestrator import CognitiveOrchestrator
except Exception:  # pragma: no cover
    CognitiveOrchestrator = None


@dataclass
class TaskContext:
    """Advisory, assembled context for a single task lifecycle moment.

    Combines strategy guidance, model recommendation, workspace reality, and
    relevant memory. Pure data — no side effects on creation.
    """

    task: str
    handoff: Optional[TaskHandoff] = None
    model_recommendation: Optional[dict] = None
    workspace_reality: Optional[dict] = None
    relevant_memory: List[dict] = field(default_factory=list)
    review_summary: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "task": self.task,
            "handoff": self.handoff.to_dict() if self.handoff else None,
            "model_recommendation": self.model_recommendation,
            "workspace_reality": self.workspace_reality,
            "relevant_memory": self.relevant_memory,
            "review_summary": self.review_summary,
        }


class FrameworkIntegrator:
    """Central coordinator across all Nexus98 frameworks.

    Accepts subsystem instances for testing; falls back to module defaults.
    """

    def __init__(
        self,
        coordinator: Optional[AgentCoordinator] = None,
        strategy: Optional[StrategyController] = None,
        memory: Optional[CodeMemory] = None,
        continuity: Optional[WorkspaceContinuity] = None,
        registry: Optional[ToolRegistry] = None,
        models: Optional["ModelIntelligence"] = None,
        reality: Optional["WorkspaceReality"] = None,
        planning: Optional["PlanningEngine"] = None,
        knowledge: Optional["KnowledgeArchitecture"] = None,
        review: Optional["ReviewSystem"] = None,
        orchestrator: Optional["CognitiveOrchestrator"] = None,
    ):
        self.coordinator = coordinator or AgentCoordinator(
            strategy=strategy or default_controller,
            memory=memory or default_memory,
            continuity=continuity or default_continuity,
            registry=registry or default_registry,
        )
        self.models = models
        self.reality = reality
        self.planning = planning
        self.knowledge = knowledge
        self.review = review
        self.orchestrator = orchestrator
        self._history: List[dict] = []

    # ------------------------------------------------------------------
    # Phase 1: per-framework integration points
    # ------------------------------------------------------------------

    def strategy_guidance(self, task: str, strategy: Optional[FrozenSet[str]] = None,
                          *, autonomous: bool = False) -> TaskHandoff:
        """Strategy Engine: advisory task guidance + router role hint."""
        return self.coordinator.plan_handoff(task, strategy, autonomous=autonomous)

    def model_recommendation(self, task: str, *, category: Optional[str] = None,
                             available_only: bool = True) -> Optional[dict]:
        """Model Intelligence: advisory model recommendation (or None)."""
        if self.models is None:
            return None
        return self.models.explain_recommendation(
            task, category=category, available_only=available_only
        )

    def refresh_workspace_context(self, **state) -> Optional[dict]:
        """Workspace Continuity: capture/refresh reality snapshot."""
        if self.reality is None:
            return None
        for k, v in state.items():
            self.reality.set_state(k, v)
        return self.reality.reality_snapshot()

    def retrieve_knowledge(self, query: str, *, limit: int = 5) -> List[dict]:
        """Code/Knowledge Memory: relevant knowledge retrieval."""
        if self.knowledge is not None:
            return self.knowledge.memory.recall(tags=None)[:limit] or \
                self.knowledge.memory.search(query)[:limit]
        return self.coordinator.recall()[:limit]

    def analyze_completion(self, subject: str, scores: Dict[str, float],
                           *, notes: str = "") -> Optional[dict]:
        """Evaluation & Review: record a completion analysis."""
        if self.review is None:
            return None
        ev = self.review.evaluate(subject, "task", scores, notes=notes)
        return ev.to_dict()

    # ------------------------------------------------------------------
    # Phase 1: assembled task context (the integration moment)
    # ------------------------------------------------------------------

    def build_task_context(
        self,
        task: str,
        strategy: Optional[FrozenSet[str]] = None,
        *,
        autonomous: bool = False,
        with_model: bool = True,
        with_workspace: bool = True,
        with_memory: bool = True,
    ) -> TaskContext:
        """Assemble advisory context from every connected framework.

        Coordination only: collects guidance, does not act on it.
        """
        handoff = self.strategy_guidance(task, strategy, autonomous=autonomous)
        model_rec = self.model_recommendation(task) if with_model else None
        reality = self.refresh_workspace_context(task=task) if with_workspace else None
        memory = self.retrieve_knowledge(task) if with_memory else []
        ctx = TaskContext(
            task=task,
            handoff=handoff,
            model_recommendation=model_rec,
            workspace_reality=reality,
            relevant_memory=memory,
        )
        self._history.append({"kind": "context", "task": task,
                              "safety_constrained": handoff.safety_constrained})
        return ctx

    def last_coordination_history(self) -> List[dict]:
        return list(self._history)

    # ------------------------------------------------------------------
    # Cognitive bootstrap (read-only startup activation)
    # ------------------------------------------------------------------

    def boot_report(self, *, startup_objective: str = "",
                    run_cognitive_cycle: bool = False) -> Optional[dict]:
        """Read-only cognitive activation report (capabilities + health + context).

        Advisory only; performs no writes or autonomy changes.
        """
        try:
            from core.cognitive.bootstrap import CognitiveBootstrap
        except Exception:
            return None
        bootstrap = CognitiveBootstrap(orchestrator=self.orchestrator)
        return bootstrap.activate(
            startup_objective=startup_objective,
            run_cognitive_cycle=run_cognitive_cycle,
        ).to_dict()

    # ------------------------------------------------------------------
    # Cognitive orchestration (advisory composition)
    # ------------------------------------------------------------------

    def cognitive_cycle(self, task: str, **kwargs) -> Optional[dict]:
        """Run an advisory cognitive cycle via the CognitiveOrchestrator.

        Returns the cycle dict, or None if no orchestrator is wired. Advisory
        only — no execution or autonomy change occurs.
        """
        if self.orchestrator is None or CognitiveOrchestrator is None:
            return None
        cycle = self.orchestrator.run_cycle(task, **kwargs)
        return cycle.to_dict()

    # ------------------------------------------------------------------
    # Planning integration (delegated)
    # ------------------------------------------------------------------

    def plan_handoff(self, plan_id: str, task_id: str) -> Optional[dict]:
        """Return the planning record for a handoff (advisory)."""
        if self.planning is None:
            return None
        plan = self.planning.get_plan(plan_id)
        if plan is None or task_id not in plan.tasks:
            return None
        node = plan.tasks[task_id]
        return {
            "plan_id": plan_id, "goal": plan.goal,
            "task": node.to_dict(), "ready": node.task_id in
            [t.task_id for t in self.planning.ready_tasks(plan_id)],
        }

    # ------------------------------------------------------------------
    # Capability awareness summary (Phase 3 foundation)
    # ------------------------------------------------------------------

    def capability_report(self) -> dict:
        """One-shot view of what the agent can see before acting."""
        report = {
            "tools": self.coordinator.capabilities(),
            "strategy_catalog": sorted(
                s for s in __import__("core.strategy", fromlist=["STRATEGIES"]).STRATEGIES
            ),
        }
        if self.models is not None:
            report["models"] = self.models.capability_summary()
        if self.reality is not None:
            report["workspace"] = self.reality.reality_snapshot()
        if self.review is not None:
            report["review"] = self.review.summary()
        return report


# Convenience singleton wiring the available defaults.
# The CognitiveOrchestrator is wired here so the advisory cognitive
# cycle is available as live backend state (default_integrator.cognitive_cycle).
default_integrator = FrameworkIntegrator(
    orchestrator=CognitiveOrchestrator() if CognitiveOrchestrator else None,
)

