"""
Nexus98 supervisor compatibility bridge.
Loads core\supervisor.py implementation and re-exports it as the
``core.supervisor`` module so that live attribute reads (e.g. auto_execute)
and test monkeypatches resolve to the executing implementation module.
"""

from pathlib import Path
import importlib.util
import sys

_impl_path = Path(__file__).parent.parent / "supervisor.py"

_spec = importlib.util.spec_from_file_location(
    "core.supervisor_impl",
    _impl_path
)

_module = importlib.util.module_from_spec(_spec)

sys.modules["core.supervisor_impl"] = _module

_spec.loader.exec_module(_module)

# Re-export the implementation as this package module. This keeps the package
# namespace live (attribute overrides and monkeypatches reach the code that
# actually runs) instead of snapshotting names at import time.
sys.modules[__name__] = _module