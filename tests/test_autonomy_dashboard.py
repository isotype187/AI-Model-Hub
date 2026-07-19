"""Phase 8 - Autonomy Observability Dashboard tests (READ-ONLY surface).

These tests exercise ui/autonomy_dashboard.py ONLY. They:
  - verify snapshot() returns exactly the 8 approved fields,
  - verify each read helper's type/value against controlled inputs,
  - verify missing/empty history + checkpoint conditions fail safe,
  - assert the dashboard performs NO writes / NO autonomy mutation.

No production code is modified. The Governor, supervisor.py, system_config.json
and autonomy levels are never written by these tests. External read sources
(audit log, checkpoints dir, path constants) are redirected to tmp/mocks via
monkeypatch so the real repo state is untouched.
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import ui.autonomy_dashboard as dash

APPROVED_FIELDS = {
    "current_level",
    "active_workflows",
    "pending_requests",
    "approval_history",
    "audit_events",
    "last_checkpoint",
    "rollback_available",
    "emergency_stop_status",
}


# ---------------------------------------------------------------------------
# Fixtures: isolate every external read source. No production writes anywhere.
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_supervisor(tmp_path, monkeypatch):
    """Redirect the dashboard's read-only file references to temp copies."""
    sup = tmp_path / "supervisor.py"
    cfg = tmp_path / "system_config.json"
    sup.write_text("auto_execute = False\n", encoding="utf-8")
    cfg.write_text(
        '{"autonomy_level": "controlled", "safety": '
        '{"require_snapshots": true, "require_validation": true, '
        '"require_approval_for_risky_actions": true}}',
        encoding="utf-8",
    )
    monkeypatch.setattr(dash, "SUPERVISOR_PATH", str(sup))
    monkeypatch.setattr(dash, "CONFIG_PATH", str(cfg))
    return {"sup": sup, "cfg": cfg}


@pytest.fixture
def fake_events(monkeypatch):
    """Deterministic audit trail with one approved-unapplied, one applied,
    one rejected request, plus an emergency_stop."""
    events = [
        {"ts": "t1", "event": "request_level_change", "request_id": "r1",
         "decision": "approved", "target_level": 2},
        {"ts": "t2", "event": "apply_level_change", "request_id": "r1",
         "to_level": 2},
        {"ts": "t3", "event": "request_level_change", "request_id": "r2",
         "decision": "rejected", "target_level": 3},
        {"ts": "t4", "event": "request_level_change", "request_id": "r3",
         "decision": "approved", "target_level": 3},  # approved, not applied
        {"ts": "t5", "event": "emergency_stop", "approver": "system",
         "consistent": True},
    ]
    monkeypatch.setattr(dash._audit, "requests", lambda: list(events))
    return events


@pytest.fixture
def fake_level(monkeypatch):
    """Pin the Governor's reported level (read-only) to L2."""
    monkeypatch.setattr(dash._governor, "current_level", lambda: 2)
    return 2


@pytest.fixture
def fake_checkpoints(tmp_path, monkeypatch):
    """Create two checkpoint dirs; the newer one must win."""
    cp_root = tmp_path / "checkpoints"
    cp_root.mkdir()
    older = cp_root / "NEXUS98_OLD"
    newer = cp_root / "NEXUS98_NEW"
    older.mkdir()
    newer.mkdir()
    os.utime(older, (1000, 1000))
    os.utime(newer, (2000, 2000))
    monkeypatch.setattr(dash, "CHECKPOINTS_DIR", str(cp_root))
    return {"root": cp_root, "newer": "NEXUS98_NEW"}


# ---------------------------------------------------------------------------
# 1. snapshot() shape
# ---------------------------------------------------------------------------

def test_snapshot_returns_exactly_eight_fields(
    fake_supervisor, fake_events, fake_level, fake_checkpoints
):
    snap = dash.snapshot()
    assert isinstance(snap, dict)
    assert set(snap.keys()) == APPROVED_FIELDS
    assert len(snap) == 8


def test_snapshot_field_container_types(
    fake_supervisor, fake_events, fake_level, fake_checkpoints
):
    snap = dash.snapshot()
    assert isinstance(snap["current_level"], dict)
    assert isinstance(snap["active_workflows"], list)
    assert isinstance(snap["pending_requests"], list)
    assert isinstance(snap["approval_history"], list)
    assert isinstance(snap["audit_events"], list)
    assert isinstance(snap["last_checkpoint"], dict)
    assert isinstance(snap["rollback_available"], bool)
    assert isinstance(snap["emergency_stop_status"], dict)


# ---------------------------------------------------------------------------
# 2. per-helper type/value
# ---------------------------------------------------------------------------

def test_current_autonomy_level(fake_supervisor, fake_level):
    out = dash.current_autonomy_level()
    assert out["level"] == 2
    assert out["name"] == dash._levels.level_name(2)
    assert out["auto_execute"] is False           # supervisor stub says False
    assert out["config_intent"] == "controlled"


def test_active_workflows_matches_levels(fake_level):
    out = dash.active_workflows()
    assert out == sorted(dash._levels.allowed_workflows(2))
    assert out == ["vscode_task_send"]


def test_pending_requests_excludes_applied_and_rejected(fake_events):
    pending = dash.pending_requests()
    ids = [e["request_id"] for e in pending]
    assert ids == ["r3"]                            # r1 applied, r2 rejected


def test_approval_history_includes_approved_and_rejected(fake_events):
    hist = dash.approval_history()
    ids = sorted(e["request_id"] for e in hist)
    assert ids == ["r1", "r2", "r3"]


def test_audit_events_newest_first_and_limited(fake_events):
    events = dash.audit_events(limit=3)
    assert len(events) == 3
    assert events[0]["ts"] == "t5"                  # newest first
    assert events[-1]["ts"] == "t3"


def test_last_checkpoint_picks_newest(fake_checkpoints):
    cp = dash.last_checkpoint()
    assert cp["name"] == fake_checkpoints["newer"]
    assert "mtime" in cp


def test_rollback_available_true_when_checkpoint_and_files(
    fake_checkpoints, fake_supervisor
):
    assert dash.rollback_available() is True


def test_emergency_stop_status_reports_last_event(fake_events, fake_supervisor):
    st = dash.emergency_stop_status()
    assert st["last_event"]["event"] == "emergency_stop"
    assert st["auto_execute_on"] is False
    assert st["level_zero_consistent"] in (True, False)


# ---------------------------------------------------------------------------
# 3. missing/empty conditions fail safe
# ---------------------------------------------------------------------------

def test_empty_audit_history_is_safe(monkeypatch):
    monkeypatch.setattr(dash._audit, "requests", lambda: [])
    assert dash.pending_requests() == []
    assert dash.approval_history() == []
    assert dash.audit_events() == []
    st = dash.emergency_stop_status()
    assert st["last_event"] is None
    assert st["engaged"] is False


def test_missing_checkpoint_dir_is_safe(tmp_path, monkeypatch):
    missing = tmp_path / "does_not_exist"
    monkeypatch.setattr(dash, "CHECKPOINTS_DIR", str(missing))
    assert dash.last_checkpoint() is None


def test_empty_checkpoint_dir_is_safe(tmp_path, monkeypatch):
    empty = tmp_path / "checkpoints_empty"
    empty.mkdir()
    monkeypatch.setattr(dash, "CHECKPOINTS_DIR", str(empty))
    assert dash.last_checkpoint() is None


def test_rollback_unavailable_without_checkpoint(tmp_path, monkeypatch):
    missing = tmp_path / "no_cp"
    monkeypatch.setattr(dash, "CHECKPOINTS_DIR", str(missing))
    assert dash.rollback_available() is False


def test_snapshot_safe_with_no_history_or_checkpoint(
    fake_supervisor, fake_level, tmp_path, monkeypatch
):
    monkeypatch.setattr(dash._audit, "requests", lambda: [])
    monkeypatch.setattr(dash, "CHECKPOINTS_DIR", str(tmp_path / "none"))
    snap = dash.snapshot()
    assert set(snap.keys()) == APPROVED_FIELDS
    assert snap["pending_requests"] == []
    assert snap["approval_history"] == []
    assert snap["audit_events"] == []
    assert snap["last_checkpoint"] is None
    assert snap["rollback_available"] is False


# ---------------------------------------------------------------------------
# 4. dashboard remains read-only (behavioral + static)
# ---------------------------------------------------------------------------

def test_snapshot_does_not_mutate_backing_files(
    fake_supervisor, fake_events, fake_level, fake_checkpoints
):
    sup_before = fake_supervisor["sup"].read_bytes()
    cfg_before = fake_supervisor["cfg"].read_bytes()
    dash.snapshot()
    assert fake_supervisor["sup"].read_bytes() == sup_before
    assert fake_supervisor["cfg"].read_bytes() == cfg_before


def test_snapshot_never_calls_governor_mutators(
    fake_supervisor, fake_events, fake_level, fake_checkpoints, monkeypatch
):
    called = []
    monkeypatch.setattr(
        dash._governor, "request_level_change",
        lambda *a, **k: called.append("request_level_change"),
    )
    monkeypatch.setattr(
        dash._governor, "emergency_stop",
        lambda *a, **k: called.append("emergency_stop"),
    )
    dash.snapshot()
    assert called == []


def test_module_source_has_no_mutation_paths():
    src = Path(dash.__file__).read_text(encoding="utf-8-sig")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "open":
            mode = "r"
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                mode = node.args[1].value
            for kw in node.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = kw.value.value
            assert not any(c in str(mode) for c in ("w", "a", "x", "+")), mode
    for banned in ("request_level_change(", "emergency_stop(",
                   "_set_auto_execute(", "_set_config_intent(", "_write_text("):
        assert banned not in src
    import re as _re
    assert _re.search(r"auto_execute\s*=\s*(True|False)", src) is None
    assert ".write(" not in src
    assert "json.dump" not in src
