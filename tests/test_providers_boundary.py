"""Tests for the Phase C provider boundary (core.providers)."""
import pytest

from core.providers import (
    ProviderRegistry, OllamaModelProvider, OpenRouterModelProvider,
    VSCodeTaskProvider, ModelProvider, TaskProvider, ProviderInfo,
)


def test_registry_has_default_providers():
    reg = ProviderRegistry()
    model_names = {p.name for p in reg._model_providers.values()}
    task_names = {p.name for p in reg._task_providers.values()}
    assert "ollama" in model_names
    assert "openrouter" in model_names
    assert "vscode" in task_names


def test_openrouter_without_key_is_unconfigured():
    p = OpenRouterModelProvider()
    assert p.is_available() is False
    models = p.list_models()
    assert models and "error" in models[0]


def test_openrouter_with_key_is_available():
    p = OpenRouterModelProvider(api_key="test-key")
    assert p.is_available() is True
    models = p.list_models()
    assert models and models[0].get("configured") is True


def test_ollama_provider_interface():
    p = OllamaModelProvider()
    assert isinstance(p, ModelProvider)
    # Does not raise even when ollama is absent.
    assert p.is_available() in (True, False)


def test_vscode_provider_interface():
    p = VSCodeTaskProvider()
    assert isinstance(p, TaskProvider)
    assert p.is_available() in (True, False)


def test_add_future_provider_without_core_edits():
    reg = ProviderRegistry()

    class FutureModel(ModelProvider):
        name = "future"

        def is_available(self):
            return True

        def list_models(self):
            return [{"id": "future:1", "name": "future-1",
                     "provider": "future"}]

    reg.register_model_provider(FutureModel())
    assert "future" in reg._model_providers


def test_status_shape():
    reg = ProviderRegistry()
    status = reg.status()
    for p in status["model_providers"]:
        ProviderInfo(**{k: (v if k != "capabilities" else [])
                         for k, v in p.items()})