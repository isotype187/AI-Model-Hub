import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.ollama import OllamaChatCompletionClient


MODELS = {
    "architect": "qwen3:30b",
    "coder": "qwen3-coder:30b",
    "researcher": "deepseek-r1:32b",
    "reviewer": "deepseek-coder:latest",
    "tester": "qwen3:14b",
    "documentation": "llama3.2:latest",
    "vision": "llava:latest",
}


def create_agent(name, model, role):

    model_client = OllamaChatCompletionClient(
        model=model,
        host="http://localhost:11434",
        model_info={
            "vision": model.startswith("llava"),
            "function_calling": False,
            "json_output": False,
            "family": "unknown",
            "structured_output": False,
        },
    )

    return AssistantAgent(
        name=name,
        model_client=model_client,
        system_message=f"""
You are the {name} agent inside AI_Model_Hub.

Role:
{role}

Rules:
- Preserve existing architecture.
- Inspect before modifying.
- Do not rewrite working systems unnecessarily.
- Keep modules independent.
- Use configuration files instead of hardcoded values.
- Explain decisions clearly.
"""
    )


async def main():

    agents = {}

    for name, model in MODELS.items():

        print(f"Starting {name} -> {model}")

        agents[name] = create_agent(
            name,
            model,
            f"Act as the {name} specialist."
        )


    print("\nAI_Model_Hub Agent Team Online")
    print("=" * 40)


    for name, agent in agents.items():

        response = await agent.on_messages(
            [
                TextMessage(
                    content=f"Introduce yourself as the {name} agent.",
                    source="manager"
                )
            ],
            CancellationToken()
        )

        print(f"\n[{name.upper()}]")
        print(response.chat_message.content)


if __name__ == "__main__":
    asyncio.run(main())
