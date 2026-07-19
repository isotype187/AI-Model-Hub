"""Code Memory Foundation tests (isolated; temp DB only)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.code_memory import CodeMemory, KNOWLEDGE_CATEGORIES


@pytest.fixture
def cm():
    db = Path(tempfile.mkdtemp()) / "cm.db"
    store = CodeMemory(project="testproj", db_path=db)
    yield store
    store.close()


def test_record_and_recall_decision(cm):
    mid = cm.record_decision(
        "Use SQLite for memory",
        "Simpler than a graph DB for v1",
        tags=["memory", "architecture"],
    )
    assert mid
    recs = cm.recall(category="decision")
    assert len(recs) == 1
    assert "DECISION" in recs[0]["content"]


def test_recall_by_tag(cm):
    cm.record_knowledge("pattern", "Wrap calls in retries", tags=["resilience"])
    cm.record_knowledge("pattern", "Use context managers", tags=["style"])
    arch = cm.recall(tags=["resilience"])
    assert len(arch) == 1
    assert "retries" in arch[0]["content"]


def test_search_ranks_by_overlap(cm):
    cm.record_knowledge("pattern", "Wrap external calls in retries for resilience", tags=["a"])
    cm.record_knowledge("pattern", "Format code with black", tags=["b"])
    results = cm.search("retry resilience external")
    assert results and "retries" in results[0]["content"].lower()


def test_verify_and_forget(cm):
    mid = cm.record_knowledge("constraint", "Do not delete backups", tags=["safety"])
    assert cm.verify(mid, "verified")
    rec = cm.get(mid)
    assert rec["verification_status"] == "verified"
    assert cm.forget(mid)
    assert cm.get(mid) is None  # soft-archived -> not returned


def test_stats(cm):
    cm.record_decision("d1", "r1")
    cm.record_knowledge("pattern", "p1")
    stats = cm.stats()
    assert stats["project"] == "testproj"
    assert stats["total"] == 2
    assert stats["by_category"]["decision"] == 1


def test_invalid_verification_rejected(cm):
    with pytest.raises(ValueError):
        cm.record_knowledge("bug", "x", verification_status="bogus")


def test_project_isolation(cm):
    other = CodeMemory(project="other", db_path=cm._svc.db_path)
    other.record_knowledge("context", "other project note", tags=["x"])
    # The original project should not see the other project's memory.
    assert cm.recall(category="context") == []
    other.close()
