"""Extension / Plugin framework tests (temp storage)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.frameworks.extension import ExtensionRegistry, LIFECYCLE


@pytest.fixture
def reg(tmp_path):
    r = ExtensionRegistry(tmp_path / "extensions.json")
    yield r
    r.close()


def test_register_and_discover(reg):
    ext = reg.register("Model Router+", "1.0", capabilities=["model_routing"],
                       hooks=["on_startup"], description="better routing")
    assert ext.state == "registered"
    found = reg.discover(capability="model_routing")
    assert found and found[0].name == "Model Router+"


def test_duplicate_register_returns_same(reg):
    a = reg.register("X", "1.0")
    b = reg.register("X", "1.0")
    assert a.ext_id == b.ext_id
    assert len(reg.list_extensions()) == 1


def test_lifecycle_enable_activate_disable(reg):
    ext = reg.register("Y", "2.0")
    assert reg.enable(ext.ext_id)
    assert reg.activate(ext.ext_id)
    assert reg.get(ext.ext_id).state == "active"
    assert reg.disable(ext.ext_id)
    assert reg.get(ext.ext_id).state == "disabled"


def test_activate_requires_enabled(reg):
    ext = reg.register("Z", "1.0")  # registered, not enabled
    assert reg.activate(ext.ext_id) is False
    assert reg.get(ext.ext_id).state == "registered"


def test_invalid_lifecycle_state_raises(reg):
    ext = reg.register("W", "1.0")
    with pytest.raises(ValueError):
        reg.set_state(ext.ext_id, "bogus")


def test_capability_summary(reg):
    reg.register("A", "1.0", capabilities=["x"])
    reg.register("B", "1.0", capabilities=["x", "y"])
    s = reg.capability_summary()
    assert "A" in s["x"] and "B" in s["x"] and "B" in s["y"]


def test_persists_across_reload(tmp_path):
    p = tmp_path / "extensions.json"
    r = ExtensionRegistry(p)
    ext = r.register("Persisted", "1.0", capabilities=["c"])
    r.activate_after_enable = None
    r.enable(ext.ext_id)
    r.close()
    r2 = ExtensionRegistry(p)
    assert r2.get(ext.ext_id).state in ("enabled", "active")
    r2.close()
