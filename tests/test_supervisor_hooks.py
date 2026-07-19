"""Phase 2: Supervisor Framework Hooks tests (fake supervisor, no real exec)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.framework_hooks import SupervisorHooks, HookRecord


class FakeSupervisor:
    """Minimal supervisor double for hook testing (no real execution)."""

    def detect_intent(self, task):
        return "information"

    def run_task(self, task):
        return {"result": "ok", "task": task}


@pytest.fixture
def hooks():
    from core.integration import FrameworkIntegrator
    return SupervisorHooks(FakeSupervisor(), FrameworkIntegrator())


def test_on_task_start_captures_context(hooks):
    hooks.on_task_start("write code", strategy=frozenset({"coding"}))
    rec = hooks.records()[-1]
    assert rec["phase"] == "start"
    assert "recommended_role" in rec["detail"]


def test_on_task_execute_uses_supervisor_intent(hooks):
    rec = hooks.on_task_execute("do something")
    assert rec["detail"]["intent"] == "information"


def test_full_lifecycle_records_phases(hooks):
    out = hooks.run_with_hooks("write a python script",
                               completion_scores={"correctness": 0.9})
    phases = [r["phase"] for r in out["hooks"]]
    assert phases == ["start", "plan", "execute", "complete"]


def test_failure_recovery_records_error(hooks):
    class Boom:
        def run_task(self, task):
            raise RuntimeError("kaboom")

    h2 = SupervisorHooks(Boom(), hooks.integrator)
    with pytest.raises(RuntimeError):
        h2.run_with_hooks("boom task")
    recs = h2.records()
    assert recs[-1]["phase"] == "recovery"
    assert recs[-1]["ok"] is False


def test_supervisor_remains_authoritative(hooks):
    # Hooks must not replace or shadow run_task behavior.
    out = hooks.run_with_hooks("anything")
    assert out["result"] == {"result": "ok", "task": "anything"}


def test_hooks_do_not_own_autonomy(hooks):
    for forbidden in ("set_auto_execute", "request_level_change"):
        assert not hasattr(hooks, forbidden)

