"""
Nexus98 Memory System - Phase 1 Tests.

Validates the MemoryService SQLite backend and the legacy->SQLite migration
against the approved Phase 1 boundary (docs/MEMORY_ARCHITECTURE_DESIGN.md
section 11.6). Uses isolated temp paths; does NOT touch the real
agent_memory.json or data/db/memory.db.

Run from repo root:
    .venv/Scripts/pytest tests/test_memory_phase1.py
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

from core.memory_service import MemoryService, VERIFICATION_STATUSES
from core import memory_migration as migration


def _tmp_db():
    return Path(tempfile.mkdtemp()) / "memory.db"


# ----------------------------------------------------------------------
# 1. Create memory
# ----------------------------------------------------------------------

def test_create_memory():
    svc = MemoryService(_tmp_db())
    mid = svc.store(
        category="routing",
        content="Prefer local Ollama for experiments.",
        source="architect",
        confidence=0.9,
        importance=4,
        verification_status="verified",
    )
    assert mid
    rec = svc.get(mid)
    assert rec is not None
    assert rec["category"] == "routing"
    assert rec["content"] == "Prefer local Ollama for experiments."
    assert rec["verification_status"] == "verified"
    svc.close()


def test_store_rejects_bad_verification():
    svc = MemoryService(_tmp_db())
    try:
        svc.store("c", "x", "s", verification_status="bogus")
        assert False, "expected ValueError"
    except ValueError:
        pass
    svc.close()


# ----------------------------------------------------------------------
# 2. Retrieve memory
# ----------------------------------------------------------------------

def test_retrieve_memory():
    svc = MemoryService(_tmp_db())
    svc.store("routing", "a", "architect")
    svc.store("prefs", "b", "user")
    routing = svc.query(category="routing")
    assert len(routing) == 1
    assert routing[0]["source"] == "architect"
    all_recs = svc.query()
    assert len(all_recs) == 2
    svc.close()


def test_retrieve_by_verification_and_importance():
    svc = MemoryService(_tmp_db())
    svc.store("c", "low", "s", importance=2, verification_status="unverified")
    svc.store("c", "high", "s", importance=5, verification_status="verified")
    verified = svc.query(verification_status="verified")
    assert len(verified) == 1
    important = svc.query(min_importance=4)
    assert len(important) == 1
    svc.close()


# ----------------------------------------------------------------------
# 3. Update memory
# ----------------------------------------------------------------------

def test_update_memory():
    svc = MemoryService(_tmp_db())
    mid = svc.store("c", "original", "s")
    ok = svc.update(mid, content="revised", importance=5)
    assert ok
    rec = svc.get(mid)
    assert rec["content"] == "revised"
    assert rec["importance"] == 5
    assert rec["version"] == 2
    assert len(rec["update_history"]) == 1
    svc.close()


# ----------------------------------------------------------------------
# 4. Delete / archive memory
# ----------------------------------------------------------------------

def test_delete_and_archive_memory():
    svc = MemoryService(_tmp_db())
    mid = svc.store("c", "x", "s")
    # archive (soft delete)
    assert svc.forget(mid)
    assert svc.get(mid) is None
    assert svc.query(include_deleted=True)[0]["deleted"] is True
    # hard delete
    assert svc.delete(mid)
    assert svc.get(mid) is None
    assert svc.query(include_deleted=True) == []
    svc.close()


# ----------------------------------------------------------------------
# 5. Restart persistence
# ----------------------------------------------------------------------

def test_restart_persistence():
    db = _tmp_db()
    svc = MemoryService(db)
    mid = svc.store("c", "survives restart", "s")
    svc.close()
    # Simulate restart: new service instance on same DB file.
    svc2 = MemoryService(db)
    rec = svc2.get(mid)
    assert rec is not None
    assert rec["content"] == "survives restart"
    assert svc2.integrity_check() is True
    svc2.close()


# ----------------------------------------------------------------------
# 6. Database integrity check
# ----------------------------------------------------------------------

def test_database_integrity_check():
    db = _tmp_db()
    svc = MemoryService(db)
    svc.store("c", "x", "s")
    svc.close()
    assert svc.integrity_check() is True
    # Corrupt the file and confirm integrity_check detects it.
    raw = bytearray(db.read_bytes())
    if raw:
        raw[0] = 0xFF
        db.write_bytes(bytes(raw))
    svc2 = MemoryService(db)
    assert svc2.integrity_check() is False
    svc2.close()


# ----------------------------------------------------------------------
# 7. Failed migration recovery
# ----------------------------------------------------------------------

def test_failed_migration_recovery(tmp_path):
    legacy = tmp_path / "agent_memory.json"
    # Valid shape but with one malformed entry to exercise validation.
    legacy.write_text(
        json.dumps(
            [
                {"task": "Design folders", "agent": "architect", "response": "ok"},
                "this is not a dict",
                {"agent": "researcher"},  # missing content
            ]
        ),
        encoding="utf-8",
    )
    db = tmp_path / "memory.db"

    # Point migration at our isolated files via a custom service.
    svc = MemoryService(db)
    result = migration.migrate(legacy_path=legacy, service=svc)
    svc.close()

    # One valid record imported; two skipped; no crash; original preserved.
    assert result["status"] == "completed"
    assert result["imported"] == 1
    assert result["skipped"] == 2
    assert legacy.exists(), "original must never be deleted"
    assert Path(result["backup_path"]).exists(), "backup must exist"

    # Rollback restores original from backup.
    ok = migration.rollback(backup_path=result["backup_path"], legacy_path=legacy)
    assert ok
    assert legacy.exists()


def test_migration_creates_backup_and_preserves_original(tmp_path):
    legacy = tmp_path / "agent_memory.json"
    legacy.write_text(
        json.dumps(
            [{"task": "T", "agent": "architect", "response": "R"}]
        ),
        encoding="utf-8",
    )
    original_text = legacy.read_text(encoding="utf-8")
    db = tmp_path / "memory.db"
    svc = MemoryService(db)
    result = migration.migrate(legacy_path=legacy, service=svc)
    svc.close()
    assert result["imported"] == 1
    assert legacy.read_text(encoding="utf-8") == original_text
    assert Path(result["backup_path"]).exists()
