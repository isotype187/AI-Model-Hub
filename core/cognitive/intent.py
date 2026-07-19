"""Nexus98 Intent Intelligence Framework.

Responsible for *understanding* user intent: representing intent, extracting
objectives, detecting ambiguity, determining clarification needs, scoring
confidence, classifying the task, and attaching intent metadata.

This framework is representational and advisory. It does NOT couple to
execution — it produces an ``Intent`` model that downstream frameworks
(Planning, Decision, Context) may consume. No autonomy-state mutation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class IntentType(str, Enum):
    """High-level task classifications."""

    INFORMATION = "information"
    ACTION = "action"
    PLANNING = "planning"
    REVIEW = "review"
    LEARNING = "learning"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"


# Keyword signals used for lightweight classification (heuristic, not authoritative).
_TYPE_SIGNALS: Dict[IntentType, List[str]] = {
    IntentType.ACTION: ["create", "write", "build", "implement", "modify", "fix", "delete", "run"],
    IntentType.PLANNING: ["plan", "design", "architect", "organize", "schedule", "roadmap"],
    IntentType.REVIEW: ["review", "audit", "check", "analyze", "inspect", "evaluate"],
    IntentType.LEARNING: ["learn", "explain", "teach", "understand", "why", "how"],
    IntentType.INFORMATION: ["what", "who", "when", "list", "show", "status", "report"],
}


@dataclass
class Objective:
    """An extracted objective from the raw intent text."""

    text: str
    priority: int = 1


@dataclass
class Intent:
    """A structured representation of user intent."""

    raw: str
    intent_type: IntentType = IntentType.UNKNOWN
    objectives: List[Objective] = field(default_factory=list)
    confidence: float = 0.0
    ambiguity: float = 0.0
    needs_clarification: bool = False
    clarification_questions: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    entities: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "raw": self.raw,
            "intent_type": self.intent_type.value,
            "objectives": [o.__dict__ for o in self.objectives],
            "confidence": self.confidence,
            "ambiguity": self.ambiguity,
            "needs_clarification": self.needs_clarification,
            "clarification_questions": self.clarification_questions,
            "metadata": self.metadata,
            "entities": self.entities,
        }


class IntentAnalyzer:
    """Produces structured ``Intent`` models from raw task text."""

    def __init__(self, ambiguity_threshold: float = 0.4,
                 confidence_threshold: float = 0.5):
        self.ambiguity_threshold = ambiguity_threshold
        self.confidence_threshold = confidence_threshold

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, text: str) -> Intent:
        raw = (text or "").strip()
        intent_type = self._classify(raw)
        objectives = self._extract_objectives(raw)
        entities = self._extract_entities(raw)
        ambiguity = self._score_ambiguity(raw, intent_type)
        confidence = self._score_confidence(raw, intent_type, ambiguity)
        questions = self._clarification(intent_type, objectives, ambiguity)
        needs = ambiguity >= self.ambiguity_threshold or bool(questions)
        meta = {
            "length": str(len(raw)),
            "word_count": str(len(raw.split())),
            "classified_as": intent_type.value,
        }
        return Intent(
            raw=raw, intent_type=intent_type, objectives=objectives,
            confidence=confidence, ambiguity=ambiguity,
            needs_clarification=needs, clarification_questions=questions,
            metadata=meta, entities=entities,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _classify(self, text: str) -> IntentType:
        low = text.lower()
        scores = {t: 0 for t in _TYPE_SIGNALS}
        for t, words in _TYPE_SIGNALS.items():
            for w in words:
                if re.search(rf"\b{re.escape(w)}", low):
                    scores[t] += 1
        best = max(scores, key=scores.get)
        if scores[best] == 0:
            return IntentType.UNKNOWN
        # Multiple competing signals -> ambiguous.
        top = sorted(scores.values(), reverse=True)
        if len(top) > 1 and top[0] == top[1] and top[0] > 0:
            return IntentType.AMBIGUOUS
        return best

    def _extract_objectives(self, text: str) -> List[Objective]:
        # Sentence/phrase split on connectors; treat clauses as objectives.
        clauses = re.split(r"[.;\n]| and | then | so that ", text)
        objs = []
        for c in clauses:
            c = c.strip().strip(".,;")
            if 3 <= len(c.split()) <= 25:
                objs.append(Objective(text=c))
        return objs[:10]

    def _extract_entities(self, text: str) -> List[str]:
        # Pull quoted strings and path-like tokens as lightweight entities.
        ents = re.findall(r'"([^"]+)"', text)
        ents += re.findall(r"[A-Za-z0-9_.\-/\\]+\.(py|json|yaml|md|txt|js|ts)", text)
        return ents[:10]

    def _score_ambiguity(self, text: str, intent_type: IntentType) -> float:
        score = 0.0
        low = text.lower()
        vague = ["something", "stuff", "whatever", "maybe", "somehow", "etc", "thing"]
        score += sum(0.2 for v in vague if v in low.split())
        if intent_type == IntentType.UNKNOWN:
            score += 0.4
        if intent_type == IntentType.AMBIGUOUS:
            score += 0.3
        if len(text.split()) < 3:
            score += 0.3
        return round(min(1.0, score), 3)

    def _score_confidence(self, text: str, intent_type: IntentType,
                          ambiguity: float) -> float:
        base = 0.5
        if intent_type not in (IntentType.UNKNOWN, IntentType.AMBIGUOUS):
            base += 0.2
        if len(text.split()) >= 5:
            base += 0.1
        base -= ambiguity * 0.5
        return round(max(0.0, min(1.0, base)), 3)

    def _clarification(self, intent_type: IntentType, objectives: List[Objective],
                      ambiguity: float) -> List[str]:
        q: List[str] = []
        if intent_type in (IntentType.UNKNOWN, IntentType.AMBIGUOUS):
            q.append("What is the primary goal of this request?")
        if not objectives:
            q.append("Can you describe the specific outcome you expect?")
        if ambiguity >= self.ambiguity_threshold:
            q.append("Which parts of the request are flexible vs fixed?")
        return q
