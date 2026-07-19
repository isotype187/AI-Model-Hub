"""Agent Coordination integration tests (advisory glue only)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import tools.file_tools as file_tools
from core.coordination import AgentCoordinator, TaskHandoff
from core.code_memory import CodeMemory
from core.continuity import WorkspaceContinuity
from core.tool_registry import ToolRegistry
from core.strategy import StrategyController


@pytest.fixture
def coordinator(tmp_path):
    db = tmp_path / "cm.db"
    cont = tmp_path / "cont.json"
    reg = ToolRegistry()
    reg.seed_from_modules({"tools.file_tools": file_tools})
    co = AgentCoordinator(
        strategy=StrategyController(),
        memory=CodeMemory(project="coord", db_path=db),
        continuity=WorkspaceContinuity(cont),
        registry=reg,
    )
    yield co
    co.memory.close()
    co.continuity.close()


def test_plan_handoff_recommends_role(coordinator):
    h = coordinator.plan_handoff("write a python script", strategy=frozenset({"coding"}))
    assert isinstance(h, TaskHandoff)
    assert h.recommended_role in {"coder", "researcher"}
    assert len(coordinator.last_handoffs()) == 1


def test_plan_handoff_autonomous_enforces_safety(coordinator):
    h = coordinator.plan_handoff(
        "ship the feature", strategy=frozenset({"cost_efficient"}), autonomous=True
    )
    assert h.safety_constrained is True
    assert "safety_first" in h.strategy


def test_coordinator_memory_roundtrip(coordinator):
    mid = coordinator.remember("decision", "Use tiers for tools", tags=["tools"])
    recs = coordinator.recall(category="decision")
    assert any("Use tiers for tools" in r["content"] for r in recs)


def test_coordinator_continuity_tracking(coordinator):
    tid = coordinator.track_task("Implement tool registry")
    assert coordinator.continuity.active_tasks()
    coordinator.complete_tracked(tid)
    assert coordinator.continuity.active_tasks() == []


def test_coordinator_tool_discovery(coordinator):
    found = coordinator.discover_tools("file")
    assert any("file_tools" in t["id"] for t in found)


def test_coordinator_does_not_touch_autonomy_state(coordinator):
    # Coordination is glue; it must not expose autonomy mutators.
    assert not hasattr(coordinator, "set_auto_execute")
    assert not hasattr(coordinator, "request_level_change")
