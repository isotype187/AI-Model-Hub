"""Nexus98 Cognitive Bootstrap (read-only activation).

Activates the cognitive layer at startup without performing any mutating or
autonomous action. It:

  * runs Capability Awareness discovery (read-only),
  * runs the Framework Validation layer (read-only diagnostics),
  * assembles a unified Context snapshot (read-only),
  * optionally runs an advisory cognitive cycle on a startup objective.

Everything here is observational. No framework writes state, no config is
changed, and no autonomy decision is made. Safe to call from ``main.py`` or
Supervisor init. The result is a structured ``BootReport`` suitable for logging
or surfacing in the UI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from core.capability_awareness import CapabilityDiscoverer
from core.frameworks.validation import FrameworkValidator
from core.cognitive.context import ContextAssembler
from core.cognitive.orchestrator import CognitiveOrchestrator


@dataclass
class BootReport:
    """Read-only snapshot of the cognitive layer at startup."""

    capabilities: Dict = field(default_factory=dict)
    validation: Dict = field(default_factory=dict)
    context: Dict = field(default_factory=dict)
    cognitive_cycle: Optional[dict] = None
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "capabilities": self.capabilities,
            "validation": self.validation,
            "context": self.context,
            "cognitive_cycle": self.cognitive_cycle,
            "notes": self.notes,
        }

    def summary_line(self) -> str:
        healthy = self.validation.get("healthy", False)
        caps = self.capabilities.get("models", {}).get("total", 0)
        return (
            f"Cognitive boot: models={caps}, "
            f"validation={'healthy' if healthy else 'issues found'}"
        )


class CognitiveBootstrap:
    """Read-only startup activation of the cognitive layer."""

    def __init__(self, discoverer: Optional[CapabilityDiscoverer] = None,
                 validator: Optional[FrameworkValidator] = None,
                 context: Optional[ContextAssembler] = None,
                 orchestrator: Optional[CognitiveOrchestrator] = None):
        self.discoverer = discoverer or CapabilityDiscoverer()
        self.validator = validator or FrameworkValidator()
        self.context = context or ContextAssembler()
        self.orchestrator = orchestrator

    def activate(self, *, startup_objective: str = "",
                 run_cognitive_cycle: bool = False) -> BootReport:
        report = BootReport()
        # 1. Capabilities (read-only)
        snap = self.discoverer.discover()
        report.capabilities = snap.to_dict()
        # 2. Validation (read-only diagnostics)
        report.validation = self.validator.validate()
        # 3. Context (read-only)
        report.context = self.context.assemble(startup_objective).to_dict()
        # 4. Optional advisory cognitive cycle (no execution)
        if run_cognitive_cycle and self.orchestrator is not None:
            try:
                report.cognitive_cycle = self.orchestrator.run_cycle(
                    startup_objective or "system startup"
                ).to_dict()
            except Exception as e:  # advisory; never fail boot
                report.notes.append(f"cognitive_cycle skipped: {e}")
        if report.validation.get("failed"):
            report.notes.append(
                f"{report.validation['failed']} validation issue(s) detected"
            )
        return report


# Module-level convenience.
default_bootstrap = CognitiveBootstrap()
