# Nexus98 Framework Integration Architecture (2026-07-18)

This document records the implementation of the **framework integration layer**
that lets the verified frameworks cooperate. It extends (does NOT replace)
`core.coordination` and the framework ecosystem. All integration code is
additive and performs no autonomy-state mutation; the Supervisor, Router,
Governor, and Guardian remain authoritative in their domains.

## Phase 1 — Framework Integration Facade (`core/integration.py`)
- `FrameworkIntegrator` is the central coordination interface wiring every
  framework together:
  * Strategy: `strategy_guidance()` -> advisory `TaskHandoff` (role hint).
  * Model Intelligence: `model_recommendation()` -> advisory model pick.
  * Planning: `plan_handoff()` -> plan/task readiness view.
  * Workspace Continuity: `refresh_workspace_context()` -> reality snapshot.
  * Code/Knowledge Memory: `retrieve_knowledge()` -> relevant recall.
  * Evaluation & Review: `analyze_completion()` -> scored verdict.
- `build_task_context()` assembles a single `TaskContext` (pure data) from all
  connected frameworks. Coordination only — no side effects on assembly.
- `capability_report()` provides a one-shot "what can I see" view.

## Phase 2 — Supervisor Framework Hooks (`core/framework_hooks.py`)
- `SupervisorHooks` wraps the existing Supervisor lifecycle
  (detect_intent -> run_task / run_action_task) with advisory hooks:
  `on_task_start`, `on_task_plan`, `on_task_execute`, `on_task_complete`,
  `on_failure_recovery`, and `run_with_hooks()`.
- The Supervisor's behavior/authority is preserved: hooks call the supervisor's
  existing functions and only record framework context around them. Failures
  are recorded then re-raised (no suppression). No autonomous escalation.

## Phase 3 — Capability Awareness (`core/capability_awareness.py`)
- `CapabilityDiscoverer.discover()` runs at boot (read-only) and assembles a
  `CapabilitySnapshot` of available tools (Tool Registry), available models
  (Model Intelligence), runtime config, and noted limitations.
- It seeds the Tool Registry from existing tool modules and queries the model
  registry; it performs no downloads, no service starts, no config writes.

## Phase 4 — Framework Validation Layer (`core/frameworks/validation.py`)
- `FrameworkValidator` checks: framework availability (import + symbol),
  dependency presence (store/config files), configuration validity
  (`config/models.json`, `config/runtime.json`), and integration health
  (capability report runs). Produces a structured `validate()` report and a
  `summary_line()`.
- Read-only diagnostics — never mutates frameworks, configs, or autonomy state.

## Integration Points Created
- `core.integration.FrameworkIntegrator` <-> Strategy / Model / Planning /
  Workspace / Memory / Review frameworks.
- `core.framework_hooks.SupervisorHooks` <-> Supervisor (lifecycle) + Integrator.
- `core.capability_awareness.CapabilityDiscoverer` <-> Tool Registry / Model
  Intelligence / `core.config`.
- `core.frameworks.validation.FrameworkValidator` <-> all frameworks + config.

## Tests (+26)
- `test_integration_facade.py` (8), `test_supervisor_hooks.py` (6),
  `test_capability_awareness.py` (6), `test_framework_validation.py` (6).

## Validation
- Full suite: **209 passed** (baseline 183; +26, 0 failures).
- Protected files (`supervisor.py`, `system_config.json`, `governor.py`)
  mtimes unchanged. `supervisor.py` was NOT edited — hooks are an external
  wrapper. No `auto_execute`/autonomy-level change.
- Checkpoint: `backups/INTEGRATION_20260718_103243/`.

## Remaining Architecture Gaps
- The integration facade + hooks are not yet *auto-invoked* by the live
  Supervisor boot path; a thin call site in `main.py`/Supervisor init would
  activate boot-time capability discovery + validation reporting.
- P1 `auto_execute` alignment + P2 legacy-path cleanup remain blocked at file
  level (no approval / external lock), unchanged by this session.
- No end-to-end "real task" execution test against the live Supervisor was run
  (would require AutoGen/Ollama); hooks were validated against a fake
  supervisor to keep tests hermetic.
