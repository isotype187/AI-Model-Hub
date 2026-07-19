from core.agent_factory import AgentFactory


class Orchestrator:


    def __init__(self):

        self.factory = AgentFactory(
            "config/models.yaml"
        )

        self.agents = {}

        self.load_agents()



    def load_agents(self):

        print("Loading Nexus98 agent team")

        for name in self.factory.config["agents"]:

            print(f"Registering agent: {name}")

            self.agents[name] = self.factory.create_agent(name)


        print("Agent team ready")



    def get_agent(self, name):

        return self.agents.get(name)



    def list_agents(self):

        return list(self.agents.keys())



    def describe_team(self):

        output = []

        for name, agent in self.agents.items():

            output.append(
                {
                    "agent": name,
                    "model": self.factory.config["agents"][name]["model"],
                    "role": self.factory.config["agents"][name]["role"]
                }
            )

        return output


