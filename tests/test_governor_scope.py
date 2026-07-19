"""Tests for the Governor runtime scope_check helper (Milestone 3, step 1).

scope_check MUST be read-only: no state mutation, no audit events. It only
answers whether a workflow may auto-execute at the current autonomy level.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import core.autonomy.governor as governor
import core.autonomy.audit as audit


def test_trusted_workflow_allowed_at_l2():
    # Live repo is L2/trusted; vscode_task_send is the seeded trusted set.
    decision = governor.scope_check("vscode_task_send")
    assert decision["known"] is True
    assert decision["allowed"] is True
    assert decision["held"] is False
    assert decision["level"] >= 2


def test_unknown_workflow_held_not_silent():
    decision = governor.scope_check("definitely_not_a_real_workflow")
    assert decision["known"] is False
    assert decision["allowed"] is False
    # Must be explicitly held for approval -- never silently auto-executed.
    assert decision["held"] is True
    assert "hold" in decision["reason"].lower()


def test_scope_check_is_read_only_no_audit_writes():
    before = len(audit.requests())
    # Call repeatedly; should not append audit records.
    for _ in range(5):
        governor.scope_check("vscode_task_send")
        governor.scope_check("nope")
    after = len(audit.requests())
    assert after == before, "scope_check must not emit audit events"


def test_scope_check_does_not_change_autonomy_state():
    level_before = governor.current_level()
    governor.scope_check("vscode_task_send")
    level_after = governor.current_level()
    assert level_before == level_after
