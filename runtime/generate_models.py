import sys
import json

sys.path.insert(
    0,
    r"D:\Nexus98"
)

from core.catalog import sync_catalog


OUTPUT = r"D:\Nexus98\config\models.json"


def generate():
    models = sync_catalog(True)

    data = {
        "project": "Nexus98",
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

