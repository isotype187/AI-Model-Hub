"""Tool Registry & Capability System tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import tools.file_tools as file_tools
import tools.git_tools as git_tools
from core.tool_registry import ToolRegistry, RiskTier, Tool


def test_register_and_describe():
    r = ToolRegistry()
    r.register(
        "demo.read",
        "Read a file safely",
        module="tools.demo",
        risk=RiskTier.READ_ONLY,
        tags=["io"],
    )
    tool = r.get("demo.read")
    assert isinstance(tool, Tool)
    d = r.describe("demo.read")
    assert d["risk"] == "read_only"
    assert d["tags"] == ["io"]


def test_search_and_by_risk():
    r = ToolRegistry()
    r.register("a.list", "list files", "tools.a", risk=RiskTier.READ_ONLY, tags=["io"])
    r.register("a.write", "write file", "tools.a", risk=RiskTier.MUTATION, tags=["io"])
    assert len(r.search("file")) == 2
    assert len(r.by_risk(RiskTier.MUTATION)) == 1
    assert len(r.by_tag("io")) == 2


def test_bind_and_invoke():
    r = ToolRegistry()

    def _double(x):
        return x * 2

    r.register("math.double", "double a number", "tools.math", fn=_double)
    assert r.invoke("math.double", 3) == 6


def test_invoke_unbound_raises():
    r = ToolRegistry()
    r.register("x.y", "noop", "m")
    with pytest.raises(RuntimeError):
        r.invoke("x.y")


def test_seed_from_modules_introspects():
    r = ToolRegistry()
    added = r.seed_from_modules({
        "tools.file_tools": file_tools,
        "tools.git_tools": git_tools,
    })
    assert added >= 2
    ids = [t.id for t in r.list_tools()]
    assert "tools.file_tools.list_files" in ids
    assert "tools.git_tools.git_status" in ids


def test_seed_makes_tools_invocable():
    r = ToolRegistry()
    r.seed_from_modules({"tools.file_tools": file_tools})
    out = r.invoke("tools.file_tools.list_files")
    assert isinstance(out, str)


def test_capability_summary_groups_by_risk():
    r = ToolRegistry()
    r.seed_from_modules({"tools.file_tools": file_tools})
    summary = r.capability_summary()
    assert "read_only" in summary
