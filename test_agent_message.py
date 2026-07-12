import asyncio

from core.agent_factory import AgentFactory
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken


async def main():

    factory = AgentFactory("config/models.yaml")

    agent = factory.create_agent("coder")

    response = await agent.on_messages(
        [
            TextMessage(
                content="Reply with only: OLLAMA TEST SUCCESS",
                source="user"
            )
        ],
        CancellationToken()
    )

    print(response.chat_message.content)


asyncio.run(main())
