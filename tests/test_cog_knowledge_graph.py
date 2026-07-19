"""Knowledge Graph Framework tests."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.cognitive.knowledge import KnowledgeGraph, NODE_KINDS, EDGE_RELATIONS


@pytest.fixture
def kg(tmp_path):
    db = tmp_path / "kg.db"
    g = KnowledgeGraph(project="kgproj", db_path=db)
    yield g
    g.close()


def test_node_kinds_valid(kg):
    assert "project" in NODE_KINDS and "pattern" in NODE_KINDS


def test_add_node_and_invalid_kind(kg):
    n = kg.add_node("module", "strategy.controller")
    assert n.kind == "module"
    try:
        kg.add_node("bogus", "x")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_connect_and_relations(kg):
    a = kg.add_node("file", "a.py")
    b = kg.add_node("file", "b.py")
    # node ids derived from labels
    aid = a.node_id
    bid = b.node_id
    e = kg.connect(aid, bid, "depends_on")
    assert e["relation"] == "depends_on"
    assert bid in kg.neighbors(aid)
    assert kg.edges_of(aid)


def test_invalid_relation_rejected(kg):
    a = kg.add_node("file", "a.py")
    b = kg.add_node("file", "b.py")
    try:
        kg.connect(a.node_id, b.node_id, "not_a_relation")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_nodes_by_kind(kg):
    kg.add_node("pattern", "Retry external calls")
    recs = kg.nodes_by_kind("pattern")
    assert any("Retry external calls" in r for r in recs)

