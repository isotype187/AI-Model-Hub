"""Nexus98 Context Intelligence Framework.

A unified context layer that gathers the *current situation* from across the
verified subsystems into a single, structured ``TaskContext``: active project,
workspace reality, recent activity, architecture state, loaded models, available
tools, runtime configuration, and the current objective.

This is a read/assemble layer. It pulls from Continuity, Workspace, Model
Intelligence, Tool Registry, and Capability Awareness — it never writes state
on its own beyond refreshing a context snapshot. No autonomy-state mutation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TaskContext:
    """Unified, assembled context for a moment in time."""

    objective: str = ""
    active_project: Optional[str] = None
    workspace: Dict = field(default_factory=dict)
    recent_activity: List[str] = field(default_factory=list)
    architecture_state: Dict = field(default_factory=dict)
    loaded_models: List[str] = field(default_factory=list)
    available_tools: List[str] = field(default_factory=list)
    runtime_config: Dict = field(default_factory=dict)
    strategy: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "objective": self.objective,
            "active_project": self.active_project,
            "workspace": self.workspace,
            "recent_activity": self.recent_activity,
            "architecture_state": self.architecture_state,
            "loaded_models": self.loaded_models,
            "available_tools": self.available_tools,
            "runtime_config": self.runtime_config,
            "strategy": self.strategy,
        }


class ContextAssembler:
    """Assembles a unified ``TaskContext`` from injected subsystems."""

    def __init__(self, continuity=None, reality=None, models=None,
                 registry=None, capability=None, config_loader=None,
                 strategy_controller=None):
        self.continuity = continuity
        self.reality = reality
        self.models = models
        self.registry = registry
        self.capability = capability
        self.config_loader = config_loader
        self.strategy = strategy_controller

    def assemble(self, objective: str = "", *, active_project: Optional[str] = None,
                 strategy: Optional[List[str]] = None) -> TaskContext:
        ctx = TaskContext(objective=objective, active_project=active_project,
                          strategy=list(strategy or []))

        if self.reality is not None:
            ctx.workspace = self.reality.reality_snapshot()
        if self.continuity is not None:
            ctx.recent_activity = [
                t.get("title", "") for t in self.continuity.active_tasks()
            ]
        if self.models is not None:
            ctx.loaded_models = [
                p.ollama for p in self.models.list_profiles()
                if p.available
            ]
        if self.registry is not None:
            ctx.available_tools = [
                t.id for t in self.registry.list_tools()
            ]
        if self.config_loader is not None:
            try:
                ctx.runtime_config = dict(self.config_loader())
            except Exception:
                ctx.runtime_config = {}
        if self.capability is not None:
            ctx.architecture_state = self.capability.discover().to_dict()
        return ctx

    def snapshot(self, objective: str = "", **kwargs) -> dict:
        return self.assemble(objective, **kwargs).to_dict()
