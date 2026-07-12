from pathlib import Path
from datetime import datetime
import re
import asyncio
import uuid

from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from core.router import route
from core.identity import IDENTITY
from core.orchestrator import Orchestrator
from core.vscode_bridge import VSCodeBridge
from core.project_engine import ProjectEngine


ROOT = Path(r"D:\AI_Model_Hub")

LOG = ROOT / "logs" / "supervisor.log"


bridge = VSCodeBridge()
engine = ProjectEngine()

_orchestrator = None



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



def clean_output(text):

    if text is None:

        return ""

    text = str(text)

    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL
    )

    return text.strip()



def engine_status():

    status = engine.status()

    log(
        f"ENGINE STATUS {status}"
    )

    return status



def report_engine_status(status):

    if status.get("engine") == "online":

        return [
            "Project Engine online",
            "Backup system ready",
            "History logging ready"
        ]

    return [
        "Project Engine unavailable"
    ]



def execute_engine_operation(
    action,
    file,
    content=None
):

    log(
        f"ENGINE OPERATION REQUEST {action} {file}"
    )


    result = engine.execute_operation(
        action,
        file,
        content
    )


    log(
        f"ENGINE OPERATION RESULT {result}"
    )


    return result








def build_task_plan(
    goal,
    steps
):

    return {

        "plan_id":
            datetime.now().strftime("%Y%m%d_%H%M%S_")
            + str(uuid.uuid4())[:8],

        "goal":
            goal,

        "steps":
            steps,

        "status":
            "pending"

    }



def validate_task_plan(
    plan
):

    if not plan:

        return False


    required = [

        "plan_id",
        "goal",
        "steps",
        "status"

    ]


    for field in required:

        if field not in plan:

            return False



    if not isinstance(
        plan["steps"],
        list
    ):

        return False



    return len(plan["steps"]) > 0




def translate_task_step(
    step,
    goal
):

    if not step:

        return None



    step_lower = step.lower()



    if (
        "create" in step_lower
        or "write" in step_lower
        or "generate" in step_lower
    ):

        return {

            "action":
                "write_file",

            "file":
                "task_output.txt",

            "reason":
                goal,

            "content":
                step

        }



    if "validate" in step_lower:

        return {

            "action":
                "validate_file",

            "file":
                "task_output.txt",

            "reason":
                goal

        }



    return {

        "action":
            "unsupported",

        "step":
            step

    }



def convert_plan_step_to_action_proposal(
    plan,
    step_index,
    agent="planner"
):

    if not validate_task_plan(
        plan
    ):

        return None



    if step_index < 0 or step_index >= len(plan["steps"]):

        return None



    translated = translate_task_step(
        plan["steps"][step_index],
        plan["goal"]
    )



    if translated["action"] == "unsupported":

        return None



    return build_agent_proposal(
        agent,
        translated["action"],
        translated["file"],
        translated["reason"],
        translated.get("content")
    )



def convert_plan_to_action_proposals(
    plan,
    agent="planner"
):

    proposals = []


    for index in range(
        len(plan["steps"])
    ):

        proposal = convert_plan_step_to_action_proposal(
            plan,
            index,
            agent
        )


        if proposal:

            proposals.append(
                proposal
            )


    return proposals


def convert_plan_step_to_proposal(
    plan,
    step_index,
    agent="planner"
):

    if not validate_task_plan(
        plan
    ):

        return None



    if step_index < 0 or step_index >= len(plan["steps"]):

        return None



    step = plan["steps"][step_index]



    return build_agent_proposal(
        agent,
        "task_step",
        step,
        plan["goal"],
        step
    )



def convert_plan_to_proposals(
    plan,
    agent="planner"
):

    proposals = []


    if not validate_task_plan(
        plan
    ):

        return proposals



    for index in range(
        len(plan["steps"])
    ):

        proposal = convert_plan_step_to_proposal(
            plan,
            index,
            agent
        )

        if proposal:

            proposals.append(
                proposal
            )


    return proposals


def parse_agent_action(
    response
):

    if not response:

        return None



    lines = response.splitlines()


    action = None
    target = None
    reason = None
    content = None


    for line in lines:

        if line.startswith("ACTION:"):

            action = line.split(
                ":",
                1
            )[1].strip()



        elif line.startswith("TARGET:"):

            target = line.split(
                ":",
                1
            )[1].strip()



        elif line.startswith("REASON:"):

            reason = line.split(
                ":",
                1
            )[1].strip()



        elif line.startswith("CONTENT:"):

            content = line.split(
                ":",
                1
            )[1].strip()



    if not action or not target:

        return None



    return build_agent_proposal(
        "agent",
        action,
        target,
        reason or "agent action proposal",
        content
    )


def build_agent_proposal(
    agent,
    action,
    target,
    reason,
    content=None
):

    return {

        "proposal_id":
            datetime.now().strftime("%Y%m%d_%H%M%S_")
            + str(uuid.uuid4())[:8],

        "agent":
            agent,

        "action":
            action,

        "target":
            target,

        "reason":
            reason,

        "content":
            content,

        "status":
            "pending_review"

    }



def validate_agent_proposal(
    proposal
):

    required = [

        "proposal_id",
        "agent",
        "action",
        "target",
        "reason"

    ]


    for field in required:

        if field not in proposal:

            return False


    return True


def build_action_request(
    agent,
    action,
    target,
    reason,
    content=None
):

    return {

        "request_id":
            datetime.now().strftime("%Y%m%d_%H%M%S_")
            + str(uuid.uuid4())[:8],

        "agent":
            agent,

        "action":
            action,

        "target":
            target,

        "reason":
            reason,

        "content":
            content,

        "approval":
            "pending"

    }


def create_engine_request(
    agent,
    action,
    file,
    reason
):

    request = engine.create_request(
        agent,
        action,
        file,
        reason
    )


    log(
        f"ENGINE REQUEST CREATED {request}"
    )


    return request




def approve_agent_proposal(
    proposal
):

    if not validate_agent_proposal(
        proposal
    ):

        return {

            "status":
                "rejected",

            "reason":
                "invalid_proposal"

        }



    request = create_engine_request(
        proposal["agent"],
        proposal["action"],
        proposal["target"],
        proposal["reason"]
    )


    return request


def approve_engine_request(
    request
):

    approved = engine.approve_request(
        request
    )


    log(
        f"ENGINE REQUEST APPROVED {approved}"
    )


    return approved



def execute_engine_request(
    request,
    content=None
):

    if request.get("approval") != "approved":

        return {

            "status":
                "blocked",

            "reason":
                "request_not_approved"

        }



    result = engine.execute_operation(
        request["action"],
        request["file"],
        content
    )


    log(
        f"ENGINE REQUEST EXECUTED {result}"
    )


    return result



def get_orchestrator():

    global _orchestrator


    if _orchestrator is None:

        print(
            "[SUPERVISOR] Creating orchestrator"
        )

        _orchestrator = Orchestrator()

        _orchestrator.load_agents()


        print(
            "[SUPERVISOR] Agent team cached"
        )


    else:

        print(
            "[SUPERVISOR] Reusing cached agents"
        )


    return _orchestrator



def create_vscode_task(
    title,
    instructions,
    rules=None
):

    task = bridge.create_task(
        title,
        instructions,
        rules
    )

    log(
        f"VS CODE TASK CREATED {task['task_id']}"
    )

    return task




def request_file_operation(
    agent,
    action,
    file,
    reason,
    content=None
):

    log(
        f"ENGINE REQUEST START {action} {file}"
    )


    request = create_engine_request(
        agent,
        action,
        file,
        reason
    )


    approved = approve_engine_request(
        request
    )


    result = execute_engine_request(
        approved,
        content
    )


    log(
        f"ENGINE REQUEST COMPLETE {result}"
    )


    return result



def detect_intent(
    task
):

    task_lower = task.lower()


    action_keywords = [

        "create file",
        "write file",
        "modify file",
        "edit file",
        "update file",
        "change code",
        "add code",
        "build app",
        "make script"

    ]


    for keyword in action_keywords:

        if keyword in task_lower:

            log(
                f"INTENT DETECTED: ACTION ({keyword})"
            )

            return "action"



    log(
        "INTENT DETECTED: INFORMATION"
    )

    return "information"


def run_task(
    task,
    status_callback=None
):

    print(
        "[SUPERVISOR] START"
    )


    def status(message):

        print(
            f"[STATUS] {message}"
        )

        if status_callback:

            status_callback(message)



    if not task.strip():

        return "No task provided"



    try:


        # INTENT ROUTER ACTIVE

        intent = detect_intent(
            task
        )


        status(
            f"Intent detected: {intent}"
        )


        if intent == "action":

            status(
                "Action request routed through Project Engine"
            )


        # ACTION ROUTING ACTIVE

        if intent == "action":

            log(
                "Action request available for Project Engine routing"
            )



        status(
            "Supervisor starting"
        )


        status(
            "Loading Project Engine"
        )


        engine_info = engine_status()


        for message in report_engine_status(engine_info):

            status(message)



        status(
            "Loading agent system"
        )


        orchestrator = get_orchestrator()


        decision = route(task)


        status(
            f"Router selected: {decision}"
        )


        agent = orchestrator.get_agent(
            decision
        )


        status(
            f"Using agent: {decision}"
        )


        prompt = (

            IDENTITY

            + "\n\nUSER REQUEST:\n"

            + task

        )


        status(
            f"Prompt prepared ({len(prompt)} chars)"
        )


        status(
            "Sending request to Ollama"
        )


        async def ask():

            response = await agent.on_messages(

                [

                    TextMessage(
                        content=prompt,
                        source="user"
                    )

                ],

                CancellationToken()

            )

            return response.chat_message.content



        output = asyncio.run(
            ask()
        )


        status(
            "Response received"
        )


        return clean_output(
            output
        )



    except Exception as e:

        log(
            f"ERROR {e}"
        )

        return f"Supervisor error: {e}"



if __name__ == "__main__":

    print(
        engine_status()
    )

    print(
        bridge.status()
    )















