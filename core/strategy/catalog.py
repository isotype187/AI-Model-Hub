"""Nexus98 Strategy Engine — pure-data catalog.

Defines the strategy catalog, bias weights, conflict detection, and read-only
helpers. This module performs NO file writes, NO autonomy-state changes, and
does NOT touch the Governor, Guardian, or supervisor.auto_execute. It is
informational/selection bias only and is designed to compose with the future
model router.

Spec: docs/NEXUS98_MODEL_INTELLIGENCE_SPECIFICATION.md (Section 6, Strategy
Engine) and docs/FUTURE_ARCHITECTURE_GAP_ANALYSIS.md (core/strategy/).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Tuple


# Bias dimensions scored by the router. Positive favors "more capable / remote";
# negative favors "cheaper / local / faster". Strategies contribute weighted
# biases that compose into a single selection bias vector.
BIAS_DIMENSIONS = ("capability", "cost", "latency", "local_first", "verified")


@dataclass(frozen=True)
class Strategy:
    """A single strategy definition (data, not code)."""

    id: str
    label: str
    description: str
    # bias weights keyed by dimension; absent dimensions default to 0.0
    biases: Dict[str, float] = field(default_factory=dict)
    # user-customizable weight multiplier (preference data, not autonomy state)
    weight: float = 1.0


# The strategy catalog. "safety_first" always wins per spec Section 6.3.
STRATEGIES: Dict[str, Strategy] = {
    "safety_first": Strategy(
        id="safety_first",
        label="Safety First",
        description="Constrains to safe/verified models and local-first; never overridden by cost/latency.",
        biases={"verified": 1.0, "local_first": 1.0, "capability": 0.3},
    ),
    "accurate": Strategy(
        id="accurate",
        label="Accurate",
        description="Prefers the best-capability model for the task.",
        biases={"capability": 1.0},
    ),
    "coding": Strategy(
        id="coding",
        label="Coding",
        description="Biases toward code-capable models and tooling.",
        biases={"capability": 0.6, "local_first": 0.2},
    ),
    "research": Strategy(
        id="research",
        label="Research",
        description="Biases toward deep-reasoning / long-context models.",
        biases={"capability": 0.7, "latency": -0.2},
    ),
    "cost_efficient": Strategy(
        id="cost_efficient",
        label="Cost Efficient",
        description="Prefers cheapest / local models; may lower model tier.",
        biases={"cost": 1.0, "local_first": 0.8, "capability": -0.4},
    ),
    "fast": Strategy(
        id="fast",
        label="Fast",
        description="Prefers lowest-latency responses.",
        biases={"latency": 1.0, "capability": -0.2},
    ),
}

# Resolution precedence (highest first) per spec Section 6.3.
PRECEDENCE: Tuple[str, ...] = (
    "safety_first",
    "accurate",
    "coding",
    "research",
    "cost_efficient",
    "fast",
)

# Dimension conflicts: pairs that pull opposite ways.
_CONFLICT_PAIRS = (
    ("capability", "cost"),
    ("capability", "latency"),
    ("local_first", "cost"),
)


def get_strategy(strategy_id: str) -> Strategy:
    """Return a strategy definition by id (read-only)."""
    return STRATEGIES[strategy_id]


def list_strategies() -> List[Strategy]:
    """All known strategies (read-only)."""
    return list(STRATEGIES.values())


def compose_bias(active: FrozenSet[str]) -> Dict[str, float]:
    """Sum weighted biases across the simultaneously-active strategy set.

    Returns a bias vector keyed by dimension. Safe-first is always included
    at the top of precedence when present in the active set.
    """
    ordered = [s for s in PRECEDENCE if s in active and s in STRATEGIES]
    vector: Dict[str, float] = {dim: 0.0 for dim in BIAS_DIMENSIONS}
    for sid in ordered:
        strat = STRATEGIES[sid]
        for dim, value in strat.biases.items():
            vector[dim] = vector.get(dim, 0.0) + value * strat.weight
    return vector


def detect_conflicts(active: FrozenSet[str]) -> List[Tuple[str, str]]:
    """Surface opposing biases among the active strategy set.

    A conflict exists when two active strategies contribute opposite signed
    biases on the same conflict dimension (e.g. Accurate pushes capability up
    while Cost Efficient pushes capability down). We compare per-dimension
    contributions directly rather than only the composed vector.
    """
    conflicts: List[Tuple[str, str]] = []
    for a, b in _CONFLICT_PAIRS:
        pushing_a = False
        pushing_b = False
        for sid in active:
            strat = STRATEGIES.get(sid)
            if strat is None:
                continue
            va = strat.biases.get(a, 0.0) * strat.weight
            vb = strat.biases.get(b, 0.0) * strat.weight
            if va > 0:
                pushing_a = True
            if vb > 0:
                pushing_b = True
        if pushing_a and pushing_b:
            conflicts.append((a, b))
    return conflicts


def explain(active: FrozenSet[str]) -> str:
    """Human-readable explanation of the active strategy composition."""
    if not active:
        return "No active strategies."
    conflicts = detect_conflicts(active)
    parts = ["Active strategies: " + ", ".join(sorted(active)) + "."]
    if conflicts:
        for a, b in conflicts:
            parts.append(f"Conflict: {a} vs {b} pulled opposite ways.")
    if "safety_first" in active:
        parts.append("Safety First constrained to verified/local models.")
    return " ".join(parts)
