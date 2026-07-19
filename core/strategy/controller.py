"""Nexus98 Strategy Engine — integration layer.

This module composes the pure-data strategy catalog (``core.strategy.catalog``)
with live orchestration surfaces: the Supervisor, the Router, and the Project
Engine. It is strictly advisory: it produces *guidance* (biases, recommended
roles, safety constraints) that downstream systems MAY consult when making
execution decisions. It never mutates autonomy state, never flips
``auto_execute``, and never bypasses the Governor or Guardian boundaries.

Safety precedence is preserved: ``safety_first`` always wins and is
auto-injected when an action touches the autonomous-execution path. Decisions
are always explainable via :meth:`StrategyController.explain`.

See docs/NEXUS98_MODEL_INTELLIGENCE_SPECIFICATION.md (Section 6) and
docs/FUTURE_ARCHITECTURE_GAP_ANALYSIS.md.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional

from core.strategy.catalog import (
    BIAS_DIMENSIONS,
    STRATEGIES,
    compose_bias,
    detect_conflicts,
    explain as _catalog_explain,
)


# Role the Router understands. The controller translates active strategies
# into a recommended routing role without re-implementing routing logic.
ROLE_HINTS = {
    "accurate": "reviewer",
    "coding": "coder",
    "research": "researcher",
    "cost_efficient": "coder",
    "fast": "documentation",
}

# If any of these strategies is active, the action must remain on the
# human-gated / verified path (Safety First boundary).
SAFETY_CONSTRAINING = frozenset({"safety_first"})


@dataclass
class StrategyDecision:
    """The output of a strategy evaluation: advisory guidance only."""

    active: FrozenSet[str]
    bias_vector: Dict[str, float] = field(default_factory=dict)
    recommended_role: str = "researcher"
    safety_constrained: bool = False
    conflicts: List[tuple] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "active": sorted(self.active),
            "bias_vector": self.bias_vector,
            "recommended_role": self.recommended_role,
            "safety_constrained": self.safety_constrained,
            "conflicts": [list(c) for c in self.conflicts],
            "explanation": self.explanation,
        }


class StrategyController:
    """Stateless, advisory bridge between the strategy catalog and runtime.

    A controller instance holds an optional *default* strategy set (e.g. a
    user's preferred strategies) but every evaluation can override the active
    set per task. The controller performs no IO and changes no global state.
    """

    def __init__(self, default_strategies: Optional[FrozenSet[str]] = None):
        self.default_strategies: FrozenSet[str] = frozenset(
            default_strategies or frozenset()
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        task: Optional[str] = None,
        active: Optional[FrozenSet[str]] = None,
        *,
        autonomous: bool = False,
    ) -> StrategyDecision:
        """Compute advisory guidance for a task.

        ``autonomous`` should be set when the decision feeds the
        autonomous-execution path. When True the controller guarantees
        ``safety_first`` is present so the Safety First boundary cannot be
        silently dropped.
        """
        active_set = frozenset(active) if active is not None else self.default_strategies

        if autonomous:
            # Safety First is non-negotiable on the autonomous path.
            active_set = active_set | SAFETY_CONSTRAINING

        active_set = frozenset(s for s in active_set if s in STRATEGIES)

        bias_vector = compose_bias(active_set)
        conflicts = detect_conflicts(active_set)
        recommended_role = self._recommend_role(active_set, task)
        safety_constrained = bool(active_set & SAFETY_CONSTRAINING)
        explanation = self.explain(active_set, task=task)

        return StrategyDecision(
            active=active_set,
            bias_vector=bias_vector,
            recommended_role=recommended_role,
            safety_constrained=safety_constrained,
            conflicts=conflicts,
            explanation=explanation,
        )

    def bias_for(self, dimension: str, active: Optional[FrozenSet[str]] = None) -> float:
        """Return the composed bias for a single dimension."""
        if dimension not in BIAS_DIMENSIONS:
            raise ValueError(f"Unknown bias dimension: {dimension}")
        active_set = frozenset(active) if active is not None else self.default_strategies
        return compose_bias(active_set).get(dimension, 0.0)

    def explain(self, active: FrozenSet[str], *, task: Optional[str] = None) -> str:
        """Human-readable explanation of an active strategy set."""
        base = _catalog_explain(active)
        if task:
            role = self._recommend_role(active, task)
            base += f" Recommended role for the task: {role}."
        return base

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _recommend_role(self, active: FrozenSet[str], task: Optional[str]) -> str:
        """Translate the highest-precedence active strategy into a router role.

        Falls back to keyword-light defaults if no strategy maps cleanly.
        """
        for sid in ("safety_first", "accurate", "coding", "research",
                    "cost_efficient", "fast"):
            if sid in active and sid in ROLE_HINTS:
                return ROLE_HINTS[sid]
        if task:
            lowered = task.lower()
            for sid, role in ROLE_HINTS.items():
                if sid in STRATEGIES and any(
                    w in lowered for w in STRATEGIES[sid].biases
                ):
                    return role
        return "researcher"


# Module-level convenience instance. Code that only needs one shared
# controller can import this; it performs no global mutation.
default_controller = StrategyController()
