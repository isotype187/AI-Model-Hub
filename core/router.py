from pathlib import Path
from datetime import datetime


ROOT = Path(r"D:\AI_Model_Hub")
LOG = ROOT / "logs" / "routing.log"


class TaskRouter:

    def __init__(self):

        self.rules = {

            "architect": [
                "architecture",
                "design",
                "structure",
                "plan",
                "organize",
                "refactor"
            ],

            "coder": [
                "code",
                "write",
                "implement",
                "python",
                "script",
                "function",
                "fix",
                "create"
            ],

            "reviewer": [
                "review",
                "audit",
                "inspect",
                "analyze",
                "check"
            ],

            "tester": [
                "test",
                "verify",
                "validate",
                "debug"
            ],

            "documentation": [
                "document",
                "readme",
                "explain",
                "describe"
            ],

            "researcher": [
                "research",
                "compare",
                "investigate",
                "why"
            ]
        }


    def route(self, task):

        text = task.lower()

        scores = {}

        for agent, words in self.rules.items():

            scores[agent] = sum(
                1
                for word in words
                if word in text
            )


        selected = max(
            scores,
            key=scores.get
        )


        if scores[selected] == 0:

            selected = "researcher"


        self.log(
            f"{task} => {selected}"
        )


        return selected



    def log(self,message):

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


_router = TaskRouter()


def route(task):

    return _router.route(task)
