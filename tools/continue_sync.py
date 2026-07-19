import json
from pathlib import Path


ROOT = Path(r"D:\AI_Model_Hub")

registry = ROOT / "config" / "models.json"

output = Path.home() / ".continue" / "config.yaml"


data = json.loads(
    registry.read_text(
        encoding="utf-8-sig"
    )
)


yaml = []

yaml.append(
"name: AI_Model_Hub\n"
"version: 1.0.0\n"
"schema: v1\n"
"models:"
)


for model in data["models"]:

    yaml.append(
f"""
  - name: {model['name']}
    provider: ollama
    model: {model['ollama']}
    apiBase: http://127.0.0.1:11434
    roles:
"""
    )

    for role in model["roles"]:
        yaml.append(
            f"      - {role}\n"
        )


output.write_text(
    "\n".join(yaml),
    encoding="utf-8"
)


print(
    "Continue config synchronized."
)