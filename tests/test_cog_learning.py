"""Learning Framework tests (passive; no self-modification)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.cognitive.learning import LearningSystem


@pytest.fixture
def ls(tmp_path):
    db = tmp_path / "learn.db"
    s = LearningSystem(project="learnproj", db_path=db)
    yield s
    s.close()


def test_record_success_pattern(ls):
    p = ls.record_pattern("success", "use retries for flaky IO",
                           outcome="success", confidence=0.7)
    assert p.kind == "success"
    assert p.occurrences == 1


def test_record_failure_and_confidence_decay(ls):
    p = ls.record_pattern("failure", "edit live config directly",
                          outcome="failure", confidence=0.6)
    assert p.kind == "failure"
    first_conf = p.confidence
    # recording again with failure nudges confidence down
    p2 = ls.record_pattern("failure", "edit live config directly",
                            outcome="failure", confidence=0.6)
    assert p2 is p
    assert p2.confidence < first_conf


def test_record_solution_and_heuristic(ls):
    ls.record_solution("OOM on parse", "stream the file")
    ls.record_heuristic("prefer local models for privacy")
    assert ls.reusable_solutions()
    assert ls.top_heuristics()


def test_retrieval_filters(ls):
    ls.record_pattern("success", "use retries for flaky IO", outcome="success")
    ls.record_pattern("failure", "edit live config directly", outcome="failure")
    assert len(ls.successful_patterns()) == 1
    assert len(ls.failed_patterns()) == 1


def test_evolution_summary(ls):
    ls.record_pattern("success", "use retries for flaky IO", outcome="success")
    ls.record_pattern("failure", "edit live config directly", outcome="failure")
    summ = ls.evolution_summary()
    assert summ["patterns"] == 2
    assert summ["success"] == 1 and summ["failure"] == 1


def test_invalid_pattern_kind(ls):
    try:
        ls.record_pattern("bogus", "x")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_persists_across_reload(tmp_path):
    db = tmp_path / "learn.db"
    s = LearningSystem(project="learnproj", db_path=db)
    s.record_pattern("success", "use retries for flaky IO", outcome="success")
    s.close()
    s2 = LearningSystem(project="learnproj", db_path=db)
    assert s2.successful_patterns()
    s2.close()

