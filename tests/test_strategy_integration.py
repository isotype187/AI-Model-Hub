"""Strategy Engine integration layer tests (advisory, no autonomy coupling)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import core.strategy as strat
from core.strategy import StrategyController, default_controller


def test_controller_evaluate_basic():
    c = StrategyController(default_strategies=frozenset({"accurate"}))
    d = c.evaluate(task="review the architecture")
    assert "accurate" in d.active
    assert d.recommended_role == "reviewer"
    assert "capability" in d.bias_vector


def test_autonomous_injects_safety_first():
    # On the autonomous path, Safety First must always be present.
    c = StrategyController(default_strategies=frozenset({"cost_efficient"}))
    d = c.evaluate(task="write a script", autonomous=True)
    assert "safety_first" in d.active
    assert d.safety_constrained is True


def test_non_autonomous_does_not_inject_safety_first():
    c = StrategyController(default_strategies=frozenset({"cost_efficient"}))
    d = c.evaluate(task="write a script", autonomous=False)
    assert "safety_first" not in d.active
    assert d.safety_constrained is False


def test_controller_does_not_mutate_autonomy_state():
    # Advisory only: must not expose any mutating autonomy surface.
    assert not hasattr(default_controller, "set_auto_execute")
    assert not hasattr(default_controller, "request_level_change")


def test_bias_for_unknown_dimension_raises():
    c = StrategyController()
    with pytest.raises(ValueError):
        c.bias_for("not_a_dimension")


def test_explainment_includes_role():
    c = StrategyController()
    text = c.explain(frozenset({"coding"}), task="implement a feature")
    assert "coding" in text.lower()
    assert "recommended role" in text.lower()


def test_role_hint_mapping():
    c = StrategyController()
    assert c.evaluate(active=frozenset({"research"})).recommended_role == "researcher"
    assert c.evaluate(active=frozenset({"coding"})).recommended_role == "coder"
    assert c.evaluate(active=frozenset({"fast"})).recommended_role == "documentation"


def test_decision_to_dict_serializable():
    d = default_controller.evaluate(active=frozenset({"accurate", "coding"}))
    payload = d.to_dict()
    assert set(payload) >= {
        "active", "bias_vector", "recommended_role",
        "safety_constrained", "conflicts", "explanation",
    }
    assert isinstance(payload["active"], list)
