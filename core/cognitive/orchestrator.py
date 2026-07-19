"""Nexus98 Cognitive Orchestrator.

The single advisory pipeline that composes the ten cognitive frameworks into
one coherent cycle per task:

    intent -> goal/context -> plan -> decision -> execution-prep ->
    review -> learning   (all coordinated over the CommunicationBus)

This orchestrator is the *glue* that connects the otherwise-disconnected
cognitive frameworks. It performs NO execution and makes NO autonomy decisions.
Every framework it calls is advisory/representational; the Supervisor remains
the execution authority and the Governor remains the autonomy authority.

The orchestrator publishes lifecycle messages on the ``CommunicationBus`` so
other subsystems (UI, Supervisor, logs) can observe the cognitive process
without the frameworks being hard-coupled to them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from core.cognitive.intent import IntentAnalyzer, Intent
from core.cognitive.context import ContextAssembler, TaskContext
from core.cognitive.planning import PlanningIntelligence
from core.cognitive.decision import DecisionEngine, Option
from core.cognitive.execution import ExecutionIntelligence
from core.cognitive.review import ReviewIntelligence
from core.cognitive.learning import LearningSystem
from core.cognitive.comms import CommunicationBus


@dataclass
class CognitiveCycle:
    """The assembled output of one cognitive cycle (pure data)."""

    task: str
    intent: Optional[dict] = None
    context: Optional[dict] = None
    plan_id: Optional[str] = None
    decision: Optional[dict] = None
    execution_plan_id: Optional[str] = None
    review: Optional[dict] = None
    learned: List[str] = field(default_factory=list)
    trace: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "task": self.task,
            "intent": self.intent,
            "context": self.context,
            "plan_id": self.plan_id,
            "decision": self.decision,
            "execution_plan_id": self.execution_plan_id,
            "review": self.review,
            "learned": self.learned,
            "trace": self.trace,
        }


class CognitiveOrchestrator:
    """Composes the cognitive frameworks into one advisory cycle.

    Subsystems are injected (dependency injection); sensible defaults are
    created when omitted so the orchestrator is usable standalone. The
    orchestrator never executes — it prepares, analyzes, and records.
    """

    def __init__(
        self,
        intent_analyzer: Optional[IntentAnalyzer] = None,
        context: Optional[ContextAssembler] = None,
        planning: Optional[PlanningIntelligence] = None,
        decision: Optional[DecisionEngine] = None,
        execution: Optional[ExecutionIntelligence] = None,
        review: Optional[ReviewIntelligence] = None,
        learning: Optional[LearningSystem] = None,
        bus: Optional[CommunicationBus] = None,
    ):
        self.intent = intent_analyzer or IntentAnalyzer()
        self.context = context or ContextAssembler()
        self.planning = planning or PlanningIntelligence()
        self.decision = decision or DecisionEngine()
        self.execution = execution or ExecutionIntelligence()
        self.review = review or ReviewIntelligence()
        self.learning = learning or LearningSystem()
        self.bus = bus or CommunicationBus()
        self._cycles: List[CognitiveCycle] = []

    # ------------------------------------------------------------------
    # The advisory cognitive cycle
    # ------------------------------------------------------------------

    def run_cycle(self, task: str, *, goal_title: Optional[str] = None,
                  strategy: Optional[List[str]] = None,
                  steps: Optional[List[dict]] = None,
                  review_type: str = "implementation",
                  review_scores: Optional[Dict[str, float]] = None) -> CognitiveCycle:
        """Run one full advisory cognitive cycle for a task.

        Produces intent, context, plan, decision, execution-prep, optional
        review, and learning — all without executing anything.
        """
        cycle = CognitiveCycle(task=task)
        self.bus.publish("strategy", "cycle_start", {"task": task}, source="orchestrator")

        # 1. Intent
        intent = self.intent.analyze(task)
        cycle.intent = intent.to_dict()
        cycle.trace.append({"stage": "intent", "type": intent.intent_type.value,
                            "confidence": intent.confidence})
        self.bus.publish("memory", "intent_analyzed", cycle.intent, source="orchestrator")

        # 2. Context
        ctx: TaskContext = self.context.assemble(
            task, strategy=strategy)
        cycle.context = ctx.to_dict()
        self.bus.publish("context", "assembled", cycle.context, source="orchestrator")

        # 3. Plan (advisory)
        plan = self.planning.create_plan(goal_title or task)
        if steps:
            for s in steps:
                self.planning.engine.add_task(plan.plan_id, s["title"],
                                              depends_on=s.get("depends_on", []))
        cycle.plan_id = plan.plan_id
        self.bus.publish("planning", "plan_created", {"plan_id": plan.plan_id},
                         source="orchestrator")

        # 4. Decision (recommend an approach; advisory)
        opts = [
            Option("plan_a", "primary approach",
                   {"capability": 0.8, "cost": 0.7, "safety": 0.9}, risk=0.2),
            Option("plan_b", "alternate approach",
                   {"capability": 0.6, "cost": 0.9, "safety": 0.8}, risk=0.3),
        ]
        decision = self.decision.evaluate(f"approach for: {task}", opts)
        cycle.decision = decision.to_dict()
        self.bus.publish("strategy", "decision_made", cycle.decision, source="orchestrator")

        # 5. Execution preparation (NO execution)
        exec_steps = steps or [{"title": "implement"}, {"title": "validate"}]
        exec_plan = self.execution.prepare(task, exec_steps,
                                           stopping_conditions=["all_done"])
        cycle.execution_plan_id = exec_plan.plan_id
        self.bus.publish("supervisor", "execution_prepared", exec_plan.to_dict(),
                         source="orchestrator")

        # 6. Review (if scores provided) + Learning (passive)
        if review_scores:
            rec = self.review.review_subject(review_type, task, review_scores)
            cycle.review = rec.to_dict()
            self.bus.publish("memory", "review_recorded", cycle.review, source="orchestrator")
            self.learning.record_pattern(
                "success" if rec.verdict == "pass" else "failure",
                f"review:{review_type}:{task}", outcome=rec.verdict,
                confidence=rec.quality if hasattr(rec, "quality") else 0.6,
            )
            cycle.learned.append(f"review:{rec.verdict}")

        self._cycles.append(cycle)
        self.bus.publish("strategy", "cycle_complete", {"task": task}, source="orchestrator")
        return cycle

    def last_cycles(self) -> List[dict]:
        return [c.to_dict() for c in self._cycles]

    # ------------------------------------------------------------------
    # Convenience: passive learning from an observed outcome
    # ------------------------------------------------------------------

    def learn_outcome(self, task: str, outcome: str, *, confidence: float = 0.6,
                      lesson: Optional[str] = None) -> None:
        """Passively record an observed outcome as a learning pattern."""
        self.learning.record_pattern(
            "success" if outcome == "success" else "failure",
            f"outcome:{task}", outcome=outcome, confidence=confidence,
        )
        if lesson:
            self.learning.record_pattern("heuristic", lesson, confidence=confidence)

    def close(self) -> None:
        for sub in (self.planning, self.review, self.learning):
            try:
                sub.close()
            except Exception:
                pass


# Convenience singleton wiring default subsystems.
default_orchestrator = CognitiveOrchestrator()
