from datetime import datetime


AGENTS = {

    "Supervisor": {
        "type": "controller",
        "status": "ONLINE",
        "description": "Master task coordinator"
    },

    "Coding Agent": {
        "type": "llm",
        "status": "READY",
        "model": "qwen3-coder:30b",
        "description": "Code generation and debugging"
    },

    "Reasoning Agent": {
        "type": "llm",
        "status": "READY",
        "model": "deepseek-r1:32b",
        "description": "Planning and architecture"
    },

    "Vision Agent": {
        "type": "vision",
        "status": "READY",
        "model": "llava:latest",
        "description": "Image and screen analysis"
    },

    "Mouse Agent": {
        "type": "automation",
        "status": "DEVELOPMENT",
        "description": "Mouse and UI automation"
    },

    "Memory Agent": {
        "type": "embedding",
        "status": "WAITING",
        "model": "nomic-embed-text:latest",
        "description": "Knowledge storage and retrieval"
    }

}


def get_agents():

    return AGENTS



def get_agent_status(name):

    agent = AGENTS.get(name)

    if not agent:
        return None

    return {
        "name": name,
        **agent
    }



def update_status(name, status):

    if name in AGENTS:

        AGENTS[name]["status"] = status

        AGENTS[name]["updated"] = (
            datetime.now()
            .isoformat()
        )

        return True

    return False



def list_agents():

    output = []

    for name, data in AGENTS.items():

        output.append(
            {
                "name": name,
                **data
            }
        )

    return output
