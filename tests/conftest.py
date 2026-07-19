"""Shared pytest fixtures for the VSCode bridge test conversion.

This module isolates the bridge HTTP tests from all external dependencies:
- No live VSCode instance is launched.
- No network access to Ollama (127.0.0.1:11434) or any server.
- No real AutoGen/supervisor execution (run_task is mocked).
- Filesystem side effects (logs/, bridge/) are redirected to tmp_path.

Production code (api/vscode_bridge.py, core/*) is NOT modified.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import api.vscode_bridge as bridge_mod
from api.vscode_bridge import app


@pytest.fixture
def client():
    """In-process Flask test client; no sockets opened."""
    app.config["TESTING"] = True
    app.config["PROPAGATE_EXCEPTIONS"] = False
    return app.test_client()


@pytest.fixture
def isolate_fs(tmp_path, monkeypatch):
    """Redirect bridge filesystem writes to a temp dir."""
    monkeypatch.setattr(bridge_mod, "LOG", tmp_path / "vscode_bridge.log")
    monkeypatch.setattr(bridge_mod, "ROOT", tmp_path)
    return tmp_path


@pytest.fixture
def fake_ollama_models():
    """Single healthy model returned by ollama_models()."""
    return {"models": [{"name": "qwen3-coder:30b", "size": 123, "modified_at": "2026-01-01"}]}


@pytest.fixture
def patch_ollama(fake_ollama_models):
    """Patch ollama_models() and ollama_chat() with deterministic fakes."""
    with mock.patch.object(
        bridge_mod, "ollama_models", return_value=fake_ollama_models["models"]
    ), mock.patch.object(
        bridge_mod, "ollama_chat", return_value="mocked chat content"
    ):
        yield


@pytest.fixture
def patch_run_task():
    """Patch supervisor.run_task so chat route never runs AutoGen."""
    with mock.patch.object(
        bridge_mod, "run_task", return_value={"model": "qwen3-coder:30b"}
    ) as m:
        yield m


@pytest.fixture
def patch_run_task_default():
    """Patch run_task to return a non-dict/empty result (exercises fallback)."""
    with mock.patch.object(bridge_mod, "run_task", return_value={}) as m:
        yield m

