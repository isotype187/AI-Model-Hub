"""Nexus98 Cognitive Architecture package.

Production intelligence frameworks that compose the verified foundation
(Strategy, Code Memory, Continuity, Planning, Review, Knowledge, Tool Registry,
Capability Awareness, Integration) into the internal cognitive layer.

These frameworks are advisory/representational: they model intent, goals,
plans, decisions, context, knowledge, execution preparation, review, learning,
and communication. They do NOT execute actions and do NOT change autonomy
state. The Supervisor, Router, Governor, and Guardian remain authoritative.

Modules:
  * intent      - intent understanding
  * goals       - long-term goal management
  * planning    - planning intelligence (execution/dependency/rollback graphs)
  * decision    - reusable decision engine
  * context     - unified context layer
  * knowledge   - knowledge graph
  * execution   - execution preparation (no execution)
  * review      - review intelligence
  * learning    - passive learning
  * comms       - unified communication layer

See docs/NEXUS98_COGNITIVE_ARCHITECTURE_20260718.md.
"""
from __future__ import annotations

__all__ = [
    "intent", "goals", "planning", "decision", "context",
    "knowledge", "execution", "review", "learning", "comms", "orchestrator", "bootstrap",
]


