"""Nexus98 Tool Registry & Capability System.

A single, authoritative catalog of the capabilities available to agents and
the orchestrator. It does NOT re-implement any tool — it *describes* the
existing tools in ``tools/``, ``integrations/``, ``core/``, the VS Code
bridge, and the UI so that future agents can discover what is available
before acting.

Design goals:
  * One registration surface for capabilities (id, module, callable, risk).
  * Capability metadata: description, safety level, side effects.
  * Discovery by keyword / capability / risk tier.
  * Read-only descriptions for agents; optional live callable binding.

This is additive. The runtime safety gate in ``core.supervisor`` and
``core.project_engine`` remains the enforcement authority; the registry only
informs. It performs no autonomy-state changes.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional


class RiskTier(str, Enum):
    """Capability risk tiers, aligned with the Tool Registry autonomy table."""

    READ_ONLY = "read_only"          # L0 safe
    PROPOSAL = "proposal"            # L1: proposes, no execution
    MUTATION = "mutation"           # L2: approved writes
    INFRASTRUCTURE = "infrastructure"  # L3+: model/agent lifecycle, downloads


@dataclass
class Tool:
    """A registered capability with metadata."""

    id: str
    description: str
    module: str
    callable_name: Optional[str] = None
    risk: RiskTier = RiskTier.READ_ONLY
    side_effects: str = "none"
    tags: List[str] = field(default_factory=list)
    # Optional live binding; registry does not require it to be populated.
    _fn: Optional[Callable] = field(default=None, repr=False, compare=False)

    @property
    def callable(self) -> Optional[Callable]:
        return self._fn

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "module": self.module,
            "callable_name": self.callable_name,
            "risk": self.risk.value,
            "side_effects": self.side_effects,
            "tags": list(self.tags),
            "bound": self._fn is not None,
        }


class ToolRegistry:
    """Registry of Nexus98 tool capabilities."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._seeded = False

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        tool_id: str,
        description: str,
        module: str,
        *,
        callable_name: Optional[str] = None,
        risk: RiskTier = RiskTier.READ_ONLY,
        side_effects: str = "none",
        tags: Optional[List[str]] = None,
        fn: Optional[Callable] = None,
    ) -> Tool:
        tool = Tool(
            id=tool_id,
            description=description,
            module=module,
            callable_name=callable_name,
            risk=RiskTier(risk) if not isinstance(risk, RiskTier) else risk,
            side_effects=side_effects,
            tags=list(tags or []),
            _fn=fn,
        )
        self._tools[tool_id] = tool
        return tool

    def bind(self, tool_id: str, fn: Callable) -> None:
        """Attach a live callable to an already-registered tool."""
        tool = self._tools.get(tool_id)
        if tool is None:
            raise KeyError(f"Unknown tool: {tool_id}")
        tool._fn = fn

    def unregister(self, tool_id: str) -> bool:
        return self._tools.pop(tool_id, None) is not None

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def get(self, tool_id: str) -> Optional[Tool]:
        return self._tools.get(tool_id)

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def describe(self, tool_id: str) -> Optional[dict]:
        tool = self._tools.get(tool_id)
        return tool.to_dict() if tool else None

    def search(self, query: str) -> List[Tool]:
        """Keyword search over id, description, and tags."""
        q = query.lower()
        results = []
        for t in self._tools.values():
            hay = " ".join([t.id, t.description] + t.tags).lower()
            if q in hay:
                results.append(t)
        return results

    def by_risk(self, risk: RiskTier) -> List[Tool]:
        return [t for t in self._tools.values() if t.risk == risk]

    def by_tag(self, tag: str) -> List[Tool]:
        return [t for t in self._tools.values() if tag in t.tags]

    def invoke(self, tool_id: str, *args, **kwargs):
        """Invoke a registered tool's bound callable, if present."""
        tool = self._tools.get(tool_id)
        if tool is None or tool._fn is None:
            raise RuntimeError(f"Tool {tool_id} is not callable/bound")
        return tool._fn(*args, **kwargs)

    # ------------------------------------------------------------------
    # Seed from existing codebase (introspection, no duplication)
    # ------------------------------------------------------------------

    def seed_from_modules(self, modules: Dict[str, object]) -> int:
        """Register public callables from already-imported modules.

        ``modules`` maps a registry namespace (e.g. ``"tools.file_tools"``)
        to the imported module object. Only public functions are registered,
        and each is tagged read_only / proposal by simple heuristics. This
        gives agents an accurate capability map without copying code.
        """
        before = len(self._tools)
        for namespace, mod in modules.items():
            for name, obj in vars(mod).items():
                if name.startswith("_"):
                    continue
                if not (inspect.isfunction(obj) or inspect.isbuiltin(obj)):
                    continue
                risk = RiskTier.READ_ONLY
                side_effects = "none"
                fn_name = name
                desc = (inspect.getdoc(obj) or name).strip().splitlines()
                desc = desc[0] if desc else name
                # Heuristic: functions that write/run are higher risk.
                low = name.lower()
                if any(k in low for k in ("write", "run", "execute", "start", "send")):
                    risk = RiskTier.MUTATION
                    side_effects = "may mutate workspace or invoke subprocess"
                elif any(k in low for k in ("list", "read", "get", "status", "scan")):
                    risk = RiskTier.READ_ONLY
                self.register(
                    f"{namespace}.{name}",
                    desc,
                    module=namespace,
                    callable_name=fn_name,
                    risk=risk,
                    side_effects=side_effects,
                    tags=[namespace.split(".")[-1], risk.value],
                    fn=obj,
                )
        self._seeded = True
        return len(self._tools) - before

    # ------------------------------------------------------------------
    # Agent-facing summary
    # ------------------------------------------------------------------

    def capability_summary(self) -> dict:
        """Compact, agent-readable map of available capabilities."""
        out: Dict[str, List[dict]] = {}
        for t in self._tools.values():
            out.setdefault(t.risk.value, []).append({
                "id": t.id,
                "description": t.description,
                "tags": t.tags,
            })
        return out


# Convenience singleton.
default_registry = ToolRegistry()
