from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.ollama import OllamaChatCompletionClient

from tools.file_tools import list_files, read_file
from tools.git_tools import git_status


class AgentFactory:


    def __init__(self, config_path):

        import yaml

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)



    def create_agent(self, name):

        settings = self.config["agents"][name]


        client = OllamaChatCompletionClient(
            model=settings["model"],
            host="http://localhost:11434",
            model_info={
                "vision": name == "vision",
                "function_calling": True,
                "json_output": False,
                "family": "unknown",
                "structured_output": False,
            },
        )


        tools = []


        if name in [
            "architect",
            "researcher",
            "reviewer",
            "coder"
        ]:

            tools.extend(
                [
                    list_files,
                    read_file,
                    git_status
                ]
            )


        return AssistantAgent(
            name=name,
            model_client=client,
            tools=tools,
            system_message=f"""
You are the {name} agent inside AI_Model_Hub.

Role:
{settings["role"]}

Rules:
- Inspect before changing.
- Use tools when information is needed.
- Preserve existing architecture.
- Avoid unnecessary rewrites.
- Explain decisions.
- Never pretend you inspected files unless you actually used tools.
"""
        )
