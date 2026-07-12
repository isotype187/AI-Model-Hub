from pathlib import Path
import os
import subprocess
import json


BASE = Path(__file__).parent
CONFIG = BASE / "config.json"


def load_config():
    with open(CONFIG, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def folder_size(path):
    total = 0
    path = Path(path)

    if not path.exists():
        return 0

    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size

    return round(total / (1024**3), 2)


def scan_storage():
    config = load_config()

    source = config["source_model_path"]
    target = config["target_model_path"]

    print("=== Ollama Storage Report ===")
    print()

    print("Source:")
    print(source)
    print(f"Size: {folder_size(source)} GB")
    print()

    print("Target:")
    print(target)
    print(f"Size: {folder_size(target)} GB")
    print()

    print("Environment:")
    print(
        os.environ.get(
            "OLLAMA_MODELS",
            "Not set"
        )
    )

    print()

    print("Installed Models:")

    result = subprocess.run(
        ["ollama", "list"],
        capture_output=True,
        text=True
    )

    print(result.stdout)


if __name__ == "__main__":
    scan_storage()
