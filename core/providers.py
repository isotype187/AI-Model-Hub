"""Phase C - Provider Boundary (integration architecture).

Prepares clean provider boundaries for external systems so vendor-specific
behavior never hard-codes into the core execution / orchestration systems.

Supported provider families today:
  * ``ollama``     - local Ollama runtime (model listing + chat availability)
  * ``openrouter`` - cloud OpenRouter API (interface only; no key needed to
                     register the provider; callers supply credentials)
  * ``vscode``     - VS Code bridge / tooling (send tasks to the editor)

Design rules:
  * Pure abstraction layer. It does NOT execute tasks and never changes
    autonomy state. It only exposes *availability + capability* surfaces and a
    uniform ``ModelProvider`` / ``TaskProvider`` interface so the rest of the
    system can stay vendor-agnostic.
  * Core execution authority (core.supervisor) and autonomy authority
    (core.autonomy.governor) remain untouched; this module is a read/bridge
    facade only.
  * Adding a future provider = registering one adapter here. No core edits.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


@dataclass
class ProviderInfo:
    """Advertised capability of a registered provider (read-only surface)."""

    name: str
    kind: str            # "model" | "task" | "editor"
    available: bool
    detail: str = ""
    capabilities: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "available": self.available,
            "detail": self.detail,
            "capabilities": list(self.capabilities),
        }


class ModelProvider:
    """Uniform interface for a model backend (local or cloud)."""

    name = "abstract"
    kind = "model"

    def is_available(self) -> bool:
        raise NotImplementedError

    def list_models(self) -> List[dict]:
        """Return normalized model records: {id, name, provider, ...}."""
        raise NotImplementedError

    def chat_available(self) -> bool:
        return self.is_available()


class TaskProvider:
    """Uniform interface for a task/execution surface (e.g. VS Code)."""

    name = "abstract"
    kind = "task"

    def is_available(self) -> bool:
        raise NotImplementedError

    def submit(self, task: str, **kwargs) -> dict:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Ollama adapter (delegates to the existing core.ollama module)
# ---------------------------------------------------------------------------

class OllamaModelProvider(ModelProvider):
    name = "ollama"
    kind = "model"

    def is_available(self) -> bool:
        try:
            from core.ollama import check_ollama
            return bool(check_ollama())
        except Exception:
            return False

    def list_models(self) -> List[dict]:
        try:
            from core.ollama import get_installed_models
            return get_installed_models()
        except Exception as exc:
            return [{"provider": "ollama", "error": str(exc)}]


# ---------------------------------------------------------------------------
# OpenRouter adapter (interface only; credentials supplied by the caller)
# ---------------------------------------------------------------------------

class OpenRouterModelProvider(ModelProvider):
    name = "openrouter"
    kind = "model"

    def __init__(self, api_key: Optional[str] = None,
                 base_url: str = "https://openrouter.ai/api/v1"):
        self.api_key = api_key
        self.base_url = base_url

    def is_available(self) -> bool:
        # Without a key the provider is "registered but not configured".
        return bool(self.api_key)

    def list_models(self) -> List[dict]:
        if not self.api_key:
            return [{"provider": "openrouter",
                     "error": "no API key configured"}]
        # Intentionally not implemented here: core systems own HTTP/auth.
        # This boundary only declares the capability; the actual call stays in
        # the vendor-specific client to keep core vendor-agnostic.
        return [{"provider": "openrouter", "configured": True,
                 "base_url": self.base_url}]


# ---------------------------------------------------------------------------
# VS Code adapter (delegates to the existing integrations.vscode_connector)
# ---------------------------------------------------------------------------

class VSCodeTaskProvider(TaskProvider):
    name = "vscode"
    kind = "task"

    def is_available(self) -> bool:
        try:
            from integrations.vscode_connector import status
            return str(status().get("status")) == "online"
        except Exception:
            return False

    def submit(self, task: str, **kwargs) -> dict:
        from integrations.vscode_connector import send_task
        return send_task(task, **kwargs)


# ---------------------------------------------------------------------------
# Provider registry (the single clean boundary point)
# ---------------------------------------------------------------------------

class ProviderRegistry:
    """Holds the known provider adapters and reports their status."""

    def __init__(self) -> None:
        self._model_providers: Dict[str, ModelProvider] = {}
        self._task_providers: Dict[str, TaskProvider] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register_model_provider(OllamaModelProvider())
        self.register_model_provider(OpenRouterModelProvider())
        self.register_task_provider(VSCodeTaskProvider())

    def register_model_provider(self, provider: ModelProvider) -> None:
        self._model_providers[provider.name] = provider

    def register_task_provider(self, provider: TaskProvider) -> None:
        self._task_providers[provider.name] = provider

    def model_providers(self) -> List[ProviderInfo]:
        out = []
        for p in self._model_providers.values():
            try:
                ok = p.is_available()
                models = p.list_models() if ok else []
                out.append(ProviderInfo(
                    name=p.name, kind=p.kind, available=ok,
                    detail="%d model(s)" % len(models),
                    capabilities=["list_models", "chat"]
                    if ok else ["list_models"],
                ))
            except Exception as exc:
                out.append(ProviderInfo(p.name, p.kind, False, str(exc)[:120]))
        return out

    def task_providers(self) -> List[ProviderInfo]:
        out = []
        for p in self._task_providers.values():
            try:
                ok = p.is_available()
                out.append(ProviderInfo(p.name, p.kind, ok,
                                        "online" if ok else "offline",
                                        ["submit_task"]))
            except Exception as exc:
                out.append(ProviderInfo(p.name, p.kind, False, str(exc)[:120]))
        return out

    def status(self) -> dict:
        return {
            "model_providers": [p.to_dict() for p in self.model_providers()],
            "task_providers": [p.to_dict() for p in self.task_providers()],
        }


# Convenience singleton: the one place the UI / integration layer asks about
# external systems. Future providers are added via register_* (no core edits).
default_registry = ProviderRegistry()