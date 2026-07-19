"""Nexus98 Capability Awareness (boot-time discovery).

At startup Nexus98 should know: available tools, available models, their
capabilities, and their limitations. This module runs once at boot and
assembles a capability report from the Tool Registry, Model Intelligence, and
the runtime Configuration system.

It performs no mutations: it reads config, introspects already-imported tool
modules, and queries the model registry. It does NOT download models, start
services, or change autonomy state. The result is a read-only snapshot
suitable for logging and for feeding the integration facade.

See docs/NEXUS98_FRAMEWORK_INTEGRATION_20260718.md (Phase 3).
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(r"D:\Nexus98")

# Tool modules to introspect at boot (read-only capability discovery). These are
# the existing tools; the registry describes them rather than re-implementing.
TOOL_MODULES = {
    "tools.file_tools": "tools.file_tools",
    "tools.git_tools": "tools.git_tools",
    "tools.agent_selector": "tools.agent_selector",
    "tools.model_router": "tools.model_router",
    "tools.agent_runner": "tools.agent_runner",
}


@dataclass
class CapabilitySnapshot:
    """Read-only boot-time view of what Nexus98 can do."""

    tools: Dict[str, List[dict]] = field(default_factory=dict)
    models: Dict[str, object] = field(default_factory=dict)
    config: Dict[str, object] = field(default_factory=dict)
    limitations: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tools": self.tools,
            "models": self.models,
            "config": self.config,
            "limitations": self.limitations,
            "notes": self.notes,
        }


class CapabilityDiscoverer:
    """Discovers and assembles boot-time capabilities."""

    def __init__(self, registry=None, models=None, config_loader=None,
                 models_explicit: bool = False):
        # Lazy imports so missing optional pieces degrade gracefully.
        # ``models_explicit`` distinguishes "caller did not pass models" (try
        # to auto-discover) from "caller explicitly passed None" (disable).
        if registry is None:
            try:
                from core.tool_registry import ToolRegistry
                registry = ToolRegistry()
                self._seed_registry(registry)
            except Exception:
                registry = None
        if models is None and not models_explicit:
            try:
                from core.frameworks.model import ModelIntelligence
                models = ModelIntelligence()
            except Exception:
                models = None
        if config_loader is None:
            try:
                from core.config import load_config
                config_loader = load_config
            except Exception:
                config_loader = None
        self.registry = registry
        self.models = models
        self.config_loader = config_loader

    def _seed_registry(self, registry) -> None:
        for mod_name in TOOL_MODULES.values():
            try:
                mod = importlib.import_module(mod_name)
                registry.seed_from_modules({mod_name: mod})
            except Exception:
                continue

    def discover(self) -> CapabilitySnapshot:
        snap = CapabilitySnapshot()

        # 1. Tools
        if self.registry is not None:
            snap.tools = self.registry.capability_summary()

        # 2. Models
        if self.models is None:
            snap.limitations.append(
                "Model registry unavailable; model recommendation disabled."
            )
        else:
            snap.models = self.models.capability_summary()
            if not snap.models.get("available"):
                snap.limitations.append(
                    "No models marked available; model execution may be unavailable."
                )

        # 3. Config
        if self.config_loader is not None:
            try:
                snap.config = dict(self.config_loader())
            except Exception as e:
                snap.limitations.append(f"Config load failed: {e}")

        # 4. Cross-cutting limitations
        if not snap.tools:
            snap.limitations.append("Tool registry empty; tool discovery limited.")
        return snap

    def report_line(self) -> str:
        snap = self.discover()
        tool_count = sum(len(v) for v in snap.tools.values())
        model_count = snap.models.get("total", 0)
        return (
            f"Capabilities: {tool_count} tools, {model_count} models, "
            f"{len(snap.limitations)} limitations noted."
        )


# Module-level convenience for boot usage.
default_discoverer = CapabilityDiscoverer()


