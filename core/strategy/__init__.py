"""Nexus98 Strategy Engine.

Public surface for the Strategy Engine. The pure-data catalog lives in
``core.strategy.catalog`` and the advisory integration layer lives in
``core.strategy.controller``. This package re-exports both so callers can
``import core.strategy`` and get the full engine.

Importing this package performs NO file IO and changes NO global state. The
controller is strictly advisory: it never mutates autonomy state, never flips
``auto_execute``, and never bypasses the Governor or Guardian boundaries.

Spec: docs/NEXUS98_MODEL_INTELLIGENCE_SPECIFICATION.md (Section 6, Strategy
Engine) and docs/FUTURE_ARCHITECTURE_GAP_ANALYSIS.md.
"""
from __future__ import annotations

from core.strategy.catalog import (
    BIAS_DIMENSIONS,
    PRECEDENCE,
    STRATEGIES,
    Strategy,
    compose_bias,
    detect_conflicts,
    explain,
    get_strategy,
    list_strategies,
)
from core.strategy.controller import (
    ROLE_HINTS,
    SAFETY_CONSTRAINING,
    StrategyController,
    StrategyDecision,
    default_controller,
)

__all__ = [
    "Strategy",
    "STRATEGIES",
    "PRECEDENCE",
    "BIAS_DIMENSIONS",
    "get_strategy",
    "list_strategies",
    "compose_bias",
    "detect_conflicts",
    "explain",
    "StrategyController",
    "StrategyDecision",
    "default_controller",
    "ROLE_HINTS",
    "SAFETY_CONSTRAINING",
]
