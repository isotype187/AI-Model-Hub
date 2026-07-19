"""Nexus98 Communication Framework.

A unified, standardized communication layer that coordinates information
*flow* between the major subsystems: Supervisor, Router, Planning, Strategy,
Memory, Knowledge, Context, Tool Registry, Capability Awareness, Project
Engine, UI, Bridge, and API.

This framework does NOT replace existing communication channels (the bridge,
API, UI signals). It provides a single in-process message bus + a typed
``Message`` envelope so subsystems can publish/subscribe without hard-coded
coupling. It is a coordinator, not an executor: messages are delivered to
in-memory subscribers only; no external sends occur here.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional


# Channels correspond to the subsystems that exchange information.
CHANNELS = (
    "supervisor", "router", "planning", "strategy", "memory", "knowledge",
    "context", "tool_registry", "capability", "project_engine", "ui",
    "bridge", "api", "system",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Message:
    """A standardized, typed message envelope."""

    message_id: str
    channel: str
    event: str
    payload: dict
    source: str = "system"
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "message_id": self.message_id, "channel": self.channel,
            "event": self.event, "payload": self.payload,
            "source": self.source, "created_at": self.created_at,
        }


class CommunicationBus:
    """In-process pub/sub bus with standardized message envelopes."""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Message], None]]] = {
            ch: [] for ch in CHANNELS
        }
        self._history: List[dict] = []

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(self, channel: str, handler: Callable[[Message], None]) -> bool:
        if channel not in self._subscribers:
            return False
        self._subscribers[channel].append(handler)
        return True

    def unsubscribe(self, channel: str, handler: Callable[[Message], None]) -> bool:
        if channel not in self._subscribers:
            return False
        if handler in self._subscribers[channel]:
            self._subscribers[channel].remove(handler)
            return True
        return False

    # ------------------------------------------------------------------
    # Publishing (in-process delivery only)
    # ------------------------------------------------------------------

    def publish(self, channel: str, event: str, payload: dict,
                *, source: str = "system") -> Message:
        if channel not in self._subscribers:
            # Unknown channel: still record, but do not deliver.
            msg = Message(uuid.uuid4().hex[:12], channel, event, payload, source)
            self._history.append(msg.to_dict())
            return msg
        msg = Message(uuid.uuid4().hex[:12], channel, event, payload, source)
        for handler in list(self._subscribers[channel]):
            try:
                handler(msg)
            except Exception:
                # A failing subscriber must not break the bus.
                continue
        self._history.append(msg.to_dict())
        return msg

    # ------------------------------------------------------------------
    # Convenience relays (typed helpers per subsystem)
    # ------------------------------------------------------------------

    def notify_supervisor(self, event: str, payload: dict) -> Message:
        return self.publish("supervisor", event, payload, source="comms")

    def notify_router(self, event: str, payload: dict) -> Message:
        return self.publish("router", event, payload, source="comms")

    def notify_planning(self, event: str, payload: dict) -> Message:
        return self.publish("planning", event, payload, source="comms")

    def notify_strategy(self, event: str, payload: dict) -> Message:
        return self.publish("strategy", event, payload, source="comms")

    def notify_memory(self, event: str, payload: dict) -> Message:
        return self.publish("memory", event, payload, source="comms")

    def notify_ui(self, event: str, payload: dict) -> Message:
        return self.publish("ui", event, payload, source="comms")

    def notify_project_engine(self, event: str, payload: dict) -> Message:
        return self.publish("project_engine", event, payload, source="comms")

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def history(self, channel: Optional[str] = None, limit: Optional[int] = None) -> List[dict]:
        h = self._history
        if channel:
            h = [m for m in h if m["channel"] == channel]
        if limit:
            h = h[-limit:]
        return h

    def channel_counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for m in self._history:
            out[m["channel"]] = out.get(m["channel"], 0) + 1
        return out
