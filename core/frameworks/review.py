"""Nexus98 Evaluation & Review framework.

Systems for Nexus98 to evaluate its own work: task outcomes, code changes,
decisions, failures, and improvement opportunities. Produces structured scoring
and append-only review records so the system can learn between sessions.

This framework is *observational + record-keeping*. It emits evaluations and
stores them; it does not auto-apply fixes or change autonomy state. Review
records are stored under ``data/reviews.json``.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(r"D:\Nexus98")
DEFAULT_PATH = ROOT / "data" / "reviews.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Weighted dimensions for a generic evaluation (each scored 0.0-1.0).
DEFAULT_DIMENSIONS = (
    "correctness", "completeness", "safety", "clarity", "efficiency",
)


@dataclass
class Evaluation:
    """A scored evaluation over named dimensions."""

    eval_id: str
    subject: str           # what was evaluated (task/file/decision id)
    subject_type: str      # task | change | decision | failure
    scores: Dict[str, float] = field(default_factory=dict)
    verdict: str = "pending"  # pass | partial | fail | needs_review
    notes: str = ""
    created_at: str = field(default_factory=_now)

    def weighted_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        if not self.scores:
            return 0.0
        weights = weights or {k: 1.0 for k in self.scores}
        total_w = 0.0
        acc = 0.0
        for k, v in self.scores.items():
            w = weights.get(k, 1.0)
            acc += v * w
            total_w += w
        return round(acc / total_w, 3) if total_w else 0.0

    def to_dict(self) -> dict:
        return {
            "eval_id": self.eval_id, "subject": self.subject,
            "subject_type": self.subject_type, "scores": dict(self.scores),
            "verdict": self.verdict, "notes": self.notes,
            "created_at": self.created_at,
        }


class ReviewSystem:
    """Records evaluations and supports retrieval/aggregation."""

    def __init__(self, path: Optional[Path] = None):
        self.path = Path(path) if path else DEFAULT_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._reviews: Dict[str, dict] = self._load()

    def _load(self) -> Dict[str, dict]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._reviews, f, indent=2)
        import shutil
        shutil.move(str(tmp), str(self.path))

    # ------------------------------------------------------------------
    # Evaluate
    # ------------------------------------------------------------------

    def evaluate(self, subject: str, subject_type: str,
                 scores: Dict[str, float], *, notes: str = "",
                 weights: Optional[Dict[str, float]] = None) -> Evaluation:
        ev = Evaluation(
            eval_id=uuid.uuid4().hex[:12], subject=subject,
            subject_type=subject_type, scores=scores, notes=notes,
        )
        overall = ev.weighted_score(weights)
        ev.verdict = self._verdict_from_score(overall)
        self._reviews[ev.eval_id] = ev.to_dict()
        self.save()
        return ev

    @staticmethod
    def _verdict_from_score(score: float) -> str:
        if score >= 0.8:
            return "pass"
        if score >= 0.5:
            return "partial"
        return "fail"

    def get(self, eval_id: str) -> Optional[dict]:
        return self._reviews.get(eval_id)

    def by_subject(self, subject: str) -> List[dict]:
        return [r for r in self._reviews.values() if r["subject"] == subject]

    def by_type(self, subject_type: str) -> List[dict]:
        return [r for r in self._reviews.values() if r["subject_type"] == subject_type]

    def failures(self) -> List[dict]:
        """Evaluations that failed or need review — improvement opportunities."""
        return [r for r in self._reviews.values()
                if r["verdict"] in ("fail", "needs_review")]

    def improvement_suggestions(self) -> List[dict]:
        """Aggregate weakest dimensions across failures for targeted learning."""
        agg: Dict[str, List[float]] = {}
        for r in self.failures():
            for dim, val in r["scores"].items():
                agg.setdefault(dim, []).append(val)
        return [
            {"dimension": d, "avg": round(sum(v) / len(v), 3), "samples": len(v)}
            for d, v in sorted(agg.items(), key=lambda kv: sum(kv[1]) / len(kv[1]))
        ]

    def summary(self) -> dict:
        verdicts = [r["verdict"] for r in self._reviews.values()]
        return {
            "total": len(self._reviews),
            "pass": verdicts.count("pass"),
            "partial": verdicts.count("partial"),
            "fail": verdicts.count("fail"),
            "needs_review": verdicts.count("needs_review"),
        }

    def close(self) -> None:
        self.save()
