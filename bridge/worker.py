from pathlib import Path
from datetime import datetime
import json
import time


ROOT = Path(r"D:\Nexus98")

REQUEST_DIR = ROOT / "bridge" / "requests"
RESPONSE_DIR = ROOT / "bridge" / "responses"
LOG_FILE = ROOT / "logs" / "vscode_worker.log"


def log(message):

    LOG_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        LOG_FILE,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            f"{datetime.now()} | {message}\n"
        )


def process_task(file):

    with open(
        file,
        "r",
        encoding="utf-8"
    ) as f:

        task = json.load(f)


    log(
        f"Processing task {task['task_id']}"
    )


    response = {

        "task_id":
            task["task_id"],

        "completed":
            datetime.now().isoformat(),

        "status":
            "completed",

        "result":
            (
                "VS Code bridge worker received task:\n\n"
                + task["instructions"]
            )

    }


    output = RESPONSE_DIR / f"{task['task_id']}.json"


    with open(
        output,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            response,
            f,
            indent=4
        )


    log(
        f"Response written {output.name}"
    )


    file.unlink()


def main():

    REQUEST_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    RESPONSE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


    log(
        "VS Code bridge worker started"
    )


    while True:

        for file in REQUEST_DIR.glob("*.json"):

            try:

                process_task(file)

            except Exception as e:

                log(
                    f"ERROR {e}"
                )


        time.sleep(1)


if __name__ == "__main__":

    main()

