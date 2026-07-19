"""Phase 1: Framework Integration Facade tests."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.integration import FrameworkIntegrator, TaskContext
from core.frameworks.model import ModelIntelligence
from core.frameworks.workspace import WorkspaceReality
from core.frameworks.review import ReviewSystem
from core.frameworks.planning import PlanningEngine


@pytest.fixture
def integrator(tmp_path):
    tmp = tmp_path
    mi = ModelIntelligence()
    wr = WorkspaceReality(tmp / "workspace.json")
    rv = ReviewSystem(tmp / "reviews.json")
    pl = PlanningEngine(tmp / "plans.json")
    integ = FrameworkIntegrator(models=mi, reality=wr, review=rv, planning=pl)
    yield integ
    wr.close()
    rv.close()
    pl.close()


def test_strategy_guidance_advisory(integrator):
    ho = integrator.strategy_guidance("write code", strategy=frozenset({"coding"}))
    assert ho.recommended_role in {"coder", "researcher"}
    assert not hasattr(integrator, "set_auto_execute")  # no autonomy ownership


def test_model_recommendation_advisory(integrator):
    rec = integrator.model_recommendation("write a python script")
    assert rec and rec["recommendation"]


def test_workspace_context_refresh(integrator):
    snap = integrator.refresh_workspace_context(phase="test")
    assert snap["system_state_keys"] == ["phase"]
    assert integrator.reality.get_state("phase") == "test"


def test_review_completion_analysis(integrator):
    ev = integrator.analyze_completion("task-1", {"correctness": 0.9, "safety": 1.0})
    assert ev["verdict"] == "pass"


def test_build_task_context_assembles_all(integrator):
    ctx = integrator.build_task_context(
        "write a python script", strategy=frozenset({"coding"}), autonomous=True
    )
    assert isinstance(ctx, TaskContext)
    assert ctx.handoff.safety_constrained is True
    assert ctx.model_recommendation
    assert ctx.workspace_reality is not None


def test_plan_handoff_advisory(integrator):
    plan = integrator.planning.create_plan("Demo", milestones=["m1"])
    node = integrator.planning.add_task(plan.plan_id, "sub")
    ph = integrator.plan_handoff(plan.plan_id, node.task_id)
    assert ph["plan_id"] == plan.plan_id
    assert ph["task"]["task_id"] == node.task_id


def test_capability_report(integrator):
    rep = integrator.capability_report()
    assert "tools" in rep
    assert "models" in rep
    assert "strategy_catalog" in rep


def test_facade_does_not_own_autonomy(integrator):
    # The integration layer must never expose autonomy mutators.
    for forbidden in ("set_auto_execute", "request_level_change", "emergency_stop"):
        assert not hasattr(integrator, forbidden)
