"""F1 config-authority regression tests.

These guard the single-source-of-truth consolidation:
- Runtime config lives in config/runtime.json (inside the config authority dir).
- The legacy root-level D:/Nexus98/config.json must NEVER be created or trusted.

No production code is modified; these are read/create assertions only.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(autouse=True)
def _no_legacy_config():
    """Ensure the legacy root config.json does not exist before/after."""
    import core.config as cfg_mod
    if os.path.exists(cfg_mod.LEGACY_CONFIG_PATH):
        pytest.fail("legacy config already present: " + cfg_mod.LEGACY_CONFIG_PATH)
    yield
    if os.path.exists(cfg_mod.LEGACY_CONFIG_PATH):
        try:
            os.remove(cfg_mod.LEGACY_CONFIG_PATH)
        except OSError:
            pass
        pytest.fail("load_config created legacy config: " + cfg_mod.LEGACY_CONFIG_PATH)


def test_core_config_imports():
    import core.config as cfg_mod
    assert cfg_mod.CONFIG_PATH.endswith("runtime.json")
    assert "config" in cfg_mod.CONFIG_PATH
    here = os.path.dirname(os.path.dirname(os.path.abspath(cfg_mod.__file__)))
    assert os.path.exists(os.path.join(here, cfg_mod.CONFIG_PATH))


def test_load_config_resolves_from_config_dir():
    import core.config as cfg_mod
    loaded = cfg_mod.load_config()
    assert loaded["base_path"] == "D:\\Nexus98"
    assert loaded["hf_dir"] == "D:\\Nexus98\\data\\models\\hf"
    assert not os.path.exists(cfg_mod.LEGACY_CONFIG_PATH)


def test_save_config_refuses_legacy_root_path():
    """save_config must refuse to write the legacy root-level config.json."""
    import core.config as cfg_mod
    real = cfg_mod.CONFIG_PATH
    try:
        cfg_mod.CONFIG_PATH = cfg_mod.LEGACY_CONFIG_PATH
        with pytest.raises(AssertionError):
            cfg_mod.save_config({"legacy": True})
    finally:
        cfg_mod.CONFIG_PATH = real
    assert not os.path.exists(cfg_mod.LEGACY_CONFIG_PATH)


def test_verify_environment_succeeds():
    import core.boot as boot
    import core.config as cfg_mod
    assert boot.verify_environment() is True
    assert not os.path.exists(cfg_mod.LEGACY_CONFIG_PATH)


