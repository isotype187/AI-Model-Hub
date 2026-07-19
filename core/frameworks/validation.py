"""Nexus98 Framework Validation Layer.

Checks the health of the framework ecosystem before/after integration: which
frameworks are importable and instantiable, whether their stores are present,
whether declared dependencies (e.g. config files) exist, and whether obvious
configuration problems are present. Produces a structured report.

This layer is *read-only diagnostics*. It never mutates frameworks, configs,
autonomy state, or the Governor/Guardian surfaces. It is safe to run at
startup and in tests.
"""
from __future__ import annotations

import importlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(r"D:\Nexus98")

# Expected-empty data stores. The following dependency files are lazily
# created by their owning framework on first write; their absence on a
# clean/empty environment is an EXPECTED WARNING, not a defect or missing
# configuration. Each framework's _load() degrades gracefully to an empty
# store when the file is missing, so validation reports them as "failed"
# but the system remains fully functional. Left unchanged intentionally.
_EXPECTED_EMPTY_STORES = {
    "dep:frameworks.workspace:workspace.json",
    "dep:frameworks.review:reviews.json",
    "dep:frameworks.extension:extensions.json",
}

# Framework module -> the symbol we expect to instantiate, plus any required
# external dependency files. Used for availability + dependency checks.
_FRAMEWORKS = {
    "strategy": {
        "module": "core.strategy",
        "symbol": "default_controller",
        "deps": [],
    },
    "code_memory": {
        "module": "core.code_memory",
        "symbol": "default_memory",
        "deps": [ROOT / "data" / "db" / "memory.db"],
    },
    "continuity": {
        "module": "core.continuity",
        "symbol": "default_continuity",
        "deps": [ROOT / "data" / "continuity.json"],
    },
    "tool_registry": {
        "module": "core.tool_registry",
        "symbol": "default_registry",
        "deps": [],
    },
    "coordination": {
        "module": "core.coordination",
        "symbol": "default_coordinator",
        "deps": [],
    },
    "integration": {
        "module": "core.integration",
        "symbol": "default_integrator",
        "deps": [],
    },
    "frameworks.workspace": {
        "module": "core.frameworks.workspace",
        "symbol": "WorkspaceReality",
        "deps": [ROOT / "data" / "workspace.json"],
    },
    "frameworks.project": {
        "module": "core.frameworks.project",
        "symbol": "ProjectIntelligence",
        "deps": [],
    },
    "frameworks.model": {
        "module": "core.frameworks.model",
        "symbol": "ModelIntelligence",
        "deps": [ROOT / "config" / "models.json"],
    },
    "frameworks.knowledge": {
        "module": "core.frameworks.knowledge",
        "symbol": "KnowledgeArchitecture",
        "deps": [ROOT / "data" / "db" / "memory.db"],
    },
    "frameworks.planning": {
        "module": "core.frameworks.planning",
        "symbol": "PlanningEngine",
        "deps": [ROOT / "data" / "plans.json"],
    },
    "frameworks.review": {
        "module": "core.frameworks.review",
        "symbol": "ReviewSystem",
        "deps": [ROOT / "data" / "reviews.json"],
    },
    "frameworks.extension": {
        "module": "core.frameworks.extension",
        "symbol": "ExtensionRegistry",
        "deps": [ROOT / "data" / "extensions.json"],
    },
}


@dataclass
class CheckResult:
    """Result of a single validation check."""

    name: str
    ok: bool
    detail: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


class FrameworkValidator:
    """Runs availability, health, dependency, and config checks."""

    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root) if root else ROOT

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def check_framework_availability(self) -> List[CheckResult]:
        results: List[CheckResult] = []
        for name, spec in _FRAMEWORKS.items():
            try:
                mod = importlib.import_module(spec["module"])
                ok = hasattr(mod, spec["symbol"])
                results.append(CheckResult(
                    f"available:{name}", ok,
                    "symbol present" if ok else "symbol missing",
                ))
            except Exception as e:  # import failure
                results.append(CheckResult(f"available:{name}", False, str(e)[:120]))
        return results

    def check_dependencies(self) -> List[CheckResult]:
        results: List[CheckResult] = []
        for name, spec in _FRAMEWORKS.items():
            for dep in spec.get("deps", []):
                exists = Path(dep).exists()
                results.append(CheckResult(
                    f"dep:{name}:{Path(dep).name}", exists,
                    str(dep) if exists else "missing",
                ))
        return results

    def check_configuration(self) -> List[CheckResult]:
        """Lightweight config sanity (no mutation, read-only)."""
        results: List[CheckResult] = []
        models_json = self.root / "config" / "models.json"
        if models_json.exists():
            try:
                data = json.loads(models_json.read_text(encoding="utf-8-sig"))
                models = data.get("models", [])
                results.append(CheckResult(
                    "config:models_json_valid", True, f"{len(models)} models",
                ))
            except (json.JSONDecodeError, OSError) as e:
                results.append(CheckResult(
                    "config:models_json_valid", False, str(e)[:120],
                ))
        else:
            results.append(CheckResult("config:models_json_valid", False, "missing"))
        runtime = self.root / "config" / "runtime.json"
        results.append(CheckResult(
            "config:runtime_authority", runtime.exists(),
            str(runtime) if runtime.exists() else "missing",
        ))
        return results

    def check_integration_health(self) -> List[CheckResult]:
        """Verify the integration facade can assemble context end-to-end."""
        results: List[CheckResult] = []
        try:
            from core.integration import default_integrator
            report = default_integrator.capability_report()
            results.append(CheckResult(
                "integration:capability_report", isinstance(report, dict),
                f"keys={sorted(report.keys())}",
            ))
        except Exception as e:
            results.append(CheckResult(
                "integration:capability_report", False, str(e)[:120],
            ))
        return results

    # ------------------------------------------------------------------
    # Aggregate report
    # ------------------------------------------------------------------

    def validate(self) -> dict:
        checks = (
            self.check_framework_availability()
            + self.check_dependencies()
            + self.check_configuration()
            + self.check_integration_health()
        )
        passed = sum(1 for c in checks if c.ok)
        failed = [c.to_dict() for c in checks if not c.ok]
        # Document which failures are EXPECTED (absent data stores on a clean
        # environment) so callers can distinguish real defects from routine
        # state. These remain listed under "failures" and still count toward
        # "failed"; they are not auto-suppressed so the report stays truthful.
        expected_failures = [
            f for f in failed if f["name"] in _EXPECTED_EMPTY_STORES
        ]
        return {
            "total": len(checks),
            "passed": passed,
            "failed": len(failed),
            "healthy": failed == [],
            "failures": failed,
            "expected_failures": expected_failures,
            "checks": [c.to_dict() for c in checks],
        }

    def summary_line(self) -> str:
        r = self.validate()
        return (
            f"Framework validation: {r['passed']}/{r['total']} ok"
            + ("" if r["healthy"] else f", {r['failed']} issues")
        )
