"""Project Intelligence framework tests (temp storage)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.frameworks.project import ProjectIntelligence, ChangePlan


@pytest.fixture
def intel(tmp_path):
    from core.frameworks.workspace import WorkspaceReality
    r = WorkspaceReality(tmp_path / "workspace.json")
    pi = ProjectIntelligence(reality=r)
    yield pi
    pi.close()


def test_understand_project(intel):
    pid = intel.reality.register_project("Core")
    rec = intel.understand_project(pid, summary="core systems", state="stable", health="good")
    assert rec["state"] == "stable"
    assert intel.project_state(pid)["health"] == "good"


def test_dependency_awareness(intel):
    a = intel.reality.register_project("A")
    b = intel.reality.register_project("B")
    intel.record_dependency(a, b, relation="depends_on")
    deps = intel.dependencies_of(a)
    assert deps and deps[0]["depends_on"] == b


def test_change_planning_separate_from_execution(intel):
    plan = intel.plan_change("Refactor router", "core/router.py", "cleaner routing", steps=["a", "b"])
    assert isinstance(plan, ChangePlan)
    assert plan.status == "planned"
    intel.update_change_status(plan.change_id, "approved")
    plans = intel.list_change_plans(status="approved")
    assert plans and plans[0]["change_id"] == plan.change_id


def test_checkpoint_and_progress_tracking(intel):
    pid = intel.reality.register_project("Core")
    intel.note_checkpoint(pid, "backups/ck1", "stable before refactor")
    rec = intel.track_progress(pid, "router refactor", done=True)
    rec2 = intel.track_progress(pid, "memory refactor", done=False)
    assert rec["progress_pct"] == 50.0
    assert rec["last_checkpoint"] == "backups/ck1"


def test_summary(intel):
    pid = intel.reality.register_project("Core")
    intel.understand_project(pid, summary="core systems")
    intel.plan_change("x", "f", "r")
    intel.record_dependency(pid, "other")
    s = intel.summary()
    assert s["projects_understood"] == 1
    assert s["change_plans"] == 1
    assert s["dependencies"] == 1


