"""Decision Engine Framework tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.cognitive.decision import DecisionEngine, Option, Policy, Decision


@pytest.fixture
def engine():
    return DecisionEngine(weights={"capability": 1.0, "cost": 1.0, "safety": 2.0})


def test_weighted_scoring(engine):
    opts = [
        Option("a", "cheap", {"capability": 0.5, "cost": 1.0, "safety": 0.5}),
        Option("b", "safe", {"capability": 0.9, "cost": 0.4, "safety": 1.0}),
    ]
    d = engine.evaluate("pick one", opts)
    assert d.recommended == "b"
    assert d.ranked[0] == "b"


def test_policy_gate_rejects(engine):
    engine.add_policy(Policy("must_be_safe", lambda o: o.scores.get("safety", 0) >= 0.8))
    opts = [
        Option("a", "risky", {"capability": 1.0, "cost": 1.0, "safety": 0.2}),
        Option("b", "safe", {"capability": 0.9, "cost": 0.4, "safety": 1.0}),
    ]
    d = engine.evaluate("pick", opts)
    assert d.rejected.get("a") == "policy:must_be_safe"
    assert d.recommended == "b"


def test_explanation_and_risk(engine):
    opts = [Option("a", "x", {"capability": 0.8, "cost": 0.8, "safety": 0.9}, risk=0.1)]
    d = engine.evaluate("q", opts)
    assert "x" in d.explanations["a"]
    assert d.risks["a"] == 0.1


def test_confidence_low_when_tied(engine):
    opts = [
        Option("a", "x", {"capability": 0.5, "cost": 0.5, "safety": 0.5}),
        Option("b", "y", {"capability": 0.5, "cost": 0.5, "safety": 0.5}),
    ]
    d = engine.evaluate("tie", opts)
    assert d.confidence <= 0.1


def test_decide_model_advisory():
    # Build a tiny model registry double.
    class P:
        def __init__(s, o, n, pr, sc, cost, tags):
            s.ollama = o; s.name = n; s.priority = pr
            s.suitability_score = lambda t: sc; s.cost_tier = cost; s.tags = tags
    class MI:
        def list_profiles(s):
            return [P("coder:1b", "Coder", 10, 5, "local", ["safety"]),
                    P("remote:1b", "Remote", 9, 1, "remote", [])]
    eng = DecisionEngine()
    d = eng.decide_model("write code", MI())
    assert d.recommended  # some model recommended
    assert isinstance(d, Decision)
