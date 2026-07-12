from flask import Flask, request, jsonify
from core.bridge import execute
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\AI_Model_Hub")

LOG = ROOT / "logs" / "server.log"


app = Flask(__name__)


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


@app.route(
    "/task",
    methods=["POST"]
)
def task():

    data = request.json

    log(
        f"REQUEST: {data}"
    )

    result = execute(
        data
    )

    log(
        "RESPONSE SENT"
    )

    return jsonify(
        result
    )


@app.route(
    "/status",
    methods=["GET"]
)
def status():

    return jsonify(
        {
            "status":
                "AI_Model_Hub online"
        }
    )


if __name__ == "__main__":

    print(
        "AI_Model_Hub Bridge Server Starting"
    )

    app.run(
        host="127.0.0.1",
        port=5050
    )

