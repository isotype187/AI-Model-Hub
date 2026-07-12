import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime


ROOT = Path(r"D:\AI_Model_Hub")

CONFIG = ROOT / "config" / "models.json"

LOG = ROOT / "logs" / "routing.log"


def load_models():

    return json.loads(
        CONFIG.read_text(
            encoding="utf-8-sig"
        )
    )["models"]



def select_model(task):

    task = task.lower()

    best = None
    score_best = -1


    for model in load_models():

        score = 0

        for tag in model.get("tags", []):

            if tag.lower() in task:
                score += model.get(
                    "priority",
                    1
                )


        if score > score_best:

            score_best = score
            best = model


    if best is None:

        for model in load_models():

            if model["category"] == "general":
                best = model
                break


    return best



def log(entry):

    LOG.parent.mkdir(
        exist_ok=True
    )

    with open(
        LOG,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            entry + "\n"
        )



def run():

    if len(sys.argv) < 2:

        print(
            'Usage: python agent_runner.py "your task"'
        )

        return


    task = " ".join(
        sys.argv[1:]
    )


    model = select_model(task)


    print("=" * 60)
    print(" AI MODEL HUB AGENT RUNNER")
    print("=" * 60)

    print(
        f"Task:\n{task}\n"
    )

    print(
        f"Selected Model:\n{model['name']}"
    )

    print(
        f"Ollama ID:\n{model['ollama']}"
    )


    log(
        f"{datetime.now()} | {model['ollama']} | {task}"
    )


    print("")
    print("Launching Ollama...")


    subprocess.run(
        [
            "ollama",
            "run",
            model["ollama"],
            task
        ]
    )



if __name__ == "__main__":
    run()
