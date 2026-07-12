from flask import Flask, request, jsonify
import datetime
import traceback
import re
import ast

from core.supervisor import run_task

app = Flask(__name__)

LOG_FILE = "logs/bridge_api.log"


def log(message):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(
            f"[{datetime.datetime.now()}] {message}\n"
        )


def clean_text(text):

    if text is None:
        return ""

    text = str(text)

    # Remove ANSI terminal escape sequences
    text = re.sub(
        r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])",
        "",
        text
    )

    return text.strip()



def extract_output(result):

    if isinstance(result, dict):

        if "output" in result:
            return result["output"]

        return str(result)


    try:

        parsed = ast.literal_eval(str(result))

        if isinstance(parsed, dict) and "output" in parsed:
            return parsed["output"]

    except Exception:
        pass


    return result



@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "name": "AI Model Hub Bridge",
        "status": "online",
        "time": str(datetime.datetime.now())
    })



@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():

    try:

        data = request.json or {}

        messages = data.get(
            "messages",
            []
        )


        prompt_parts = []

        for message in messages:

            content = message.get(
                "content",
                ""
            )

            prompt_parts.append(
                str(content)
            )


        prompt = "\n".join(prompt_parts)


        log(
            "REQUEST:\n" + prompt
        )


        raw_result = run_task(
            prompt
        )


        output = extract_output(
            raw_result
        )


        output = clean_text(
            output
        )


        log(
            "OUTPUT:\n" + output[:500]
        )


        return jsonify({

            "id": "aihub-chat-response",

            "object": "chat.completion",

            "choices": [

                {

                    "index": 0,

                    "message": {

                        "role": "assistant",

                        "content": clean_text(output)

                    },

                    "finish_reason": "stop"

                }

            ]

        })


    except Exception:

        error = traceback.format_exc()

        log(error)

        return jsonify({
            "error": error
        }),500



@app.route("/task", methods=["POST"])
def task():

    try:

        data = request.json or {}

        result = run_task(
            data.get("task","")
        )

        return jsonify({
            "success": True,
            "result": clean_text(result)
        })

    except Exception:

        error = traceback.format_exc()

        log(error)

        return jsonify({
            "success": False,
            "error": error
        }),500



if __name__ == "__main__":

    log("Bridge starting")

    app.run(
        host="127.0.0.1",
        port=5050,
        debug=False
    )

