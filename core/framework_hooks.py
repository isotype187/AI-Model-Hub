"""Nexus98 Supervisor Framework Hooks.

Safe, *advisory* hooks that wrap the existing Supervisor lifecycle
(detect_intent -> run_task / run_action_task) with framework awareness. These
hooks DO NOT modify the Supervisor's behavior or authority: the Supervisor
remains the execution authority and the Router remains the routing authority.
The hooks only:

  * capture active workspace state around a task,
  * pull relevant memory before acting,
  * record a strategy recommendation for the task,
  * record a review/completion analysis after acting,
  * record failure-recovery context on exceptions.

All framework writes performed here are persistence/record-keeping actions the
agent is already authorized to perform (memory, continuity, workspace reality,
reviews). This module never flips ``auto_execute`` and never invokes the
Governor/Guardian for state writes. No autonomous escalation occurs.

Designed so it can be composed with the integration facade
(:mod:`core.integration`). It is safe to unit-test with a fake supervisor.
"""
from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from core.integration import FrameworkIntegrator, default_integrator


@dataclass
class HookRecord:
    """One captured lifecycle moment."""

    phase: str  # start | plan | execute | complete | recovery
    task: str
    detail: dict = field(default_factory=dict)
    ok: bool = True
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "phase": self.phase, "task": self.task,
            "detail": self.detail, "ok": self.ok, "error": self.error,
        }


class SupervisorHooks:
    """Advisory framework hooks around the Supervisor lifecycle.

    ``supervisor`` is injected (the real ``core.supervisor`` module or a fake
    in tests). The hooks call the supervisor's existing functions and record
    framework context around them.
    """

    def __init__(self, supervisor, integrator: Optional[FrameworkIntegrator] = None,
                 orchestrator=None):
        self.supervisor = supervisor
        self.integrator = integrator or default_integrator
        # Optional CognitiveOrchestrator for advisory cognitive cycles.
        self.orchestrator = orchestrator
        self._records: List[HookRecord] = []

    # ------------------------------------------------------------------
    # Individual lifecycle hooks (coordination only)
    # ------------------------------------------------------------------

    def on_task_start(self, task: str, strategy: Optional[frozenset] = None) -> dict:
        """Capture strategy guidance + workspace context at task start."""
        ctx = self.integrator.build_task_context(task, strategy)
        reality = self.integrator.refresh_workspace_context(
            last_task=task, phase="start"
        )
        rec = HookRecord("start", task, {
            "recommended_role": ctx.handoff.recommended_role,
            "safety_constrained": ctx.handoff.safety_constrained,
            "model": (ctx.model_recommendation or {}).get("recommendation"),
            "workspace": reality,
        })
        self._records.append(rec.to_dict())
        if self.orchestrator is not None:
            try:
                self.orchestrator.run_cycle(task, strategy=list(strategy) if strategy else None)
            except Exception:
                # Cognitive cycle is advisory; never break the hook.
                pass
        return ctx.to_dict()

    def on_task_plan(self, task: str) -> dict:
        """Record planning awareness (advisory; no execution)."""
        rec = HookRecord("plan", task, {"note": "planning delegated to PlanningEngine"})
        self._records.append(rec.to_dict())
        return rec.to_dict()

    def on_task_execute(self, task: str, intent: Optional[str] = None) -> dict:
        """Wrap an intent detection (Router/Supervisor remain authoritative)."""
        detected = None
        if hasattr(self.supervisor, "detect_intent"):
            detected = self.supervisor.detect_intent(task)
        rec = HookRecord("execute", task, {
            "intent": detected if intent is None else intent,
            "note": "supervisor/router remain authoritative for execution",
        })
        self._records.append(rec.to_dict())
        return rec.to_dict()

    def on_task_complete(self, task: str, subject_id: str,
                         scores: Optional[Dict[str, float]] = None,
                         notes: str = "") -> dict:
        """Record a completion analysis via the Review framework."""
        review = None
        if scores:
            review = self.integrator.analyze_completion(subject_id, scores, notes=notes)
        rec = HookRecord("complete", task, {
            "subject": subject_id,
            "verdict": (review or {}).get("verdict"),
        })
        self._records.append(rec.to_dict())
        return rec.to_dict()

    def on_failure_recovery(self, task: str, exc: BaseException) -> dict:
        """Capture failure-recovery context without suppressing the error."""
        rec = HookRecord(
            "recovery", task,
            {"traceback": traceback.format_exception_only(type(exc), exc)[-1].strip()},
            ok=False, error=str(exc)[:200],
        )
        self._records.append(rec.to_dict())
        # Also hand a recovery hint to continuity if available.
        try:
            self.integrator.coordinator.record_recovery(
                resume_hint=f"Recover from failure on task: {task}"
            )
        except Exception:
            pass
        return rec.to_dict()

    # ------------------------------------------------------------------
    # High-level orchestration helper (still advisory + safe)
    # ------------------------------------------------------------------

    def run_with_hooks(self, task: str, strategy: Optional[frozenset] = None,
                       completion_scores: Optional[Dict[str, float]] = None,
                       subject_id: Optional[str] = None) -> dict:
        """Execute the Supervisor lifecycle wrapped in framework hooks.

        The actual execution delegates to the injected supervisor's
        ``run_task``. If that raises, the failure is recorded and re-raised so
        the Supervisor's authority and error behavior are preserved.
        """
        self.on_task_start(task, strategy)
        self.on_task_plan(task)
        self.on_task_execute(task)
        try:
            if hasattr(self.supervisor, "run_task"):
                result = self.supervisor.run_task(task)
            else:
                result = {"note": "no run_task on supervisor"}
        except Exception as e:
            self.on_failure_recovery(task, e)
            raise
        self.on_task_complete(
            task, subject_id or f"task:{task}",
            scores=completion_scores,
        )
        return {"result": result, "hooks": self.records()}

    def records(self) -> List[dict]:
        return list(self._records)

    def reset(self) -> None:
        self._records.clear()
