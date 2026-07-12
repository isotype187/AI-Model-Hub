import asyncio
from autogen_ext.models.ollama import OllamaChatCompletionClient

async def main():

    client = OllamaChatCompletionClient(
        model="qwen3-coder:30b",
        host="http://localhost:11434",
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": False,
            "family": "unknown",
            "structured_output": False,
        },
    )

    result = await client.create(
        messages=[
            {
                "role": "user",
                "content": "Write one sentence saying hello."
            }
        ]
    )

    print(result)

asyncio.run(main())
