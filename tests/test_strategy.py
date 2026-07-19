"""Strategy Engine unit tests (isolated; no autonomy/Guardian coupling)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import core.strategy as strat


def test_catalog_includes_safety_first():
    assert "safety_first" in strat.STRATEGIES
    assert strat.get_strategy("accurate").label == "Accurate"


def test_compose_bias_sums_weights():
    vec = strat.compose_bias(frozenset({"accurate", "cost_efficient"}))
    # accurate -> capability +1.0 ; cost_efficient -> capability -0.4, cost +1.0
    assert vec["capability"] == pytest.approx(0.6)
    assert vec["cost"] == pytest.approx(1.0)


def test_detect_conflicts_finds_capability_vs_cost():
    conflicts = strat.detect_conflicts(frozenset({"accurate", "cost_efficient"}))
    assert ("capability", "cost") in conflicts


def test_no_conflict_when_aligned():
    conflicts = strat.detect_conflicts(frozenset({"accurate", "coding"}))
    assert conflicts == []


def test_explain_includes_safety_first():
    text = strat.explain(frozenset({"safety_first", "accurate"}))
    assert "Safety First" in text
    assert "Active strategies" in text


def test_module_is_pure_data_no_writes():
    # The module must not expose any mutating autonomy surface.
    assert not hasattr(strat, "set_auto_execute")
    assert not hasattr(strat, "request_level_change")
