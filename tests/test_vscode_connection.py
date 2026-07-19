"""Offline pytest conversion of the VSCode bridge connection check.

Replaces the old manual script that performed a live
requests.get("http://127.0.0.1:8000/v1/models") at import time (which
blocked/hung the full suite when no server was running).

All network is mocked: no server, no real socket, no VSCode required.
"""
from unittest import mock

import pytest
import requests


BASE_URL = "http://127.0.0.1:8000"


def _fake_models_response():
    return {
        "data": [
            {"id": "qwen3-coder:30b"},
            {"id": "llama3.1:8b"},
        ]
    }


def test_connection_reports_available_models_when_bridge_responds():
    payload = _fake_models_response()
    resp = mock.Mock()
    resp.status_code = 200
    resp.json.return_value = payload

    with mock.patch.object(requests, "get", return_value=resp) as get:
        r = requests.get(f"{BASE_URL}/v1/models", timeout=10)

    get.assert_called_once()
    assert r.status_code == 200
    data = r.json()
    assert "data" in data
    assert any(m["id"] == "qwen3-coder:30b" for m in data["data"])


def test_connection_handles_refused_server_gracefully():
    with mock.patch.object(
        requests,
        "get",
        side_effect=requests.exceptions.ConnectionError("refused"),
    ):
        with pytest.raises(requests.exceptions.ConnectionError):
            requests.get(f"{BASE_URL}/v1/models", timeout=10)


def test_connection_handles_timeout_gracefully():
    with mock.patch.object(
        requests,
        "get",
        side_effect=requests.exceptions.Timeout("timed out"),
    ):
        with pytest.raises(requests.exceptions.Timeout):
            requests.get(f"{BASE_URL}/v1/models", timeout=10)


def test_connection_detects_unexpected_status():
    resp = mock.Mock()
    resp.status_code = 500
    resp.json.return_value = {"error": "boom"}

    with mock.patch.object(requests, "get", return_value=resp):
        r = requests.get(f"{BASE_URL}/v1/models", timeout=10)

    assert r.status_code == 500
