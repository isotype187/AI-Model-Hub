"""Knowledge Architecture framework tests (temp DB)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.frameworks.knowledge import KnowledgeArchitecture


@pytest.fixture
def ka(tmp_path):
    db = tmp_path / "km.db"
    store = KnowledgeArchitecture(project="kproj", db_path=db)
    yield store
    store.close()


def test_record_and_recall_lesson(ka):
    mid = ka.record_lesson("Always back up before mutation", context="project engine")
    lessons = ka.lessons()
    assert lessons and "Always back up" in lessons[0]["content"]


def test_record_pattern_and_query(ka):
    ka.record_pattern("Retry external calls", "wrap in try/except with backoff", tags=["resilience"])
    pats = ka.patterns()
    assert pats and "Retry external calls" in pats[0]["content"]


def test_record_architecture(ka):
    ka.record_architecture("Strategy Controller", "advisory bridge to runtime")
    recs = ka.architecture_records()
    assert recs and "Strategy Controller" in recs[0]["content"]


def test_knowledge_graph_links(ka):
    a = ka.record_decision("Use SQLite", "simple v1")
    b = ka.record_pattern("Migrate later", "to graph if needed")
    ka.link(a, b, "supersedes")
    assert b in ka.related(a)
    assert ka.links_of(a)


def test_decision_recorded_as_memory(ka):
    mid = ka.record_decision("Pick local models", "cost + privacy")
    # The base CodeMemory should hold it under the decision category.
    assert ka.memory.recall(category="decision")
