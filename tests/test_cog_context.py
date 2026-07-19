"""Context Intelligence Framework tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.cognitive.context import ContextAssembler, TaskContext
from core.frameworks.workspace import WorkspaceReality
from core.frameworks.model import ModelIntelligence
from core.tool_registry import ToolRegistry
import tools.file_tools as file_tools


@pytest.fixture
def assembler(tmp_path):
    real_root = tmp_path
    reality = WorkspaceReality(real_root / "workspace.json")
    reality.register_project("Nexus98")
    reality.set_state("phase", "build")
    registry = ToolRegistry()
    registry.seed_from_modules({"tools.file_tools": file_tools})
    # model intelligence uses real config (read-only)
    mi = ModelIntelligence()
    return ContextAssembler(reality=reality, models=mi, registry=registry)


def test_assemble_unified_context(assembler):
    ctx = assembler.assemble("implement the router", active_project="Nexus98",
                             strategy=["coding"])
    d = ctx.to_dict()
    assert d["objective"] == "implement the router"
    assert d["active_project"] == "Nexus98"
    assert d["workspace"]["active_projects"] == ["Nexus98"]
    assert d["available_tools"]  # file_tools registered
    assert d["loaded_models"]    # models from config


def test_context_to_dict_roundtrip(assembler):
    ctx = assembler.assemble("x")
    assert isinstance(ctx, TaskContext)
    assert "objective" in ctx.to_dict()


def test_snapshot_helper(assembler):
    snap = assembler.snapshot("objective here")
    assert snap["objective"] == "objective here"
