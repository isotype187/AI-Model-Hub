from pathlib import Path
import json
import time
from datetime import datetime


ROOT = Path(r"D:\Nexus98")
REQUESTS = ROOT / "bridge" / "requests"
RESPONSES = ROOT / "bridge" / "responses"


def log(msg):
    print(f"[VS CODE BRIDGE] {msg}")


def process_request(file):

    try:
        with open(file, "r", encoding="utf-8") as f:
            request = json.load(f)

        task_id = request.get(
            "id",
            file.stem
        )

        task = request.get(
            "task",
            ""
        )

        log(f"Received task {task_id}")
        log(task)

        response = {
            "id": task_id,
            "status": "received",
            "timestamp": str(datetime.now()),
            "message": "VS Code bridge received request successfully"
        }

        output = RESPONSES / f"{task_id}_result.json"

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

        file.unlink()

        log(f"Completed {task_id}")

    except Exception as e:

        log(
            f"ERROR: {e}"
        )


def main():

    REQUESTS.mkdir(
        exist_ok=True
    )

    RESPONSES.mkdir(
        exist_ok=True
    )

    log("Listener online")

    while True:

        files = list(
            REQUESTS.glob("*.json")
        )

        for file in files:
            process_request(file)

        time.sleep(2)


if __name__ == "__main__":
    main()

