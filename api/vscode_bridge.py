
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify
import logging
import requests
import sys


ROOT = Path(r"D:\AI_Model_Hub")

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT)
    )


from core.supervisor import run_task


app = Flask(__name__)


LOG = ROOT / "logs" / "vscode_bridge.log"

logging.basicConfig(
    filename=str(LOG),
    level=logging.INFO
)



def log(message):

    logging.info(
        f"{datetime.now()} | {message}"
    )





def ollama_chat(model, prompt):

    try:

        response = requests.post(
            "http://127.0.0.1:11434/api/chat",
            json={
                "model": model,
                "messages":[
                    {
                        "role":"user",
                        "content":prompt
                    }
                ],
                "stream":False
            },
            timeout=180
        )

        data = response.json()

        return (
            data
            .get("message", {})
            .get("content", "")
        )

    except Exception as e:

        log(
            f"OLLAMA CHAT ERROR {e}"
        )

        return f"Ollama error: {e}"


def ollama_models():

    try:

        response = requests.get(
            "http://127.0.0.1:11434/api/tags",
            timeout=10
        )

        data = response.json()

        return data.get(
            "models",
            []
        )

    except Exception as e:

        log(
            f"OLLAMA MODEL ERROR {e}"
        )

        return []



@app.route("/health", methods=["GET"])
def health():

    return jsonify(
        {
            "status":"online",
            "service":"AI Hub Bridge"
        }
    )



@app.route("/v1/models", methods=["GET"])
def models():

    discovered = []

    for model in ollama_models():

        discovered.append(
            {
                "id":model.get("name"),
                "object":"model",
                "owned_by":"AI Hub Ollama",
                "size":model.get("size"),
                "modified":model.get("modified_at")
            }
        )


    return jsonify(
        {
            "object":"list",
            "data":discovered
        }
    )



@app.route("/v1/chat/completions", methods=["POST"])
def chat():

    data = request.json or {}

    messages = data.get(
        "messages",
        []
    )


    prompt = ""

    for message in messages:

        prompt += (
            message.get("role","")
            +
            ": "
            +
            message.get("content","")
            +
            "\n"
        )


    log(
        "REQUEST " + prompt[:500]
    )


    result = run_task(
        prompt
    )


    selected_model = "qwen3-coder:30b"

    if isinstance(result,dict):

        selected_model = (
            result.get("model")
            or selected_model
        )

    output = ollama_chat(
        selected_model,
        prompt
    )

    selected = {
        "model": selected_model
    }



    log(
        "MODEL RESULT " + str(selected)
    )


    return jsonify(
        {
            "id":"aihub-response",
            "object":"chat.completion",
            "choices":[
                {
                    "index":0,
                    "message":
                    {
                        "role":"assistant",
                        "content":output
                    },
                    "finish_reason":"stop"
                }
            ]
        }
    )



if __name__=="__main__":

    app.run(
        host="127.0.0.1",
        port=8000
    )

