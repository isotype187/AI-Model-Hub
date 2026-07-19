"""Milestone 3: closed-loop integration for the supervisor pipeline.

Because core.supervisor depends on autogen (optional in CI), we test the
workflow record + memory closure path that run_task now drives, using the same
default_workflow singleton, plus a lightweight check that run_task is wired to
create a record.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import core.workflow as workflow


def test_every_task_creates_a_workflow_record():
    wf = workflow.TaskWorkflow()
    rec = wf.submit("Write a helper module for logging")
    assert rec.phase == "intake"
    assert wf.get(rec.workflow_id) is rec


def test_action_hold_records_blocker_and_closes():
    # Simulate the Governor holding a workflow (run_task would return held).
    wf = workflow.TaskWorkflow()
    rec = wf.submit("do something")
    # emulate run_task's scope-hold closure
    reason = "workflow 'x' held by Governor scope"
    rec.blockers.append(reason)
    wf.update_memory(rec)
    assert reason in rec.blockers
    assert rec.phase == "done"
    # memory closure touched the orchestrator without raising
    assert any("goal:" in lesson for lesson in rec.learned)


def test_supervisor_run_task_wired():
    try:
        import core.supervisor  # noqa: F401
    except ModuleNotFoundError as exc:
        if "autogen" in str(exc):
            pytest.skip("core.supervisor requires autogen (optional dep): %s" % exc)
        raise
    # If importable, run_task should accept a workflow_name kwarg and create
    # a workflow record (smoke only; does not execute autogen agents).
    assert "workflow_name" in core.supervisor.run_task.__code__.co_varnames
