import json
from pathlib import Path


class Memory:

    def __init__(self):

        self.path = Path(
            "agent_memory.json"
        )

        if not self.path.exists():
            self.path.write_text(
                json.dumps([]),
                encoding="utf-8"
            )


    def save(self, item):

        data = json.loads(
            self.path.read_text(
                encoding="utf-8"
            )
        )

        data.append(item)

        self.path.write_text(
            json.dumps(
                data,
                indent=4
            ),
            encoding="utf-8"
        )


    def load(self):

        return json.loads(
            self.path.read_text(
                encoding="utf-8"
            )
        )
