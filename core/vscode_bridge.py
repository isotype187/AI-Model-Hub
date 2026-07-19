from pathlib import Path
from datetime import datetime
import json
import uuid


ROOT = Path(r"D:\Nexus98")

REQUEST_DIR = ROOT / "bridge" / "requests"
RESPONSE_DIR = ROOT / "bridge" / "responses"
LOG_FILE = ROOT / "logs" / "vscode_bridge.log"



class VSCodeBridge:


    def __init__(self):

        REQUEST_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        RESPONSE_DIR.mkdir(
            parents=True,
            exist_ok=True
        )



    def log(self, message):

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



    def create_task(
        self,
        title,
        instructions,
        rules=None
    ):

        task_id = str(uuid.uuid4())


        payload = {

            "task_id": task_id,

            "created":
                datetime.now().isoformat(),

            "title":
                title,

            "instructions":
                instructions,

            "rules":
                rules or [],

            "approval_required":
                True,

            "status":
                "waiting"

        }


        file = REQUEST_DIR / f"{task_id}.json"


        with open(
            file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                payload,
                f,
                indent=4
            )


        self.log(
            f"TASK CREATED {task_id}"
        )


        return payload



    def check_response(
        self,
        task_id
    ):

        file = RESPONSE_DIR / f"{task_id}.json"


        if not file.exists():

            return None


        with open(
            file,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)



    def status(self):

        return {

            "requests":
                len(
                    list(
                        REQUEST_DIR.glob("*.json")
                    )
                ),

            "responses":
                len(
                    list(
                        RESPONSE_DIR.glob("*.json")
                    )
                ),

            "online":
                True

        }



if __name__ == "__main__":

    bridge = VSCodeBridge()

    print(
        json.dumps(
            bridge.status(),
            indent=4
        )
    )

