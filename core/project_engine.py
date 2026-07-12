from pathlib import Path
from datetime import datetime
import json
import shutil
import subprocess
import uuid


ROOT = Path(r"D:\AI_Model_Hub")

BACKUP_DIR = ROOT / "backups"
HISTORY_DIR = ROOT / "history"


class ProjectEngine:


    def __init__(self):

        BACKUP_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        HISTORY_DIR.mkdir(
            parents=True,
            exist_ok=True
        )



    def timestamp(self):

        return datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )



    def log_change(
        self,
        action,
        file,
        result
    ):

        record = {

            "timestamp":
                datetime.now().isoformat(),

            "action":
                action,

            "file":
                str(file),

            "result":
                result

        }


        output = HISTORY_DIR / (
            self.timestamp()
            + "_change.json"
        )


        with open(
            output,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                record,
                f,
                indent=4
            )



    def read_file(
        self,
        file
    ):

        path = ROOT / file

        return path.read_text(
            encoding="utf-8"
        )



    def backup_file(
        self,
        file
    ):

        source = ROOT / file


        if not source.exists():

            return None


        backup = BACKUP_DIR / (
            source.name
            + "."
            + self.timestamp()
            + ".bak"
        )


        shutil.copy2(
            source,
            backup
        )


        return backup



    def write_file(
        self,
        file,
        content
    ):

        backup = self.backup_file(
            file
        )


        target = ROOT / file


        target.write_text(
            content,
            encoding="utf-8"
        )


        valid = self.validate_file(
            file
        )


        if not valid:

            if backup:

                shutil.copy2(
                    backup,
                    target
                )

            self.log_change(
                "write_file",
                file,
                "rolled_back_validation_failure"
            )

            return False



        self.log_change(
            "write_file",
            file,
            "success"
        )


        return True



    def validate_file(
        self,
        file
    ):

        path = ROOT / file


        if path.suffix == ".py":

            result = subprocess.run(
                [
                    "python",
                    "-m",
                    "py_compile",
                    str(path)
                ],
                capture_output=True,
                text=True
            )


            return result.returncode == 0



        if path.suffix == ".json":

            try:

                json.loads(
                    path.read_text(
                        encoding="utf-8"
                    )
                )

                return True

            except Exception:

                return False



        return True

    def operation_id(self):

        return (
            self.timestamp()
            + "_"
            + uuid.uuid4().hex[:8]
        )


    def create_request(
        self,
        agent,
        action,
        file,
        reason
    ):

        request_id = self.operation_id()

        request = {

            "request_id":
                request_id,

            "agent":
                agent,

            "action":
                action,

            "file":
                str(file),

            "reason":
                reason,

            "approval":
                "pending"

        }


        output = HISTORY_DIR / (
            request_id
            + "_request.json"
        )


        with open(
            output,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                request,
                f,
                indent=4
            )


        return request



    def approve_request(
        self,
        request
    ):

        request["approval"] = "approved"

        return request
    def history_path(
        self,
        category,
        identifier
    ):

        folder = HISTORY_DIR / category

        folder.mkdir(
            parents=True,
            exist_ok=True
        )


        return folder / (
            identifier
            + ".json"
        )



    def save_history_record(
        self,
        category,
        identifier,
        data
    ):

        output = self.history_path(
            category,
            identifier
        )


        with open(
            output,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4
            )


        return output



    def log_operation(
        self,
        operation
    ):

        operation_dir = HISTORY_DIR / "operations"

        operation_dir.mkdir(
            parents=True,
            exist_ok=True
        )


        output = operation_dir / (
            operation["operation_id"]
            + ".json"
        )


        with open(
            output,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                operation,
                f,
                indent=4
            )



    # AUTO_OPERATION_LOGGING
    def build_operation_record(
        self,
        operation_id,
        request_id=None,
        agent=None,
        action=None,
        file=None,
        result=None,
        validation=None,
        backup_created=False
    ):

        return {

            "operation_id":
                operation_id,

            "request_id":
                request_id,

            "agent":
                agent,

            "action":
                action,

            "file":
                str(file),

            "backup_created":
                backup_created,

            "validation":
                validation,

            "result":
                result,

            "timestamp":
                datetime.now().isoformat()

        }



    def execute_operation(
        self,
        action,
        file,
        content=None
    ):

        operation_id = self.operation_id()


        operation = {

            "operation_id":
                operation_id,

            "action":
                action,

            "file":
                str(file),

            "timestamp":
                datetime.now().isoformat()

        }


        if action == "write_file":

            success = self.write_file(
                file,
                content
            )


            operation["result"] = (
                "success"
                if success
                else "failed"
            )

            operation["validation"] = (
                "passed"
                if success
                else "failed"
            )


            self.log_operation(
                operation
            )


            return operation



        operation["result"] = "unsupported_operation"

        self.log_operation(
            operation
        )


        return operation


    def restore_backup(
        self,
        backup,
        destination
    ):

        shutil.copy2(
            backup,
            ROOT / destination
        )

    
    def status(self):

        return {

            "engine":
                "online",

            "backup_directory":
                str(BACKUP_DIR),

            "history_directory":
                str(HISTORY_DIR)

        }



if __name__ == "__main__":

    engine = ProjectEngine()

    print(
        "Project Engine online"
    )






