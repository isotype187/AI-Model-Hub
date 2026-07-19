import json
import sys
from pathlib import Path


CONFIG = Path(
    r"D:\Nexus98\config\models.json"
)


def load():

    return json.loads(
        CONFIG.read_text(
            encoding="utf-8-sig"
        )
    )


def choose(task):

    task = task.lower()

    models = load()["models"]

    scored = []

    for model in models:

        score = 0

        for tag in model["tags"]:

            if tag.lower() in task:
                score += model["priority"]

        scored.append(
            (
                score,
                model
            )
        )


    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )


    return scored[0][1]



if __name__ == "__main__":

    if len(sys.argv) < 2:
        print(
            "Usage: python agent_selector.py \"task description\""
        )
        exit()


    result = choose(
        " ".join(sys.argv[1:])
    )


    print("=" * 60)
    print(" AI MODEL SELECTION")
    print("=" * 60)

    print(
        f"Task:\n{ ' '.join(sys.argv[1:]) }\n"
    )

    print(
        f"Selected:\n{result['name']}"
    )

    print(
        f"Ollama:\n{result['ollama']}"
    )

    print(
        f"Category:\n{result['category']}"
    )

