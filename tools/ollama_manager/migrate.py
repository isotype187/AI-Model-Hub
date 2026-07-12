from pathlib import Path
import json
import shutil
import subprocess
import os
import time


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


def stop_ollama():
    print("[*] Stopping Ollama...")

    subprocess.run(
        [
            "powershell",
            "-Command",
            "Stop-Process -Name ollama -Force -ErrorAction SilentlyContinue"
        ],
        capture_output=True
    )

    time.sleep(3)


def check_space(destination):
    drive = Path(destination).drive

    usage = shutil.disk_usage(drive + "\\")

    free = usage.free / (1024**3)

    print(f"[*] Free space on {drive}: {free:.2f} GB")

    return free


def prepare_migration():
    config = load_config()

    source = Path(config["source_model_path"])
    target = Path(config["target_model_path"])

    print("=== Ollama Migration Preview ===")
    print()

    print("Source:")
    print(source)

    print(f"Size: {folder_size(source)} GB")
    print()

    print("Destination:")
    print(target)

    print(f"Current size: {folder_size(target)} GB")
    print()

    required = folder_size(source)

    free = check_space(target)

    print()

    if free < required + 5:
        print("[ERROR] Not enough free space.")
        return

    print("[READY]")
    print("Migration can proceed.")
    print()
    print("No files were changed.")


if __name__ == "__main__":
    prepare_migration()
