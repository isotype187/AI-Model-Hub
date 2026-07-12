from datetime import datetime
from core.orchestrator import Orchestrator
from core.supervisor import run_task


def log(message):

    with open(
        r"D:\AI_Model_Hub\logs\orchestrator_bridge_test.log",
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            str(message) + "\n"
        )


print("")
print("=== ORCHESTRATOR LOAD TEST ===")

try:

    hub = Orchestrator()

    hub.load_agents()

    agents = hub.describe_team()

    print("")
    print("REGISTERED AGENTS:")
    print(agents)

    log(
        {
            "time": datetime.now().isoformat(),
            "agents": agents
        }
    )

    print("")
    print("ORCHESTRATOR STATUS: OK")


except Exception as e:

    print("")
    print("ORCHESTRATOR FAILURE:")
    print(type(e).__name__, e)

    log(
        "ORCHESTRATOR FAILURE: "
        + str(e)
    )



print("")
print("=== SUPERVISOR PIPELINE TEST ===")

try:

    result = run_task(
        "Design a plugin architecture for AI_Model_Hub"
    )

    print("")
    print("SUPERVISOR RESULT:")
    print(result)

    log(
        {
            "time": datetime.now().isoformat(),
            "supervisor_result": str(result)[:2000]
        }
    )

    print("")
    print("SUPERVISOR STATUS: OK")


except Exception as e:

    print("")
    print("SUPERVISOR FAILURE:")
    print(type(e).__name__, e)

    log(
        "SUPERVISOR FAILURE: "
        + str(e)
    )


print("")
print("=== TEST COMPLETE ===")
