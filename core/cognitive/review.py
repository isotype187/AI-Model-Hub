"""Nexus98 Review Intelligence Framework.

Expands the review architecture into specialized review types: implementation,
code, architecture, and regression review, plus lessons learned, actionable
recommendations, and quality scoring. Built on top of
``core.frameworks.review.ReviewSystem`` (it does not replace it).

Observational/record-keeping only. It produces structured reviews and stores
them; it never auto-applies fixes or changes autonomy state.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from core.frameworks.review import ReviewSystem, Evaluation


# Quality dimensions per review type.
REVIEW_DIMENSIONS = {
    "implementation": ["correctness", "completeness", "safety"],
    "code": ["clarity", "efficiency", "style", "safety"],
    "architecture": ["cohesion", "coupling", "extensibility", "safety"],
    "regression": ["stability", "coverage", "safety"],
}


@dataclass
class ReviewRecord:
    """A structured review of one subject."""

    review_id: str
    review_type: str
    subject: str
    scores: Dict[str, float]
    verdict: str
    recommendations: List[str]
    lessons: List[str]
    created_at: str

    def to_dict(self) -> dict:
        return {
            "review_id": self.review_id, "review_type": self.review_type,
            "subject": self.subject, "scores": self.scores,
            "verdict": self.verdict,
            "recommendations": self.recommendations,
            "lessons": self.lessons, "created_at": self.created_at,
        }


class ReviewIntelligence:
    """Specialized, multi-type review built on ReviewSystem."""

    def __init__(self, review: Optional[ReviewSystem] = None, path=None):
        self.review = review or ReviewSystem(path)

    def review_subject(self, review_type: str, subject: str,
                       scores: Dict[str, float], *,
                       recommendations: Optional[List[str]] = None,
                       lessons: Optional[List[str]] = None) -> ReviewRecord:
        if review_type not in REVIEW_DIMENSIONS:
            raise ValueError(f"Unknown review type: {review_type}")
        # Ensure all expected dimensions are present (default 0).
        full = {d: float(scores.get(d, 0.0)) for d in REVIEW_DIMENSIONS[review_type]}
        ev: Evaluation = self.review.evaluate(
            subject, review_type, full,
            notes=f"type={review_type}",
        )
        rec = ReviewRecord(
            review_id=uuid.uuid4().hex[:12], review_type=review_type,
            subject=subject, scores=full, verdict=ev.verdict,
            recommendations=list(recommendations or []),
            lessons=list(lessons or []),
            created_at=ev.created_at,
        )
        return rec

    def quality_score(self, review_type: str, scores: Dict[str, float]) -> float:
        full = {d: float(scores.get(d, 0.0)) for d in REVIEW_DIMENSIONS[review_type]}
        if not full:
            return 0.0
        return round(sum(full.values()) / len(full), 3)

    def lessons_learned(self, review_type: Optional[str] = None) -> List[ReviewRecord]:
        recs = self.review.by_type(review_type) if review_type else \
            [r for r in self.review._reviews.values()]
        # Return stored ReviewRecords would require persistence; here we surface
        # failure-derived lessons from the underlying ReviewSystem.
        out = []
        for r in self.review.failures():
            out.append(ReviewRecord(
                review_id=r["eval_id"], review_type=r.get("subject_type", "unknown"),
                subject=r["subject"], scores=r["scores"], verdict=r["verdict"],
                recommendations=[], lessons=[], created_at=r["created_at"],
            ))
        return out

    def recommendations(self) -> List[dict]:
        """Aggregate improvement suggestions across all reviews."""
        return self.review.improvement_suggestions()

    def close(self) -> None:
        self.review.close()
