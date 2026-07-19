"""Goal Management Framework tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.cognitive.goals import GoalManager, Goal


@pytest.fixture
def gm(tmp_path):
    m = GoalManager(tmp_path / "goals.json")
    yield m
    m.close()


def test_add_and_get_goal(gm):
    g = gm.add_goal("Build platform", priority=5)
    assert gm.get(g.goal_id).title == "Build platform"


def test_subgoals_and_parent_filter(gm):
    parent = gm.add_goal("Platform")
    child = gm.add_goal("Subsystem", parent_id=parent.goal_id)
    subs = gm.list_goals(parent_id=parent.goal_id)
    assert subs and subs[0].goal_id == child.goal_id


def test_dependencies_and_milestones(gm):
    a = gm.add_goal("A")
    b = gm.add_goal("B", depends_on=[a.goal_id])
    gm.add_milestone(b.goal_id, "first cut")
    assert a.goal_id in gm.get(b.goal_id).depends_on
    assert "first cut" in gm.get(b.goal_id).milestones


def test_progress_tracking(gm):
    g = gm.add_goal("G")
    gm.set_progress(g.goal_id, 42.5)
    assert gm.get(g.goal_id).progress_pct == 42.5


def test_active_goals_priority_order(gm):
    low = gm.add_goal("Low", priority=1)
    high = gm.add_goal("High", priority=5)
    active = gm.active_goals()
    assert active[0].priority >= active[-1].priority


def test_interruption_resume_context(gm):
    gm.add_goal("Persisted", priority=4)
    ctx = gm.resume_context()
    assert ctx["active_count"] == 1
    assert ctx["active_goals"][0]["title"] == "Persisted"


def test_persists_across_reload(tmp_path):
    p = tmp_path / "goals.json"
    m = GoalManager(p)
    g = m.add_goal("Reloaded")
    m.close()
    m2 = GoalManager(p)
    assert m2.get(g.goal_id).title == "Reloaded"
    m2.close()
