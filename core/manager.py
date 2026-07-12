from core.agent_factory import AgentFactory


class ManagerAgent:

    def __init__(self):

        factory = AgentFactory(
            "config/models.yaml"
        )

        self.agent = factory.create_agent(
            "architect"
        )


    def get_agent(self):
        return self.agent
