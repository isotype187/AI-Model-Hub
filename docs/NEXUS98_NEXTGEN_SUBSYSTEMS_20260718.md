# Nexus98 Next-Generation Subsystems (2026-07-18)

This document records the implementation of five production subsystems that
extend (not replace) the stable Nexus98 foundation. All new code is additive,
performs no autonomy-state mutation, and preserves the Governor/Guardian
safety boundaries.

## 1. Strategy Engine Integration (`core/strategy/`)

**Before:** `core/strategy/__init__.py` held a pure-data catalog only.

**Now:**
- `core/strategy/catalog.py` — pure-data strategy catalog, bias composition,
  conflict detection, explanation (extracted from the old `__init__.py`).
- `core/strategy/controller.py` — `StrategyController`, the advisory bridge
  between the catalog and runtime (Supervisor / Router / Project Engine).
- `core/strategy/__init__.py` — re-exports the catalog + controller.

`StrategyController.evaluate(task, active, autonomous=)` returns a
`StrategyDecision` containing a bias vector, a recommended Router role, a
`safety_constrained` flag, detected conflicts, and a human-readable
explanation. When `autonomous=True`, `safety_first` is auto-injected so the
Safety First boundary can never be silently dropped. The controller is
stateless and performs no IO. It never flips `auto_execute` and exposes no
autonomy mutators.

## 2. Code Memory Foundation (`core/code_memory.py`)

Built on the existing `MemoryService` (SQLite). `CodeMemory` is project-scoped
and provides:
- Knowledge categories: `decision`, `pattern`, `constraint`, `bug`, `context`,
  `history`.
- `record_decision` / `record_knowledge` / `record_history` for agents.
- `recall(category=, tags=, min_importance=)` with AND tag filtering.
- `search(text)` free-text ranking across project knowledge.
- `verify` / `forget` (soft-archive) delegation to `MemoryService`.
- `stats()` for a per-project summary.

It does not replace `MemoryService` or the legacy `Memory` shim; it is a
semantic layer on top. All persistence stays in `data/db/memory.db`.

## 3. Workspace Continuity Foundation (`core/continuity.py`)

Extends the legacy `core/resume.py` into a structured store
(`data/continuity.json`) with:
- Active task tracking (`start_task` / `update_task` / `complete_task`).
- Workspace state snapshots (`set_workspace_state`).
- Development context preservation (`set_context`).
- Recovery information (`set_recovery`: last checkpoint, resume hint,
  last good phase).
- `snapshot()` resume-oriented summary and corruption-safe load (backs up a
  corrupt store and starts fresh rather than crashing).

The legacy `save_state` / `load_state` API is preserved as a shim.

## 4. Tool Registry & Capability System (`core/tool_registry.py`)

A single authoritative catalog of agent-visible capabilities. It does NOT
re-implement tools — it *describes* existing ones. Provides:
- `register(...)` with `RiskTier` (read_only / proposal / mutation /
  infrastructure), side-effects, and tags.
- `seed_from_modules(...)` to introspect already-imported modules and register
  their public callables with a conservative risk heuristic.
- `search` / `by_risk` / `by_tag` discovery.
- `invoke` to call a bound tool, and `capability_summary()` for agents.

This gives future agents an accurate capability map before acting, without
duplicating the existing tool system.

## 5. Agent Coordination (`core/coordination.py`)

A thin facade wiring the subsystems together with clean interfaces:
- `plan_handoff(task, strategy, autonomous=)` -> `TaskHandoff` (strategy
  guidance + Router role hint; does not route).
- Memory / continuity / tool discovery delegation.
- Structured handoff logging.

It owns no state of its own beyond references to subsystem instances and never
changes autonomy state.

## Tests

New modules each carry dedicated pytest suites (temp DB / temp file only; the
real `data/` store is never touched):
- `tests/test_strategy_integration.py` (8)
- `tests/test_code_memory.py` (7)
- `tests/test_continuity.py` (7)
- `tests/test_tool_registry.py` (7)
- `tests/test_coordination.py` (6)

Full suite: **141 passed** (baseline 106).

## Safety Notes

- No `auto_execute` change; no autonomy-level change.
- Governor (`core/autonomy/governor.py`) remains the sole writer of autonomy
  state; none of the new code imports or invokes it for writes.
- Protected files (`supervisor.py`, `system_config.json`, `governor.py`)
  mtimes unchanged by this work.
