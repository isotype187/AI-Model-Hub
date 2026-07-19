"""
Nexus98 Memory Service (Phase 1).

Single import surface for persistent memory. Backed by SQLite only.

Phase 1 boundary (see docs/MEMORY_ARCHITECTURE_DESIGN.md section 11):
  - Interface: store, query, update, delete/forget, verify, export, import
  - SQLite backend only (no vector, embeddings, graph, multi-agent, autonomous)
  - Schema versioning, migration support, integrity checks, atomic writes,
    backup before migration.
  - Record minimum fields: memory_id, category, content, source, created_at,
    updated_at, confidence, importance, verification_status.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


DEFAULT_DB_PATH = Path(r"D:\Nexus98\data\db\memory.db")

SCHEMA_VERSION = 1

VERIFICATION_STATUSES = {"unverified", "verified", "disputed", "archived"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


class MemoryService:
    """Persistent memory store backed by SQLite."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = None
        self._open_connection()

    def _open_connection(self) -> None:
        """Open (or reopen) the SQLite connection.

        A corrupted or otherwise unopenable database must not crash
        construction: the connection is stored so that integrity_check()
        can later report the corruption instead of raising during init.
        """
        try:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._ensure_schema()
        except sqlite3.DatabaseError:
            # Leave the connection as-is (open or None); integrity_check()
            # will detect and report the corruption gracefully.
            if self._conn is None:
                try:
                    self._conn = sqlite3.connect(str(self.db_path))
                    self._conn.row_factory = sqlite3.Row
                except sqlite3.DatabaseError:
                    self._conn = None

    # ------------------------------------------------------------------
    # Schema / integrity
    # ------------------------------------------------------------------

    def _ensure_schema(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                )
                """
            )
            row = self._conn.execute(
                "SELECT version FROM schema_version"
            ).fetchone()
            current = row["version"] if row else 0
            if current < SCHEMA_VERSION:
                self._apply_migrations(current)

    def _apply_migrations(self, from_version: int) -> None:
        # Forward-only, idempotent. Phase 1 defines version 1.
        if from_version < 1:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id          TEXT PRIMARY KEY,
                    category           TEXT NOT NULL,
                    content            TEXT NOT NULL,
                    source             TEXT NOT NULL,
                    created_at         TEXT NOT NULL,
                    updated_at         TEXT NOT NULL,
                    confidence         REAL NOT NULL,
                    importance         INTEGER NOT NULL,
                    verification_status TEXT NOT NULL,
                    type               TEXT NOT NULL DEFAULT 'episodic',
                    project            TEXT NOT NULL DEFAULT 'nexus98',
                    version            INTEGER NOT NULL DEFAULT 1,
                    update_history     TEXT NOT NULL DEFAULT '[]',
                    deleted            INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_mem_category "
                "ON memories (category)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_mem_source "
                "ON memories (source)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_mem_verification "
                "ON memories (verification_status)"
            )
            self._conn.execute(
                "INSERT INTO schema_version (version) VALUES (1)"
            )

    def integrity_check(self) -> bool:
        """Return True if the database passes PRAGMA integrity_check.

        Returns False (rather than raising) when the database is corrupted
        or cannot be opened, so callers can detect corruption gracefully.
        """
        try:
            if self._conn is None:
                self._conn = sqlite3.connect(str(self.db_path))
                self._conn.row_factory = sqlite3.Row
            try:
                self._conn.execute("PRAGMA integrity_check")
            except sqlite3.ProgrammingError:
                # Connection was closed; reconnect against the same DB file.
                self._conn = sqlite3.connect(str(self.db_path))
                self._conn.row_factory = sqlite3.Row
            rows = self._conn.execute("PRAGMA integrity_check").fetchall()
            return all(r[0] == "ok" for r in rows)
        except sqlite3.DatabaseError:
            return False

    # ------------------------------------------------------------------
    # Create / update
    # ------------------------------------------------------------------

    def store(
        self,
        category: str,
        content: str,
        source: str,
        confidence: float = 1.0,
        importance: int = 3,
        verification_status: str = "unverified",
        memory_type: str = "episodic",
        project: str = "nexus98",
        memory_id: Optional[str] = None,
    ) -> str:
        if verification_status not in VERIFICATION_STATUSES:
            raise ValueError(f"Invalid verification_status: {verification_status}")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if not 1 <= importance <= 5:
            raise ValueError("importance must be between 1 and 5")

        mid = memory_id or _new_id()
        now = _now()
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO memories (
                    memory_id, category, content, source, created_at,
                    updated_at, confidence, importance, verification_status,
                    type, project, version, update_history, deleted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, '[]', 0)
                """,
                (
                    mid,
                    category,
                    content,
                    source,
                    now,
                    now,
                    confidence,
                    importance,
                    verification_status,
                    memory_type,
                    project,
                ),
            )
        return mid

    def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        category: Optional[str] = None,
        confidence: Optional[float] = None,
        importance: Optional[int] = None,
        verification_status: Optional[str] = None,
        source: Optional[str] = None,
    ) -> bool:
        existing = self._get_row(memory_id)
        if not existing or existing["deleted"]:
            return False
        if verification_status is not None and verification_status not in VERIFICATION_STATUSES:
            raise ValueError(f"Invalid verification_status: {verification_status}")

        history = json.loads(existing["update_history"])
        changes: dict[str, Any] = {}
        new_category = category if category is not None else existing["category"]
        new_content = content if content is not None else existing["content"]
        new_conf = confidence if confidence is not None else existing["confidence"]
        new_imp = importance if importance is not None else existing["importance"]
        new_ver = verification_status if verification_status is not None else existing["verification_status"]
        new_source = source if source is not None else existing["source"]

        if category is not None and category != existing["category"]:
            changes["category"] = existing["category"]
        if content is not None and content != existing["content"]:
            changes["content"] = existing["content"]
        if confidence is not None and confidence != existing["confidence"]:
            changes["confidence"] = existing["confidence"]
        if importance is not None and importance != existing["importance"]:
            changes["importance"] = existing["importance"]
        if verification_status is not None and verification_status != existing["verification_status"]:
            changes["verification_status"] = existing["verification_status"]

        if not changes:
            return True

        history.append(
            {
                "ts": _now(),
                "by": new_source,
                "changed": changes,
            }
        )

        with self._conn:
            self._conn.execute(
                """
                UPDATE memories SET
                    category=?, content=?, confidence=?, importance=?,
                    verification_status=?, source=?, updated_at=?, version=version+1,
                    update_history=?
                WHERE memory_id=?
                """,
                (
                    new_category,
                    new_content,
                    new_conf,
                    new_imp,
                    new_ver,
                    new_source,
                    _now(),
                    json.dumps(history),
                    memory_id,
                ),
            )
        return True

    # ------------------------------------------------------------------
    # Query / verify / delete / export / import
    # ------------------------------------------------------------------

    def query(
        self,
        category: Optional[str] = None,
        source: Optional[str] = None,
        verification_status: Optional[str] = None,
        memory_type: Optional[str] = None,
        project: Optional[str] = None,
        min_confidence: Optional[float] = None,
        min_importance: Optional[int] = None,
        include_deleted: bool = False,
        limit: Optional[int] = None,
    ) -> list[dict]:
        clauses = []
        params: list[Any] = []
        if not include_deleted:
            clauses.append("deleted = 0")
        if category is not None:
            clauses.append("category = ?")
            params.append(category)
        if source is not None:
            clauses.append("source = ?")
            params.append(source)
        if verification_status is not None:
            clauses.append("verification_status = ?")
            params.append(verification_status)
        if memory_type is not None:
            clauses.append("type = ?")
            params.append(memory_type)
        if project is not None:
            clauses.append("project = ?")
            params.append(project)
        if min_confidence is not None:
            clauses.append("confidence >= ?")
            params.append(min_confidence)
        if min_importance is not None:
            clauses.append("importance >= ?")
            params.append(min_importance)

        sql = "SELECT * FROM memories"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY updated_at DESC"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)

        rows = self._conn.execute(sql, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get(self, memory_id: str) -> Optional[dict]:
        row = self._get_row(memory_id)
        if not row or row["deleted"]:
            return None
        return self._row_to_dict(row)

    def verify(self, memory_id: str, status: str, source: str = "system") -> bool:
        if status not in VERIFICATION_STATUSES:
            raise ValueError(f"Invalid verification_status: {status}")
        return self.update(memory_id, verification_status=status, source=source)

    def delete(self, memory_id: str) -> bool:
        """Hard delete (used by tests / rollback)."""
        with self._conn:
            cur = self._conn.execute(
                "DELETE FROM memories WHERE memory_id = ?", (memory_id,)
            )
        return cur.rowcount > 0

    def forget(self, memory_id: str, source: str = "system") -> bool:
        """Soft archive: mark deleted, preserve record for audit/rollback."""
        existing = self._get_row(memory_id)
        if not existing or existing["deleted"]:
            return False
        with self._conn:
            self._conn.execute(
                """
                UPDATE memories SET deleted=1, verification_status='archived',
                    updated_at=?, version=version+1,
                    update_history=?
                WHERE memory_id=?
                """,
                (
                    _now(),
                    json.dumps(
                        json.loads(existing["update_history"])
                        + [{"ts": _now(), "by": source, "changed": {"deleted": False}}]
                    ),
                    memory_id,
                ),
            )
        return True

    def export(self, path: Optional[Path] = None) -> list[dict]:
        data = self.query(include_deleted=True)
        if path is not None:
            Path(path).write_text(
                json.dumps(data, indent=2), encoding="utf-8"
            )
        return data

    def import_records(self, records: list[dict], source: str = "import") -> int:
        count = 0
        for rec in records:
            if not self._validate_record(rec):
                continue
            self.store(
                category=rec.get("category", "uncategorized"),
                content=str(rec.get("content", "")),
                source=rec.get("source", source),
                confidence=float(rec.get("confidence", 1.0)),
                importance=int(rec.get("importance", 3)),
                verification_status=rec.get("verification_status", "unverified"),
                memory_type=rec.get("type", "episodic"),
                project=rec.get("project", "nexus98"),
                memory_id=rec.get("memory_id"),
            )
            count += 1
        return count

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_row(self, memory_id: str):
        return self._conn.execute(
            "SELECT * FROM memories WHERE memory_id = ?", (memory_id,)
        ).fetchone()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        d = dict(row)
        d["update_history"] = json.loads(d["update_history"])
        d["deleted"] = bool(d["deleted"])
        return d

    @staticmethod
    def _validate_record(rec: dict) -> bool:
        required = ("content", "source")
        if not all(k in rec for k in required):
            return False
        try:
            float(rec.get("confidence", 1.0))
            int(rec.get("importance", 3))
        except (TypeError, ValueError):
            return False
        return True

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "MemoryService":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
