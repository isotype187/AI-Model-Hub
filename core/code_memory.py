"""Nexus98 Code Memory Foundation.

A thin, purpose-built layer over the persistent :class:`MemoryService`
(``core.memory_service``) that gives agents a structured, project-scoped way
to record and recall engineering knowledge between sessions. It does NOT
replace the existing memory architecture — it consumes it.

Provided capabilities:
  * Project knowledge storage (decisions, patterns, constraints, bugs).
  * Decision / history tracking with rationale and outcome.
  * Retrieval by project, category, tags, and free-text search.
  * Agent-accessible helper functions (record_*, recall_*).

All persistence is delegated to ``MemoryService`` (SQLite). This module adds
only categorization, tagging, and search semantics on top. It performs no
autonomy-state changes and never mutates the Governor/Guardian surfaces.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional

from core.memory_service import MemoryService, VERIFICATION_STATUSES


# Canonical knowledge categories used across Nexus98 engineering memory.
KNOWLEDGE_CATEGORIES = (
    "decision",      # an architecture/design decision with rationale
    "pattern",       # a reusable code/structure pattern
    "constraint",    # a hard rule or boundary that must be respected
    "bug",           # a known defect and its fix/symptoms
    "context",       # ambient project context (owner, intent, stack)
    "history",       # a record of a past action/event for recovery
)


def _normalize_tags(tags) -> str:
    """Render a tag list/set into a stable, comma-separated string."""
    if tags is None:
        return ""
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
    return ",".join(str(t).strip() for t in tags if str(t).strip())


class CodeMemory:
    """Project-scoped engineering memory built on ``MemoryService``.

    A single ``CodeMemory`` instance is bound to one project. Multiple
    projects can be tracked simultaneously by creating multiple instances
    with different ``project`` ids.
    """

    def __init__(self, project: str = "nexus98", db_path=None):
        self.project = project
        self._svc = MemoryService(db_path)
        self._tag_index: Dict[str, set] = {}

    # ------------------------------------------------------------------
    # Write helpers (agent-accessible)
    # ------------------------------------------------------------------

    def record_knowledge(
        self,
        category: str,
        content: str,
        *,
        source: str = "agent",
        tags=None,
        confidence: float = 0.8,
        importance: int = 3,
        verification_status: str = "unverified",
    ) -> str:
        """Store a knowledge item in the given category.

        ``category`` should be one of :data:`KNOWLEDGE_CATEGORIES`, but any
        string is accepted for forward-compatibility. Returns the memory id.
        """
        if verification_status not in VERIFICATION_STATUSES:
            raise ValueError(f"Invalid verification_status: {verification_status}")
        payload = content
        if tags:
            payload = f"{content}\n#tags: {_normalize_tags(tags)}"
        mid = self._svc.store(
            category=category,
            content=payload,
            source=source,
            confidence=confidence,
            importance=importance,
            verification_status=verification_status,
            memory_type="semantic",
            project=self.project,
        )
        self._index_tags(mid, tags)
        return mid

    def record_decision(
        self,
        title: str,
        rationale: str,
        *,
        source: str = "agent",
        outcome: str = "pending",
        tags=None,
    ) -> str:
        """Record an engineering decision with its rationale and outcome."""
        content = f"DECISION: {title}\nRATIONALE: {rationale}\nOUTCOME: {outcome}"
        return self.record_knowledge(
            "decision", content, source=source, tags=tags,
            confidence=0.9, importance=4, verification_status="unverified",
        )

    def record_history(
        self,
        event: str,
        *,
        source: str = "agent",
        tags=None,
    ) -> str:
        """Record a discrete historical event for later recovery/context."""
        return self.record_knowledge(
            "history", event, source=source, tags=tags,
            confidence=1.0, importance=3, verification_status="unverified",
        )

    def verify(self, memory_id: str, status: str = "verified", source: str = "agent") -> bool:
        """Mark a memory verified/disputed/archived."""
        return self._svc.verify(memory_id, status, source=source)

    def forget(self, memory_id: str, source: str = "agent") -> bool:
        """Soft-archive a memory (preserves record for audit)."""
        return self._svc.forget(memory_id, source=source)

    # ------------------------------------------------------------------
    # Read helpers (agent-accessible)
    # ------------------------------------------------------------------

    def recall(
        self,
        category: Optional[str] = None,
        *,
        tags=None,
        min_importance: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[dict]:
        """Recall knowledge for this project, optionally filtered.

        When ``tags`` are supplied, results are further filtered by tag
        membership (AND semantics on the stored ``#tags:`` line).
        """
        records = self._svc.query(
            category=category,
            project=self.project,
            memory_type="semantic",
            min_importance=min_importance,
            limit=limit,
        )
        if tags:
            wanted = set(_normalize_tags(tags).split(","))
            records = [r for r in records if wanted <= self._tags_of(r)]
        return records

    def search(self, text: str, *, limit: Optional[int] = None) -> List[dict]:
        """Free-text search across this project's knowledge content."""
        wanted = set(re.findall(r"\w+", text.lower()))
        records = self._svc.query(project=self.project, memory_type="semantic")
        scored = []
        for r in records:
            words = set(re.findall(r"\w+", r["content"].lower()))
            score = len(wanted & words)
            if score:
                scored.append((score, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        result = [r for _, r in scored]
        return result[:limit] if limit else result

    def get(self, memory_id: str) -> Optional[dict]:
        """Fetch a single memory by id (project-scoped)."""
        rec = self._svc.get(memory_id)
        if rec and rec.get("project") == self.project:
            return rec
        return None

    def stats(self) -> dict:
        """Lightweight summary of stored knowledge for this project."""
        records = self._svc.query(project=self.project, memory_type="semantic")
        by_category: Dict[str, int] = {}
        for r in records:
            by_category[r["category"]] = by_category.get(r["category"], 0) + 1
        return {
            "project": self.project,
            "total": len(records),
            "by_category": by_category,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _tags_of(record: dict) -> set:
        m = re.search(r"#tags:\s*(.+)", record.get("content", ""))
        if not m:
            return set()
        return set(t.strip() for t in m.group(1).split(",") if t.strip())

    def _index_tags(self, memory_id: str, tags) -> None:
        for t in _normalize_tags(tags).split(","):
            if t:
                self._tag_index.setdefault(t, set()).add(memory_id)

    def close(self) -> None:
        self._svc.close()

    def __enter__(self) -> "CodeMemory":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


# Convenience singleton for the default project.
default_memory = CodeMemory()
