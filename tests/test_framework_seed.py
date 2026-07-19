"""Tests for Phase C first-run store seeding.

Ensures core.frameworks.seed.seed_expected_stores():
  * creates the three expected-empty stores when absent,
  * is idempotent (does not recreate/overwrite existing stores),
  * produces files in each framework canonical shape.
"""
from pathlib import Path

from core.frameworks.seed import seed_expected_stores

STORES = {
    "workspace": Path("data/workspace.json"),
    "reviews": Path("data/reviews.json"),
    "extensions": Path("data/extensions.json"),
}


def _teardown():
    for p in STORES.values():
        if p.exists():
            p.unlink()


def test_seed_creates_missing_stores():
    _teardown()
    created = seed_expected_stores()
    assert set(created) == {"workspace", "reviews", "extensions"}
    for p in STORES.values():
        assert p.exists(), f"{p} should exist after seeding"


def test_seed_is_idempotent():
    # First call may create; ensure a second call creates nothing and data is
    # preserved (no clobber).
    seed_expected_stores()
    before = {name: p.read_text(encoding="utf-8") for name, p in STORES.items()}
    created = seed_expected_stores()
    assert created == []
    after = {name: p.read_text(encoding="utf-8") for name, p in STORES.items()}
    assert before == after


def test_seeded_shapes_are_canonical():
    seed_expected_stores()
    import json
    ws = json.loads(STORES["workspace"].read_text(encoding="utf-8"))
    assert ws.get("version") == 1 and "projects" in ws and "components" in ws
    assert json.loads(STORES["reviews"].read_text(encoding="utf-8")) == {}
    assert json.loads(STORES["extensions"].read_text(encoding="utf-8")) == {}
