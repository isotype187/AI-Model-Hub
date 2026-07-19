"""Nexus98 Model Intelligence framework.

Gives Nexus98 an accurate, queryable understanding of the AI models available
locally (Ollama). It reads the authoritative model configuration
(``config/models.json`` and ``config/models.yaml``), enriches it with
capability metadata, strengths/weaknesses, cost/performance awareness, and
produces routing recommendations. It is advisory only — it never launches or
downloads models (those remain infrastructure-level, Level 2+/Guardian-gated).

This complements (does not duplicate) the Strategy Engine: Strategy expresses
*reasoning style* bias; Model Intelligence maps that intent onto concrete,
available models.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(r"D:\Nexus98")
MODELS_JSON = ROOT / "config" / "models.json"


@dataclass
class ModelProfile:
    """Enriched understanding of a single model."""

    ollama: str
    name: str
    category: str
    priority: int = 5
    context: int = 8192
    tags: List[str] = field(default_factory=list)
    roles: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    cost_tier: str = "local"      # local | remote; local == no $ cost
    performance_tier: str = "standard"  # fast | standard | thorough
    available: bool = True

    def to_dict(self) -> dict:
        return {
            "ollama": self.ollama, "name": self.name, "category": self.category,
            "priority": self.priority, "context": self.context,
            "tags": list(self.tags), "roles": list(self.roles),
            "strengths": list(self.strengths), "weaknesses": list(self.weaknesses),
            "cost_tier": self.cost_tier, "performance_tier": self.performance_tier,
            "available": self.available,
        }

    def suitability_score(self, task: str) -> float:
        """Heuristic score of how well this model fits a task string.

        Uses word-level token matching (so "plan" matches the "planning" tag
        and "architecture" matches the "architecture" tag) rather than raw
        substring containment, which would miss spaced/inflected forms.
        """
        import re
        # Only meaningful tokens (length >= 3) participate in matching so that
        # stop-words like "a"/"the" do not spuriously match every tag.
        tokens = {tok for tok in re.findall(r"[a-z0-9]+", task.lower()) if len(tok) >= 3}
        score = 0.0
        for tag in self.tags:
            t = tag.lower()
            if t in tokens or any(
                (t in tok or tok in t) and len(t) >= 3 for tok in tokens
            ):
                score += self.priority
        for role in self.roles:
            r = role.lower()
            if r in tokens:
                score += 2.0
        return float(score)


# Default heuristic enrichment when the config lacks explicit metadata.
_CATEGORY_STRENGTHS = {
    "coding": ["code generation", "debugging", "scripts"],
    "reasoning": ["planning", "architecture", "analysis"],
    "general": ["chat", "summarization", "general Q&A"],
}
_CATEGORY_WEAKNESSES = {
    "coding": ["long-form prose"],
    "reasoning": ["fast autocomplete"],
    "general": ["specialized code tasks"],
}


class ModelIntelligence:
    """Registry + routing advisor for available models."""

    def __init__(self, models_json: Optional[Path] = None):
        self.models_json = Path(models_json) if models_json else MODELS_JSON
        self._profiles: Dict[str, ModelProfile] = {}
        self.load()

    def load(self) -> int:
        """Load profiles from the authoritative config."""
        if not self.models_json.exists():
            return 0
        try:
            data = json.loads(self.models_json.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError):
            return 0
        self._profiles.clear()
        for m in data.get("models", []):
            cat = m.get("category", "general")
            prof = ModelProfile(
                ollama=m.get("ollama", m.get("name", "")),
                name=m.get("name", m.get("ollama", "")),
                category=cat,
                priority=int(m.get("priority", 5)),
                context=int(m.get("context", 8192)),
                tags=list(m.get("tags", [])),
                roles=list(m.get("roles", [])),
                strengths=list(_CATEGORY_STRENGTHS.get(cat, [])),
                weaknesses=list(_CATEGORY_WEAKNESSES.get(cat, [])),
            )
            self._profiles[prof.ollama] = prof
        return len(self._profiles)

    def register(self, profile: ModelProfile) -> None:
        self._profiles[profile.ollama] = profile

    def get(self, ollama_id: str) -> Optional[ModelProfile]:
        return self._profiles.get(ollama_id)

    def list_profiles(self) -> List[ModelProfile]:
        return list(self._profiles.values())

    def by_category(self, category: str) -> List[ModelProfile]:
        return [p for p in self._profiles.values() if p.category == category]

    def set_availability(self, ollama_id: str, available: bool) -> None:
        prof = self._profiles.get(ollama_id)
        if prof:
            prof.available = available

    def recommend(self, task: str, *, category: Optional[str] = None,
                  available_only: bool = True) -> Optional[ModelProfile]:
        """Recommend the best-fit model for a task.

        Orders by suitability score, then by priority. Optionally constrained
        to a category and/or to available models.
        """
        candidates = list(self._profiles.values())
        if category:
            candidates = [c for c in candidates if c.category == category]
        if available_only:
            candidates = [c for c in candidates if c.available]
        if not candidates:
            return None
        candidates.sort(key=lambda c: (c.suitability_score(task), c.priority),
                        reverse=True)
        return candidates[0]

    def explain_recommendation(self, task: str, **kwargs) -> dict:
        rec = self.recommend(task, **kwargs)
        if rec is None:
            return {"task": task, "recommendation": None, "reason": "no candidate"}
        return {
            "task": task,
            "recommendation": rec.ollama,
            "name": rec.name,
            "category": rec.category,
            "strengths": rec.strengths,
            "weaknesses": rec.weaknesses,
            "cost_tier": rec.cost_tier,
            "performance_tier": rec.performance_tier,
            "score": rec.suitability_score(task),
        }

    def capability_summary(self) -> dict:
        return {
            "total": len(self._profiles),
            "categories": sorted({p.category for p in self._profiles.values()}),
            "available": sum(1 for p in self._profiles.values() if p.available),
        }



