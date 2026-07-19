"""Phase C - Real Task Execution Pipeline (advisory).

Converts Nexus98 from a validated platform into a useful operating system for
AI workflows. This module is the *next layer* that ties the existing
authority-bounded systems together into one end-to-end, advisory flow:

    user goal input -> task decomposition -> agent assignment ->
    execution tracking -> review cycle -> memory/state update

It deliberately delegates every authoritative decision to the systems that
already own it, and never crosses an authority boundary:

  * Execution authority  -> core.supervisor.run_task / run_action_task
  * Routing authority     -> core.router.route
  * Autonomy authority    -> core.autonomy.governor (NOT invoked here)
  * Advisory composition  -> core.cognitive.orchestrator (CognitiveCycle)
  * Coordination facade   -> core.integration.FrameworkIntegrator
  * Planning / review     -> core.frameworks.planning / .review
  * Continuity / recovery -> core.continuity.WorkspaceContinuity

The pipeline is *advisory + record-keeping*: it creates plans, assigns owners,
tracks progress, records reviews, and writes continuity/memory exactly as the
agent is already authorized to do. It does NOT call request_level_change /
emergency_stop, does NOT flip auto_execute, and does NOT execute tasks itself.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Human-readable labels for the pipeline phase. Used by the UI and store so an
# operator can see exactly where a goal is in the workflow at a glance.
PHASES = (
    "intake",        # goal received, intent analyzed
    "planning",      # decomposed into tasks
    "assigning",     # tasks routed to agent roles
    "tracking",      # execution in flight (handled by Supervisor)
    "reviewing",     # review cycle recorded
    "updating",      # memory/continuity updated
    "done",          # whole pipeline complete
)


@dataclass
class WorkflowRecord:
    """One end-to-end goal run through the pipeline (pure data)."""

    workflow_id: str
    goal: str
    phase: str = "intake"
    intent: Optional[dict] = None
    plan_id: Optional[str] = None
    tasks: List[dict] = field(default_factory=list)
    agent_assignments: Dict[str, str] = field(default_factory=dict)
    review: Optional[dict] = None
    learned: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    decisions: List[dict] = field(default_factory=list)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "goal": self.goal,
            "phase": self.phase,
            "intent": self.intent,
            "plan_id": self.plan_id,
            "tasks": list(self.tasks),
            "agent_assignments": dict(self.agent_assignments),
            "review": self.review,
            "learned": list(self.learned),
            "blockers": list(self.blockers),
            "decisions": list(self.decisions),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def _resolve_dependencies() -> dict:
    """Lazily resolve the advisory subsystems this pipeline coordinates.

    Each import is wrapped so a missing/optional subsystem degrades gracefully
    (the pipeline still runs the steps available). Intentionally does NOT
    import the Governor for writes.
    """
    deps: dict = {}

    def safe(fn):
        try:
            return fn()
        except Exception:
            return None

    deps["router"] = safe(lambda: __import__("core.router", fromlist=["route"]).route)
    deps["intent"] = safe(lambda: __import__(
        "core.cognitive.intent", fromlist=["IntentAnalyzer"]).IntentAnalyzer())
    deps["planner"] = safe(lambda: __import__(
        "core.frameworks.planning", fromlist=["PlanningEngine"]).PlanningEngine())
    deps["review"] = safe(lambda: __import__(
        "core.frameworks.review", fromlist=["ReviewSystem"]).ReviewSystem())
    deps["continuity"] = safe(lambda: __import__(
        "core.continuity", fromlist=["default_continuity"]).default_continuity)
    deps["integrator"] = safe(lambda: __import__(
        "core.integration", fromlist=["default_integrator"]).default_integrator)
    deps["orchestrator"] = safe(lambda: __import__(
        "core.cognitive.orchestrator",
        fromlist=["CognitiveOrchestrator"]).CognitiveOrchestrator())
    deps["agent_registry"] = safe(lambda: __import__(
        "core.agent_registry", fromlist=["get_agents"]).get_agents)
    return deps


class TaskWorkflow:
    """Coordinates the advisory task pipeline across existing systems.

    Usage:
        wf = TaskWorkflow()
        rec = wf.submit("Summarize the latest meeting notes")
        rec = wf.decompose(rec)        # -> plan + tasks
        rec = wf.assign_agents(rec)    # -> router role per task
        rec = wf.review(rec, scores)   # -> review cycle
        rec = wf.update_memory(rec)    # -> continuity + learning
    """

    # Default decomposition hints when the user goal is thin. These are
    # advisory task stubs the operator/agent then refines; never executed.
    _DEFAULT_STEPS = [
        "Clarify goal and acceptance criteria",
        "Research relevant context and memory",
        "Draft implementation plan",
        "Execute the primary action",
        "Validate output against acceptance criteria",
        "Record review and update memory",
    ]

    def __init__(self, deps: Optional[dict] = None):
        self.deps = deps or _resolve_dependencies()
        self._records: Dict[str, WorkflowRecord] = {}

    # ------------------------------------------------------------------
    # Step 1: goal intake + intent
    # ------------------------------------------------------------------

    def submit(self, goal: str) -> WorkflowRecord:
        """Register a new goal and run advisory intent analysis."""
        goal = (goal or "").strip()
        if not goal:
            raise ValueError("goal must be a non-empty string")
        wid = uuid.uuid4().hex[:12]
        intent = None
        analyzer = self.deps.get("intent")
        if analyzer is not None:
            intent = analyzer.analyze(goal).to_dict()
        rec = WorkflowRecord(workflow_id=wid, goal=goal, phase="intake",
                             intent=intent)
        self._records[wid] = rec
        # Continuity: hand off to the recovery/context subsystem so an
        # interrupted run can resume. Record-keeping only.
        cont = self.deps.get("continuity")
        if cont is not None:
            try:
                cont.start_task("goal:" + goal[:80], owner="workflow",
                                kind="goal", detail=wid)
            except Exception:
                pass
        return rec

    # ------------------------------------------------------------------
    # Step 2: task decomposition
    # ------------------------------------------------------------------

    def decompose(self, record: WorkflowRecord,
                  subtasks: Optional[List[str]] = None) -> WorkflowRecord:
        """Decompose the goal into a plan + tasks (advisory, never executed).

        Milestone 3: when a goal is supplied without explicit subtasks, derive
        goal-aware decomposition steps from the existing intent analysis and
        the PlanningEngine instead of always using the static default list.
        Planning remains strictly advisory -- nothing here executes or mutates
        autonomy state.
        """
        planner = self.deps.get("planner")
        if planner is None:
            record.blockers.append("planning engine unavailable")
            return record
        plan = planner.create_plan(record.goal)
        record.plan_id = plan.plan_id
        if subtasks:
            steps = list(subtasks)
        else:
            steps = self._derive_steps(record)
        for step in steps:
            node = planner.add_task(plan.plan_id, step, owner="unassigned",
                                    detail="Advisory task for: " + record.goal)
            record.tasks.append(node.to_dict())
        record.phase = "planning"
        record.updated_at = _now()
        self._touch_continuity(record, "decomposed into %d tasks" % len(steps))
        return record

    @staticmethod
    def _derive_steps(record: WorkflowRecord) -> List[str]:
        """Goal-aware advisory step derivation (no new planner created).

        Uses the already-computed ``record.intent`` to shape the decomposition,
        falling back to the static default steps when intent is unavailable.
        """
        intent = record.intent or {}
        intent_type = (intent.get("intent_type") or "unknown").lower()
        goal = record.goal or ""
        base = [
            "Clarify goal and acceptance criteria",
            "Research relevant context and memory",
            "Draft implementation plan",
            "Execute the primary action",
            "Validate output against acceptance criteria",
            "Record review and update memory",
        ]
        # Tailor the middle of the pipeline to the classified intent.
        focused = {
            "action": "Implement the change for: " + goal[:80],
            "planning": "Design the structure for: " + goal[:80],
            "review": "Audit and analyze: " + goal[:80],
            "learning": "Explain and capture knowledge for: " + goal[:80],
            "information": "Gather and summarize: " + goal[:80],
        }.get(intent_type, "Execute the primary action for: " + goal[:80])
        steps = list(base)
        steps[3] = focused
        return steps

    # ------------------------------------------------------------------
    # Step 3: agent assignment (Router authority, consulted only)
    # ------------------------------------------------------------------

    def assign_agents(self, record: WorkflowRecord) -> WorkflowRecord:
        """Ask the Router for a role per task; never executes or mutates."""
        route = self.deps.get("router")
        agents_fn = self.deps.get("agent_registry")
        agents = agents_fn() if callable(agents_fn) else (agents_fn or {})
        assignments: Dict[str, str] = {}
        decisions: List[dict] = []
        for task in record.tasks:
            title = task.get("title", record.goal)
            role = route(title) if route is not None else "researcher"
            owner = self._best_agent_for_role(agents, role)
            assignments[task["task_id"]] = owner
            task["owner"] = owner
            task["role"] = role
            decisions.append({
                "task_id": task["task_id"],
                "title": title,
                "routed_role": role,
                "assigned_agent": owner,
                "reason": "router role hint; agent selected by capability",
            })
        record.agent_assignments = assignments
        record.decisions = decisions
        record.phase = "assigning"
        record.updated_at = _now()
        self._touch_continuity(record, "agents assigned")
        return record

    @staticmethod
    def _best_agent_for_role(agents: dict, role: str) -> str:
        """Map a router role to an available registered agent (best-effort)."""
        role_agents = {
            "coder": "Coding Agent",
            "architect": "Reasoning Agent",
            "reviewer": "Reasoning Agent",
            "tester": "Coding Agent",
            "documentation": "Reasoning Agent",
            "researcher": "Reasoning Agent",
        }
        preferred = role_agents.get(role)
        if agents and preferred and preferred in agents:
            return preferred
        # Fall back to the first ONLINE/READY agent, else unassigned.
        for name, data in (agents or {}).items():
            if str(data.get("status", "")).upper() in ("ONLINE", "READY"):
                return name
        return preferred or "unassigned"

    # ------------------------------------------------------------------
    # Step 4: execution tracking (delegated to the Supervisor)
    # ------------------------------------------------------------------

    def track_execution(self, record: WorkflowRecord,
                        supervisor_run=None) -> WorkflowRecord:
        """Hand execution to the Supervisor (execution authority).

        ``supervisor_run`` is an optional callable(task_text) -> result that the
        caller wires to ``core.supervisor.run_task``. This method performs NO
        execution itself; it only marks the phase and records outcomes.
        """
        record.phase = "tracking"
        record.updated_at = _now()
        self._touch_continuity(record, "execution delegated to Supervisor")
        if supervisor_run is None:
            return record
        results = []
        for task in record.tasks:
            try:
                result = supervisor_run(task.get("title", record.goal))
                task["status"] = "done"
                results.append({"task_id": task["task_id"],
                                "status": "done", "result": str(result)[:500]})
            except Exception as exc:  # record, but never suppress
                task["status"] = "blocked"
                record.blockers.append(
                    "task %s failed: %s" % (task.get("task_id"), str(exc)[:120]))
                results.append({"task_id": task["task_id"],
                                "status": "blocked", "error": str(exc)[:200]})
        record.decisions.append({
            "note": "execution delegated to Supervisor (execution authority)",
            "results": results,
        })
        record.updated_at = _now()
        return record

    # ------------------------------------------------------------------
    # Step 5: review cycle
    # ------------------------------------------------------------------

    def review(self, record: WorkflowRecord,
               scores: Optional[Dict[str, float]] = None) -> WorkflowRecord:
        """Record a review cycle for the goal via the Review framework."""
        review_sys = self.deps.get("review")
        if review_sys is None:
            record.blockers.append("review system unavailable")
            return record
        scores = scores or {"correctness": 0.7, "completeness": 0.7,
                           "safety": 1.0, "clarity": 0.8, "efficiency": 0.7}
        ev = review_sys.evaluate(record.goal, "task", scores,
                                 notes="Phase C review cycle")
        record.review = ev.to_dict()
        record.phase = "reviewing"
        record.updated_at = _now()
        self._touch_continuity(record, "review recorded: " + ev.verdict)
        return record

    # ------------------------------------------------------------------
    # Step 6: memory / state update
    # ------------------------------------------------------------------

    def update_memory(self, record: WorkflowRecord) -> WorkflowRecord:
        """Persist a learning pattern + continuity recovery note."""
        orchestrator = self.deps.get("orchestrator")
        if orchestrator is not None:
            try:
                verdict = (record.review or {}).get("verdict")
                lesson = "goal:%s -> %s" % (record.goal[:60],
                                            verdict or "reviewed")
                orchestrator.learn_outcome(
                    record.goal,
                    "success" if verdict == "pass" else "observed",
                    lesson=lesson)
                record.learned.append(lesson)
            except Exception:
                pass
        self._touch_continuity(record, "memory updated", complete=True)
        record.phase = "done"
        record.updated_at = _now()
        return record

    # ------------------------------------------------------------------
    # Convenience + helpers
    # ------------------------------------------------------------------

    def run(self, goal: str, subtasks: Optional[List[str]] = None,
            scores: Optional[Dict[str, float]] = None,
            supervisor_run=None) -> WorkflowRecord:
        """Run the full advisory pipeline end-to-end (no autonomous execution)."""
        rec = self.submit(goal)
        rec = self.decompose(rec, subtasks)
        rec = self.assign_agents(rec)
        rec = self.track_execution(rec, supervisor_run)
        rec = self.review(rec, scores)
        rec = self.update_memory(rec)
        return rec

    def get(self, workflow_id: str) -> Optional[WorkflowRecord]:
        return self._records.get(workflow_id)

    def list_records(self) -> List[dict]:
        return [r.to_dict() for r in self._records.values()]

    def _touch_continuity(self, record: WorkflowRecord, note: str,
                          complete: bool = False) -> None:
        cont = self.deps.get("continuity")
        if cont is None:
            return
        try:
            cont.set_recovery(
                resume_hint="Goal %s: %s (phase=%s)"
                % (record.workflow_id, note, record.phase))
            if complete:
                cont.set_context(last_goal=record.goal,
                                 last_workflow=record.workflow_id)
        except Exception:
            pass


# Convenience singleton for the UI / integration layer.
default_workflow = TaskWorkflow()