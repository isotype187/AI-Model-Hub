"""Phase 3: Capability Awareness (boot-time discovery) tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.capability_awareness import CapabilityDiscoverer, CapabilitySnapshot


def test_discover_returns_snapshot():
    disc = CapabilityDiscoverer()
    snap = disc.discover()
    assert isinstance(snap, CapabilitySnapshot)
    assert "tools" in snap.to_dict()


def test_tools_discovered_from_existing_modules():
    disc = CapabilityDiscoverer()
    snap = disc.discover()
    # The tool registry should have seeded at least file_tools + git_tools.
    flat = [t for v in snap.tools.values() for t in v]
    ids = [t["id"] for t in flat]
    assert any("file_tools" in i for i in ids)
    assert any("git_tools" in i for i in ids)


def test_models_discovered_from_config():
    disc = CapabilityDiscoverer()
    snap = disc.discover()
    assert snap.models.get("total", 0) >= 1


def test_config_loaded():
    disc = CapabilityDiscoverer()
    snap = disc.discover()
    assert "base_path" in snap.config


def test_report_line_informative():
    disc = CapabilityDiscoverer()
    line = disc.report_line()
    assert "tools" in line and "models" in line


def test_limitation_recorded_when_models_missing():
    # Force models to None to simulate no model registry.
    disc = CapabilityDiscoverer(models=None, models_explicit=True)
    snap = disc.discover()
    assert any("model registry unavailable" in lim.lower() for lim in snap.limitations)


