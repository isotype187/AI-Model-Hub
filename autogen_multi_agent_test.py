import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.ollama import OllamaChatCompletionClient


async def run_agent(agent, task):
    response = await agent.on_messages(
        [
            TextMessage(
                content=task,
                source="user",
            )
        ],
        CancellationToken(),
    )

    print("\n" + "=" * 60)
    print(agent.name.upper())
    print("=" * 60)
    print(response.chat_message.content)


async def main():

    architect_client = OllamaChatCompletionClient(
        model="qwen3:14b",
        host="http://localhost:11434",
    )

    coder_client = OllamaChatCompletionClient(
        model="qwen2.5-coder:14b",
        host="http://localhost:11434",
    )

    reviewer_client = OllamaChatCompletionClient(
        model="llama3.2:3b",
        host="http://localhost:11434",
    )


    architect = AssistantAgent(
        name="architect",
        model_client=architect_client,
        system_message="""
You are the AI_Model_Hub architecture agent.

Focus on:
- modular design
- scalability
- configuration-driven systems
- minimizing unnecessary rewrites
""",
    )


    coder = AssistantAgent(
        name="coder",
        model_client=coder_client,
        system_message="""
You are the AI_Model_Hub coding agent.

Focus on:
- implementation details
- clean Python
- maintainability
- integration safety
""",
    )


    reviewer = AssistantAgent(
        name="reviewer",
        model_client=reviewer_client,
        system_message="""
You are the AI_Model_Hub review agent.

Focus on:
- finding risks
- catching design mistakes
- suggesting improvements
""",
    )


    task = """
Design a safe way to add automatic model routing
to AI_Model_Hub.

Explain the architecture approach.
"""


    await run_agent(architect, task)
    await run_agent(coder, task)
    await run_agent(reviewer, task)


if __name__ == "__main__":
    asyncio.run(main())
