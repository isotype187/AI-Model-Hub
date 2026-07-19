"""
Backward-compatible memory shim (Phase 1).

Preserves the original public API of the legacy Memory class
(agent_memory.json append store) by routing calls into the new
MemoryService SQLite backend. Existing callers keep working unchanged.

Legacy API:
    m = Memory()
    m.save(item_dict)   -> appends/creates a record
    m.load()            -> returns all records as a list of dicts

No vector/embeddings/graph/multi-agent/autonomous behavior is added.
"""

from __future__ import annotations

from pathlib import Path

from core.memory_service import MemoryService


class Memory:
    """Compatibility shim over MemoryService.

    Maintains cwd-relative agent_memory.json behavior for legacy callers
    while persisting through the SQLite-backed MemoryService.
    """

    def __init__(self, path: str = "agent_memory.json"):
        # Keep the legacy path attribute for backward compatibility.
        self.path = Path(path)
        self._service = MemoryService()

    def save(self, item):
        """Append a legacy item dict as a new memory record."""
        if not isinstance(item, dict):
            item = {"content": str(item)}
        category = (item.get("task") or item.get("category") or "legacy")
        content = str(item.get("response", item.get("content", "")))
        source = str(item.get("agent", item.get("source", "legacy")))
        self._service.store(
            category=category,
            content=content,
            source=source,
            confidence=1.0,
            importance=3,
            verification_status="unverified",
            memory_type="episodic",
        )
        return True

    def load(self):
        """Return all stored records as a list of dicts (legacy shape)."""
        records = self._service.query(include_deleted=False)
        return [
            {
                "memory_id": r["memory_id"],
                "task": r["category"],
                "agent": r["source"],
                "response": r["content"],
                "verification_status": r["verification_status"],
            }
            for r in records
        ]

    def close(self):
        self._service.close()
