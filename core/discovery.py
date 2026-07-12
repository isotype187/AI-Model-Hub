import requests

from core.ollama import get_installed_models


def discover_hf():
    try:
        r = requests.get(
            "https://huggingface.co/api/models?search=text-generation&limit=10",
            timeout=10
        )

        return [
            {
                "id": m["modelId"],
                "name": m["modelId"],
                "source": "huggingface",
                "type": "hf",
                "installed": False
            }
            for m in r.json()
        ]

    except Exception:
        return []


def discover_ollama():
    models = get_installed_models()

    for model in models:
        model["source"] = "ollama"
        model["type"] = "ollama"

    return models


def discover_github():
    try:
        r = requests.get(
            "https://api.github.com/search/repositories?q=llama+OR+gguf+OR+ollama&per_page=10",
            timeout=10
        )

        return [
            {
                "id": x["html_url"],
                "name": x["name"],
                "source": "github",
                "type": "repo",
                "installed": False
            }
            for x in r.json().get("items", [])
        ]

    except Exception:
        return []


def build_catalog():
    return (
        discover_ollama()
        + discover_hf()
        + discover_github()
    )
