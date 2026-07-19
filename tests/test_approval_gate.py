"""Milestone 3, step 2/5: real approval gate in ProjectEngine.

Replaces the unconditional approve_request stub with a gate that:
  * reads config safety.require_approval_for_risky_actions,
  * enforces the Governor trusted-workflow scope,
  * still supports write_file,
  * does NOT enable shell/run/delete,
  * requires approval for risky actions, and
  * auto-allows non-risky trusted L2 workflows.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import core.project_engine as pe
from core.project_engine import ProjectEngine


@pytest.fixture
def engine(tmp_path, monkeypatch):
    # ProjectEngine writes to the module-level ROOT (and backup/history dirs
    # derived from it). Redirect those module globals away from the real
    # repo root so the gate tests never touch live files.
    eng = ProjectEngine()
    # ProjectEngine writes to module-level globals (ROOT/BACKUP_DIR/HISTORY_DIR).
    monkeypatch.setattr(pe, "ROOT", tmp_path)
    monkeypatch.setattr(pe, "BACKUP_DIR", tmp_path / "backups")
    monkeypatch.setattr(pe, "HISTORY_DIR", tmp_path / "history")
    tmp_path.joinpath("backups").mkdir(exist_ok=True)
    tmp_path.joinpath("history").mkdir(exist_ok=True)
    return eng


def _req(engine, action="write_file", file="out.txt"):
    return engine.create_request("supervisor", action, file, "M3 test")


def test_trusted_write_auto_approves(engine):
    req = _req(engine)
    out = engine.approve_request(req, workflow="vscode_task_send")
    assert out["approval"] == "auto_approved"
    assert out.get("approved_by", "").startswith("governor_trusted:")


def test_unknown_workflow_is_rejected(engine):
    req = _req(engine)
    out = engine.approve_request(req, workflow="not_a_real_workflow")
    assert out["approval"] == "rejected"
    assert "trusted set" in (out.get("rejection_reason") or "")


def test_risky_action_requires_approval(engine):
    req = _req(engine)
    out = engine.approve_request(req)  # no workflow tag, no approved_by
    assert out["approval"] == "rejected"
    assert "requires explicit approval" in (out.get("rejection_reason") or "")


def test_risky_action_with_approval_succeeds(engine):
    req = _req(engine)
    out = engine.approve_request(req, approved_by="human-operator")
    assert out["approval"] == "approved"
    assert out.get("approved_by") == "human-operator"


def test_blocked_request_does_not_write(engine):
    blocked = _req(engine)
    blocked["approval"] = "rejected"
    blocked["rejection_reason"] = "scope"
    op = engine.execute_operation("write_file", "out.txt",
                                  content="x=1", request=blocked)
    assert op["result"] == "blocked"
    assert not (pe.ROOT / "out.txt").exists()


def test_approved_write_succeeds_and_validates(engine):
    good = _req(engine)
    good["approval"] = "auto_approved"
    op = engine.execute_operation("write_file", "out.py",
                                  content="x = 1\n", request=good)
    assert op["result"] == "success"
    assert (pe.ROOT / "out.py").exists()


def test_unsupported_action_not_enabled(engine):
    # shell/run/delete remain unsupported (not in the gate's allowed set).
    op = engine.execute_operation("run_shell", "evil.sh", content="rm -rf /")
    assert op["result"] == "unsupported_operation"
