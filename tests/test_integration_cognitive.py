"""Integration-of-cognitive-orchestrator tests."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.integration import FrameworkIntegrator
from core.cognitive.orchestrator import CognitiveOrchestrator
from core.cognitive.planning import PlanningIntelligence
from core.cognitive.review import ReviewIntelligence
from core.cognitive.learning import LearningSystem
from core.cognitive.comms import CommunicationBus


@pytest.fixture
def integ(tmp_path):
    orch = CognitiveOrchestrator(
        planning=PlanningIntelligence(path=tmp_path / "plans.json"),
        review=ReviewIntelligence(path=tmp_path / "reviews.json"),
        learning=LearningSystem(project="o", db_path=tmp_path / "learn.db"),
        bus=CommunicationBus(),
    )
    return FrameworkIntegrator(orchestrator=orch)


def test_integrator_exposes_orchestrator(integ):
    assert integ.orchestrator is not None


def test_cognitive_cycle_via_integrator(integ):
    out = integ.cognitive_cycle("implement the router",
                                review_scores={"correctness": 0.9, "completeness": 0.8, "safety": 1.0})
    assert out["intent"]["intent_type"]
    assert out["execution_plan_id"]
    assert out["review"]["verdict"] == "pass"


def test_cognitive_cycle_none_without_orchestrator():
    integ = FrameworkIntegrator()
    assert integ.cognitive_cycle("x") is None


def test_framework_hooks_accept_orchestrator():
    from core.framework_hooks import SupervisorHooks

    class FakeSup:
        def detect_intent(self, t):
            return "information"

    orch = CognitiveOrchestrator(bus=CommunicationBus())
    hooks = SupervisorHooks(FakeSup(), orchestrator=orch)
    rec = hooks.on_task_start("write code", strategy=frozenset({"coding"}))
    assert rec["handoff"]["recommended_role"]
    assert orch.last_cycles()
