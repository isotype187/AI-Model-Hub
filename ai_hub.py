import asyncio

from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from core.agent_factory import AgentFactory
from core.router import TaskRouter
from core.memory import Memory


class AIHub:

    def __init__(self):

        print("Initializing AI_Model_Hub...")

        self.factory = AgentFactory(
            "config/models.yaml"
        )

        self.agents = {}

        for name in self.factory.config["agents"]:

            print(f"Loading agent: {name}")

            self.agents[name] = (
                self.factory.create_agent(name)
            )

        self.router = TaskRouter(
            self.agents
        )

        self.memory = Memory()

        print("Agent loading complete.")


    async def process(self, task):

        agent = self.router.route(task)

        print(
            f"\nAssigned Agent: {agent.name}"
        )

        response = await agent.on_messages(
            [
                TextMessage(
                    content=task,
                    source="user"
                )
            ],
            CancellationToken()
        )

        result = (
            response.chat_message.content
        )

        self.memory.save(
            {
                "agent": agent.name,
                "task": task,
                "response": result
            }
        )

        return result



async def main():

    hub = AIHub()

    print()
    print("=" * 50)
    print(" AI_Model_Hub ONLINE ")
    print("=" * 50)
    print()
    print("Enter tasks. Type exit to quit.")

    while True:

        task = input(
            "\nTask > "
        )

        if task.lower() in [
            "exit",
            "quit"
        ]:
            break


        try:

            result = await hub.process(
                task
            )

            print()
            print(result)

        except Exception as e:

            print()
            print("ERROR:")
            print(e)



if __name__ == "__main__":

    asyncio.run(main())
