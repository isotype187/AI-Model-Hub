# Nexus98 - Model Intelligence Specification

Status: DESIGN SPECIFICATION ONLY (documentation; no implementation, no production changes).
Source of truth: docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md (v2),
docs/NEXUS98_UI_DESIGN_SPECIFICATION.md, docs/NEXUS98_CODE_MEMORY_SPECIFICATION.md,
docs/NEXUS98_CODEBASE_INTELLIGENCE_REPORT.md.
Constraints: Tkinter/ttk only (no new UI deps); no new runtime dependencies unless separately
approved; Nexus98 does NOT own Git/recovery (Guardian does); the Autonomy Governor remains the
sole authority/writer of autonomy state; observability stays read-only in the UI.

This document defines the AI intelligence architecture: how Nexus98 understands intent, routes
models across local/cloud providers, auto-selects, honors user override, remembers capability, runs
multiple strategies, coordinates agents, and presents reasoning in the UI — all within the documented
safety boundaries. It does not change code, config, tests, Guardian, or dependencies.

## 1. Intent Understanding Layer

The Intent Understanding Layer turns a raw user request into a structured task description that
downstream selection (router/strategy/agent) can act on. It is the front door of the Intelligence Layer
(handoff #3).

### 1.1 Interpretation
- Input arrives via the chat-first conversation surface (handoff #10) or command-center actions.
- A lightweight classifier (keyword/structural rules today, per core/router.py; model-assisted later)
  parses the request into: intent_type, target artifacts (files/symbols/agents mentioned), action
  posture (informational vs. mutating), and constraints (local-only, privacy, cost cap).
- The layer produces a TaskIntent object (not free text) so selection is deterministic and auditable.
  This replaces the current ad-hoc route() keyword mapping with a typed contract.

### 1.2 Task type determination
Task types (non-exhaustive): query, explain, generate, edit, refactor, test, research, orchestrate,
recovery-request, session. Determination uses:
- Explicit signals (commands, selected Mode/Project, toolbar action).
- Structural cues (file paths, code symbols resolved via Code Memory, 'explain/trace/find' verbs).
- Confidence threshold: below threshold, the request is treated as conversational (safe/analytical) and
  never auto-mutates. Mutating intent requires the Governor/Project Engine path.
- Outcome: a TaskIntent that carries task_type + scope + risk hint, consumed by the Automatic Selection
  System. Informational tasks stay in the handoff Safe tier (automatic analysis/search/reports).

## 2. Model Router Design

The Model Router is the unified selection authority (handoff #7). It is NOT a model executor; it
chooses provider/model/strategy and returns a selection the execution layer honors.

### 2.1 Unified local/cloud provider abstraction
- A single ProviderAdapter interface: list_models(), get_model_meta(), health(), chat_completion()
  (or generate()), cost_estimate(). Concrete adapters: OllamaAdapter (local, today), and future
  CloudAdapter(s) behind the same interface.
- The router holds a registry of adapters; it never hardcodes provider URLs in call sites (fixes the
  current scattered localhost:11434 / 127.0.0.1:8000 / 127.0.0.1:8765 references noted in the
  intelligence report). Adapter endpoints come from config (providers.json + future config_manager).
- Local-first default (handoff #7, UI #5.3): local adapter is tried first; cloud is opt-in and
  configuration-driven, never auto-upgraded without user intent.

### 2.2 Provider independence
- Execution code (supervisor, api/vscode_bridge, core/pipeline) calls the router, not a provider
  directly. This retires the duplicate ollama_models()/vscode_bridge paths flagged as debt and enables
  local/cloud switching without touching callers.
- Adapters are swappable; adding a provider = adding an adapter + config entry, no changes to selection
  logic. Provider health/availability is reported by the adapter and surfaced read-only in the UI.

### 2.3 Model capability matching
- Each model carries a metadata record (from config/models.json + catalog + a new capabilities layer):
  category (coding/reasoning/vision/writing/embedding), context window, tags, roles (chat/edit/apply/
  autocomplete), cost tier, latency tier, and compatible agents.
- Matching scores a candidate model against the TaskIntent: required category/roles, context fit,
  capability tags, and any privacy/cost constraints. Highest score wins unless overridden.

## 3. Automatic Selection System

Given a TaskIntent, the router computes four coordinated selections. All are non-mutating to autonomy
state; they choose HOW to act, not WHETHER Nexus may act (that is the Governor's domain).

### 3.1 Model selection
- Score candidate models (Section 2.3) for the intent; pick the top by capability fit, then by
  Model Capability Memory performance/confidence, then by cost/latency preference.
- Honor the active strategy set's model bias (Section 6).

### 3.2 Provider selection
- Choose the adapter that serves the selected model and satisfies constraints (local-first; cloud only
  if the model is cloud-only or the user opted in). Availability/health gates the choice; an unavailable
  provider falls back to the next valid adapter with a logged reason.

### 3.3 Agent selection
- Agents are composed from models via config/models.yaml (architect/coder/reviewer/tester/...). The
  router maps intent -> required agent role(s), then binds each role to the selected model.
- Agent compatibility (UI #5.4) is enforced: a model incompatible with a role is not assigned.
- Selection reflects core/agent_registry status (online/role) and the orchestrator team.

### 3.4 Strategy selection
- Strategies (handoff #8: Fast, Accurate, Coding, Research, Creative, Safety First, Cost Efficient) are
  a SET, not a single mode. The router activates the strategies implied by intent + Mode/Project
  defaults, then resolves conflicts (Section 6).
- Strategy selection biases model/provider choice (e.g. Cost Efficient prefers local/cheap; Accurate
  prefers highest-capability model) without changing autonomy level.

## 4. User Override System

Override is always one action away and persists per Mode/Project (UI #5.7). Override never writes
autonomy state; it sets selection preferences the router respects.

### 4.1 Dropdown overrides
- Provider, Model, Strategy, and Agent selectors in the Smart AI dashboard (UI #5) expose current
  effective selection + a visible override control. Selecting a value pins it for the active
  Mode/Project; 'Auto' restores automatic selection.
- Overrides are sticky per Mode/Project and restored on return (UI workspace pin/collapse behavior).

### 4.2 Manual selection
- A user may fully manual-select provider+model+strategy+agent. Manual selection is recorded as the
  effective choice and shown as 'user override' in the reasoning view.

### 4.3 Recommendations
- The router always computes its automatic recommendation even when overridden, and surfaces it
  ('Suggested: qwen3-coder:30b — coding task, local, low cost'). Recommendations are non-binding.

### 4.4 Explanations
- Every effective selection (auto or override) carries a human-readable rationale: matched intent,
  capability score, cost/latency, strategy bias, and any fallback. This is the 'why it was chosen'
  required by UI #5.1/#5.2 and supports reasoning visibility (Section 8).

## 5. Model Capability Memory

A sub-store of memory (aligned with Code Memory's pattern: SQLite, schema_version, soft-delete) that
records how models actually perform, so selection improves over time. No secrets; performance only.

### 5.1 Performance tracking
- Per (model, task_type, strategy) tuple: success rate, latency p50/p95, cost incurred, user-acceptance
  of outputs, and failure/tamper flags. Written after task completion by the execution layer (governed
  hook), never by the model call itself.
- Tracks only aggregate signals; raw prompts/responses stay in conversation/episodic memory, not here.

### 5.2 Confidence scores
- Each model+task_type gets a confidence score (0-1) derived from performance history + verification
  status. The router uses confidence as a tie-breaker and as a visibility signal ('low confidence: few
  samples'). Mirrors memory_service confidence/importance fields.

### 5.3 Editable recommendations
- Users/operators can adjust a model's recommended use cases, compatible agents, and cost/latency tags
  (editability required by handoff #7 + UI #5.2). Edits are versioned (update_history) and marked
  source='user', so learned vs. curated metadata is distinguishable. Edits are local-only and
  configuration-driven; they do not alter autonomy state.

## 6. Strategy Engine

Strategies are simultaneously active and compose into the selection bias (handoff #8).

### 6.1 Multiple simultaneous strategies
- ActiveStrategies is a set; default seeded from Mode/Project. Examples can coexist: Coding + Accurate,
  or Research + Cost Efficient. Each strategy contributes weighted biases to model/provider scoring.

### 6.2 Strategy conflicts
- Conflicts arise when strategies pull opposite ways (Accurate wants best model; Cost Efficient wants
  cheapest). The engine detects conflicting biases rather than silently picking one.

### 6.3 Priority rules
- Resolution order (highest precedence first):
  1. Safety First — always wins; constrains to safe/verified models and local-first; never overridden by
     cost/latency.
  2. Explicit user override — beats automatic strategy bias.
  3. Mode/Project default strategy set.
  4. Task-type implied strategy.
  5. Cost/latency preference as the final tie-breaker among equally capable models.
- Conflicts are surfaced as an explanation ('Cost Efficient lowered model tier; Safety First kept local').

### 6.4 User customization
- Users add/remove strategies per Mode/Project and tune weights. Customization is preference data
  (settings), not autonomy state, and persists per workspace. New strategies are data, not code changes.

## 7. Agent Interaction Model

### 7.1 Cooperation
- The Intelligence Layer selects; the Execution Layer (supervisor + orchestrator + agent team) runs.
  Models are bound to agent roles by the router; agents cooperate as today via AutoGen, now with explicit,
  explainable model assignments instead of static config-only mapping.
- The supervisor's information path (run_task -> orchestrator/agents) and action path
  (run_action_task -> Project Engine proposals) are unchanged; the router only informs WHICH model/agent
  serves each step.

### 7.2 Task delegation
- Delegation is role-driven: intent -> required roles -> agent instances -> bound models. A coding task
  delegates to coder+reviewer; a research task to researcher; a planning task to architect. The router
  ensures each delegated role gets a capable, compatible, available model.
- Delegation stays inside the Governor's auto_execute floor and the trusted-workflow set (L2
  vscode_task_send today); new delegated workflows are added only via governance, never by the router.

## 8. UI Requirements

The Smart AI dashboard (UI #5) is the surface for all selection/override/reasoning.

### 8.1 Dropdown information
- Model dropdown shows: name, category, context window, strengths, weaknesses, compatible agents,
  recommended use cases, cost/latency tier, and live availability (handoff #7, UI #5.2).
- Provider dropdown shows availability/health; Strategy dropdown shows active set + weights; Agent
  dropdown shows registry status + model compatibility.

### 8.2 Recommendation display
- Current effective selection (provider/model/strategy/agents) is always visible, labeled Auto or
  Override, with the automatic suggestion shown alongside for one-click restore.

### 8.3 Reasoning visibility
- A collapsible 'why' panel shows the selection rationale (intent matched, capability score, strategy
  bias, cost/latency, fallback). Read-only; sourced from the router's explanation object. Consistent
  with the read-only autonomy observability invariant.

## 9. Safety Boundaries

### 9.1 Automatic (Safe tier, handoff #6)
Nexus may decide automatically, without approval:
- Intent classification and task-type detection.
- Provider/model/strategy/agent SELECTION (how to act) for informational and trusted-workflow tasks.
- Local-first provider preference and cloud opt-in honoring.
- Confidence/performance scoring and recommendation computation.
- Read-only reasoning display.

### 9.2 Requires approval (Medium/High risk, handoff #6)
Selection never grants execution authority. The following remain governed and OUTSIDE the router:
- Any code modification / configuration change / restructuring -> Project Engine + approval (Medium).
- Governor changes, Guardian changes, security changes, recovery changes -> Guardian-protected (High).
- Promoting a new autonomous workflow beyond the trusted set -> governance + checkpoint + human sign-off.
- Cloud execution when the user has not explicitly opted in (privacy/cost boundary).
- Editing autonomy state (supervisor.auto_execute / system_config) — Governor sole writer only.
The router may REQUEST but never EXECUTE these. UI selection is non-mutating to autonomy state.

## 10. Implementation Phases

Each phase follows the handoff Development Rule:
checkpoint -> analyze -> document -> approve -> implement -> validate.

- Phase 1 - Intent contract: typed TaskIntent + classifier replacing ad-hoc route(); read-only,
  no execution change. Validate against existing supervisor/router tests.
- Phase 2 - Provider abstraction: ProviderAdapter interface + OllamaAdapter; retire duplicate
  ollama_models()/vscode_bridge call sites behind the router. Validate local parity.
- Phase 3 - Router core: unified model/provider/agent/strategy selection with capability matching;
  non-mutating. Unit tests with temp DB/config.
- Phase 4 - Capability memory: performance/confidence store (SQLite) + editable recommendations;
  wired post-task via a governed hook. Validate scoring + edit versioning.
- Phase 5 - Strategy engine: simultaneous strategies, conflict detection, priority rules, per
  Mode/Project customization. Validate conflict explanations.
- Phase 6 - Override + UI: dropdown overrides, manual selection, recommendations, reasoning panel in
  the Smart AI dashboard (read-only display; only after the frozen GUI spec is approved).
- Phase 7 - Agent delegation wiring: bind selected models to agent roles; keep Governor floor + trusted
  workflows intact. Validate delegation without new autonomous permissions.
- Phase 8 - Cloud seam (deferred, opt-in): CloudAdapter behind config; local-first enforced; cloud only
  with explicit user opt-in. Highest privilege; implemented last, with Guardian/Governor sign-off.

Deferral note: cloud providers, self-editing, and any autonomy promotion are HIGH risk and require
separate approval + Guardian protection. The router is foundation work that unblocks the chat-first UI
and safer delegation.

*End of specification. No production files were modified.*
