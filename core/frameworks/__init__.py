"""Nexus98 internal framework ecosystem.

This package collects the architecture-layer frameworks built on top of the
verified foundation (Strategy Engine, Code Memory, Continuity, Tool Registry,
Coordination). Each framework is self-contained, additive, and performs no
autonomy-state mutation.

Frameworks:
  * workspace  - WWW / Workspace Reality Continuity
  * project    - Project Intelligence (extends Project Engine)
  * model      - Model Intelligence
  * knowledge  - Knowledge Architecture (extends Code Memory)
  * planning   - Planning (separate from execution authority)
  * review     - Evaluation & Review
  * extension  - Extension / Plugin lifecycle (complements Tool Registry)

See docs/NEXUS98_FRAMEWORK_ECOSYSTEM_20260718.md.
"""
from __future__ import annotations

__all__ = [
    "workspace",
    "project",
    "model",
    "knowledge",
    "planning",
    "review",
    "extension",
    "validation",
]


