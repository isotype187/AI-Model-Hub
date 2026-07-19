"""Phase C - first-run store seeding (read-only intent, idempotent).

Nexus98 framework stores start as *expected-empty* files:
  * data/workspace.json   (WorkspaceReality)
  * data/reviews.json     (ReviewSystem)
  * data/extensions.json  (ExtensionRegistry)

Each owning framework degrades gracefully to an empty default when its file is
absent, so a missing file is an expected warning, not a defect. This module
seeds those three stores with their framework canonical empty structure on
first run so the boot-validation report reads healthy and the on-disk layout is
explicit.

Design rules:
  * Idempotent: only writes when the file is missing. Never overwrites data.
  * Uses each framework own load/save so the on-disk shape stays canonical.
  * No autonomy change, no config write, no execution. Setup only.
  * Authority boundaries preserved: startup state setup, not Governor/integration.
"""
from __future__ import annotations

from typing import List

from core.frameworks.workspace import WorkspaceReality
from core.frameworks.review import ReviewSystem
from core.frameworks.extension import ExtensionRegistry


_SEEDERS = (
    ("workspace", WorkspaceReality),
    ("reviews", ReviewSystem),
    ("extensions", ExtensionRegistry),
)


def seed_expected_stores() -> List[str]:
    """Create the expected-empty stores if absent.

    Returns store names created this call (empty if all already existed).
    Safe to call repeatedly; never clobbers existing data.
    """
    created: List[str] = []
    for name, cls in _SEEDERS:
        try:
            inst = cls()
            if not inst.path.exists():
                inst.save()
                created.append(name)
        except Exception:
            continue
    return created
