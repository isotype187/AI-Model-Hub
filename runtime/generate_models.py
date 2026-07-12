import sys
import json

sys.path.insert(
    0,
    r"D:\AI_Model_Hub"
)

from core.catalog import sync_catalog


OUTPUT = r"D:\AI_Model_Hub\config\models.json"


def generate():
    models = sync_catalog(True)

    data = {
        "project": "AI_Model_Hub",
        "version": "1.0.0",
        "models": models
    }

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            indent=4
        )

    print(f"Generated: {OUTPUT}")
    print(f"Models: {len(models)}")


if __name__ == "__main__":
    generate()
