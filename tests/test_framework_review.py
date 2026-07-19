"""Evaluation & Review framework tests (temp storage)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.frameworks.review import ReviewSystem, Evaluation


@pytest.fixture
def rs(tmp_path):
    sys = ReviewSystem(tmp_path / "reviews.json")
    yield sys
    sys.close()


def test_evaluate_produces_verdict(rs):
    ev = rs.evaluate("task-1", "task", {"correctness": 0.9, "safety": 0.9}, notes="good")
    assert ev.verdict == "pass"
    assert ev.weighted_score() >= 0.9


def test_partial_and_fail_verdicts(rs):
    p = rs.evaluate("t2", "task", {"correctness": 0.6, "safety": 0.6})
    f = rs.evaluate("t3", "task", {"correctness": 0.2, "safety": 0.1})
    assert p.verdict == "partial"
    assert f.verdict == "fail"


def test_weighted_scoring(rs):
    ev = Evaluation(eval_id="e", subject="s", subject_type="change",
                    scores={"correctness": 1.0, "efficiency": 0.0})
    # correctness weighted 2x -> (1*2 + 0*1)/3 = 0.667
    score = ev.weighted_score({"correctness": 2.0, "efficiency": 1.0})
    assert round(score, 3) == 0.667


def test_failures_and_improvements(rs):
    rs.evaluate("a", "change", {"safety": 0.1, "clarity": 0.2})
    rs.evaluate("b", "change", {"safety": 0.9, "clarity": 0.8})
    fails = rs.failures()
    assert len(fails) == 1
    sugg = rs.improvement_suggestions()
    assert sugg and sugg[0]["dimension"] == "safety"


def test_by_subject_and_type(rs):
    rs.evaluate("task-x", "task", {"correctness": 0.9})
    rs.evaluate("task-x", "task", {"correctness": 0.5})
    assert len(rs.by_subject("task-x")) == 2
    assert len(rs.by_type("task")) == 2


def test_summary_counts(rs):
    rs.evaluate("a", "task", {"correctness": 0.9})
    rs.evaluate("b", "task", {"correctness": 0.1})
    s = rs.summary()
    assert s["total"] == 2
    assert s["pass"] == 1 and s["fail"] == 1
