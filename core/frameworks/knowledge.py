"""Nexus98 Knowledge Architecture framework.

Extends (does NOT replace) Code Memory with structured *knowledge organization*:
explicit relationships between knowledge items, decision records, lessons
learned, architecture knowledge, and reusable patterns. The base persistence
remains :class:`core.code_memory.CodeMemory` (SQLite via MemoryService); this
framework adds a relationship graph and typed knowledge collections on top.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from core.code_memory import CodeMemory, KNOWLEDGE_CATEGORIES


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Knowledge types this framework specializes beyond the base categories.
KNOWLEDGE_TYPES = (
    "decision", "lesson", "architecture", "pattern", "constraint", "context",
)


@dataclass
class KnowledgeLink:
    """A typed relationship between two memory items (the knowledge graph)."""

    link_id: str
    from_id: str
    to_id: str
    relation: str  # relates_to | implements | contradicts | supersedes | depends_on
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "link_id": self.link_id, "from_id": self.from_id, "to_id": self.to_id,
            "relation": self.relation, "note": note if (note := self.note) else "",
        }


class KnowledgeArchitecture:
    """Typed knowledge organization built on CodeMemory."""

    def __init__(self, memory: Optional[CodeMemory] = None, project: str = "nexus98",
                 db_path: Optional[Path] = None):
        self.memory = memory or CodeMemory(project=project, db_path=db_path)
        self._links: Dict[str, KnowledgeLink] = {}
        self._link_store: Path = (
            Path(db_path).parent / "knowledge_links.json"
            if db_path else Path(r"D:\Nexus98\data\db\knowledge_links.json")
        )
        self._load_links()

    # ------------------------------------------------------------------
    # Link persistence
    # ------------------------------------------------------------------

    def _load_links(self) -> None:
        if self._link_store.exists():
            try:
                rows = __import__("json").loads(
                    self._link_store.read_text(encoding="utf-8")
                )
                for r in rows:
                    self._links[r["link_id"]] = KnowledgeLink(**r)
            except Exception:
                self._links = {}

    def _save_links(self) -> None:
        import json
        self._link_store.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._link_store.with_suffix(".tmp")
        rows = [l.to_dict() for l in self._links.values()]
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2)
        import shutil
        shutil.move(str(tmp), str(self._link_store))

    # ------------------------------------------------------------------
    # Typed knowledge capture
    # ------------------------------------------------------------------

    def record_decision(self, title: str, rationale: str, outcome: str = "pending",
                        tags=None) -> str:
        return self.memory.record_decision(title, rationale, outcome=outcome, tags=tags)

    def record_lesson(self, lesson: str, *, context: str = "", tags=None) -> str:
        content = f"LESSON: {lesson}"
        if context:
            content += f"\nCONTEXT: {context}"
        return self.memory.record_knowledge(
            "context", content, tags=["lesson"] + list(tags or []),
            importance=4, confidence=0.85,
        )

    def record_architecture(self, component: str, description: str, tags=None) -> str:
        content = f"ARCHITECTURE: {component}\n{description}"
        return self.memory.record_knowledge(
            "context", content, tags=["architecture"] + list(tags or []),
            importance=4,
        )

    def record_pattern(self, name: str, description: str, tags=None) -> str:
        content = f"PATTERN: {name}\n{description}"
        return self.memory.record_knowledge(
            "pattern", content, tags=["reusable"] + list(tags or []),
            importance=4,
        )

    # ------------------------------------------------------------------
    # Knowledge graph
    # ------------------------------------------------------------------

    def link(self, from_id: str, to_id: str, relation: str, note: str = "") -> KnowledgeLink:
        lid = uuid.uuid4().hex[:12]
        link = KnowledgeLink(lid, from_id, to_id, relation, note)
        self._links[lid] = link
        self._save_links()
        return link

    def links_of(self, memory_id: str) -> List[KnowledgeLink]:
        return [l for l in self._links.values()
                if l.from_id == memory_id or l.to_id == memory_id]

    def related(self, memory_id: str) -> List[str]:
        out = []
        for l in self._links.values():
            if l.from_id == memory_id:
                out.append(l.to_id)
            elif l.to_id == memory_id:
                out.append(l.from_id)
        return out

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def lessons(self) -> List[dict]:
        return [r for r in self.memory.recall(tags=["lesson"])
                if "LESSON:" in r["content"]]

    def patterns(self) -> List[dict]:
        return self.memory.recall(category="pattern", tags=["reusable"])

    def architecture_records(self) -> List[dict]:
        return [r for r in self.memory.recall(tags=["architecture"])
                if "ARCHITECTURE:" in r["content"]]

    def close(self) -> None:
        self._save_links()
        self.memory.close()
