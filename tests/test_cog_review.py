"""Review Intelligence Framework tests."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.cognitive.review import ReviewIntelligence, REVIEW_DIMENSIONS


@pytest.fixture
def rv(tmp_path):
    r = ReviewIntelligence(path=tmp_path / "reviews.json")
    yield r
    r.close()


def test_review_types_defined(rv):
    assert set(REVIEW_DIMENSIONS) == {"implementation", "code", "architecture", "regression"}


def test_implementation_review(rv):
    rec = rv.review_subject("implementation", "task-1",
                            {"correctness": 0.9, "completeness": 0.8, "safety": 1.0},
                            recommendations=["add tests"], lessons=["learned x"])
    assert rec.verdict == "pass"
    assert rec.recommendations == ["add tests"]


def test_code_review_failure(rv):
    rec = rv.review_subject("code", "task-2",
                            {"clarity": 0.2, "efficiency": 0.1, "style": 0.3, "safety": 0.2})
    assert rec.verdict == "fail"


def test_quality_score(rv):
    s = rv.quality_score("architecture", {"cohesion": 0.8, "coupling": 0.6,
                                          "extensibility": 0.7, "safety": 1.0})
    assert 0.0 <= s <= 1.0


def test_unknown_review_type_rejected(rv):
    try:
        rv.review_subject("bogus", "x", {})
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_recommendations_aggregation(rv):
    rv.review_subject("code", "t1", {"clarity": 0.1, "efficiency": 0.2,
                                     "style": 0.3, "safety": 0.1})
    sugg = rv.recommendations()
    assert isinstance(sugg, list)
