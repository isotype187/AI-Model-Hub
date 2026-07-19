"""Phase 4: Framework Validation Layer tests."""
from __future__ import annotations

import sys
from pathlib import Path
import tempfile

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.frameworks.validation import FrameworkValidator, CheckResult


@pytest.fixture
def validator(tmp_path):
    return FrameworkValidator(root=tmp_path)


def test_framework_availability_checks(validator):
    results = validator.check_framework_availability()
    names = {r.name for r in results}
    assert "available:strategy" in names
    assert "available:integration" in names
    assert "available:frameworks.model" in names


def test_dependency_checks_present(validator):
    results = validator.check_dependencies()
    # Dependency checks reference the real framework store files (e.g. the
    # memory.db used by Code Memory / Knowledge frameworks).
    names = {r.name for r in results}
    assert any("memory.db" in n for n in names)


def test_configuration_checks(validator):
    results = validator.check_configuration()
    names = {r.name for r in results}
    assert "config:runtime_authority" in names
    # Under tmp_path, runtime.json is absent -> reported as a config issue.
    rt = [r for r in results if r.name == "config:runtime_authority"][0]
    assert rt.ok is False


def test_integration_health_check(validator):
    results = validator.check_integration_health()
    names = {r.name for r in results}
    assert "integration:capability_report" in names


def test_validate_aggregates(validator):
    rep = validator.validate()
    assert rep["total"] == len(rep["checks"])
    assert rep["passed"] <= rep["total"]
    assert isinstance(rep["healthy"], bool)


def test_summary_line(validator):
    line = validator.summary_line()
    assert "Framework validation" in line

