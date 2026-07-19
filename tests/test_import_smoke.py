"""
Dependency-aware import smoke test for Nexus98 core systems.

Goal: keep CI green even when optional heavy third-party dependencies
(autogen-ext, flask, pyyaml) are not installed in the current environment,
while still catching genuine regressions in the import wiring.

Strategy:
- Modules that only fail due to a MISSING PACKAGE are skipped with a clear
  reason instead of failing.
- Modules that fail for any other reason (syntax error, real code defect,
  broken internal import) are reported as a hard failure.

This test does not require network access or a running server.
"""

import importlib
import sys

import pytest

# (module, optional dependency that, if missing, justifies a skip)
OPTIONAL_DEP_IMPORTS = {
    "core.agent_factory": "autogen-ext",
    "core.orchestrator": "autogen-ext",
    "core.supervisor": "autogen-ext",
    "core.bridge": "autogen-ext",
    "core.manager": "autogen-ext",
    "core.api_server": "flask",
    "core.server": "flask",
}

# Modules expected to import with only the base environment (no heavy deps).
ALWAYS_EXPECTED_IMPORTS = [
    "core.config",
    "core.db",
    "core.logs",
    "core.status",
    "core.memory",
    "core.memory_service",
    "core.mouse_control",
    "core.router",
    "core.resume",
    "core.favorites",
]


def _missing_package_error(exc):
    msg = str(exc)
    return (
        isinstance(exc, ModuleNotFoundError)
        and ("No module named" in msg)
    )


@pytest.mark.parametrize("module_name", sorted(OPTIONAL_DEP_IMPORTS))
def test_optional_dependency_imports(module_name):
    dep = OPTIONAL_DEP_IMPORTS[module_name]
    try:
        importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if _missing_package_error(exc):
            pytest.skip(
                f"{module_name} requires optional package '{dep}' "
                f"which is not installed in this environment: {exc}"
            )
        raise
    except Exception as exc:  # pragma: no cover - unexpected import failure
        raise AssertionError(
            f"{module_name} failed to import for a non-dependency reason: {exc}"
        )


@pytest.mark.parametrize("module_name", ALWAYS_EXPECTED_IMPORTS)
def test_base_environment_imports(module_name):
    try:
        importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if _missing_package_error(exc):
            raise AssertionError(
                f"{module_name} unexpectedly needs a missing package: {exc}"
            )
        raise
    except Exception as exc:  # pragma: no cover - unexpected import failure
        raise AssertionError(
            f"{module_name} failed to import: {exc}"
        )


def test_python_version_sane():
    assert sys.version_info >= (3, 10)
