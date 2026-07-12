from datetime import datetime
from pathlib import Path
import json

from core.supervisor import run_task
from core.command import Command


ROOT = Path(r"D:\AI_Model_Hub")

LOG = ROOT / "logs" / "bridge.log"

CONTEXT = ROOT / "config" / "system_context.json"



def load_context():

    if CONTEXT.exists():

        with open(
            CONTEXT,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    return {}



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



def execute(request):

    try:

        command = Command(
            request
        )


        if not command.validate():

            return {

                "status":
                    "error",

                "message":
                    "Invalid command"

            }



        context = load_context()


        enriched_task = f"""
SYSTEM CONTEXT:
{json.dumps(context, indent=2)}

USER REQUEST:
{command.task}
"""


        log(
            f"COMMAND: {command.to_dict()}"
        )


        result = run_task(
            enriched_task
        )


        return {

            "status":
                "complete",

            "command":
                command.command,

            "mode":
                command.mode,

            "response":
                result

        }


    except Exception as e:

        log(
            f"ERROR: {e}"
        )

        return {

            "status":
                "error",

            "message":
                str(e)

        }
