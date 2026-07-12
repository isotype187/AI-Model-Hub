from datetime import datetime


class Command:

    def __init__(
        self,
        data
    ):

        self.raw = data or {}

        self.command = (
            self.raw.get(
                "command",
                "ask"
            )
        )

        self.mode = (
            self.raw.get(
                "mode",
                "normal"
            )
        )

        self.task = (
            self.raw.get(
                "task",
                ""
            )
        )

        self.created = (
            datetime.now()
            .isoformat()
        )


    def to_dict(self):

        return {

            "command":
                self.command,

            "mode":
                self.mode,

            "task":
                self.task,

            "created":
                self.created
        }


    def validate(self):

        if not self.task:

            return False

        return True
