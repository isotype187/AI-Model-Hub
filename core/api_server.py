from flask import Flask, request, jsonify
from datetime import datetime
import uuid

from core.bridge import execute


app = Flask(__name__)



@app.route(
    "/status",
    methods=["GET"]
)
@app.route(
    "/api/status",
    methods=["GET"]
)
def status():

    return jsonify(

        {

            "service":
                "Nexus98 API",

            "status":
                "online",

            "time":
                str(datetime.now())

        }

    )



@app.route(
    "/task",
    methods=["POST"]
)
@app.route(
    "/api/task",
    methods=["POST"]
)
def task():

    data = request.json


    result = execute(
        data
    )


    return jsonify(

        {

            "request_id":
                str(uuid.uuid4()),

            **result

        }

    )



if __name__ == "__main__":

    print(
        "Nexus98 API SERVER STARTED"
    )


    app.run(

        host="127.0.0.1",

        port=8000

    )

