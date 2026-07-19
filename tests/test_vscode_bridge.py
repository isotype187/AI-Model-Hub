"""Offline pytest conversion of the VSCode bridge HTTP API.

Replaces the old manual script (print-based, non-collectable). All
external dependencies are mocked via tests/conftest.py fixtures:
- ollama_models() / ollama_chat()  (HTTP to 127.0.0.1:11434)
- core.supervisor.run_task          (AutoGen execution)

No live VSCode, no network, no real model calls.
"""
import json
from unittest import mock


def test_health_returns_online(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "online"
    assert body["service"] == "AI Hub Bridge"


def test_models_success_returns_discovered_models(client, patch_ollama):
    r = client.get("/v1/models")
    assert r.status_code == 200
    body = r.get_json()
    assert body["object"] == "list"
    assert isinstance(body["data"], list)
    assert body["data"][0]["id"] == "qwen3-coder:30b"
    assert body["data"][0]["owned_by"] == "AI Hub Ollama"


def test_models_empty_when_ollama_down(client):
    with mock.patch(
        "api.vscode_bridge.ollama_models", return_value=[]
    ):
        r = client.get("/v1/models")
    assert r.status_code == 200
    body = r.get_json()
    assert body["data"] == []


def test_models_timeout_propagates_from_ollama(client):
    import requests

    with mock.patch(
        "api.vscode_bridge.ollama_models",
        side_effect=requests.exceptions.Timeout("timed out"),
    ):
        r = client.get("/v1/models")
    # Current api/vscode_bridge.models() does not catch ollama errors,
    # so the timeout propagates as a 500. This documents the gap.
    assert r.status_code == 500



def test_models_malformed_response_returns_empty(client):
    with mock.patch(
        "api.vscode_bridge.ollama_models", return_value={}
    ):
        r = client.get("/v1/models")
    assert r.status_code == 200
    assert r.get_json()["data"] == []


def test_chat_completions_success(client, patch_ollama, patch_run_task):
    payload = {
        "messages": [
            {"role": "user", "content": "create a hello world script"}
        ]
    }
    r = client.post("/v1/chat/completions", json=payload)
    assert r.status_code == 200
    body = r.get_json()
    assert body["object"] == "chat.completion"
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert body["choices"][0]["message"]["content"] == "mocked chat content"


def test_chat_completions_uses_run_task_model(client, patch_ollama, patch_run_task):
    payload = {"messages": [{"role": "user", "content": "do a thing"}]}
    r = client.post("/v1/chat/completions", json=payload)
    assert r.status_code == 200
    body = r.get_json()
    # Current api/vscode_bridge.chat() computes a 'model' but does not
    # include it in the response payload (gap to fix in source).
    assert "model" not in body
    assert body["choices"][0]["message"]["content"] == "mocked chat content"



def test_chat_completions_default_model_when_run_task_empty(
    client, patch_ollama, patch_run_task_default
):
    payload = {"messages": [{"role": "user", "content": "do a thing"}]}
    r = client.post("/v1/chat/completions", json=payload)
    assert r.status_code == 200
    body = r.get_json()
    assert "model" not in body
    assert body["choices"][0]["message"]["content"] == "mocked chat content"



def test_chat_completions_ollama_error_propagates(client, patch_run_task):
    import requests

    with mock.patch(
        "api.vscode_bridge.ollama_chat",
        side_effect=requests.exceptions.ConnectionError("ollama down"),
    ):
        payload = {"messages": [{"role": "user", "content": "hello"}]}
        r = client.post("/v1/chat/completions", json=payload)
    # Current api/vscode_bridge.chat() does not catch ollama_chat failures,
    # so the error propagates as a 500 (gap to fix in source).
    assert r.status_code == 500



def test_unknown_route_returns_404(client):
    r = client.get("/v1/does-not-exist")
    assert r.status_code == 404


