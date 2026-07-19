"""Communication Framework tests (unified in-process bus)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.cognitive.comms import CommunicationBus, Message, CHANNELS


@pytest.fixture
def bus():
    return CommunicationBus()


def test_channels_defined(bus):
    assert "supervisor" in CHANNELS and "api" in CHANNELS


def test_publish_delivers_to_subscriber(bus):
    received = []
    bus.subscribe("supervisor", lambda m: received.append(m))
    bus.notify_supervisor("task_start", {"task": "x"})
    assert len(received) == 1
    assert received[0].event == "task_start"


def test_unsubscribe(bus):
    received = []
    handler = lambda m: received.append(m)
    bus.subscribe("router", handler)
    bus.unsubscribe("router", handler)
    bus.notify_router("route", {})
    assert received == []


def test_message_envelope(bus):
    m = bus.notify_memory("stored", {"id": "1"})
    assert isinstance(m, Message)
    assert m.to_dict()["channel"] == "memory"


def test_history_and_counts(bus):
    bus.notify_supervisor("a", {})
    bus.notify_supervisor("b", {})
    bus.notify_ui("c", {})
    assert bus.channel_counts()["supervisor"] == 2
    assert len(bus.history(channel="supervisor")) == 2


def test_subscriber_failure_isolated(bus):
    bad = lambda m: (_ for _ in ()).throw(Exception("boom"))
    bus.subscribe("strategy", bad)
    good = []
    bus.subscribe("strategy", lambda m: good.append(m))
    bus.notify_strategy("eval", {})
    assert good  # other subscriber still received


def test_unknown_channel_recorded(bus):
    m = bus.publish("nonexistent_channel", "evt", {})
    assert m.channel == "nonexistent_channel"
