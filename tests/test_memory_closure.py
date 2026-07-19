"""Milestone 3, step 4: memory closure via CognitiveOrchestrator.

Successful and failed executions must update memory through the existing
learn_outcome / record_pattern functions. No new memory architecture is added.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.cognitive.orchestrator import CognitiveOrchestrator
import core.workflow as workflow


def test_learn_outcome_success_records_pattern():
    orch = CognitiveOrchestrator()
    orch.learn_outcome("build a calculator", "success", lesson="goal captured")
    assert any("goal captured" in (r.summary or "") for r in orch.learning._index.values())
    orch.close()


def test_learn_outcome_failure_records_pattern():
    orch = CognitiveOrchestrator()
    orch.learn_outcome("risky migration", "failure", lesson="goal failed")
    assert any("goal failed" in (r.summary or "") for r in orch.learning._index.values())
    orch.close()


def test_workflow_update_memory_calls_orchestrator():
    wf = workflow.TaskWorkflow()
    rec = wf.submit("Document the public API")
    # Drive the same closure run_task uses for both success and failure.
    wf.update_memory(rec)
    assert rec.phase == "done"
    # The orchestrator learned something about this goal.
    assert any("goal:" in l for l in rec.learned)
