import os
from core.config import load_config


def verify_environment():
    cfg = load_config()

    paths = [
        cfg['base_path'],
        cfg['hf_dir'],
        cfg['gguf_dir']
    ]

    for p in paths:
        os.makedirs(p, exist_ok=True)

    return True
