import os

# F1 fix (2026-07-18): verify_environment now reads runtime configuration from
# the consolidated config/runtime.json (see core/config.py) instead of the
# legacy root-level D:\Nexus98\config.json. This keeps environment setup aligned
# with the single config/ authority and prevents divergent auto-created config.

from core.config import load_config


def verify_environment():
    cfg = load_config()

    paths = [
        cfg['base_path'],
        cfg['hf_dir'],
        cfg['gguf_dir'],
    ]

    for p in paths:
        os.makedirs(p, exist_ok=True)

    # Phase C: seed expected-empty framework stores on first run so the boot
    # validation report reads healthy. Idempotent; never overwrites data.
    try:
        from core.frameworks.seed import seed_expected_stores
        seed_expected_stores()
    except Exception:
        # Best-effort setup; never break startup over store seeding.
        pass

    return True
