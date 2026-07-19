"""Execution Intelligence Framework tests (prepares, never executes)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.cognitive.execution import ExecutionIntelligence, RetryPolicy, ExecutionPlan


@pytest.fixture
def ei():
    return ExecutionIntelligence()


def test_prepare_plan(ei):
    plan = ei.prepare("build", [
        {"title": "a"}, {"title": "b", "depends_on": []}, {"title": "c", "depends_on": ["x"]},
    ])
    assert isinstance(plan, ExecutionPlan)
    assert len(plan.steps) == 3


def test_topological_sequence(ei):
    plan = ei.prepare("p", [
        {"title": "a"}, {"title": "b", "depends_on": ["a_id_placeholder"]},
    ])
    # depends_on placeholder not a real step -> still produces a complete order
    assert len(plan.sequence) == len(plan.steps)


def test_batching(ei):
    plan = ei.prepare("p", [
        {"title": "a", "batch": "io"}, {"title": "b", "batch": "io"},
        {"title": "c", "batch": "cpu"},
    ])
    batches = ei.batch_steps(plan.plan_id)
    assert len(batches["io"]) == 2
    assert len(batches["cpu"]) == 1


def test_ready_steps(ei):
    # Build plan, then wire b's real dependency on a.
    plan = ei.prepare("p", [{"title": "a"}, {"title": "b"}])
    a_id = [s for s in plan.steps.values() if s.title == "a"][0].step_id
    b_id = [s for s in plan.steps.values() if s.title == "b"][0].step_id
    plan.steps[b_id].depends_on = [a_id]
    # Before a completes, b is not ready; after a completes, b is ready.
    assert b_id not in ei.ready_steps(plan.plan_id, completed=[])
    assert b_id in ei.ready_steps(plan.plan_id, completed=[a_id])


def test_stopping_conditions(ei):
    plan = ei.prepare("p", [{"title": "a"}], stopping_conditions=["all_done"])
    assert ei.should_stop(plan.plan_id, conditions_met=["all_done"]) is True
    assert ei.should_stop(plan.plan_id, completed=[list(plan.steps)[0]]) is True


def test_retry_policy_stored(ei):
    plan = ei.prepare("p", [{"title": "a", "retry": {"max_attempts": 3, "backoff_seconds": 2.0}}])
    step = list(plan.steps.values())[0]
    assert step.retry.max_attempts == 3


def test_execution_does_not_execute(ei):
    # The framework prepares only; no execution surface.
    assert not hasattr(ei, "execute") and not hasattr(ei, "run_steps")


