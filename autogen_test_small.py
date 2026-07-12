import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.ollama import OllamaChatCompletionClient


async def main():

    model_client = OllamaChatCompletionClient(
        model="llama3.2:3b",
        host="http://localhost:11434",
    )

    agent = AssistantAgent(
        name="architect",
        model_client=model_client,
        system_message="""
You are the AI_Model_Hub architecture agent.

Rules:
- Preserve modular architecture.
- Analyze before changing.
- Avoid unnecessary rewrites.
- Prefer configuration-driven systems.
- Respect existing project structure.
"""
    )

    response = await agent.on_messages(
        [
            TextMessage(
                content="Explain your role in this AI development team.",
                source="user",
            )
        ],
        CancellationToken(),
    )

    print(response.chat_message.content)


if __name__ == "__main__":
    asyncio.run(main())
