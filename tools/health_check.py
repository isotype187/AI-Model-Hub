import os
import subprocess
from pathlib import Path

print("=" * 60)
print(" AI MODEL HUB ADVANCED HEALTH CHECK")
print("=" * 60)
print()

continue_config = Path(
    r"C:\Users\isoty\.continue\config.yaml"
)

required_models = [
    "qwen3-coder:30b",
    "qwen3:30b",
    "deepseek-r1:32b",
    "qwen2.5-coder:14b",
    "nomic-embed-text:latest"
]


def result(name, ok, detail=""):
    status = "[OK]" if ok else "[FAIL]"
    print(f"{status} {name}")
    if detail:
        print(f"      {detail}")


print("=== CONTINUE CONFIG ===")

result(
    "Continue config exists",
    continue_config.exists(),
    str(continue_config)
)

config_text = ""

if continue_config.exists():
    config_text = continue_config.read_text(
        encoding="utf-8-sig"
    )

    result(
        "Continue config readable",
        len(config_text) > 0,
        f"{len(config_text)} bytes"
    )

print()

print("=== OLLAMA MODELS ===")

try:
    output = subprocess.check_output(
        ["ollama", "list"],
        text=True
    )

    result(
        "Ollama available",
        True
    )

    for model in required_models:
        result(
            f"Model {model}",
            model in output
        )

except Exception as e:
    result(
        "Ollama available",
        False,
        str(e)
    )


print()

print("=== CONFIG MODEL CHECK ===")

for model in required_models:
    result(
        f"Continue references {model}",
        model in config_text
    )


print()

print("=== STORAGE ===")

junction = Path(
    r"C:\Users\isoty\.ollama\models"
)

target = Path(
    r"D:\AI\Models\ollama"
)

result(
    "Ollama junction exists",
    junction.exists()
)

result(
    "D drive model storage exists",
    target.exists()
)

print()

print("=" * 60)
print(" ADVANCED HEALTH CHECK COMPLETE")
print("=" * 60)
