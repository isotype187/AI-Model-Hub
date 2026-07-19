"""Cognitive Orchestrator tests (advisory composition of frameworks)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.cognitive.orchestrator import CognitiveOrchestrator
from core.cognitive.planning import PlanningIntelligence
from core.cognitive.review import ReviewIntelligence
from core.cognitive.learning import LearningSystem
from core.cognitive.comms import CommunicationBus


@pytest.fixture
def orch(tmp_path):
    o = CognitiveOrchestrator(
        planning=PlanningIntelligence(path=tmp_path / "plans.json"),
        review=ReviewIntelligence(path=tmp_path / "reviews.json"),
        learning=LearningSystem(project="o", db_path=tmp_path / "learn.db"),
        bus=CommunicationBus(),
    )
    yield o
    o.close()


def test_run_cycle_produces_full_trace(orch):
    cycle = orch.run_cycle("write a python script",
                          steps=[{"title": "implement"}, {"title": "test"}])
    d = cycle.to_dict()
    assert d["intent"]["intent_type"]
    assert d["plan_id"]
    assert d["decision"]["recommended"]
    assert d["execution_plan_id"]
    assert d["trace"][0]["stage"] == "intent"


def test_cycle_with_review_and_learning(orch):
    cycle = orch.run_cycle(
        "implement feature",
        review_scores={"correctness": 0.9, "completeness": 0.8, "safety": 1.0},
    )
    d = cycle.to_dict()
    assert d["review"]["verdict"] == "pass"
    assert "review:pass" in d["learned"]


def test_cycle_publishes_on_bus(orch):
    got = []
    orch.bus.subscribe("strategy", lambda m: got.append(m.event))
    orch.run_cycle("do something")
    assert "cycle_start" in got
    assert "cycle_complete" in got


def test_learn_outcome_passive(orch):
    orch.learn_outcome("task-x", "success", lesson="prefer local models")
    assert orch.learning.successful_patterns()


def test_orchestrator_does_not_execute(orch):
    # No execution surface anywhere in the cycle.
    assert not hasattr(orch, "execute")
    cycle = orch.run_cycle("x")
    # The execution plan is prepared, not run.
    assert cycle.execution_plan_id


def test_last_cycles_recorded(orch):
    orch.run_cycle("a")
    orch.run_cycle("b")
    assert len(orch.last_cycles()) == 2
