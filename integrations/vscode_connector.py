import requests
import json
import uuid
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\Nexus98")

API = "http://127.0.0.1:8000"

LOG = ROOT / "logs" / "hybrid_connector.log"


session = requests.Session()


def log(message):

    LOG.parent.mkdir(
        exist_ok=True
    )

    with open(
        LOG,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            f"{datetime.now()} | {message}\n"
        )


def status():

    try:

        r = session.get(
            f"{API}/status",
            timeout=10
        )

        return r.json()

    except Exception as e:

        return {
            "status":"offline",
            "error":str(e)
        }



def send_task(task, mode="hybrid"):

    request_id = str(
        uuid.uuid4()
    )


    payload = {

        "request_id": request_id,

        "mode": mode,

        "task": task

    }


    log(
        f"SENDING {request_id}: {task}"
    )


    response = session.post(

        f"{API}/task",

        json=payload,

        timeout=600

    )


    result = response.json()


    log(
        f"COMPLETE {request_id}"
    )


    return result



if __name__ == "__main__":


    print(
        json.dumps(
            status(),
            indent=2
        )
    )


    result = send_task(

        "Explain the next development phase for AI_Model_Hub",

        "hybrid"

    )


    print(

        json.dumps(

            result,

            indent=2

        )

    )

