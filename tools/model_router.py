import json
import subprocess
from pathlib import Path


ROOT = Path(r"D:\AI_Model_Hub")

CONFIG = ROOT / "config" / "models.json"


def ollama_models():

    output = subprocess.check_output(
        ["ollama", "list"],
        text=True
    )

    return output


def load():

    return json.loads(
        CONFIG.read_text(
            encoding="utf-8-sig"
        )
    )


def scan():

    installed = ollama_models()

    data = load()

    print("=" * 60)
    print(" AI MODEL ROUTER")
    print("=" * 60)

    for model in data["models"]:

        name = model["name"]
        tag = model["ollama"]

        if tag in installed:
            status = "READY"
        else:
            status = "MISSING"

        print(
            f"{status:8} | {name:25} | {tag}"
        )


if __name__ == "__main__":
    scan()
