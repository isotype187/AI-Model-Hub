"""Tests for the Phase C advisory task pipeline (core.workflow)."""
import pytest

from core.workflow import TaskWorkflow, WorkflowRecord, PHASES


def test_phases_are_ordered():
    assert PHASES[0] == "intake"
    assert PHASES[-1] == "done"


def test_submit_requires_goal():
    wf = TaskWorkflow()
    with pytest.raises(ValueError):
        wf.submit("   ")


def test_submit_creates_record_with_intent():
    wf = TaskWorkflow()
    rec = wf.submit("Write a hello world script in python")
    assert isinstance(rec, WorkflowRecord)
    assert rec.phase == "intake"
    assert rec.intent is not None
    assert rec.intent["intent_type"] in {
        "action", "planning", "review", "information",
        "learning", "ambiguous", "unknown"}


def test_full_pipeline_runs_advisory():
    wf = TaskWorkflow()
    rec = wf.run("Build a small calculator")
    assert rec.phase == "done"
    assert rec.plan_id is not None
    assert len(rec.tasks) == 6  # default decomposition steps
    assert len(rec.agent_assignments) == len(rec.tasks)
    assert rec.review is not None
    assert rec.review["verdict"] in {"pass", "partial", "fail", "needs_review"}


def test_pipeline_assigns_router_roles():
    wf = TaskWorkflow()
    rec = wf.run("Review the authentication module for bugs")
    roles = {t["role"] for t in rec.tasks}
    # At least one task should have been routed to a known role.
    assert roles & {"reviewer", "coder", "architect", "researcher",
                    "tester", "documentation"}


def test_pipeline_records_review_and_learning():
    wf = TaskWorkflow()
    rec = wf.run("Document the public API")
    assert rec.review is not None
    assert any("goal:" in lesson for lesson in rec.learned)


def test_pipeline_handles_execution_failure_without_suppressing():
    wf = TaskWorkflow()

    def boom(task):
        raise RuntimeError("simulated execution failure")

    rec = wf.run("Run the risky migration", supervisor_run=boom)
    assert any("failed" in b for b in rec.blockers)
    assert any(t.get("status") == "blocked" for t in rec.tasks)


def test_provider_boundary_is_read_only():
    # The provider registry must not require live services and must not mutate.
    from core.providers import default_registry
    status = default_registry.status()
    assert "model_providers" in status
    assert "task_providers" in status
    names = {p["name"] for p in status["model_providers"]}
    assert {"ollama", "openrouter"} <= names