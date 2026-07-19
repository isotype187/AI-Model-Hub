"""
Nexus98 Memory Migration (Phase 1).

Migrates legacy agent_memory.json into the MemoryService SQLite store.

Requirements (docs/MEMORY_ARCHITECTURE_DESIGN.md section 11.5):
  - never delete the original agent_memory.json
  - create a backup copy before import
  - validate imported records
  - provide a rollback path
  - log migration results
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from core.memory_service import MemoryService


LEGACY_PATH = Path(r"D:\Nexus98\agent_memory.json")


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def migrate(
    legacy_path: Optional[Path] = None,
    service: Optional[MemoryService] = None,
    backup_suffix: str = ".bak",
) -> dict:
    """Migrate legacy agent_memory.json into the memory service.

    Returns a result dict suitable for logging. On any failure the
    rollback path is honored and original files are left untouched.
    """
    src = Path(legacy_path) if legacy_path else LEGACY_PATH
    owned_service = service is None
    svc = service or MemoryService()

    result: dict[str, Any] = {
        "started_at": _ts(),
        "source": str(src),
        "backup_path": None,
        "imported": 0,
        "skipped": 0,
        "errors": [],
        "rolled_back": False,
        "status": "pending",
    }

    if not src.exists():
        result["status"] = "no_source"
        result["errors"].append("Legacy memory file not found; nothing to migrate.")
        if owned_service:
            svc.close()
        return result

    # 1. Backup the original (never delete it).
    backup_path = src.with_suffix(src.suffix + backup_suffix)
    try:
        shutil.copy2(src, backup_path)
        result["backup_path"] = str(backup_path)
    except Exception as exc:  # pragma: no cover - defensive
        result["errors"].append(f"Backup failed: {exc}")
        result["status"] = "failed"
        if owned_service:
            svc.close()
        return result

    # 2. Validate + import.
    try:
        raw = json.loads(src.read_text(encoding="utf-8"))
    except Exception as exc:
        result["errors"].append(f"Source unreadable: {exc}")
        result["status"] = "failed"
        result["rolled_back"] = True
        if owned_service:
            svc.close()
        return result

    if not isinstance(raw, list):
        result["errors"].append("Source is not a JSON list; aborting.")
        result["status"] = "failed"
        result["rolled_back"] = True
        if owned_service:
            svc.close()
        return result

    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            result["skipped"] += 1
            result["errors"].append(f"Item {idx}: not a dict; skipped.")
            continue
        # Validate required fields before import. A record without usable
        # content (or source) cannot be persisted and is skipped, preserving
        # the design requirement to validate imported records.
        content = str(item.get("response", item.get("content", ""))).strip()
        source = str(item.get("agent", item.get("source", "migration"))).strip()
        if not content or not source:
            result["skipped"] += 1
            result["errors"].append(
                f"Item {idx}: missing content or source; skipped."
            )
            continue
        try:
            svc.store(
                category=(item.get("task") or item.get("category") or "legacy")
                .strip()
                .replace("\n", " ")[:200]
                or "legacy",
                content=content,
                source=source,
                confidence=1.0,
                importance=3,
                verification_status="unverified",
                memory_type="episodic",
                project="nexus98",
            )
            result["imported"] += 1
        except Exception as exc:
            result["skipped"] += 1
            result["errors"].append(f"Item {idx}: {exc}")

    result["status"] = "completed"
    result["finished_at"] = _ts()

    if owned_service:
        svc.close()

    return result


def rollback(backup_path: Optional[Path] = None, legacy_path: Optional[Path] = None) -> bool:
    """Restore agent_memory.json from its backup.

    Returns True if the original was restored. Does NOT purge the SQLite
    store; callers may drop the memory DB separately if a full rollback
    is desired.
    """
    src = Path(legacy_path) if legacy_path else LEGACY_PATH
    bak = Path(backup_path) if backup_path else src.with_suffix(src.suffix + ".bak")
    if not bak.exists():
        return False
    shutil.copy2(bak, src)
    return True


def log_result(result: dict, path: Optional[Path] = None) -> None:
    target = Path(path) if path else Path(r"D:\Nexus98\logs\memory_migration.log")
    target.parent.mkdir(parents=True, exist_ok=True)
    line = (
        f"{result.get('finished_at', result.get('started_at'))} | "
        f"status={result['status']} | "
        f"imported={result['imported']} | "
        f"skipped={result['skipped']} | "
        f"backup={result.get('backup_path')} | "
        f"errors={len(result['errors'])}\n"
    )
    with open(target, "a", encoding="utf-8") as f:
        f.write(line)
        for err in result["errors"]:
            f.write(f"    - {err}\n")
