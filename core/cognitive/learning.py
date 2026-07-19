"""Nexus98 Learning Framework.

Passive learning architecture: records successful patterns, failed patterns,
reusable solutions, heuristics, confidence updates, and knowledge evolution.
Learning is strictly *passive* — it records and retrieves; it does NOT modify
code, config, or autonomy state (no self-modifying behavior).

Built on Code Memory: patterns/lessons/decisions are stored as knowledge
records; the learning index (pattern -> outcome stats) lives in
``data/db/learning.json``.
"""
from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from core.code_memory import CodeMemory


ROOT = Path(r"D:\Nexus98")
DEFAULT_INDEX = ROOT / "data" / "db" / "learning.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class PatternRecord:
    """A learned pattern with observed outcomes."""

    pattern_id: str
    kind: str            # success | failure | solution | heuristic
    summary: str
    outcome: str = "unknown"
    confidence: float = 0.5
    occurrences: int = 1
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "pattern_id": self.pattern_id, "kind": self.kind,
            "summary": self.summary, "outcome": self.outcome,
            "confidence": self.confidence, "occurrences": self.occurrences,
            "updated_at": self.updated_at,
        }


class LearningSystem:
    """Passive learner over Code Memory + a local pattern index."""

    def __init__(self, memory: Optional[CodeMemory] = None, project: str = "nexus98",
                 db_path: Optional[Path] = None, index_path: Optional[Path] = None):
        self.memory = memory or CodeMemory(project=project, db_path=db_path)
        if index_path is None and db_path is not None:
            # Keep the learning index alongside the memory DB (never the real
            # default path when an explicit DB path was given).
            index_path = Path(db_path).parent / "learning_index.json"
        self.index_path = Path(index_path) if index_path else DEFAULT_INDEX
        self._index: Dict[str, PatternRecord] = self._load_index()

    # ------------------------------------------------------------------
    # Index persistence
    # ------------------------------------------------------------------

    def _load_index(self) -> Dict[str, PatternRecord]:
        if self.index_path.exists():
            try:
                rows = json.loads(self.index_path.read_text(encoding="utf-8"))
                return {pid: PatternRecord(**r) for pid, r in rows.items()}
            except (json.JSONDecodeError, OSError, TypeError):
                return {}
        return {}

    def _save_index(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.index_path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({pid: p.to_dict() for pid, p in self._index.items()}, f, indent=2)
        shutil.move(str(tmp), str(self.index_path))

    # ------------------------------------------------------------------
    # Passive recording
    # ------------------------------------------------------------------

    def record_pattern(self, kind: str, summary: str, *,
                       outcome: str = "unknown", confidence: float = 0.5,
                       tags=None) -> PatternRecord:
        if kind not in ("success", "failure", "solution", "heuristic"):
            raise ValueError(f"Invalid pattern kind: {kind}")
        pid = uuid.uuid5(uuid.NAMESPACE_URL, f"pat:{kind}:{summary}").hex[:12]
        rec = self._index.get(pid) or PatternRecord(
            pattern_id=pid, kind=kind, summary=summary,
            outcome=outcome, confidence=confidence,
        )
        rec.occurrences += 0 if pid in self._index else 0
        if pid in self._index:
            rec.occurrences += 1
            # Passive confidence update: nudge toward observed outcome.
            if outcome == "success":
                rec.confidence = min(1.0, rec.confidence + 0.05)
            elif outcome == "failure":
                rec.confidence = max(0.0, rec.confidence - 0.05)
        rec.outcome = outcome
        rec.updated_at = _now()
        self._index[pid] = rec
        # Mirror into Code Memory for searchability.
        self.memory.record_knowledge(
            "pattern", f"[{kind}] {summary} (outcome={outcome})",
            tags=[kind, "learning"] + list(tags or []),
            importance=4, confidence=confidence,
        )
        self._save_index()
        return rec

    def record_solution(self, problem: str, solution: str, *,
                        confidence: float = 0.7) -> PatternRecord:
        return self.record_pattern("solution", f"{problem} => {solution}",
                                   outcome="success", confidence=confidence)

    def record_heuristic(self, heuristic: str, confidence: float = 0.6) -> PatternRecord:
        return self.record_pattern("heuristic", heuristic, confidence=confidence)

    # ------------------------------------------------------------------
    # Retrieval / evolution
    # ------------------------------------------------------------------

    def successful_patterns(self) -> List[PatternRecord]:
        return [p for p in self._index.values()
                if p.kind in ("success", "solution")]

    def failed_patterns(self) -> List[PatternRecord]:
        return [p for p in self._index.values() if p.kind == "failure"]

    def reusable_solutions(self) -> List[PatternRecord]:
        return [p for p in self._index.values() if p.kind == "solution"]

    def top_heuristics(self, limit: int = 5) -> List[PatternRecord]:
        hs = [p for p in self._index.values() if p.kind == "heuristic"]
        hs.sort(key=lambda p: p.confidence, reverse=True)
        return hs[:limit]

    def evolution_summary(self) -> dict:
        """Knowledge evolution snapshot (passive observation only)."""
        return {
            "patterns": len(self._index),
            "success": sum(1 for p in self._index.values() if p.kind in ("success", "solution")),
            "failure": sum(1 for p in self._index.values() if p.kind == "failure"),
            "avg_confidence": round(
                sum(p.confidence for p in self._index.values()) / max(1, len(self._index)), 3),
        }

    def close(self) -> None:
        self._save_index()
        self.memory.close()

