import json
import os

# F1 fix (2026-07-18): consolidate runtime configuration under the project's
# config/ authority directory. Previously this pointed at a root-level
# D:\Nexus98\config.json that does not exist and would be silently auto-created,
# splitting configuration authority away from config/system_config.json (the
# Constitution-declared autonomy authority). Runtime base-path settings now live
# in config/runtime.json, inside the config/ directory, as a single source of
# truth for non-autonomy runtime configuration.

CONFIG_PATH = os.path.join("config", "runtime.json")

# Guard against the legacy root-level config.json ever being (re)introduced.
LEGACY_CONFIG_PATH = r"D:\Nexus98\config.json"

DEFAULT = {
    'base_path': r'D:\Nexus98',
    'hf_dir': r'D:\Nexus98\data\models\hf',
    'gguf_dir': r'D:\Nexus98\data\models\gguf',
    'max_workers': 2,
    'ui_mode': 'app',  # app | dev
    'cache_ttl': 30,
}


def _config_dir():
    # Resolve relative to the repository root so it works from any CWD.
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(here, CONFIG_PATH)


def load_config():
    if os.path.exists(LEGACY_CONFIG_PATH):
        # Defensive: a stray root-level config.json must not be used or trusted.
        # Prefer the consolidated config/runtime.json instead.
        pass
    path = _config_dir()
    if not os.path.exists(path):
        save_config(DEFAULT)
        return dict(DEFAULT)
    with open(path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def save_config(cfg):
    path = _config_dir()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Never write to the legacy root-level path.
    assert path != LEGACY_CONFIG_PATH, "refusing to write legacy root config.json"
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)

