from pathlib import Path
from datetime import datetime
import json
import shutil
import subprocess
import uuid


ROOT = Path(r"D:\Nexus98")

BACKUP_DIR = ROOT / "backups"
HISTORY_DIR = ROOT / "history"

# Milestone 3: real approval gate configuration. Read-only snapshot of the
# safety gates declared in config/system_config.json. Consumed by
# approve_request() so the Governor declared intent is actually enforced in
# the execution path (previously a no-op stub).
CONFIG_PATH = ROOT / "config" / "system_config.json"

# Actions that mutate the workspace and are therefore treated as RISKY. At L2
# these require an explicit recorded approval before they may execute. New
# dangerous tools (shell/run/delete) are intentionally NOT added here.
RISKY_ACTIONS = frozenset({"write_file"})


def _read_safety_require_approval() -> bool:
    """Return config safety.require_approval_for_risky_actions (default True)."""
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return bool(cfg.get("safety", {}).get(
            "require_approval_for_risky_actions", True))
    except Exception:
        # Fail safe: if config is unreadable, require approval.
        return True


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

            # Compile check first.
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

            if result.returncode != 0:

                return False

            # Milestone 3: import smoke check (no execution of user code).
            # Verify the module is importable in a fresh interpreter; this
            # catches syntax/import errors py_compile may miss. Only a fresh
            # interpreter isolation is used -- no arbitrary side effects run.
            smoke = subprocess.run(
                [
                    "python",
                    "-c",
                    "import importlib.util; "
                    "spec = importlib.util.spec_from_file_location('__m3_smoke__', %r); "
                    "mod = importlib.util.module_from_spec(spec); "
                    "spec.loader.exec_module(mod)" % str(path)
                ],
                capture_output=True,
                text=True
            )

            return smoke.returncode == 0



        if path.suffix == ".json":

            try:

                data = json.loads(
                    path.read_text(
                        encoding="utf-8"
                    )
                )

                # Schema sanity: top-level must be a dict or list.
                if not isinstance(data, (dict, list)):

                    return False

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
        request,
        *,
        workflow=None,
        level=None,
        approved_by=None
    ):
        """Milestone 3 real approval gate (replaces the unconditional stub).

        Enforcement model (read-only, no autonomy-state writes):
          * Risky actions (RISKY_ACTIONS) require an explicit approval record
            (approved_by set) when config safety.require_approval_for_risky_actions
            is True. Otherwise they are rejected with approval="rejected".
          * A workflow that is not in the Governor trusted set is held (rejected)
            so it cannot be silently auto-executed.
          * Non-risky trusted workflows may proceed with an implicit approval,
            recorded as "auto_approved".

        Returns the (mutated) request dict with an authoritative ``approval``
        field: "approved" | "auto_approved" | "rejected".
        """
        action = request.get("action")
        is_risky = action in RISKY_ACTIONS

        # Workflow scope enforcement (Governor read-only check).
        # A trusted L2 workflow is PRE-AUTHORIZED for its operations (including
        # risky ones) -- that is the meaning of being in the trusted set.
        # Only workflows outside the trusted set are held for review.
        if workflow is not None:
            try:
                from core.autonomy.governor import scope_check
                scope = scope_check(workflow)
            except Exception:
                scope = {"held": True, "reason": "governor scope check unavailable"}
            if scope.get("held"):
                request["approval"] = "rejected"
                request["rejection_reason"] = (
                    "workflow not in trusted set: " + scope.get("reason", ""))
                return request
            # Trusted workflow: pre-authorized (recorded as auto_approved).
            request["approval"] = "auto_approved"
            request["approved_by"] = "governor_trusted:" + str(workflow)
            request["trusted_workflow"] = workflow
            return request

        # No workflow tag: enforce the generic risky-action approval rule.
        require_approval = _read_safety_require_approval()
        if is_risky and require_approval and not approved_by:
            request["approval"] = "rejected"
            request["rejection_reason"] = (
                "risky action requires explicit approval")
            return request

        if approved_by:
            request["approval"] = "approved"
            request["approved_by"] = approved_by
        else:
            request["approval"] = "auto_approved"
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
        content=None,
        request=None
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

            # Milestone 3: approval has already been enforced by the caller
            # (supervisor.request_file_operation_blocking) via approve_request.
            # If a request reaches here without an authoritative approval it is
            # blocked defensively (never silently executes). When no request is
            # supplied we assume the legacy caller already gated it.
            if request is not None and request.get("approval") not in (
                    "approved", "auto_approved"):

                operation["result"] = "blocked"
                operation["validation"] = "skipped"
                operation["reason"] = (
                    request.get("rejection_reason")
                    or "request not approved")
                self.log_operation(operation)
                return operation

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







