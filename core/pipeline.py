from datetime import datetime
import requests
import time


class AgentPipeline:


    def __init__(self, orchestrator):

        self.orchestrator = orchestrator

        self.results = []



    def model_timeout(self, model):

        if "32b" in model:
            return 600

        if "30b" in model:
            return 480

        if "14b" in model:
            return 240

        return 180



    def run_agent(self, agent, task):

        name = agent["name"]
        model = agent["model"]

        print(
            f"[PIPELINE] Running {name}"
        )

        start = time.time()


        timeout = self.model_timeout(model)


        prompt = f"""
You are the {name} agent inside AI_Model_Hub.

Role:
{agent.get("role","")}

Task:
{task}

Provide a useful technical response.
"""


        try:

            response = requests.post(

                "http://127.0.0.1:11434/api/generate",

                json={

                    "model": model,

                    "prompt": prompt,

                    "stream": False,

                    "keep_alive": "30m"

                },

                timeout=timeout

            )


            data = response.json()


            elapsed = time.time() - start


            print(
                f"[PIPELINE] {name} complete ({elapsed:.1f}s)"
            )


            return {

                "agent": name,

                "model": model,

                "output":
                    data.get(
                        "response",
                        ""
                    ),

                "time":
                    elapsed

            }


        except Exception as e:


            elapsed = time.time() - start


            print(
                f"[PIPELINE] {name} FAILED"
            )


            return {

                "agent": name,

                "model": model,

                "error": str(e),

                "time":
                    elapsed

            }



    def execute(self, task):


        print(
            "[PIPELINE] START"
        )


        self.results = []


        for name in self.orchestrator.list_agents():


            agent = self.orchestrator.get_agent(name)


            result = self.run_agent(

                {
                    "name": name,
                    **agent
                },

                task

            )


            self.results.append(result)



        print(
            "[PIPELINE] FINISHED"
        )


        return {

            "task": task,

            "pipeline": self.results,

            "timestamp":
                datetime.now().isoformat()

        }
