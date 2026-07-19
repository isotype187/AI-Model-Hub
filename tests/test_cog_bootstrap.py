"""Cognitive Bootstrap tests (read-only startup activation)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.cognitive.bootstrap import CognitiveBootstrap, BootReport
from core.capability_awareness import CapabilityDiscoverer
from core.frameworks.validation import FrameworkValidator
from core.cognitive.context import ContextAssembler
from core.cognitive.orchestrator import CognitiveOrchestrator
from core.cognitive.planning import PlanningIntelligence
from core.cognitive.review import ReviewIntelligence
from core.cognitive.learning import LearningSystem
from core.cognitive.comms import CommunicationBus


@pytest.fixture
def boot(tmp_path):
    disc = CapabilityDiscoverer()
    val = FrameworkValidator(root=tmp_path)
    ctx = ContextAssembler()
    orch = CognitiveOrchestrator(
        planning=PlanningIntelligence(path=tmp_path / "plans.json"),
        review=ReviewIntelligence(path=tmp_path / "reviews.json"),
        learning=LearningSystem(project="o", db_path=tmp_path / "learn.db"),
        bus=CommunicationBus(),
    )
    return CognitiveBootstrap(discoverer=disc, validator=val, context=ctx, orchestrator=orch)


def test_activate_read_only(boot):
    r = boot.activate(startup_objective="boot test", run_cognitive_cycle=True)
    assert isinstance(r, BootReport)
    assert "tools" in r.capabilities
    assert "total" in r.validation
    assert r.context["objective"] == "boot test"
    assert r.cognitive_cycle is not None


def test_activate_without_cycle(boot):
    boot.orchestrator = None
    r = boot.activate()
    assert r.cognitive_cycle is None


def test_summary_line(boot):
    r = boot.activate()
    line = r.summary_line()
    assert "Cognitive boot" in line


def test_bootstrap_does_not_fail_on_validation_issues(boot):
    # Validation may report issues; bootstrap must still return a report.
    r = boot.activate()
    assert isinstance(r.validation, dict)
    assert "healthy" in r.validation
