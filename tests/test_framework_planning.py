"""Planning framework tests (temp storage)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.frameworks.planning import PlanningEngine, TaskNode, Plan


@pytest.fixture
def pe(tmp_path):
    eng = PlanningEngine(tmp_path / "plans.json")
    yield eng
    eng.close()


def test_create_plan(pe):
    plan = pe.create_plan("Build framework ecosystem", milestones=["F1", "F2"])
    assert plan.goal == "Build framework ecosystem"
    assert pe.get_plan(plan.plan_id)


def test_decompose_and_dependencies(pe):
    plan = pe.create_plan("Refactor router")
    parent = pe.decompose(plan.plan_id, "Refactor", ["extract rules", "add tests"])
    children = [t for t in plan.tasks.values() if t.parent_id == parent]
    assert len(children) == 2
    # add a dependent task
    dep = pe.add_task(plan.plan_id, "document", depends_on=[parent])
    assert dep.depends_on == [parent]


def test_ready_tasks_respects_dependencies(pe):
    plan = pe.create_plan("P")
    root = pe.add_task(plan.plan_id, "root")
    child = pe.add_task(plan.plan_id, "child", depends_on=[root.task_id])
    # nothing done yet -> only root is ready
    assert {t.title for t in pe.ready_tasks(plan.plan_id)} == {"root"}
    pe.update_task_status(plan.plan_id, root.task_id, "done")
    assert {t.title for t in pe.ready_tasks(plan.plan_id)} == {"child"}


def test_progress_tracking(pe):
    plan = pe.create_plan("P")
    pe.add_task(plan.plan_id, "a")
    pe.add_task(plan.plan_id, "b")
    pe.update_task_status(plan.plan_id, list(plan.tasks)[0], "done")
    prog = pe.progress(plan.plan_id)
    assert prog["pct"] == 50.0


def test_planning_never_executes(pe):
    # Sanity: PlanningEngine exposes no execution surface.
    assert not hasattr(pe, "execute") and not hasattr(pe, "run_task")


def test_persists_across_reload(tmp_path):
    p = tmp_path / "plans.json"
    eng = PlanningEngine(p)
    plan = eng.create_plan("Persisted plan")
    eng.close()
    eng2 = PlanningEngine(p)
    assert eng2.get_plan(plan.plan_id).goal == "Persisted plan"
    eng2.close()
