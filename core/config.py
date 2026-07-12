import json
import os

CONFIG_PATH = r'D:\AI_Model_Hub\config.json'

DEFAULT = {
    'base_path': r'D:\AI_Model_Hub',
    'hf_dir': r'D:\AI_Model_Hub\data\models\hf',
    'gguf_dir': r'D:\AI_Model_Hub\data\models\gguf',
    'max_workers': 2,
    'ui_mode': 'app',  # app | dev
    'cache_ttl': 30
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT)
        return DEFAULT

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)

    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)
