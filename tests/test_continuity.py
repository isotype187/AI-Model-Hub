"""Workspace Continuity Foundation tests (isolated; temp file)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.continuity import WorkspaceContinuity, save_state, load_state


@pytest.fixture
def wc(tmp_path):
    store = WorkspaceContinuity(tmp_path / "continuity.json")
    yield store
    store.close()


def test_start_and_track_active_task(wc):
    tid = wc.start_task("Build strategy engine", owner="agent")
    assert wc.active_tasks()
    assert wc.get_task(tid)["status"] == "in_progress"


def test_complete_task_removes_from_active(wc):
    tid = wc.start_task("Task A")
    wc.complete_task(tid, outcome="completed")
    assert wc.active_tasks() == []


def test_persists_across_reload(tmp_path):
    p = tmp_path / "continuity.json"
    wc = WorkspaceContinuity(p)
    wc.start_task("Persisted task", detail="implement X")
    wc.set_recovery(checkpoint="backups/ck", resume_hint="keep going")
    wc.close()
    wc2 = WorkspaceContinuity(p)
    assert wc2.active_tasks()
    assert wc2.get_recovery()["resume_hint"] == "keep going"
    wc2.close()


def test_workspace_state_and_context(wc):
    wc.set_workspace_state(phase="implementation", files=["core/x.py"])
    wc.set_context(goal="autonomous workstation")
    assert wc.get_workspace_state()["phase"] == "implementation"
    assert wc.get_context()["goal"] == "autonomous workstation"


def test_snapshot_shape(wc):
    wc.start_task("Snapshot task")
    snap = wc.snapshot()
    assert set(snap) >= {
        "updated_at", "active_tasks", "workspace_state",
        "recovery", "context",
    }


def test_corrupt_store_recovers(tmp_path):
    p = tmp_path / "continuity.json"
    p.write_text("{ not valid json", encoding="utf-8")
    wc = WorkspaceContinuity(p)  # must not raise
    assert wc.active_tasks() == []
    wc.close()


def test_legacy_resume_api(tmp_path, monkeypatch):
    # Redirect the legacy path to a temp file.
    import core.continuity as cmod
    monkeypatch.setattr(cmod, "LEGACY_PATH", tmp_path / "resume.json")
    monkeypatch.setattr(cmod, "_legacy_store", cmod.WorkspaceContinuity(tmp_path / "resume.json"))
    save_state("qwen3", 0.5)
    assert load_state().get("qwen3") == 0.5
