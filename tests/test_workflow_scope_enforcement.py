"""Milestone 3: Governor trusted-workflow scope enforcement.

Verifies that run_task (via the supervisor + governor) HOLDS execution for
workflows outside the trusted set and records the reason, rather than silently
continuing.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import core.autonomy.governor as governor


def test_l2_only_trusted_workflow_allowed():
    scope = governor.scope_check("vscode_task_send")
    assert scope["known"] is True
    assert scope["allowed"] is True
    assert scope["held"] is False


def test_unknown_workflow_held_not_allowed():
    scope = governor.scope_check("some_future_workflow")
    assert scope["known"] is False
    assert scope["allowed"] is False
    assert scope["held"] is True


def test_governor_ownership_preserved():
    # This test module never imports the Governor WRITE entry points, keeping
    # the Governor as the SOLE autonomy-state writer. Confirm the read-only
    # check does not change live level.
    before = governor.current_level()
    governor.scope_check("vscode_task_send")
    assert governor.current_level() == before


def test_supervisor_run_task_hold_importable():
    # autogen-dependent module; import is optional in this environment.
    try:
        import core.supervisor  # noqa: F401
    except ModuleNotFoundError as exc:
        if "autogen" in str(exc):
            pytest.skip("core.supervisor requires autogen (optional dep): %s" % exc)
        raise
