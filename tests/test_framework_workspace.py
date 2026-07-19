"""WWW / Workspace Reality Continuity framework tests (temp storage)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.frameworks.workspace import WorkspaceReality, ComponentRef


@pytest.fixture
def reality(tmp_path):
    store = WorkspaceReality(tmp_path / "workspace.json")
    yield store
    store.close()


def test_register_and_get_project(reality):
    pid = reality.register_project("Nexus98 Core", description="core systems", owner="agent")
    proj = reality.get_project(pid)
    assert proj["name"] == "Nexus98 Core"
    assert proj["status"] == "active"


def test_list_active_projects(reality):
    reality.register_project("A")
    reality.register_project("B", status="archived")
    active = reality.list_projects(status="active")
    assert len(active) == 1


def test_register_component_and_find_by_path(reality):
    cid = reality.register_component("core/supervisor.py", "file", project="nexus98")
    comp = reality.find_component_by_path("core/supervisor.py")
    assert comp and comp["id"] == cid


def test_relationships_and_neighbors(reality):
    a = reality.register_component("a.py", "file")
    b = reality.register_component("b.py", "file")
    reality.link(a, b, "imports")
    assert reality.relations_of(a)
    assert b in reality.neighbors(a)


def test_system_state_and_snapshot(reality):
    reality.set_state("ollama", "online")
    snap = reality.reality_snapshot()
    assert snap["system_state_keys"] == ["ollama"]
    assert snap["components"] == 0


def test_persists_across_reload(tmp_path):
    p = tmp_path / "workspace.json"
    r = WorkspaceReality(p)
    pid = r.register_project("Persisted")
    r.register_component("x.py", "file")
    r.close()
    r2 = WorkspaceReality(p)
    assert r2.get_project(pid)["name"] == "Persisted"
    assert r2.find_component_by_path("x.py")
    r2.close()


def test_corrupt_store_recovers(tmp_path):
    p = tmp_path / "workspace.json"
    p.write_text("{bad json", encoding="utf-8")
    r = WorkspaceReality(p)  # must not raise
    assert r.list_projects() == []
    r.close()
