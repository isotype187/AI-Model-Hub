"""Integration: boot_report + orchestrator end-to-end via integrator."""
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


def test_boot_report_read_only(integ):
    report = integ.boot_report(startup_objective="boot", run_cognitive_cycle=True)
    assert report is not None
    assert "capabilities" in report
    assert "validation" in report
    assert "context" in report
    assert report["cognitive_cycle"] is not None


def test_full_cycle_via_integrator_runs_all_stages(integ):
    out = integ.cognitive_cycle("implement the router",
                                review_scores={"correctness": 0.9, "completeness": 0.8, "safety": 1.0})
    stages = [t["stage"] for t in out["trace"]]
    assert stages[0] == "intent"
    assert out["execution_plan_id"]
    assert out["review"]["verdict"] == "pass"
