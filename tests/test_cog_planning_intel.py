"""Planning Intelligence Framework tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.cognitive.planning import PlanningIntelligence, PlanAnalysis, ExecutionEdge


@pytest.fixture
def pi(tmp_path):
    eng = PlanningIntelligence(path=tmp_path / "plans.json")
    yield eng
    eng.close()


def test_decompose_and_graphs(pi):
    plan = pi.create_plan("Build feature")
    root = pi.decompose(plan.plan_id, "Implement", ["write code", "write tests"])
    ship = pi.engine.add_task(plan.plan_id, "ship", depends_on=[root])
    edges = pi.execution_graph(plan.plan_id)
    assert any(e.kind == "sequence" for e in edges)
    assert any(e.kind == "dependency" for e in edges)
    dg = pi.dependency_graph(plan.plan_id)
    assert ship.task_id in dg and root in dg[ship.task_id]


def test_alternative_and_checkpoint_and_rollback(pi):
    plan = pi.create_plan("P")
    root = pi.decompose(plan.plan_id, "Do it", ["step a"])
    alt = pi.add_alternative(plan.plan_id, "Do it differently", ["step alt"])
    pi.mark_checkpoint(plan.plan_id, root)
    rb = pi.add_rollback_plan(plan.plan_id, root, ["revert x"])
    analysis = pi.estimate(plan.plan_id, hours_per_task=2.0)
    assert analysis.alternatives >= 1
    assert analysis.checkpoints == 1
    assert analysis.rollback_points >= 1
    assert analysis.estimated_effort_hours > 0


def test_critical_path(pi):
    plan = pi.create_plan("P")
    a = pi.engine.add_task(plan.plan_id, "a")
    b = pi.engine.add_task(plan.plan_id, "b", depends_on=[a.task_id])
    c = pi.engine.add_task(plan.plan_id, "c", depends_on=[b.task_id])
    analysis = pi.estimate(plan.plan_id)
    assert analysis.critical_path[-1] == c.task_id


def test_planning_is_advisory_only(pi):
    assert not hasattr(pi, "execute") and not hasattr(pi, "run")

