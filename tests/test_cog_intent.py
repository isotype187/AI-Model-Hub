"""Intent Intelligence Framework tests."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.cognitive.intent import IntentAnalyzer, IntentType, Objective, Intent


@pytest.fixture
def analyzer():
    return IntentAnalyzer()


def test_classify_action(analyzer):
    i = analyzer.analyze("write a python script to fix the bug")
    assert i.intent_type == IntentType.ACTION


def test_classify_planning(analyzer):
    i = analyzer.analyze("plan the architecture and design the module")
    assert i.intent_type == IntentType.PLANNING


def test_classify_information(analyzer):
    i = analyzer.analyze("what is the status of the build")
    assert i.intent_type == IntentType.INFORMATION


def test_ambiguous_detection(analyzer):
    i = analyzer.analyze("do something with stuff")
    assert i.ambiguity > 0.0
    assert i.needs_clarification is True
    assert i.clarification_questions


def test_objective_extraction(analyzer):
    i = analyzer.analyze("create the API and write the tests then document it")
    assert len(i.objectives) >= 1


def test_confidence_scoring(analyzer):
    i = analyzer.analyze("write a python script to parse logs")
    assert 0.0 <= i.confidence <= 1.0
    assert i.confidence >= 0.5


def test_metadata_and_entities(analyzer):
    i = analyzer.analyze('read config.json and update "the parser"')
    assert i.metadata.get("classified_as")
    assert any("json" in e for e in i.entities)


def test_to_dict_roundtrip(analyzer):
    i = analyzer.analyze("review the code")
    d = i.to_dict()
    assert d["intent_type"] == i.intent_type.value

