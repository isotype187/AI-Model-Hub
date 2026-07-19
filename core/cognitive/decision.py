"""Nexus98 Decision Engine Framework.

A reusable, policy-driven decision engine: weighted scoring across options,
policy evaluation (hard constraints), tradeoff analysis, confidence,
explanation, risk evaluation, and recommendation generation. Integrates with
Strategy (biases), Planning (plan selection), and Capability Awareness
(known limitations) — but remains advisory: it recommends, it does not act.

No autonomy-state mutation. The Governor remains the sole writer of autonomy
state; this engine only produces recommendations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class Option:
    """A candidate decision option with scored criteria."""

    option_id: str
    label: str
    scores: Dict[str, float] = field(default_factory=dict)  # criterion -> 0..1
    risk: float = 0.0            # 0..1 estimated risk
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class Policy:
    """A hard constraint: if it returns False the option is rejected."""

    name: str
    test: Callable[[Option], bool]


@dataclass
class Decision:
    """The output of a decision evaluation."""

    question: str
    recommended: Optional[str]
    ranked: List[str]
    explanations: Dict[str, str]
    confidence: float
    risks: Dict[str, float]
    rejected: Dict[str, str]   # option_id -> reason

    def to_dict(self) -> dict:
        return {
            "question": self.question, "recommended": self.recommended,
            "ranked": self.ranked, "explanations": self.explanations,
            "confidence": self.confidence, "risks": self.risks,
            "rejected": self.rejected,
        }


class DecisionEngine:
    """Weighted, policy-gated decision maker."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {"capability": 1.0, "cost": 1.0, "safety": 2.0}
        self._policies: List[Policy] = []

    def add_policy(self, policy: Policy) -> None:
        self._policies.append(policy)

    def evaluate(self, question: str, options: List[Option]) -> Decision:
        rejected: Dict[str, str] = {}
        scored: Dict[str, float] = {}
        risks: Dict[str, float] = {}
        explanations: Dict[str, str] = {}

        for opt in options:
            # Policy gate (hard constraints).
            blocked_by = [p.name for p in self._policies if not p.test(opt)]
            if blocked_by:
                rejected[opt.option_id] = f"policy:{','.join(blocked_by)}"
                continue
            score = self._weighted(opt.scores)
            scored[opt.option_id] = score
            risks[opt.option_id] = opt.risk
            explanations[opt.option_id] = self._explain(opt, score)

        ranked = sorted(scored, key=scored.get, reverse=True)
        recommended = ranked[0] if ranked else None

        # Confidence: gap between top two + inverse of recommended risk.
        confidence = 0.0
        if recommended:
            top = scored[recommended]
            second = scored[ranked[1]] if len(ranked) > 1 else 0.0
            gap = (top - second) / (top + 1e-6)
            confidence = round(max(0.0, min(1.0, gap * (1 - risks[recommended]))), 3)

        return Decision(
            question=question, recommended=recommended, ranked=ranked,
            explanations=explanations, confidence=confidence,
            risks=risks, rejected=rejected,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _weighted(self, scores: Dict[str, float]) -> float:
        total_w = 0.0
        acc = 0.0
        for crit, val in scores.items():
            w = self.weights.get(crit, 1.0)
            acc += val * w
            total_w += w
        return round(acc / total_w, 4) if total_w else 0.0

    def _explain(self, opt: Option, score: float) -> str:
        parts = [f"{opt.label}: weighted score {score:.3f}"]
        if opt.risk:
            parts.append(f"risk {opt.risk:.2f}")
        return "; ".join(parts)

    # ------------------------------------------------------------------
    # Integration helpers (advisory)
    # ------------------------------------------------------------------

    def decide_model(self, task: str, model_intel, options: Optional[List[Option]] = None):
        """Recommend a model using Model Intelligence + a safety policy."""
        if options is None and model_intel is not None:
            opts = []
            for p in model_intel.list_profiles():
                opts.append(Option(
                    option_id=p.ollama, label=p.name,
                    scores={"capability": p.suitability_score(task) / max(1, p.priority),
                            "cost": 1.0 if p.cost_tier == "local" else 0.3,
                            "safety": 1.0 if "safety" in p.tags else 0.7},
                    risk=0.2 if p.cost_tier == "local" else 0.6,
                ))
            options = opts
        # Safety policy: prefer local/cost-safe models.
        self.add_policy(Policy("local_preferred",
                               lambda o: o.risk <= 0.6))
        return self.evaluate(f"model for: {task}", options or [])
