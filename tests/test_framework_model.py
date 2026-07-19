"""Model Intelligence framework tests."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.frameworks.model import ModelIntelligence, ModelProfile


@pytest.fixture
def mi(tmp_path):
    # Build a tiny models config to avoid depending on the real one.
    cfg = tmp_path / "models.json"
    cfg.write_text(
        '{"models": ['
        '{"name":"Coder","ollama":"coder:1b","category":"coding","priority":10,'
        '"context":32768,"tags":["python","debug"],"roles":["edit","apply"]},'
        '{"name":"Reasoner","ollama":"reason:1b","category":"reasoning","priority":9,'
        '"context":65536,"tags":["planning","analysis"],"roles":["chat"]},'
        '{"name":"General","ollama":"gen:1b","category":"general","priority":5,'
        '"context":8192,"tags":["chat"],"roles":["chat"]}'
        ']}',
        encoding="utf-8",
    )
    return ModelIntelligence(models_json=cfg)


def test_loads_profiles(mi):
    assert mi.load() == 3
    assert mi.get("coder:1b").category == "coding"


def test_recommend_by_task(mi):
    rec = mi.recommend("write a python script")
    assert rec.ollama == "coder:1b"
    expl = mi.explain_recommendation("plan the architecture")
    assert expl["recommendation"] == "reason:1b"
    assert expl["cost_tier"] == "local"


def test_category_filter(mi):
    rec = mi.recommend("chat casually", category="general")
    assert rec.ollama == "gen:1b"


def test_strengths_weaknesses_awareness(mi):
    prof = mi.get("coder:1b")
    assert "code generation" in prof.strengths
    assert "long-form prose" in prof.weaknesses


def test_availability_filter(mi):
    mi.set_availability("coder:1b", False)
    rec = mi.recommend("write python", available_only=True)
    assert rec.ollama != "coder:1b"
    rec2 = mi.recommend("write python", available_only=False)
    assert rec2.ollama == "coder:1b"


def test_capability_summary(mi):
    s = mi.capability_summary()
    assert s["total"] == 3
    assert "coding" in s["categories"]
