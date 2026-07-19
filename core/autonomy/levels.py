"""Phase 8 - Autonomy Governor: level definitions (declarative, no side effects).

This module is PURE DATA + helpers. It never writes supervisor.auto_execute
or config. The Governor (governor.py) is the only writer of autonomy state.
"""

from typing import Dict, FrozenSet, List

# Level names (L0-L4). Levels are strictly ordered.
LEVEL_NAMES = {
    0: "Manual only",
    1: "Assisted operation",
    2: "Trusted workflows",
    3: "Expanded autonomous workflows",
    4: "Experimental / restricted",
}

# Permission summary per level (human-readable; not enforced here).
LEVEL_PERMISSIONS = {
    0: ["read-only queries", "no proposals executed"],
    1: ["propose + checkpoint", "human approves before execution", "no auto-write"],
    2: ["trusted-workflow set auto-executes after checkpoint + validation",
       "everything else stays Level 1"],
    3: ["expanded workflow set auto-executes",
       "risky actions still gated by require_approval_for_risky_actions"],
    4: ["experimental set only", "sandbox + full audit", "auto-off on anomaly"],
}

# The trusted Level 2 workflow set. Seeded with the already-validated
# Phase 7 vscode_task_send promotion. No other workflow is added here.
TRUSTED_WORKFLOWS_L2: FrozenSet[str] = frozenset({"vscode_task_send"})

# Expanded Level 3 set starts empty; added one-at-a-time under governance.
TRUSTED_WORKFLOWS_L3: FrozenSet[str] = frozenset()

# Experimental Level 4 set starts empty; explicit opt-in toggle only.
TRUSTED_WORKFLOWS_L4: FrozenSet[str] = frozenset()


def level_name(level: int) -> str:
    return LEVEL_NAMES[level]


def allowed_workflows(level: int) -> FrozenSet[str]:
    """Return the set of workflow names permitted to auto-execute at `level`."""
    if level <= 1:
        return frozenset()
    allowed = set(TRUSTED_WORKFLOWS_L2)
    if level >= 3:
        allowed |= set(TRUSTED_WORKFLOWS_L3)
    if level >= 4:
        allowed |= set(TRUSTED_WORKFLOWS_L4)
    return frozenset(allowed)


def is_workflow_allowed(workflow: str, level: int) -> bool:
    return workflow in allowed_workflows(level)


def max_level() -> int:
    return max(LEVEL_NAMES.keys())


def valid_level(level: int) -> bool:
    return level in LEVEL_NAMES
