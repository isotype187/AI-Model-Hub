# Nexus98 Constitution

> Status: SINGLE SOURCE OF TRUTH (structural master). This document does not
> replace, merge, or delete any existing document. It is an umbrella that
> enumerates the complete structure of the Nexus98 knowledge base and
> cross-references the authoritative detailed documents.
>
> Rule: Do not invent architecture. Every section below references the existing
> document(s) that currently hold the detail. All statements here are drawn from
> the referenced docs and finalized architecture decisions; no new architecture
> is introduced.

## Table of Contents

- [1. Foundational Handoff & Vision](#1-foundational-handoff--vision)
- [2. Project Identity & Migration](#2-project-identity--migration)
- [3. Core Architecture Layers](#3-core-architecture-layers)
- [4. Autonomy Model & Governor](#4-autonomy-model--governor)
- [5. Guardian (Separate Project)](#5-guardian-separate-project)
- [6. Configuration Authority](#6-configuration-authority)
- [7. UI Architecture & Design](#7-ui-architecture--design)
- [8. Intelligence Layer: Model & Strategy](#8-intelligence-layer-model--strategy)
- [9. Memory Architecture](#9-memory-architecture)
- [10. Code Memory](#10-code-memory)
- [11. Execution Layer: Supervisor & Project Engine](#11-execution-layer-supervisor--project-engine)
- [12. Agents & Orchestration](#12-agents--orchestration)
- [13. Model & Provider Systems](#13-model--provider-systems)
- [14. Tools & Integrations](#14-tools--integrations)
- [15. Mouse Agent System](#15-mouse-agent-system)
- [16. Conversation & Context Systems](#16-conversation--context-systems)
- [17. Documents, WWW & Dont Forget](#17-documents-www--dont-forget)
- [18. VS Code Integration & Workflow](#18-vs-code-integration--workflow)
- [19. Current Repository Intelligence](#19-current-repository-intelligence)
- [20. Extension Points](#20-extension-points)
- [21. Future Architecture & Gap Analysis](#21-future-architecture--gap-analysis)
- [22. Technical Debt](#22-technical-debt)
- [23. Phase 5 — Stability Before Autonomy](#23-phase-5--stability-before-autonomy)
- [24. Phase 7 — Level 2 Activation](#24-phase-7--level-2-activation)
- [25. Phase 7.5 — Autonomy Control Interface](#25-phase-75--autonomy-control-interface)
- [26. Phase 8 — Autonomy Governor](#26-phase-8--autonomy-governor)
- [27. Phase 9 — UI Overhaul](#27-phase-9--ui-overhaul)
- [28. Autonomous Operating Rules](#28-autonomous-operating-rules)
- [29. Implementation Governance & Development Rule](#29-implementation-governance--development-rule)
- [30. Document Index & Cross-Reference Map](#30-document-index--cross-reference-map)

---

## 1. Foundational Handoff & Vision

> Cross-reference: `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md` (source of truth), `docs/Nexus98_Vision_Architecture.md`.

### 1.1 Purpose of the Handoff

The Master Architecture Handoff v2 is the canonical source of truth that preserves design intent across ChatGPT architecture sessions, Codex implementation sessions, and future development. It defines the project identity, vision, core architecture, Guardian separation, autonomy model, and current development status. It exists so that architectural decisions are not lost or silently overridden between sessions.

### 1.2 Vision Statement

Nexus98 is a local-first AI operating environment capable of managing conversations, models, providers, agents, projects, tools, code, memory, documentation, and workflows while maintaining safety, recoverability, continuity, and user control. The goal of autonomy is to let the system propose, checkpoint, and — when authorized — execute controlled operations without sacrificing safety or reversibility.

### 1.3 Design Tenets

- Local-first: models and data stay on the workstation; no required cloud.
- Safety by default: execution is gated; `auto_execute = False` at rest.
- Checkpoint everything: every mutation is reversible.
- Transparent routing: intent is classified and routed explicitly.
- Graceful degradation: failures are caught and reported, never silent.

### 1.4 Development Rule (canonical)

Every implementation step follows: checkpoint -> analyze -> document -> approve -> implement -> validate. No major UI implementation begins until the design specification is complete. Codex immediate tasks are read-only (architecture inventory, migration map, extension analysis, risk report) and explicitly must NOT rewrite UI, merge Guardian, alter autonomy logic, change workflows, or modify production behavior.

*Diagram placeholder: Handoff -> Vision -> Layers relationship map.*

---

## 2. Project Identity & Migration

> Cross-reference: `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md` (#1), `docs/README.md`.

### 2.1 Current Project

The current project is **Nexus98**. It is a local-first AI operating/workstation hub that coordinates local models, project automation, and developer tooling under a supervised agent runtime.

### 2.2 Historical Origin (AI Model Hub)

Nexus98 originated as **AI Model Hub** and migrated to Nexus98. Historical AI Model Hub references still exist in parts of the tree (e.g. `core/identity.py` branding, legacy strings in `main.py`/`launcher.py`, some health-check banners). These are intentional and must not be blindly replaced.

### 2.3 Migration Policy (no blind replacement)

Migration from AI Model Hub -> Nexus98 should be intentional and verified. Blind replacement of the "AI Model Hub" string is prohibited. Legacy/archive trees (`AI_Model_Hub_archive/`, `archive/`, `diagnostic_parts/`, `ollama_cleanup_backups/`) are superseded and NOT live components.

### 2.4 Remaining Naming Inconsistencies

- `core/identity.py` still identifies as "AI Model Hub Agent" while Operating Rules use "Nexus98 Agent" (cosmetic; unify in a later branding pass).
- `main.py` prints "Starting AI Model Hub..."; `launcher.py` prints "AI Model Hub launcher ready".
- `api/vscode_bridge.py` health reports `"service":"AI Hub Bridge"`; `config/vscode.json` names it "AI Hub VS Code Bridge".
- `tools/health_check.py` banner reads "AI MODEL HUB ADVANCED HEALTH CHECK".
- `config/system_context.json.current_phase` is stale ("AutoGen Multi-Agent Foundation") vs actual Phase 6 documentation stage.

---

## 3. Core Architecture Layers

> Cross-reference: `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md` (#3), `docs/CURRENT_ARCHITECTURE_MAP.md`, `docs/Nexus98_Vision_Architecture.md` (#3).

### 3.1 User Interface Layer

Responsible for interaction, dashboards, conversations, controls, and visualization. Implemented as a Tkinter/ttk "Command Center" (`ui/main_window.py`) with a 7-tab `ttk.Notebook`; future design moves to a chat-first workspace model. The UI never writes autonomy state; it observes via `ui.autonomy_dashboard.snapshot()` and requests via the Governor.

### 3.2 Intelligence Layer

Responsible for model routing, agent selection, strategy selection, and context selection. Implemented today only partially (keyword `router.py`); the future unified Model Router + Strategy Engine is specified in `docs/NEXUS98_MODEL_INTELLIGENCE_SPECIFICATION.md`.

### 3.3 Execution Layer

Responsible for tasks, tools, coding, and workflows. Implemented via `core/supervisor.py` (intent detection + routing) and `core/project_engine.py` (the sole file-mutation authority). Action intents flow through proposals -> checkpoint requests -> Project Engine; information intents flow to the orchestrator/agents.

### 3.4 Memory Layer

Responsible for knowledge, code understanding, and continuity. Implemented as `core/memory_service.py` (SQLite, Phase 1 foundation) plus the future Code Memory index (`docs/NEXUS98_CODE_MEMORY_SPECIFICATION.md`). Source files remain authoritative; memory is derived/index.

### 3.5 Governor

Responsible for autonomy levels, permissions, and execution safety. Implemented as `core/autonomy/*` (Phase 8). The Governor is the SOLE writer of autonomy state (`supervisor.auto_execute` + `system_config.json` intent). UI/agents only request changes.

### 3.6 Guardian (Separate Project)

Responsible for health, recovery, backups, and Git. Guardian is a SEPARATE project at `D:\Nexus98_Guardian`, NOT merged into Nexus98. Nexus98 may request recovery/checkpoint/session/health actions; Guardian owns Git, recovery, and backup authority. Integration is TBD (preferred initial model: external Guardian via controlled interfaces).

*Diagram placeholder: Layered architecture diagram (UI -> Intelligence -> Execution -> Memory, Governor sidecar, Guardian external).*

---

## 4. Autonomy Model & Governor

> Cross-reference: `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md` (#6), `docs/PHASE8_AUTONOMY_GOVERNOR_DESIGN.md`, `docs/PHASE8_AUTONOMY_OBSERVABILITY_DESIGN.md`, `docs/PHASE8_AUTONOMY_GOVERNOR_IMPLEMENTATION_PLAN.md`, `docs/PHASE8_GOVERNOR_FOUNDATION_VALIDATION_REPORT.md`, `docs/PHASE8_UI_PANEL_VALIDATION_REPORT.md`, `docs/Nexus98_Autonomous_Operating_Rules.md`, `docs/CURRENT_ARCHITECTURE_MAP.md` (#9).

### 4.1 Autonomy Levels (L0–L4)

- L0 Manual only: read-only queries; no proposals executed.
- L1 Assisted operation: propose + checkpoint; human approves before execution; no auto-write.
- L2 Trusted workflows: a fixed pre-approved set (seeded with `vscode_task_send`) auto-executes after checkpoint + validation; everything else stays L1.
- L3 Expanded autonomous workflows: broader, still checkpointed + validated workflow set; risky actions still gated by `require_approval_for_risky_actions`.
- L4 Experimental/restricted: opt-in, time-boxed, heavily monitored sandbox; never default.

The system ships at L0/L1 (`supervisor.auto_execute = False`). Raising the level is an explicit, recorded, checkpointed, human-approved decision — never implicit.

### 4.2 Trusted Workflow Set (vscode_task_send, L2)

`TRUSTED_WORKFLOWS_L2 = {"vscode_task_send"}` is the only seeded trusted workflow. L3/L4 sets start empty and are added one-at-a-time under governance. `vscode_task_send` is the proven reference promotion (Phase 7) that the Governor wraps.

### 4.3 Governor as Sole Writer of Autonomy State

`core/autonomy/governor.py` is the only component permitted to change `supervisor.auto_execute` (the code-level safety floor) and `config/system_config.json` `autonomy_level` (intent). `levels.py` is pure data; `policies.py` decides only; `audit.py` appends only. The UI/agents call `request_level_change(...)` and never write autonomy state directly.

### 4.4 Policies & Approval Engine

`core/autonomy/policies.py` validates a level-change request: valid level range (0–L4), target >= current (no downgrade via promotion), human sign-off required if target > current, fresh pre-promotion checkpoint required if target > 1, and the requested workflow set must be within the allowed set for the target. The Governor applies the change ONLY after `policies.approve() == True`.

### 4.5 Audit Log

`core/autonomy/audit.py` maintains an append-only log under `history/autonomy/audit.log` of every request, decision, level transition, and checkpoint reference. The UI audit view is read-only. Non-repudiable; supports rollback review.

### 4.6 Observability (Read-Only Dashboard)

`ui/autonomy_dashboard.snapshot()` exposes eight read-only fields: current level, active workflows, pending requests, approval history, audit events, last checkpoint, rollback availability, emergency-stop status. Passive displays use `snapshot()` only; no Governor imports in observability views.

### 4.7 Emergency Stop

`governor.emergency_stop(approver)` forces `auto_execute = False` and reverts to L0/L1 immediately, then triggers rollback review. Any client (UI button, audit rule, supervisor anomaly) may invoke it. Auto-downgrade occurs if validation fails, an audit rule trips, or a checkpoint write fails.

### 4.8 Migration Plan (Phase 7 -> Governor)

The Phase 7 `vscode_task_send` L2 promotion is the reference implementation and remains the first governed workflow. `core/autonomy/*` wraps the existing `supervisor.auto_execute` + `system_config` writes; the Phase 7 promotion checklist is ported into `policies.py`; the UI is pointed at `governor.request_level_change(...)`; L3 workflows expand one at a time; L4 is an explicit experimental toggle.

*Diagram placeholder: Governor authority boundary (who may write supervisor.auto_execute / system_config).*
[RULE]: The Governor is the sole authority/writer of autonomy state; UI requests, never writes.

---

## 5. Guardian (Separate Project)

> Cross-reference: `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md` (#4, #5), `docs/GUARDIAN_ARCHITECTURE_AUDIT.md`, `docs/GUARDIAN_DEVELOPMENT_ROADMAP.md`, `docs/CURRENT_ARCHITECTURE_MAP.md` (#10).

### 5.1 Separation Principle

Guardian currently exists as a separate project and is NOT merged into Nexus98. Integration is TBD. Preferred initial model: external Guardian — Nexus98 communicates with Guardian through controlled interfaces. Future models: Hybrid (Guardian gains Nexus connectors) or Full Merge (future possibility only). Nexus98 does NOT own Git operations.

### 5.2 Guardian Responsibilities (Git, Recovery, Health, Memory Maintenance)

Guardian owns: Git (commits, pushes, history, rollback, branch management); Recovery (checkpoints, recovery points, last known good state); Health (Nexus98 health, dependencies, tests, failures); Memory Maintenance (cleanup, compression, duplicate removal). Nexus98 may search GitHub, download tools, and inspect repositories, but does not own Git operations.

### 5.3 Guardian Architecture Audit

Guardian (`D:\Nexus98_Guardian`) is today a PowerShell-based toolkit/recovery scaffold (launcher `Nexus98.ps1` v3.0.0), not a running service. Only the snapshot/inventory engine (`New-NexusSnapshot`, SHA256 hash inventory) is substantive. Recovery/verification engines are stubs; no real restore logic; no known-good tracking; no monitoring; no alerts. The safety engine is a pass-through (`approved=True` always). Verdict: NOT safe to run unattended in its current state.

### 5.4 Guardian Development Roadmap

End state: a standalone, request-driven recovery & integrity authority running as a long-lived local service (localhost-only interface). Components: API/Interface Layer, hardened Snapshot Engine, expanded Verification Engine (application-level health), real Recovery Engine, Known-Good Manager, enforcing Safety/Approval Engine, Git Authority, consolidated State Store, correlated Logging. Non-goals: no autonomy logic for Nexus98, no modification of Nexus98 code/autonomy, no UI beyond read-only status/recovery-request.

### 5.5 Communication Layer (Nexus98 Client Only)

Nexus98 must gain a Guardian CLIENT only (read-only status first), calling a versioned request/response contract: `create_checkpoint`, `save_session`, `create_dont_forget`, `report_health`, `request_recovery`, `get_status`. Guardian exposes the API; Nexus98 requests, never assumes. No merge; no Git ownership transfer.

### 5.6 Authority Boundaries

Guardian may modify its own tree (`config/`, `data/`, `snapshots/`, `logs/`, `reports/`) and, via Git Authority, the Nexus98 repo it owns. Guardian must NOT modify Nexus98 autonomy state, governor logic, or application source beyond Git-owned version control, nor any non-Nexus98 user data outside declared recovery targets. The stub safety engine must be replaced by an enforcing gate BEFORE any autonomous or push capability is enabled.

*Diagram placeholder: Nexus98 <-> Guardian request/response contract boundary.*

---

## 6. Configuration Authority

> Cross-reference: `docs/CONFIG_AUTHORITY.md`, `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md`, `docs/CURRENT_ARCHITECTURE_MAP.md` (#3 configuration), `docs/TECHNICAL_DEBT_REPORT.md` (#1 split config authority).

### 6.1 Configuration Sources

Major sources: `config/system_config.json` (autonomy/safety), `config/system_context.json` (phase state), `config/models.json` + `config/models.yaml` (model selection), `config/providers.json` (provider flags), `config/vscode_workflow.json` (VS Code), `config/mouse_agent.json` (mouse agent), `config/settings.json` (user prefs), plus `core/config.py` (points at a DIFFERENT file `D:\Nexus98\config.json`).

### 6.2 Authoritative Files

- Autonomy & safety gate: `config/system_config.json` (`autonomy_level`, `safety.*`, `mode`). Note: handoff treats this as the autonomy authority; `core/config.py` pointing at `config.json` is a flagged split-authority inconsistency.
- Phase/milestone state: `config/system_context.json`.
- Model selection: `config/models.json` is authoritative; `models.yaml` mirrors/extends.
- VS Code: `config/vscode_workflow.json` only.

### 6.3 Override Precedence

1. Runtime code constants (`core/supervisor.py: auto_execute = False` hard floor — cannot be overridden by config alone).
2. `config/system_config.json` (primary runtime authority).
3. `config/system_context.json` (project/phase state).
4. Feature-specific config (`models.json`/`models.yaml`, `providers.json`, `vscode_workflow.json`, `mouse_agent.json`, `settings.json`).
5. Environment variables / runtime flags (e.g. `TMPDIR`).
6. Generated caches / snapshots (lowest; always regenerable).

A config request to raise autonomy does NOT by itself enable execution; `supervisor.auto_execute` must also be set `True` via an explicit, checkpointed, human-approved action.

### 6.4 Files Not To Be Manually Edited

- `core/supervisor.py` `auto_execute` constant (safety floor; change only via approved autonomy-promotion procedure).
- Any `*.backup*`, `*.pre_nexus98_migration_backup`, `*_before_*` snapshot.
- `history/`, `checkpoints/`, `snapshots/`, `backups/` (recovery data).
- `data/db/` and `data/system_state.json` (runtime state; regenerate if corrupt).
- Generated caches under `core/cache.py` / `data/cache/`.

### 6.5 Recovery On Disagreement

Identify the conflict and apply the higher-precedence source. Safety first: if `system_config.json` safety flags disagree with runtime, treat the stricter (safer) value as correct and restore `require_approval_for_risky_actions/require_snapshots/require_validation = true`. Restore from the most recent matching backup (`backups/`, `snapshots/config_repair_baseline_*`, or the HARD_BACKUP checkpoints). Re-run `tests/test_import_smoke.py` and the full suite; confirm `auto_execute` remains `False`. Record the resolution in the checkpoint/history entry.

### 6.6 Known Inconsistencies

- `config/system_context.json.current_phase` = "AutoGen Multi-Agent Foundation" is stale (actually Phase 6 documentation/audit). Correct during a permitted config-edit pass.
- Branding mismatch: `core/identity.py` "AI Model Hub Agent" vs Operating Rules "Nexus98 Agent" (cosmetic).
- Split config authority: `system_config.json` (autonomy) vs `core/config.py`'s `D:\Nexus98\config.json` auto-write (unresolved; flagged HIGH in debt).

[RULE]: system_config.json is the autonomy authority; do not introduce a competing config writer.

---

## 7. UI Architecture & Design

> Cross-reference: `docs/NEXUS98_UI_DESIGN_SPECIFICATION.md`, `docs/PHASE9_GUI_BEHAVIOR_SPEC.md`, `docs/PHASE9_UI_OVERHAUL_PLAN.md`, `docs/CURRENT_ARCHITECTURE_MAP.md` (#4), `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md` (#10, #12, #13).

### 7.1 UI Philosophy (Companion + Command Center)

The UI is a single window that is both an AI companion (conversational, context-aware) and a command center (models, agents, tools, system, autonomy, recovery). The companion is the front door; the command center is one click away. Chat-first by default; complexity expands via the workspace model, never by cluttering the default view.

### 7.2 Navigation & Toolbar

A persistent top toolbar hosts six primary controls: Mode, Project, AI, Workspace, Tools, System. Each is a labeled menu/selector with hover explanations. Selecting a toolbar item opens a panel/overlay, not a full-page nav change, preserving the chat context underneath. Session controls (Save Session / Don't Forget) are reachable from System.

### 7.3 Workspace Model

The central region is an adaptive workspace whose layout adapts to Mode and Project. Chat is the anchor; panels (conversation, results, diagnostics, autonomy read-only, documents, tools) are modular, dockable, and independently pin/collapse/hide. Layout state is saved per workspace and restored on return. No panel auto-expands to hide the conversation without user intent. Named workspaces: Coding, Research, Assistant.

### 7.4 Conversation Architecture

Separate conversations (Personal Assistant, Coding, Nexus Development, Research, Planning, Guardian, Custom) can share approved context. Conversations are project-linked or personal standalone; continuity is preserved across sessions.

### 7.5 AI Control Design

The Smart AI dashboard shows the effective selection (provider, model, strategy set, active agents) plus why it was chosen (automatic) and controls to override. Model dropdowns show strengths/weaknesses/compatible agents/recommended use cases; provider selector shows availability/health with local-first default; strategy combinations are displayed; automatic selection with one-action user override is the norm.

### 7.6 Tools System

Tools panel lists discoverable tools with capability metadata, GitHub search, installed tools, and custom tool generation. Discovered tools are declared, not auto-granted; risky tools are gated. Custom tool generation flows through Project Engine proposals (checkpoint -> write -> validate).

### 7.7 Documents System

Documents section contains architecture, roadmap, decisions, changelog, Guardian documentation, and memory documentation. Project documents, a global Nexus knowledge library, an interactive roadmap, and generated documentation are all in-app browsable views (docs exist on disk but no in-app Documents view yet).

### 7.8 Guardian Integration (UI)

A read-first Guardian client panel/button (toolbar System + Control Panel) communicates with Guardian via a defined client interface. Guardian health/status is shown as read-only indicators; unreachable Guardian degrades gracefully (offline state), never blocks the UI. The UI may REQUEST recovery actions with explicit confirmation; Guardian owns and executes recovery. NO Git commit/push/history/rollback controls are exposed in Nexus98.

### 7.9 Session System

Save Session persists workspace layout, active conversation(s), Mode/Project, and AI selection for resume. Don't Forget is a manual emergency context save (recovery point + memory update + WWW summary) reachable as a prominent quick action. On startup after proper shutdown or a Don't Forget event, a "Where Were We" summary restores context (current task, recent decisions, system status, unfinished work, user intent) — dismissible and read-only.

### 7.10 Control Panel

A consolidated Control Panel (opened from System) presents labeled toggles with hover explanations: AI toggle, Bridge toggle, Mouse tool toggle, agent status, Guardian status, Recovery controls, Memory controls. Toggles reflect real backend state and confirm risky changes. The Control Panel observes via `ui.autonomy_dashboard.snapshot()` and requests changes only through the Governor.

### 7.11 Future Expansion (Voice, Shell, VS Code, Self-Mod)

Highest-privilege capabilities are deferred and sit in the High Risk tier (Guardian-protected): Voice integration (local-first, opt-in), Internal shell (approval-gated, checkpointed, Governor-authorized, last), deeper VS Code integration (new governed workflows, not new permissions), and Self-modification (Project Engine proposals -> backup/write/validate under Governor authorization; implemented only after foundations, memory, Guardian client, and UI shell are approved and validated).

### 7.12 GUI Behavior Spec (Frozen)

`docs/PHASE9_GUI_BEHAVIOR_SPEC.md` is a DESIGN FREEZE defining application identity, main window behavior, major UI areas, visual design, interaction rules, and autonomy UI invariants. The Autonomy tab is STRICTLY READ-ONLY. Governor authority, read-only dashboard behavior, and approval boundaries are invariants that must be preserved.

### 7.13 UI Overhaul Plan

`docs/PHASE9_UI_OVERHAUL_PLAN.md` plans the move from the tabbed Command Center to the chat-first workspace. Guiding constraints are non-negotiable: preserve `launch_ui()` contract, Tkinter/ttk only (no new deps), view-builder patterns, and the read-only autonomy behavior. Phased rollout: checkpoint -> implement -> validate -> test per step.

### 7.14 Cross-Cutting UI Invariants

- Governor is the sole authority/writer of autonomy state; the UI requests, never writes.
- All passive autonomy displays use `ui.autonomy_dashboard.snapshot()` only; no Governor imports in observability views.
- Guardian stays separate; Nexus98 is a client. No Git ownership in Nexus98.
- Configuration-driven and path-abstracted as the UI grows; preserve `launch_ui()` and existing view-builder patterns.
- No new autonomy levels, no workflow expansion, no new permissions introduced by the UI.
- Every implementation step: checkpoint -> analyze -> document -> approve -> implement -> validate.

*Diagram placeholder: Workspace/toolbar/panel layout.*
[RULE]: All selection is non-mutating to autonomy state; execution remains Governor-gated.

---

## 8. Intelligence Layer: Model & Strategy

> Cross-reference: `docs/NEXUS98_MODEL_INTELLIGENCE_SPECIFICATION.md`, `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md` (#7, #8), `docs/NEXUS98_UI_DESIGN_SPECIFICATION.md` (#5), `docs/CURRENT_ARCHITECTURE_MAP.md` (#7), `docs/EXTENSION_POINT_MAP.md` (#1, #2, #3).

### 8.1 Intent Understanding Layer

A lightweight classifier parses a raw request into a typed `TaskIntent` (intent_type, target artifacts, action posture, constraints) replacing the current ad-hoc `route()` keyword mapping. Task types: query, explain, generate, edit, refactor, test, research, orchestrate, recovery-request, session. Below a confidence threshold, a request is treated as conversational (Safe tier) and never auto-mutates.

### 8.2 Model Router Design

A unified `ProviderAdapter` interface (`list_models`, `get_model_meta`, `health`, `chat_completion`, `cost_estimate`) with concrete OllamaAdapter today and future CloudAdapter(s) behind the same interface. The router holds a registry and never hardcodes provider URLs in call sites. Local-first default; cloud is opt-in and configuration-driven. Provider independence means execution code calls the router, not a provider directly (retires duplicate `ollama_models()`/`vscode_bridge` paths).

### 8.3 Automatic Selection System

Given a `TaskIntent`, the router computes four coordinated, non-mutating selections: model (capability-fit + performance/confidence + cost/latency), provider (serves the model, satisfies constraints, health-gated, local-first fallback), agent (intent -> required role(s) -> model binding, compatibility-enforced), and strategy (active strategy set biased into selection without changing autonomy level).

### 8.4 User Override System

Override is always one action away and persists per Mode/Project. Dropdowns (provider/model/strategy/agent) expose current effective selection + a visible override; 'Auto' restores automatic. Manual full selection is recorded as 'user override'. The router always computes its automatic recommendation and surfaces it ('Suggested: ...'). Every effective selection carries a human-readable explanation.

### 8.5 Model Capability Memory

A SQLite sub-store records per (model, task_type, strategy) performance: success rate, latency p50/p95, cost, user-acceptance, failure flags. Each model+task_type gets a confidence score (0–1) used as tie-breaker and visibility signal. Users/operators can edit recommended use cases, compatible agents, and cost/latency tags (versioned, `source='user'`); edits are local-only preference data, not autonomy state.

### 8.6 Strategy Engine

Strategies (Fast, Accurate, Coding, Research, Creative, Safety First, Cost Efficient) are a SET, not a single mode, and compose into selection bias. Conflicts (e.g. Accurate vs Cost Efficient) are detected, not silently resolved. Priority: (1) Safety First always wins; (2) explicit user override; (3) Mode/Project default set; (4) task-type implied strategy; (5) cost/latency as final tie-breaker. Users customize strategies per Mode/Project (data, not code changes).

### 8.7 Agent Interaction Model

The Intelligence Layer selects; the Execution Layer (supervisor + orchestrator + agent team) runs. Models are bound to agent roles by the router; agents cooperate via AutoGen with explicit, explainable model assignments. Delegation is role-driven: intent -> required roles -> agent instances -> bound models. Delegation stays inside the Governor's `auto_execute` floor and the trusted-workflow set (L2 `vscode_task_send` today); new delegated workflows are added only via governance.

### 8.8 UI Requirements (Reasoning Visibility)

The Smart AI dashboard shows dropdown information (name, category, context window, strengths, weaknesses, compatible agents, recommended use cases, cost/latency, availability), recommendation display (effective selection labeled Auto/Override + automatic suggestion), and a collapsible read-only 'why' panel with the selection rationale sourced from the router's explanation object.

### 8.9 Safety Boundaries (Auto vs Approval)

Automatic (Safe tier): intent classification, provider/model/strategy/agent SELECTION, local-first preference, confidence/scoring, recommendation computation, read-only reasoning display. Requires approval (Medium/High risk, Governor/Guardian): any code/config/restructure modification (Project Engine + approval), Governor/Guardian/security/recovery changes (Guardian-protected), promoting a new autonomous workflow, cloud execution without explicit opt-in, and editing autonomy state (Governor sole writer). The router may REQUEST but never EXECUTE these.

### 8.10 Implementation Phases

1. Intent contract (typed `TaskIntent` + classifier). 2. Provider abstraction (adapter + OllamaAdapter; retire duplicate call sites). 3. Router core (unified selection + capability matching). 4. Capability memory (performance/confidence + editable recommendations). 5. Strategy engine (simultaneous strategies, conflict detection, priority, customization). 6. Override + UI (after frozen GUI spec approved). 7. Agent delegation wiring (keep Governor floor). 8. Cloud seam deferred, opt-in, High Risk.

*Diagram placeholder: Intent -> Router -> Provider/Model/Strategy/Agent selection flow.*

---

## 9. Memory Architecture

> Cross-reference: `docs/MEMORY_ARCHITECTURE_DESIGN.md`, `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md` (#16), `docs/CURRENT_ARCHITECTURE_MAP.md` (#8), `docs/NEXUS98_CODEBASE_INTELLIGENCE_REPORT.md` (#5, #8).

### 9.1 Purpose & Constraints

Memory is the system's persistent operating substrate — not chat history. Hard constraints: today memory is `core/memory.py` (fragile `agent_memory.json`); SQLite is an accepted, dependency-free option (`data/db/models.db`); config convention is JSON in `config/`; the fixed install root `D:\Nexus98` assumption is preserved (path configurability is additive). Design goals: persistent, structured, auditable, controlled, scalable from one assistant to many agents/projects.

### 9.2 Memory Layers (Identity/Project/Episodic/Semantic/Operational/Decision)

Six logical layers carried in the `type` enum: identity (user preferences, access_control restricted), project (architecture decisions, milestones, discoveries), episodic (events/journal), semantic (learned knowledge, patterns), operational (current state, high-churn), decision (critical; requires `alternatives_considered`/`reason`/`risks_accepted`/`authority`/`date`, verified + high importance).

### 9.3 Data Model

One core record per row: `memory_id` (UUID PK), `type`, `category`, `content`, `source`, `project`, `created_at`, `updated_at`, `confidence` (0–1), `importance` (1–5), `verification_status` (unverified/verified/disputed/archived), `version`, `update_history` (append-only JSON), plus optional `expiration_policy`, `access_control`, `related_memories`. Backward-compatible migration maps legacy `agent_memory.json` -> memory records.

### 9.4 Storage (SQLite)

Phase 1 = SQLite (reusing `data/db/` pattern). Rationale: zero new deps, atomic transactions, WAL, indexing, `PRAGMA integrity_check`, easy backup (`VACUUM INTO`). A `StorageBackend` abstraction allows v2 vector and v3 graph backends behind the same API; the API never references SQLite directly so swapping is a config change.

### 9.5 Retrieval Design

Tier 1 (v1): exact + structured SQL filtering (type/category/project/source/verification/confidence/importance) with a ranking function `score = importance*w1 + confidence*w2 + recency_decay*w3`, verified boosted, archived/disputed demoted. Tier 2 (v2): semantic similarity (structured prefilter + vector re-rank). Tier 3 (v3): knowledge-graph traversal of `related_memories` edges.

### 9.6 Scaling Roadmap

Phase 1 SQLite single-writer; Phase 2 + vector index; Phase 3 + graph store; Phase 4 sharded by project. Each phase is additive — API and data model unchanged; only backends/retrievers added behind interfaces.

### 9.7 Migration Strategy

Versioned `schema_version` table; `Memory.migrate()` runs idempotent forward steps only. Backward/forward safe: import `agent_memory.json` via the mapping, keep original as `.migrated`. No destructive moves (copy-then-flag). On load run `PRAGMA integrity_check`; on failure fall back to latest `.bak`. Verification gates assert row counts + checksum parity before deleting backups.

### 9.8 Security Model

Prevent uncontrolled growth (importance/expiration drive archival; VACUUM/prune job). Prevent duplicates (deterministic dedupe on `(type, category, content_hash)`). Prevent false permanence (`verification_status` starts unverified; only user/system verify can set verified; disputed quarantined). Prevent sensitive storage (identity layer forbids secret-shaped fields; scanner refuses credential patterns). Prevent silent modification (every mutation appends `update_history` + bumps `version`). Access control: shared/agent_private/restricted.

### 9.9 Conflict & Decay Handling

Conflicting memories are never overwritten; a new write with the same key creates a new record, the existing flips to `disputed`, and `related_memories` links them; resolution is an explicit `verify()`. Decay/archive lowers effective rank as `last_verified` ages; operational memories expire by TTL; durable layers archive only when superseded by a newer, verified record. Single serialized writer; agent-private memories filtered by `source`.

### 9.10 Implementation Phases

1. Memory Service API + SQLite backend (store/query/update/forget/verify, schema v1, single-writer lock, integrity check, migration). 2. Retrieval tier 1. 3. Audit & security (update_history, dedupe, verification gates, sensitive scanner, backup/prune). 4. Integration into Supervisor/Orchestrator. 5. Tier 2 semantic. 6. Tier 3 graph + multi-project sharding.

*Diagram placeholder: Memory Service API -> Storage / Index / Integrity layers.*

---

## 10. Code Memory

> Cross-reference: `docs/NEXUS98_CODE_MEMORY_SPECIFICATION.md`, `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md` (#17), `docs/NEXUS98_CODEBASE_INTELLIGENCE_REPORT.md` (#8), `docs/MEMORY_ARCHITECTURE_DESIGN.md`.

### 10.1 Purpose of Code Memory

A structured, queryable understanding of the Nexus98 codebase (files, modules, functions/classes, dependencies, relationships, hashes, versions, decisions, docs) built on top of `memory_service`. It preserves knowledge, not clutter; source files remain authoritative; code memory is derived/index, never a second source of truth, and is rebuildable from source at any time.

### 10.2 Data Model (Files/Modules/Functions/Classes/Dependencies/Relationships/Hashes/Versions/Decisions/Docs)

Entities: files (identity + source_hash + index_status), modules (qualified name + public API), functions/classes (symbol_id, qualified_name, parent_symbol, location, code_hash, summary, dependencies), dependencies (directed edges: imports/calls/references/inherits/contains/documents/decides), relationships (semantic links to decisions/docs), hashes (source_hash per file, code_hash per symbol for change detection), versions (index_run_id per batch), decisions (decision_refs to canonical decision memory), documentation links (doc_refs to docs/ paths).

### 10.3 SQLite Schema Proposal

New tables in the same `data/db/memory.db`: `code_index_runs`, `code_files` (PK project+file_path), `code_symbols` (PK symbol_id, soft-delete `deleted`), `code_edges` (directed edges), `code_memory_links` (symbol <-> decision/doc). Mirrors memory_service conventions: `schema_version`, WAL, forward-only idempotent migrations, JSON payload columns, indexes on file_path/qualified_name/source_hash/code_hash/edge refs. A separate `code_memory.db` sibling is permitted only if a future approved decision splits storage.

### 10.4 Indexing System

AST parsing via stdlib `ast` (Python) and `json`/`PyYAML` (config); no third-party parser. Incremental: compute `source_hash` per file, skip unchanged; re-parse and upsert only changed files scoped to a run_id. Change detection at file level (source_hash) and symbol level (code_hash) so only changed symbols need re-summarization. Prioritization by importance: high-value core/autonomy/supervisor/memory modules get agent summaries; low-value tests/scripts get metadata only — reducing token cost.

### 10.5 Memory Lifecycle (Active/Archived/Compressed/Deleted)

Active = current, hash-consistent with live file. Archived = older-run symbols kept for history/rollback (`verification_status='archived'`). Compressed = collapse verbose summaries for untouched low-importance records (hashes/edges preserved; compression is Guardian-owned per handoff #5 once Guardian exists; local gated+logged until then). Deleted = soft-delete (`deleted=1`) like `memory_service.forget()`; hard DELETE only via migration/cleanup with checkpoint. Stale-run symbols soft-deleted in bulk at new run start. Lifecycle invariant: Active records always reflect live source.

### 10.6 Integration Points

Supervisor reads (impact pre-check before `run_action_task`); Project Engine is the sole mutator and emits a governed reindex notification for changed files post-validate (incremental, not full sweep); UI queries read-only (future chat/control surfaces); agents read and may PROPOSE summary/decision-link updates via governed paths; Guardian future integration compares `code_files.source_hash` against known-good inventory for integrity (Nexus98 requests, Guardian executes).

### 10.7 Search Capabilities

Read-only queries: find function (by name/qualified_name), explain module (module + summary + public API + doc_refs), trace dependency (graph walk over code_edges), locate related code (dependency + 'related' + shared decision/doc edges), by decision (symbols citing a decision memory_id), by doc (symbols documenting a docs/ path), by hash (lookup by source_hash/code_hash).

### 10.8 Security Boundaries

Stores NO secrets, credentials, autonomy state, or executable payloads — structural metadata + summaries only. Source files remain authoritative; a corrupted index is regenerated, never trusted over source. Write access restricted to the Code Memory service API; Supervisor/UI/agents read; only the indexing pipeline (triggered by Project Engine hooks) writes, via the API. Indexing never executes indexed code (static AST, no import/eval). Autonomy state is out of scope (Governor sole writer).

### 10.9 Migration Strategy

Phase 0 documentation only. Bootstrap migration adds `code_*` tables via forward-only idempotent step in memory_service (new `SCHEMA_VERSION`), backing up the DB first. Backfill first full run for default scope. Coexistence: legacy `memories` table untouched; Code Memory is additive. Rollback: run-scoped soft-delete; DB restorable from pre-migration backup.

### 10.10 Implementation Phases

1. Schema + migration. 2. Indexer core (AST/JSON parser + backfill + hashes). 3. Incremental + hooks (Project Engine reindex, change detection). 4. Edges + links (dependency graph, decision/doc cross-links). 5. Search API (read-only query methods + tests with temp DB). 6. Consumer wiring (Supervisor pre-check, future UI, agent read). 7. Lifecycle + Guardian seam (archived/compressed/deleted; Guardian hash-compare contract).

*Diagram placeholder: Code Memory index pipeline (parse -> hash -> store -> query).*

---

## 11. Execution Layer: Supervisor & Project Engine

> Cross-reference: `docs/PHASE5_SUPERVISOR_PROJECTENGINE.md`, `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md` (#3 Execution), `docs/CURRENT_ARCHITECTURE_MAP.md` (#5), `docs/NEXUS98_CODEBASE_INTELLIGENCE_REPORT.md` (#5), `docs/Nexus98_Vision_Architecture.md` (#4).

### 11.1 Supervisor (Intent Detection & Task Routing)

`core/supervisor.py` (706 lines) performs `detect_intent`, `run_task` (information path -> orchestrator/agents), and `run_action_task` (action path -> proposals -> Project Engine). `auto_execute = False` is the module-scope safety floor. ADDITIVE ONLY change (Phase 5) wired the action branch; non-action intents unchanged.

### 11.2 Information Path vs Action Path

Information intents: `detect_intent == "information"` -> `route` -> `get_orchestrator` -> agent -> Ollama (UNCHANGED). Action intents: `run_action_task` -> `build_task_plan` -> `convert_plan_to_action_proposals` -> `approve_agent_proposal` (creates engine request/checkpoint via `ProjectEngine.create_request`) -> `request_file_operation_blocking` (gated by `auto_execute`).

### 11.3 Project Engine (File-Mutation Authority)

`core/project_engine.py` (345 lines) is the ONLY authorized file mutator: `backup_file` -> `write_file` (with validate) -> `execute_operation` -> `history/` logging. Provides `create_request`, `approve_request`, `restore_backup`, `log_operation`. All mutations are checkpointed and reversible.

### 11.4 Safety Invariants

`supervisor.auto_execute` remains `False` by default; no file is written for an action intent unless a caller explicitly enables autonomous execution. Proposal + checkpoint records persist for every action intent regardless of outcome. The existing `approve_engine_request`/`execute_engine_request` functions are untouched; the gate is applied in the new additive helper.

### 11.5 Flow Diagram

```
run_task(task)
  -> detect_intent(task)
       == "action"  --> run_action_task -> build_task_plan
                          -> convert_plan_to_action_proposals (proposals)
                          -> approve_agent_proposal (engine request / checkpoint)
                          -> request_file_operation_blocking
                               auto_execute=False -> awaiting_approval (no write)
                               auto_execute=True  -> approve + execute (writes file)
       == "information" --> router -> orchestrator -> agent -> Ollama (UNCHANGED)
```

### 11.6 Validation

Tests: `tests/test_supervisor_phase5.py` (dependency-aware; skips when autogen runtime unavailable). Phase 5 stable baseline: 78 passed, 1 warning; import smoke 18 passed. Environment note: venv references a removed Python base; live execution could not run in the original session (static structural validation used instead).

### 11.7 Deferred Next Steps

Install a working Python + `autogen-ext`/`flask` to enable live import and end-to-end `run_task`. Add a human approval UI hook reading `awaiting_approval`. Consolidate config authority (`system_config.json`) and remove stale supervisor snapshots once the live path is verified.

*Diagram placeholder: Supervisor -> Orchestrator / Project Engine request-approve-execute flow.*

---

## 12. Agents & Orchestration

> Cross-reference: `docs/CURRENT_ARCHITECTURE_MAP.md` (#6), `docs/NEXUS98_CODEBASE_INTELLIGENCE_REPORT.md` (#2, #5), `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md`.

### 12.1 Agent Factory

`core/agent_factory.py` builds AutoGen `AssistantAgent`s from a config path (`config/models.yaml`) using `OllamaChatCompletionClient` (host `http://localhost:11434`) and tool bindings (`tools/file_tools`, `tools/git_tools`). Has a hard import-time dependency on `autogen_agentchat`/`autogen_ext`; tests skip when unavailable.

### 12.2 Orchestrator

`core/orchestrator.py` loads the configured agent team via `AgentFactory`. Registry of agents drives the Agents view.

### 12.3 Agent Registry

`core/agent_registry.py` holds a static `AGENTS` dict (Supervisor, Coding Agent, etc.) with type/status/description, and exposes `list_agents` for the UI.

### 12.4 Agent Assignments & Roles

`config/system_context.json` lists agent assignments (architect->qwen3:30b, coder->qwen2.5-coder:14b, reviewer->llama3.2:3b, etc.) and available agents (architect, coder, researcher, reviewer, tester, documentation, vision). `config/models.yaml` maps 7 agents to Ollama models with category/capabilities.

### 12.5 Manager / Pipeline

`core/manager.py` is a thin wrapper over `AgentFactory`. `core/pipeline.py` (`AgentPipeline`) performs direct HTTP to Ollama generate with fixed URLs (no provider abstraction) — flagged as fragile/debt.

---

## 13. Model & Provider Systems

> Cross-reference: `docs/CURRENT_ARCHITECTURE_MAP.md` (#7), `docs/NEXUS98_CODEBASE_INTELLIGENCE_REPORT.md` (#3, #7), `docs/NEXUS98_MODEL_INTELLIGENCE_SPECIFICATION.md`, `docs/config/models.yaml`, `docs/config/models.json`.

### 13.1 Providers (Ollama / HuggingFace / GitHub / Cloud)

Ollama is the primary local provider (`http://localhost:11434`), used by agent_factory, vscode_bridge, and pipeline. HuggingFace and GitHub are discovery/download tools (read/inspect; Nexus98 does not own Git). No cloud provider layer exists today; system is local-only (handoff #7 local/cloud switching is a future module). `config/providers.json` flags ollama/huggingface/github booleans.

### 13.2 Catalog & Recommender

`core/catalog.py` (build/sync/get catalog), `core/discovery.py` (Ollama installed models), `core/recommender.py` (hardware-aware recommendations), `core/db.py` (SQLite `data/db/models.db`), `core/inspector.py` (model inspection), `core/display.py` (formatting) implement the model catalog + recommender (implemented).

### 13.3 Model Metadata & Capability Matching

`config/models.json` (6 models with category/priority/context/tags/roles) and `config/models.yaml` (7 agent->model mappings) are the model metadata sources. The future Model Router consumes this metadata for capability matching and dropdown display. Provider metadata (strengths/weaknesses/compatible agents) is NOT yet modeled.

### 13.4 Local/Cloud Switching

Not implemented. The future `core/providers/` abstraction (adapters behind one interface) enables local/cloud switching with local-first default and cloud opt-in. Until then the system is local-only.

### 13.5 Local Model Runtime (Ollama)

Ollama at `localhost:11434` is the local model runtime; 16 models verified available at the Phase 5 milestone. `core/ollama.py` is a read-only inventory client; `tools/ollama_manager/` manages lifecycle (requires Level2+ authorization).

---

## 14. Tools & Integrations

> Cross-reference: `docs/Nexus98_Tool_Registry.md`, `docs/EXTENSION_POINT_MAP.md` (#4, #5, #10), `docs/NEXUS98_CODEBASE_INTELLIGENCE_REPORT.md` (#2, #7), `docs/CURRENT_ARCHITECTURE_MAP.md` (#11).

### 14.1 Local File Tools

`tools/file_tools.py`: `list_files()` (read-only inventory), `read_file(path)` (read contents). Safety: read-only, no mutation.

### 14.2 Git Tools (Read/Inspect Only in Nexus98)

`tools/git_tools.py`: `git_status()` — read-only by default. Commits/branches are NOT created by the agent unless explicitly directed; Git write authority belongs to Guardian.

### 14.3 Model / Agent Tools

`tools/agent_runner.py` (`load_models`, `select_model`, `run`), `tools/agent_selector.py` (`load`, `choose`), `tools/model_router.py` (`ollama_models`, `load`, `scan` — duplicate of `api/vscode_bridge.ollama_models`), `tools/continue_sync.py` (Continue config sync), `tools/health_check.py` (structured health reporting).

### 14.4 Ollama Management

`tools/ollama_manager/` + `tools/ollama-startup.ps1` manage the local Ollama runtime. Model lifecycle operations are infrastructure-level and require human/Level2+ authorization.

### 14.5 VS Code Integration (Connectors / Bridge / Extension)

`integrations/vscode_connector.py` (HTTP client to 127.0.0.1:8000), `api/vscode_bridge.py` (Flask app: `/health`, `/v1/models`, `/v1/chat/completions`), `bridge/vscode_listener.py` + `bridge/worker.py` (file-drop), `vscode_extension/extension.js` (client front-end). Not an autonomous action surface; manual/user-driven.

### 14.6 Core Services

Supervisor (intent/approval gate/Project Engine wiring), Project Engine (sole file mutator), Memory (`memory.py`/`memory_service.py`), Orchestrator, Config (`config.py`/`config_manager/`), State/Events/Rules (`state_manager/`/`event_bus/`/`rule_engine/` — empty scaffolds), Installer/Bootstrap, Discovery/Catalog, Downloaders (`downloader`/`huggingface`/`github`/`gguf` — network/infra, Level2+).

### 14.7 Autonomy Levels vs Tool Access

L0: read-only (`list_files`, `read_file`, `git_status`, status queries). L1: + proposals/checkpoints (no execution). L2: + Project Engine writes (approved), VS Code task send. L3: + model/agent lifecycle, downloads (trusted workflows). The Tool Registry is a catalog, not an authorization list — access is constrained by the safety gate.

### 14.8 Configuration Surface

Authoritative config map is `docs/CONFIG_AUTHORITY.md` (sources, authoritative files, generated/derived, override precedence, do-not-edit files, recovery). `core/config.py` points at a different `config.json` — a flagged split-authority inconsistency.

### 14.9 Integration Status

Ollama local runtime reachable (16 models); VS Code Bridge Flask API + listener queryable; HY3/Codex integration present (hard backups). Duplicate `ollama_models()` and dual `vscode_bridge` (core/ vs api/) are flagged debt.

### 14.10 Tool Discovery & Custom Tool Generation

Tool registry doc exists; dynamic discovery + custom generation are NOT implemented. Future: `core/tools_registry/` (discovery + capability metadata) and `core/tool_gen/` (governed code generation via Project Engine proposals). Discovered tools are declared, not auto-granted; risky tools gated.

---

## 15. Mouse Agent System

> Cross-reference: `docs/MOUSE_AGENT_SYSTEM.md`, `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md` (#13 Control Panel), `docs/CURRENT_ARCHITECTURE_MAP.md` (#6), `docs/Nexus98_Tool_Registry.md` (#7).

### 15.1 Overview

The Mouse Agent gives Nexus98 agents safe computer-interaction capability. Two non-overlapping parts: (a) `core/mouse_control.py` — programmatic, bounds-checked, logged control API (primary interface); (b) `tools/mouse_agent/ai_mouse_mode.py` — human-assistive tray macro (hold-drag-to-copy / middle-click-to-paste), independent of the API. Status: COMPLETE (2026-07-17).

### 15.2 Architecture

`core/mouse_control.py` exposes `MouseControl` class + `get_mouse_control()` singleton + module wrappers; backends: `pynput.mouse.Controller` (input), `ctypes user32` (screen metrics/bounds), `PIL.ImageGrab` (screenshots). `core/mouse_agent.py` manages the tray tool (`start_mouse_mode`/`stop_mouse_mode`/`mouse_status`). No new installs required (pynput, Pillow, ctypes already present).

### 15.3 Capabilities

Input control (all return structured dicts): `move`, `click`, `double_click`, `right_click`, `middle_click`, `drag`, `scroll`. Coordinate management via ctypes with boundary checking and a deterministic 1920x1080 fallback. Screen awareness via `screenshot()` / `get_screen_bounds()` / `get_position()`.

### 15.4 Response Format

Every action returns `{"ts", "action", "ok", "result", "error", "dry_run"}`. Agents branch on `ok`; failures never raise for normal control flow.

### 15.5 Safety Systems

Action validation (type/range); bounds enforcement (off-screen/invalid rejected); emergency stop (`emergency_stop()` blocks all until `reset_emergency_stop()`, visible via `status()`); session limit (`max_actions_per_session`); per-action `action_timeout` in a worker thread; JSONL logging to `logs/mouse_agent.log` + bounded ring buffer; dry_run validation without real input (all tests use dry_run; auto-degrades to dry_run if pynput missing).

### 15.6 Configuration

`config/mouse_agent.json` (merged over built-in defaults; bad/missing falls back). Keys: motion smoothing, timing, `scroll_amount`, `action_timeout`, `safety` (enforce_bounds, boundary_margin, use_virtual_desktop, fail_on_out_of_bounds, max_actions_per_session, emergency_stop_default), `logging`, `screenshot`.

### 15.7 Usage

`from core import mouse_control as mouse` then `mouse.move(...)` / `mouse.click(...)` / `mouse.drag(...)` / `mouse.screenshot(...)`; or `get_mouse_control()` singleton for `emergency_stop()` / `reset_emergency_stop()`.

### 15.8 Testing

`tests/test_mouse_agent.py` — 27 tests, all dry_run (movement, clicking, invalid input, drag/scroll, safety limits, introspection, config fallback, error recovery). Result: 27 passed; memory suite 10/10 (no regression).

### 15.9 Future Improvements

Optional real-input integration test (opt-in); target detection/template matching on `screenshot()` (needs vision lib, deferred); multi-monitor per-display helpers; wire convenience wrappers into `core/mouse_agent.py` once writable.

---

## 16. Conversation & Context Systems

> Cross-reference: `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md` (#9, #14, #15), `docs/NEXUS98_UI_DESIGN_SPECIFICATION.md` (#4, #9), `docs/FUTURE_ARCHITECTURE_GAP_ANALYSIS.md` (#2).

### 16.1 Separate Conversations

The handoff defines separate conversations (Personal Assistant, Coding, Nexus Development, Research, Planning, Guardian, Custom) that can share approved context. NOT yet built — supervisor is task-oriented, not conversation-oriented.

### 16.2 Shared Memory / Context

Conversations share approved context via the Memory layer. Context-sharing policy is a future `core/conversations/` module (proposed in gap analysis).

### 16.3 Project-Linked Conversations

Conversations can be scoped to a Project, linking conversations, documents, and code memory to that project (UI design Section 4/7). Switching Project updates linked context.

### 16.4 Personal Standalone Conversations

Conversations can also be personal standalone (not project-scoped), with their own history and settings.

### 16.5 Continuity

Continuity is preserved across sessions via Save Session and the WWW/"Where Were We" summary.

### 16.6 WWW ("Where Were We") System

Triggered by proper shutdown or the Don't Forget button. Restores user context: current task, recent decisions, system status, unfinished work, user intent.

### 16.7 Don't Forget (Emergency Context Save)

Manual emergency context save creating a recovery point (requested via Guardian where applicable), a memory update, and a WWW summary. Reachable as a prominent quick action; confirms what was captured.

---

## 17. Documents, WWW & Dont Forget

> Cross-reference: `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md` (#14, #15, #18), `docs/NEXUS98_UI_DESIGN_SPECIFICATION.md` (#7, #9.3).

### 17.1 Documents Section (Architecture/Roadmap/Decisions/Changelog)

The Nexus98 Documents section contains architecture, roadmap, decisions, changelog, Guardian documentation, memory documentation, and tool library. Today these docs exist on disk (`docs/`) but there is NO in-app Documents view yet.

### 17.2 Project Documents

Per-project documentation browser (architecture/roadmap/decisions) scoped to the active project.

### 17.3 Global Nexus Knowledge Library

A global, cross-project knowledge library of Nexus98 design intent and learned knowledge.

### 17.4 Interactive Roadmap

An interactive roadmap view of phases/milestones, linking to the relevant docs and checkpoints.

### 17.5 Generated Documentation

Auto-generated documentation (e.g. from Code Memory) surfaced in the Documents system.

---

## 18. VS Code Integration & Workflow

> Cross-reference: `docs/vscode_workflow_setup.md`, `docs/CURRENT_ARCHITECTURE_MAP.md` (#11), `docs/Nexus98_Tool_Registry.md` (#5), `docs/NEXUS98_CODEBASE_INTELLIGENCE_REPORT.md` (#7), `docs/PHASE7_VSCODE_TASK_SEND_ACTIVATION_CHECKLIST.md`, `docs/_vscode_task_send_monitor_probe.md`.

### 18.1 Bridge API (Flask)

`api/vscode_bridge.py` is a Flask app on `127.0.0.1:8000` exposing `/health`, `/v1/models`, `/v1/chat/completions` (which calls `supervisor.run_task`). A duplicate `core/vscode_bridge.py` exists (flagged debt).

### 18.2 Bridge Listener & Worker

`bridge/vscode_listener.py` + `bridge/worker.py` process file-drop tasks locally; responses land in `bridge/responses/`. External companion process pattern under `D:\AI\Nexus98_Bridge` (closest analogue to an "external Guardian" seam).

### 18.3 VS Code Connector

`integrations/vscode_connector.py` is an HTTP client (`vscode_connector.log/status/send_task`) to `127.0.0.1:8000` — the request half of the bridge pattern (request/response, mirroring the Governor client pattern).

### 18.4 VS Code Extension

`vscode_extension/extension.js` + `package.json` is the client-side extension that sends tasks to `api/vscode_bridge.py` and renders status. Not an autonomous action surface; manual/user-driven.

### 18.5 vscode_task_send (Trusted Workflow, L2)

`vscode_task_send` is the seeded L2 trusted workflow — the proven reference promotion (Phase 7) that the Governor wraps. New VS Code actions become new governed workflows, not new permissions.

### 18.6 Workflow Setup & Laptop Auto-Open

`scripts/setup_vscode_workflow.ps1`, `scripts/launch_vscode_laptop.ps1`, `scripts/sync_vscode_setup.ps1`, `scripts/validate_vscode_workflow.ps1` configure desktop/laptop roles, extensions, workspace, and tunnel (`config/vscode_workflow.json`). Laptop auto-opens the shared workspace on VS Code launch.

### 18.7 Monitored Validation Probe

`_vscode_task_send_monitor_probe.md` records a monitored validation probe of the `vscode_task_send` workflow activation.

---

## 19. Current Repository Intelligence

> Cross-reference: `docs/NEXUS98_CODEBASE_INTELLIGENCE_REPORT.md`, `docs/CURRENT_ARCHITECTURE_MAP.md`.

### 19.1 Repository Structure

Active source folders: `core/`, `ui/`, `api/`, `bridge/`, `integrations/`, `tools/`, `runtime/`, `scripts/`, `vscode_extension/`, `config/`, `tests/`, `main.py`. State/history (recoverable, NOT source): `history/`, `checkpoints/` (54 dirs), `snapshots/` (4), `backups/`, `agent_logs/`, `logs/`, `reports/`, `data/`. Superseded/archive (excluded): `archive/`, `AI_Model_Hub_archive/`, `diagnostic_parts/`, `ollama_cleanup_backups/`, `.venv_broken_*`, `build/`, `dist/`.

### 19.2 Python Module Map

`core/` has 64 `.py` files. Supervisor imports router/identity/orchestrator/vscode_bridge/project_engine; Project Engine is standalone writer; Governor (core/autonomy/*) is sole autonomy writer; UI imports only core slices read-only; `api/vscode_bridge` imports supervisor.run_task; `bridge/*` imports core.bridge -> supervisor.

### 19.3 Configuration Map

See Section 6. Config files: system_config.json (autonomy authority), providers.json, settings.json, models.yaml, models.json, system_context.json, mouse_agent.json, vscode_workflow.json, vscode.json. Split authority: system_config.json vs `core/config.py`'s `D:\Nexus98\config.json` auto-write.

### 19.4 UI Architecture

`ui/main_window.py` is composition/entry only: `tk.Tk()` "Nexus98 Command Center" 1600x950, `theme.apply_theme`, `ttk.Notebook` with 7 tabs (Dashboard, Models, Supervisor, Agents, Bridge, Autonomy, Logs/System), each hosting a view builder from `ui/views/`. `autonomy_panel.py` (request-capable) is unwired; `autonomy_dashboard.py` is read-only `snapshot()`; `main_window_BEFORE_STATUS.py` is a stale sibling.

### 19.5 Backend Architecture

Supervisor (info/action paths), Project Engine (sole mutator), Router (keyword), Orchestrator + AgentFactory + agent_registry (agents), Memory (memory_service SQLite + legacy), Bridge (controller + api + listener + connector), Autonomy (governor/levels/policies/audit). Live state: autonomy_level "trusted" (L2), auto_execute True; safety gates all True.

### 19.6 Duplicate & Legacy Detection

Live stale modules: `core/supervisor_before_final_autogen_fix.py`, `ui/main_window_BEFORE_STATUS.py`, `core/orchestrator.py.backup_*`, `api/vscode_bridge*.backup*`, plus many `*.pre_nexus98_migration_backup` in tools/scripts. Root-level one-off patch scripts (9 files) string-patch `ui/main_window.py` and should be retired. Duplicate `ollama_models()` (tools/model_router.py + api/vscode_bridge.py); dual `vscode_bridge` (core/ vs api/); dual memory backends (memory.py + memory_service.py).

### 19.7 Dependency Map

Third-party: autogen_agentchat/autogen_core/autogen_ext (agent runtime, import-time), flask (bridge), requests (HTTP), psutil (bridge status), pystray + pynput (tray/mouse), PIL (vision), huggingface_hub (discovery), sqlite3 (stdlib), yaml (PyYAML), tkinter/ttk (UI). Internal direction: UI -> core (read-only); supervisor -> router/orchestrator/agent_factory/vscode_bridge/project_engine; governor -> supervisor.auto_execute + system_config. Environment coupling: hardcoded `D:\Nexus98` (25 places in core/), `D:\AI\Nexus98_Bridge`, `C:\Users\isoty\.continue`.

### 19.8 Code Memory Foundation

See Section 10. DB structure: extend memory_service (or sibling code_memory.db) with code_index tables (files/symbols/edges/links). Indexing: AST parse, incremental by source_hash/code_hash, prioritized by importance. Metadata per symbol: identity, location, integrity hashes, understanding, dependencies, confidence, importance.

### 19.9 Technical Debt Ranking

HIGH: hardcoded paths; split config authority; stale/duplicate supervisor+UI shells; duplicate ollama_models()/vscode_bridge. MEDIUM: root patch scripts; dual memory backends; four overlapping server entry points; checkpoint sprawl; duplicate model/context configs. LOW: legacy "AI Model Hub" strings; empty scaffold packages; core/config.py auto-write side effect; untested UI.

### 19.10 Recommended Implementation Order

1. Foundation hardening (path/config abstraction, retire legacy, consolidate servers). 2. Model Router + Providers. 3. Strategy System. 4. Memory maturation (code_memory + checkpoint/DB consolidation). 5. Guardian communication layer (client only). 6. Context continuity (WWW + Don't Forget). 7. UI evolution (only after frozen GUI spec approved). 8. Internal development surface (last, High Risk).

---

## 20. Extension Points

> Cross-reference: `docs/EXTENSION_POINT_MAP.md`, `docs/FUTURE_ARCHITECTURE_GAP_ANALYSIS.md` (#3), `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md`.

### 20.1 Model / Provider Router

Existing seams: `core/router.py`, `core/agent_factory.py`, `tools/model_router.py`, `core/catalog.py`. Proposed home: new `core/model_router/` exposing `select(provider, model, strategy, override)` with a metadata catalog feeding UI dropdowns. Constraint: user override first-class; selection non-mutating to autonomy state.

### 20.2 Local / Cloud Model Switching

Existing seams: Ollama-only access points + `config/providers.json`. Proposed home: `core/providers/` with a common adapter interface (ollama, cloud_*) selected by the Model Router. Constraint: local-first default; cloud opt-in, configuration-driven.

### 20.3 Agent Orchestration

Existing seams: `core/orchestrator.py`, `core/agent_registry.py`, `core/manager.py`, `core/pipeline.py`, `core/supervisor.py`. Proposed home: extend orchestrator + fill empty `core/supervisor/` package; strategy-aware team selection via the Model Router. Constraint: execution gated by Governor/`auto_execute`.

### 20.4 Tool Discovery

Existing seams: `tools/`, `docs/Nexus98_Tool_Registry.md`, agent tool bindings. Proposed home: `core/tools_registry/` (discovery + capability metadata) registered into agent tool sets. Constraint: discovered tools declared, not auto-granted; risky tools gated.

### 20.5 Custom Tool Generation

Existing seams: Project Engine (governed writes) + supervisor action path. Proposed home: `core/tool_gen/` producing tool code via Project Engine proposals (checkpoint -> write -> validate). Constraint: Medium/High risk; requires approval; never bypass Project Engine or Governor.

### 20.6 Memory Database

Existing seams: `core/memory_service.py` (SQLite) + `core/memory_migration.py`. Proposed home: memory_service is canonical; add indexes/categories per MEMORY_ARCHITECTURE_DESIGN.md. Constraint: retire legacy `core/memory.py`; DB over file sprawl.

### 20.7 Code Memory

Existing seams: none dedicated; memory_service can store records; tools/file_tools can read modules. Proposed home: `core/code_memory/` — AST parse tracking functions/classes/deps/hashes/summaries, persisted in the memory DB. Constraint: source files authoritative; code memory derived/index.

### 20.8 Guardian Communication Layer

Existing seams: `core/bridge_controller.py` (external companion process pattern) is the closest analogue; git_tools (read/inspect). Proposed home: `core/guardian/` — a CLIENT to the separate Guardian project for health/recovery/git/memory-maintenance requests. Constraint: Guardian owns Git/recovery; Nexus98 requests, never assumes; no merge.

### 20.9 Voice Integration

Existing seams: none (no audio modules). Proposed home: `core/voice/` (STT/TTS adapters) + a UI control; routed like any other input to the supervisor. Constraint: local-first preferred; opt-in; no dependency additions without approval.

### 20.10 VS Code Integration

Existing seams: api/vscode_bridge, bridge/*, integrations/vscode_connector, vscode_extension/extension.js; governed workflow vscode_task_send (L2). Proposed home: consolidate bridge/API/connector roles behind one documented interface; extend via new governed workflows (not new permissions). Constraint: preserve L2 vscode_task_send.

### 20.11 Internal Shell / Editor

Existing seams: Project Engine (governed writes) + supervisor action path; no shell/editor surface. Proposed home: `core/dev_surface/` (shell exec + self-edit) + future `ui/views/editor_view.py`. Constraint: HIGHEST risk tier; approval-gated, checkpointed, Governor-authorized; implement last.

### 20.12 Cross-Cutting Integration Rules

All state-changing capabilities route through the Governor; observability stays read-only via `ui.autonomy_dashboard.snapshot()`. Prefer configuration-driven design; resolve paths via `config_manager`. Fill reserved empty packages (event_bus, rule_engine, state_manager, config_manager, supervisor) as natural homes for cross-cutting concerns. Every integration follows: checkpoint -> analyze -> document -> approve -> implement -> validate.

---

## 21. Future Architecture & Gap Analysis

> Cross-reference: `docs/FUTURE_ARCHITECTURE_GAP_ANALYSIS.md`, `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md` (#11, #19), `docs/EXTENSION_POINT_MAP.md`.

### 21.1 Existing Pieces Already Implemented

Execution Layer, Governor (core/autonomy/*), Autonomy dashboard (read-only), UI refactor foundation/view separation, Local model runtime (Ollama), Model catalog + recommender, Memory (DB-backed foundation), VS Code integration, partial control-panel primitives, Test stabilization (96 tests passing), Checkpoint/recovery surfaces (file-based).

### 21.2 Missing Systems

Model Router (unified), Local/Cloud switching, Strategy System, Conversation System, Chat-first UI, Toolbar, Unified Control Panel, WWW + Don't Forget, Code Memory, Documents section (in-app), Guardian communication layer, Internal development surface, Tool discovery/generation, Provider metadata for dropdowns.

### 21.3 Required Future Modules

`core/model_router/`, `core/providers/`, `core/strategy/`, `core/conversations/`, `core/code_memory/`, `core/guardian/` (client only), `core/context/`, `core/tools_registry/` + `core/tool_gen/`, UI `views/chat_view.py` + `views/documents_view.py` + `ui/toolbar.py` + `ui/control_panel.py`, and fill existing scaffolds (event_bus/rule_engine/state_manager/config_manager/supervisor).

### 21.4 Migration Risks

AI_Model_Hub -> Nexus98 naming (blind replacement forbidden); hardcoded absolute paths (D:\Nexus98, D:\AI\Nexus98_Bridge) block portability; duplicate/legacy modules risk wrong-file edits; Governor authority must be preserved (no mutation path bypassing it); chat-first pivot risks regressing validated read-only autonomy; memory clutter (54 checkpoint dirs) vs DB-forward mandate; Guardian boundary (no Git in Nexus98); multiple server entry points risk port/role confusion.

### 21.5 Recommended Implementation Order

1. Foundation hardening (path/config abstraction, retire duplicates, consolidate servers). 2. Model Router + Providers. 3. Strategy System. 4. Memory maturation (code_memory + checkpoint/DB consolidation). 5. Guardian communication layer (client only). 6. Context continuity (WWW + Don't Forget). 7. UI evolution (after frozen GUI spec approved). 8. Internal development surface (last, High Risk). Every step follows the Development Rule.

---

## 22. Technical Debt

> Cross-reference: `docs/TECHNICAL_DEBT_REPORT.md`, `docs/NEXUS98_CODEBASE_INTELLIGENCE_REPORT.md` (#9), `docs/CURRENT_ARCHITECTURE_MAP.md`.

### 22.1 Hardcoded Paths (HIGH)

Absolute `D:\Nexus98` (and external `D:\AI\Nexus98_Bridge`) embedded across core modules (config.py, db.py, memory_service.py, project_engine.py, supervisor.py, router.py, server.py, api/vscode_bridge.py, bridge/*, mouse_agent.py, favorites.py, installer.py, logs.py, resume.py, status.py) and root patch scripts. `config/system_config.json` is the autonomy authority, but `core/config.py` points at a DIFFERENT file (`D:\Nexus98\config.json`) — split config authority. Recommendation: centralize via config_manager + environment/base-path resolution; do NOT change in the analysis phase.

### 22.2 Duplicate / Superseded Systems

Supervisor: `core/supervisor.py` (live) vs `core/supervisor_STATUS_BEFORE.py` + `core/supervisor_before_final_autogen_fix.py` (stale) + empty `core/supervisor/`. Bridge API: `api/vscode_bridge.py` vs `.backup` copies. UI: `ui/main_window.py` vs `ui/main_window_BEFORE_STATUS.py`. Config duplicates: `models_before_small_test_models.yaml`, `system_context_before_autogen.json`, `Nexus98_Tool_Registry.md.bak`, `data/db/models.db.backup_*`. Two Ollama listers. Multiple server entry points.

### 22.3 Fragile Modules

`core/agent_factory.py`/`core/orchestrator.py` (hard autogen import-time dep; tests skip). `core/pipeline.py`/`core/supervisor_before_final_autogen_fix.py` (direct HTTP to Ollama, no provider abstraction). Bridge stack (file-drop + HTTP + external venv, environment-specific). Root one-off patch scripts (brittle string patching). `core/config.py` DEFAULT auto-writes config on first load (implicit side effect).

### 22.4 Missing Abstractions

No provider/model router interface; no strategy layer; no unified config/path resolver; no conversation/session abstraction; no code-memory index; no Guardian client interface; empty scaffold packages (event_bus, rule_engine, state_manager, config_manager, supervisor) declare intent but provide no API.

### 22.5 Testing Limitations

96 tests pass but coverage is uneven: strong on vscode bridge, mouse agent, memory phase1, supervisor phase5; UI largely untested (no GUI harness). Agent/orchestrator tests skipped without AutoGen runtime. No tests for router strategy selection, catalog/discovery, or new UI view builders. Pytest requires a TMPDIR workaround (environment fragility, not code).

### 22.6 UI Limitations

Tkinter-only; dense text; limited widgets. Command Center is tab-based, not chat-first. No toolbar, no consolidated control panel, no Documents/Chat views, no WWW. `ui/autonomy_panel.py` unwired. Legacy "AI Model Hub" strings remain. No hover explanations/accessibility yet.

### 22.7 Storage / Memory Concerns

Checkpoint sprawl (54 checkpoints/ + 4 snapshots/ + backups/) conflicts with handoff #16 (DB over file sprawl). Two memory backends coexist (legacy `core/memory.py` + modern `core/memory_service.py`) with migration not clearly retired. Split state (system_state.json, system_context.json, history/, DBs) — no single continuity source. DB backups stored beside live DB. No compression/cleanup/dedup policy (Guardian-owned).

---

## 23. Phase 5 — Stability Before Autonomy

> Cross-reference: `docs/NEXUS98_PHASE5_STABLE_BEFORE_AUTONOMY_20260717.md`, `docs/PHASE5_SUPERVISOR_PROJECTENGINE.md`.

### 23.1 Checkpoint Purpose

Freeze the verified Phase 5 stable baseline so autonomy-enablement documentation/configuration work can be reverted or audited. NOT committed to git. Captured 2026-07-17.

### 23.2 Recovery Procedure

Documented only (no git commit/branch yet). Restore from `checkpoints/` hard backups (HARD_BACKUP_BEFORE_HY3_INTEGRATION_20260716_052637, HARD_BACKUP_BEFORE_PATH_MIGRATION_20260716_061932), `snapshots/config_repair_baseline_*`, and git `main` @ `9e5ef70` / branch `before_6am_recovery_20260712` @ `df4349a`. If a commit is desired later, `git stash` or `git add -A && git commit` reproduces the state.

### 23.3 Git Status Summary

Branch `main` @ `9e5ef70` (up to date with origin/main). Working tree: 101 entries (57 modified, 9 deleted, 33 untracked). Nothing staged. Full list in `docs/_checkpoint_status_20260717.txt`.

### 23.4 Working Tree Snapshot

57 modified, 9 deleted, 33 untracked files. Python env: `.venv` (Python 3.13.5). Test runner: pytest 9.1.1. Ollama: 16 models at localhost:11434.

### 23.5 Test Results (verified)

`.venv/Scripts/python.exe -m pytest -q` (TMPDIR redirected to writable workspace due to locked system pytest temp): **78 passed, 1 warning** (cosmetic SyntaxWarning in core/supervisor/__init__.py:3). Import smoke: 18 passed.

### 23.6 Environment Summary

OS Windows (America/Chicago); Python 3.13.5 (venv at D:\Nexus98\.venv); pytest 9.1.1; Ollama reachable at http://localhost:11434 (16 models).

### 23.7 Dependency Summary

Installed: autogen-agentchat/core/ext 0.7.5, click 8.4.2, ollama 0.6.2, pillow 12.3.0, psutil 7.2.2, PyAutoGUI 0.9.54, pytest 9.1.1, pywin32/pywin32-ctypes, PyYAML 6.0.3, requests 2.34.2, tqdm 4.68.3. Declared in requirements.txt: requests, huggingface_hub, psutil, pynput, pystray, Pillow, flask, autogen-agentchat, autogen-core, autogen-ext.

### 23.8 Safety Model State (preserved)

`core/supervisor.py`: `auto_execute = False` (action intents held for approval). `request_file_operation_blocking(...)` returns `awaiting_approval` when `auto_execute` is False. `run_action_task`/`run_task` action branch wired per Phase 5 doc. Project Engine remains the sole authorized file mutator with backup+validate.

---

## 24. Phase 7 — Level 2 Activation

> Cross-reference: `docs/PHASE7_LEVEL2_PROMOTION_PLAN.md`, `docs/PHASE7_LEVEL2_PROMOTION_PROCEDURE.md`, `docs/PHASE7_LEVEL2_ACTIVATION_CHECKLIST.md`, `docs/PHASE7_LEVEL2_CLOSEOUT_REPORT.md`, `docs/PHASE7_LEVEL2_PROMOTION_REHEARSAL_REPORT.md`, `docs/PHASE7_FINAL_ACTIVATION_READINESS_REPORT.md`, `docs/PHASE7_VSCODE_TASK_SEND_ACTIVATION_CHECKLIST.md`.

### 24.1 Promotion Plan

Plan to promote ONE trusted workflow (`vscode_task_send`) to L2. Selected workflow candidate is the already-validated Phase 7 `vscode_task_send` promotion. Current safety controls reviewed and must remain in force. Suitability recommendation: approve as the first governed workflow.

### 24.2 Promotion Procedure

Procedure: promotion preconditions (checkpoint present, tests green, human sign-off), trusted-workflow definition (seed `TRUSTED_WORKFLOWS_L2 = {vscode_task_send}`), first promotion run (Before/During/After), emergency rollback procedure, promotion approval checklist (readiness assessment + exact remaining action).

### 24.3 Activation Checklist

Pre-activation verification (checkpoint + safety gates), exact checkpoint creation step, exact activation step (execute only with explicit human sign-off), first-run monitoring procedure, post-activation validation. Sign-off summary required.

### 24.4 First-Run Monitoring

Monitor the first promoted run for anomalies; stop-and-report on any deviation. The L2 set auto-executes `vscode_task_send` after checkpoint + validation; everything else stays L1.

### 24.5 Closeout Report

Records: activation checkpoint reference, read-only + write-bearing validation results, request/operation IDs, backup/rollback artifacts, history/operations evidence, final trusted workflow boundary, current autonomy state, remaining limitations, Phase 8 prerequisites.

### 24.6 Rehearsal Report

Documents checklist items passed (verified this rehearsal), items requiring human action, discrepancies between documentation and repository, and exact final steps required for real L2 activation.

### 24.7 Final Activation Readiness

Readiness verdict based on four gates: checkpoint PASS, safety state PASS (all unchanged, pre-activation), workflow boundary (`vscode_task_send`) PASS, validation readiness PASS.

---

## 25. Phase 7.5 — Autonomy Control Interface

> Cross-reference: `docs/PHASE7_5_AUTONOMY_CONTROL_INTERFACE_DESIGN.md`, `docs/PHASE8_AUTONOMY_OBSERVABILITY_DESIGN.md`.

### 25.1 Autonomy Dial Concept

A single always-visible control reflecting and requesting the autonomy level. Dial positions L0–L4. Two states per position: current (live, read from Governor) and requested (queued, not yet approved). Invariant: turning the dial only creates a `governor.request_level_change(...)` call; it never writes `auto_execute` or `system_config.json`.

### 25.2 Level 0–4 Display

L0 dial disabled from requesting above L0 unless an explicit promote flow opens. Each level shows current vs requested/pending marker. Visual cue: current solid; pending outlined until approval resolves.

### 25.3 Promotion Request Flow

User selects target -> UI collects scope + justification -> `governor.request_level_change(target, scope, justification)` -> policies validates -> returns request id + pending -> UI shows "Requested: L<n> (pending approval)" and locks further changes -> on approval, Governor applies and current marker moves.

### 25.4 Approval Workflow

In-UI approval card (approve/reject) bound to recorded approver identity + timestamp. Approval persisted by `core/autonomy/audit.py` + `history/`. No self-approval for risky promotion (L(n)->L(n+1) above L1 requires explicit human sign-off). Rejection clears pending; current unchanged.

### 25.5 Checkpoint Verification

Before submission, UI queries Governor for checkpoint status; requires a fresh `checkpoints/NEXUS98_BEFORE_PHASE*_*` + `MANIFEST.txt` (Phase 7 convention). UI shows present/missing and blocks submit when missing, with a "Create checkpoint" action that asks the Governor (it performs the snapshot, not the UI).

### 25.6 Rollback Integration

Rollback control is request-only: calls `governor.initiate_rollback()` or `emergency_stop()`. Governor performs restore via `ProjectEngine.restore_backup()`, matching `checkpoints/` tree, or `git checkout`. UI shows rollback availability (Phase 5 baseline, HARD_BACKUPs, config-repair snapshots, history/) and last successful checkpoint. Emergency Stop maps to `governor.emergency_stop()`.

### 25.7 Audit History Display

Read-only feed from `core/autonomy/audit.py` + `history/operations`: timestamp, request id, from->to level, scope, approver, outcome. No write actions; transparency surface for the human-approval boundary.

### 25.8 UI / Backend Separation

UI (client) renders state, collects requests, displays approval/checkpoint/rollback/audit; has NO code path writing `auto_execute`/`autonomy_level`/`system_config.json`. Backend (Governor) is the sole writer, applying only after policies marks approved. Same client-request/server-authority split as `vscode_connector.py` (request) vs `api/vscode_bridge.py` + `bridge/*` (act). If UI is compromised, worst case is a request; policies + human approval still gate any change.

### 25.9 Migration from Manual Control

Today `auto_execute` is a code constant flipped by a human through the approved checkpointed Phase 7 procedure; no UI touches it. Phase 7.5->8 makes the Autonomy Control Interface the only supported way to REQUEST a level change; the Governor wraps the same writes so the hard floor is preserved. The manual procedure remains the recovery fallback. No behavior regression; the `vscode_task_send` L2 promotion is migrated in as the Governor's first governed workflow.

---

## 26. Phase 8 — Autonomy Governor

> Cross-reference: `docs/PHASE8_AUTONOMY_GOVERNOR_DESIGN.md`, `docs/PHASE8_AUTONOMY_GOVERNOR_IMPLEMENTATION_PLAN.md`, `docs/PHASE8_AUTONOMY_OBSERVABILITY_DESIGN.md`, `docs/PHASE8_GOVERNOR_FOUNDATION_VALIDATION_REPORT.md`, `docs/PHASE8_UI_PANEL_VALIDATION_REPORT.md`, `docs/PHASE7_TO_PHASE8_TRANSITION_PLAN.md`, `docs/PHASE7_TO_PHASE8_TRANSITION_CHECKPOINT.md`.

### 26.1 Governor Concept

A central authority that OWNS the current autonomy level and is the only component permitted to change it. Clients (UI, agent, scheduler) may only REQUEST a level change; the Governor validates against policy + approval state and either rejects or applies it through the existing `supervisor.auto_execute` + `system_config.json` path.

### 26.2 Architecture & Data Flow

Package `core/autonomy/`: `governor.py` (authority, single writer), `levels.py` (declarative L0–L4 + trusted sets, pure data), `policies.py` (approval/scope engine, decides only), `audit.py` (append-only log). Request flow: UI/agent -> `request_level_change` -> `policies` checks -> `levels` resolves -> `governor` applies -> `audit` records. The Governor never grants by itself; it only applies a policies-approved change.

### 26.3 UI Control Design

UI control panel is request-only: reflects current level, collects promotion requests (scope + justification), displays approval/checkpoint/rollback/audit. No direct autonomy-state writes. Mirrors the bridge pattern (client request vs server authority).

### 26.4 Integration Points

Wraps `supervisor.auto_execute` + `system_config.json` intent. Reads gates from `system_config.json`; writes intent level only (execution enablement still requires `auto_execute`). May record active posture in `system_context.json` but is not the source of truth for the safety floor. Adjacent to `supervisor` (same process, owned by supervisor wiring); UI/agent are clients.

### 26.5 Safety Model

Human approval boundaries enforced (every L(n)->L(n+1) needs explicit sign-off). `require_snapshots = true` stays; promotion blocked without fresh `checkpoints/` snapshot. Rollback via `ProjectEngine.restore_backup()` (auto on validate fail) + `checkpoints/` + `git checkout`. Validation requires green suite (approved TMPDIR redirect) + per-operation `validate_file`. Audit logging append-only, non-repudiable.

### 26.6 Migration Plan (Phase 7 -> Governor)

Freeze current state (keep `vscode_task_send` L2 as first governed workflow). Introduce `core/autonomy/` wrapping existing writes. Encode L0–L4 + trusted set into `levels.py`; port Phase 7 checklist into `policies.py`. Point UI at `governor.request_level_change(...)`. Re-route approvals to policies records; pre-promotion checkpoint to Governor precondition. Backfill audit from `history/operations` + `checkpoints/`. Expand L3 one at a time; L4 explicit toggle.

### 26.7 Risks & Implementation Order

Risks: accidental privilege escalation (mitigation: policies scope + approver, levels caps, audited/reversible), config conflicts (Governor single writer; stricter value correct), UI bypass (request-only invariant + code review), recovery scenarios (rollback + emergency_stop). Implementation order: levels.py -> audit.py -> policies.py -> governor.py -> UI control panel -> migrate vscode_task_send + expand.

### 26.8 Implementation Plan

Implementation order as above; existing code integration points are supervisor.auto_execute + system_config.json; migration strategy is the Phase 7->Governor port; testing strategy reuses import smoke + workflow tests with TMPDIR redirect; rollback strategy reuses ProjectEngine + checkpoints + git; first milestone is levels.py + audit.py + policies.py + governor.py wrapping existing writes without behavior change.

### 26.9 Observability Design

Objective: read-only dashboard exposing the eight fields (level, workflows, pending, approvals, audit, checkpoint, rollback, emergency-stop). Hard invariants carried from Governor design: Governor sole writer; UI requests only; no Governor imports in observability views; snapshot() is the only read path. Placement: `ui/autonomy_dashboard.py` (already implemented, read-only). Explicit non-goals: no write path, no new autonomy levels. Approval gate: design must be approved before implementation.

### 26.10 Foundation Validation

Validation report (run): levels.py PASS, policies.py PASS, audit.py PASS, governor.py PASS, regression PASS. Out-of-scope (per rules): UI panel wiring, live promotion, cloud. Verdict: foundation validated; safe to proceed to UI panel + Phase 7 migration behind approval.

### 26.11 UI Panel Validation

Validation report: implemented surfaces are request-only (autonomy_panel.submit_level_request -> governor.request_level_change). Validation results PASS. Standing boundaries preserved (Governor sole writer; UI never assigns auto_execute or writes system_config). Note on config intent: Governor writes intent level; auto_execute remains the hard floor. Verdict: request-only panel validated.

### 26.12 Phase 7 -> Phase 8 Transition

Transition checkpoint captures end-of-Phase-7 state and the standing boundary (vscode_task_send L2 trusted; auto_execute floor; request-only UI). Transition plan: Phase 7 completion criteria met; Phase 8 prerequisites (Governor design validated, foundation tests PASS) satisfied; recommended order (design -> foundation -> UI panel -> migrate); explicit non-goals (no new autonomy levels, no behavior regression); first Phase 8 milestone is the `core/autonomy/*` foundation.

---

## 27. Phase 9 — UI Overhaul

> Cross-reference: `docs/PHASE9_UI_OVERHAUL_PLAN.md`, `docs/PHASE9_GUI_BEHAVIOR_SPEC.md`, `docs/NEXUS98_UI_DESIGN_SPECIFICATION.md`.

### 27.1 Current Framework & Entry Points

Tkinter + ttk (clam theme), no external UI toolkit, no deps. Entry: `main.py` -> `ui.main_window.launch_ui()` (crash-logged to `logs/startup_crash.log`); `debug_launch.py` dev harness. `launch_ui()` builds the themed `ttk.Notebook` shell and hosts view builders.

### 27.2 Existing Tabs / Views / Widgets

7 tabs: Dashboard, Models, Supervisor, Agents, Bridge, Autonomy (read-only), Logs/System. Views in `ui/views/` (one class + `build()` each). Theming centralized in `ui/theme.py`.

### 27.3 main_window.py Structure

`ui/main_window.py` is composition/entry only (Phase 9 Step 1-2 refactor). Title bar + `ttk.Notebook` with 7 tabs; each tab hosts a view builder; coordinated `refresh()` (models + agents); search trace; footer buttons; initial `refresh()`; `app.mainloop()`. No backend/autonomy logic.

### 27.4 Backend Data Sources

`ui/autonomy_dashboard.py` (READ-ONLY snapshot), `ui/autonomy_panel.py` (REQUEST-CAPABLE, unwired), `governor` (SOLE AUTONOMY AUTHORITY), `core/status.py` (system status), Ollama, `core/bridge_controller.py` (bridge), and supporting providers. Passive displays use `snapshot()` only.

### 27.5 Components To Preserve

Preserve: `launch_ui()` contract, theme, view-builder pattern, read-only autonomy behavior, the 7-tab structure as a fallback, the autonomy dashboard `snapshot()` surface, and all safety invariants.

### 27.6 Overhaul Plan & Constraints

Guiding constraints (non-negotiable): Tkinter/ttk only; no new deps; preserve `launch_ui()`; data-driven views; read-only autonomy; phased rollout. Target architecture: chat-first workspace with toolbar + dynamic panels (per UI Design Spec). Autonomy tab stays read-only. Threading + responsiveness must not block the UI. New "System" tab optional/additive. Cleanup is non-behavioral (retire legacy siblings, not rewrites). Phased rollout: checkpoint -> implement -> validate -> test. Validation per step. Risks: regressing read-only autonomy; mitigate by preserving snapshot() and request-only panel.

### 27.7 GUI Behavior Spec (Frozen)

`docs/PHASE9_GUI_BEHAVIOR_SPEC.md` is a DESIGN FREEZE: application identity, main window behavior (startup, default landing, navigation, resize, panels), major UI areas (Dashboard/Models/Supervisor/Agents/Bridge/Autonomy read-only/Logs), visual design (theme/colors/density/icons/typography/status/animations), interaction rules (buttons/toggles/sliders/notifications/confirmations/approval dialogs), and autonomy UI invariants (Governor authority, read-only dashboard, approval boundaries). Scope boundaries for future implementation are defined.

---

## 28. Autonomous Operating Rules

> Cross-reference: `docs/Nexus98_Autonomous_Operating_Rules.md`, `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md` (#6), `docs/Nexus98_Vision_Architecture.md` (#6).

### 28.1 Guiding Principles

1. Inspect before changing (use a real tool to read). 2. Preserve existing architecture (surgical, minimal changes). 3. Explain decisions (record the "why"). 4. Never pretend identity (identify as Nexus98 Agent, not ChatGPT/OpenAI; underlying model may be Qwen/DeepSeek). 5. Keep changes reversible (checkpoint/backup).

### 28.2 Autonomy Levels

Single gate `supervisor.auto_execute` (default False). L0 Supervised (all action intents -> awaiting_approval; no writes). L1 Assisted (proposals + checkpoint; human approves). L2 Semi-Autonomous (True scoped; approved-by-policy actions execute). L3 Autonomous (True broad; trusted workflows; checkpoint + monitoring). Ships at L0/L1. Information intents always routed to agent path, no approval.

### 28.3 Intent Routing (verified)

`supervisor.detect_intent(task)` classifies action keywords (create/write/modify/edit/update/change/add/build/make file/code) -> action; everything else -> information. Action -> `run_action_task` -> Project Engine proposals -> checkpoint requests. Information -> `run_task` -> `route` -> `get_orchestrator`.

### 28.4 Safety Gate (mandatory)

`auto_execute` defaults False. When disabled, `request_file_operation_blocking` sets `status="awaiting_approval"` and returns without executing. Execution only proceeds when `auto_execute` is True AND request `approval == "approved"`. `ProjectEngine.execute_engine_request` blocks any request whose approval is not "approved".

### 28.5 Checkpoint Requirements

Checkpoint required before ANY mutation (file writes/creates, dependency/env changes, config edits, production code modification). Contents: copy of files about to change (or git snapshot), reason, rollback command. Convention: `checkpoints/<NAME>_<YYYYMMDD_HHMMSS>/` with README.txt/MANIFEST.txt.

### 28.6 Recovery Procedures

Stale/locked temp dirs: redirect TMPDIR rather than delete. Failed file write: ProjectEngine restores backup from BACKUP_DIR/history/. Code change rollback: restore checkpoints/ or git checkout. Agent/Ollama failure: agent path degrades gracefully (`run_task` returns error string, no crash). Recovery anchors enumerated in 6b.

### 28.7 Operational Discipline

Batch related changes into one operation + one checkpoint. Verify every change (imports, tests, diff) before done. Do not modify production code just to make tests pass; report real defects and obtain approval. Do not begin deployment/launcher work until the milestone is documented and validated.

### 28.8 Stop Conditions (escalate to human)

Stop and report when: destructive action required; production architecture must change; credentials/secrets required; admin privileges unavoidable; production behavior defect found (report, do not unilaterally change).

### 28.9 Relaxable vs Strict Rules

Relaxable post-Phase 5 (read-only/docs only, while auto_execute=False): R1 require approval before file read (relax to read-only), R2 halt on untracked file creation (relax to docs-only), R3 re-verify env per step (relax frequency), R4 treat every import as needing smoke test (relax to code change). Must remain strict: no autonomous production mutation without approval; no dependency install without sign-off; no launcher/deploy until framework documented/validated; no destructive/credential/admin action without approval; stop-and-report on defects. Relaxation bounded: applies only while auto_execute=False and only to read-only/docs/checkpoint ops; flipping auto_execute True or touching production re-engages strict rules.

---

## 29. Implementation Governance & Development Rule

> Cross-reference: `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md` (Development Rule), `docs/Nexus98_Autonomous_Operating_Rules.md`, all Phase plans.

### 29.1 Canonical Development Rule

Before implementation: checkpoint -> analyze -> document -> approve -> implement -> validate. This is mandatory for every step. No major UI implementation begins until the design specification is complete.

### 29.2 Checkpoint Discipline

A checkpoint is required before any mutation (file/dependency/config/production code). Convention `checkpoints/<NAME>_<YYYYMMDD_HHMMSS>/` with README.txt/MANIFEST.txt (purpose, scope, revert). Pre-promotion checkpoints (`NEXUS98_BEFORE_PHASE*_*`) are a Governor promotion precondition (`require_snapshots = true`).

### 29.3 Approval & Governance Gates

Autonomy changes require human sign-off captured as an approval record (policies). L(n)->L(n+1) above L1 needs explicit human sign-off; the UI cannot self-approve. New autonomous workflows added one-at-a-time via the governed promotion path. High Risk / Guardian-protected capabilities (internal shell, self-modification) require Guardian protection.

### 29.4 Validation Requirements

Promotion requires the green test suite (with approved TMPDIR redirect) and per-operation `validate_file`. Import smoke (`tests/test_import_smoke.py`) + relevant workflow tests. UI changes validated per Phase 9 step. Foundation phases validated before UI/integration (Phase 8 pattern).

### 29.5 Standing Boundaries

Governor is sole writer of autonomy state; UI requests only. Nexus98 never owns Git or performs recovery writes; Guardian owns those. Guardian remains a separate project; Nexus98 is a client. Source files remain authoritative over any index/memory. Local-first default; cloud opt-in. No new autonomy levels, workflows, or permissions introduced by the UI. Tkinter/ttk only; no new deps unless separately approved.

[RULE]: checkpoint -> analyze -> document -> approve -> implement -> validate (mandatory for every step).

---

## 30. Document Index & Cross-Reference Map

> This section is the master index of every existing document. No document is
> modified, merged, or deleted by this Constitution.

### 30.1 Architecture & Handoff

- `docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md` — master source of truth (handoff v2).
- `docs/Nexus98_Vision_Architecture.md` — vision & component architecture.
- `docs/CURRENT_ARCHITECTURE_MAP.md` — read-only current architecture audit.
- `docs/FUTURE_ARCHITECTURE_GAP_ANALYSIS.md` — gap analysis vs handoff.
- `docs/EXTENSION_POINT_MAP.md` — where future systems integrate.
- `docs/TECHNICAL_DEBT_REPORT.md` — read-only debt analysis.
- `docs/NEXUS98_CODEBASE_INTELLIGENCE_REPORT.md` — repository intelligence report.

### 30.2 UI & Design

- `docs/NEXUS98_UI_DESIGN_SPECIFICATION.md` — future UI architecture (spec).
- `docs/PHASE9_GUI_BEHAVIOR_SPEC.md` — frozen GUI behavior contract.
- `docs/PHASE9_UI_OVERHAUL_PLAN.md` — Phase 9 UI overhaul plan.

### 30.3 Intelligence & Memory

- `docs/NEXUS98_MODEL_INTELLIGENCE_SPECIFICATION.md` — model/strategy intelligence spec.
- `docs/MEMORY_ARCHITECTURE_DESIGN.md` — memory system design.
- `docs/NEXUS98_CODE_MEMORY_SPECIFICATION.md` — code memory spec.

### 30.4 Autonomy & Governor

- `docs/PHASE8_AUTONOMY_GOVERNOR_DESIGN.md`
- `docs/PHASE8_AUTONOMY_GOVERNOR_IMPLEMENTATION_PLAN.md`
- `docs/PHASE8_AUTONOMY_OBSERVABILITY_DESIGN.md`
- `docs/PHASE8_GOVERNOR_FOUNDATION_VALIDATION_REPORT.md`
- `docs/PHASE8_UI_PANEL_VALIDATION_REPORT.md`
- `docs/PHASE7_5_AUTONOMY_CONTROL_INTERFACE_DESIGN.md`
- `docs/Nexus98_Autonomous_Operating_Rules.md`

### 30.5 Guardian (Separate Project)

- `docs/GUARDIAN_ARCHITECTURE_AUDIT.md`
- `docs/GUARDIAN_DEVELOPMENT_ROADMAP.md`

### 30.6 Configuration

- `docs/CONFIG_AUTHORITY.md` — configuration authority map.

### 30.7 Tools & Agents

- `docs/Nexus98_Tool_Registry.md`
- `docs/MOUSE_AGENT_SYSTEM.md`
- `docs/PHASE5_SUPERVISOR_PROJECTENGINE.md`

### 30.8 Phase 7 (Level 2 Activation)

- `docs/PHASE7_LEVEL2_PROMOTION_PLAN.md`
- `docs/PHASE7_LEVEL2_PROMOTION_PROCEDURE.md`
- `docs/PHASE7_LEVEL2_ACTIVATION_CHECKLIST.md`
- `docs/PHASE7_LEVEL2_CLOSEOUT_REPORT.md`
- `docs/PHASE7_LEVEL2_PROMOTION_REHEARSAL_REPORT.md`
- `docs/PHASE7_FINAL_ACTIVATION_READINESS_REPORT.md`
- `docs/PHASE7_VSCODE_TASK_SEND_ACTIVATION_CHECKLIST.md`

### 30.9 Phase 7 -> 8 Transition

- `docs/PHASE7_TO_PHASE8_TRANSITION_PLAN.md`
- `docs/PHASE7_TO_PHASE8_TRANSITION_CHECKPOINT.md`

### 30.10 Phase 5 Checkpoint

- `docs/NEXUS98_PHASE5_STABLE_BEFORE_AUTONOMY_20260717.md`

### 30.11 VS Code Workflow

- `docs/vscode_workflow_setup.md`
- `docs/_vscode_task_send_monitor_probe.md`

### 30.12 Misc / Index

- `docs/README.md` — documentation index (AI_Model_Hub / Nexus98).

*Diagram placeholder: Full document dependency / cross-reference graph.*

---

*End of Constitution. This document is structural only; all authoritative detail
remains in the referenced existing documents, which are preserved unchanged.*

---

# Appendix A: Interview Decision Integration Amendments

## Purpose

This appendix captures finalized architectural decisions from the Nexus98 interview process.

These decisions supplement existing Constitution sections and should be incorporated into future revisions.

---

# Command-Driven Nexus Operation

Nexus98 should support natural language operational requests.

Example:

"Hey Nexus, do this."

Nexus98 interprets intent, determines required systems, validates permissions, and executes approved actions.

The user remains the final authority.

---

# Automatic Intelligence Selection

Nexus98 automatically evaluates:

- model
- provider
- agent
- strategy

The selected intelligence path should be visible.

Nexus98 explains:

- what was selected
- why it was selected
- strengths
- limitations

The user may override automatic selection.

---

# WWW Continuity System

WWW (Where Were We) restores user context after:

- normal shutdown
- Don't Forget activation
- interrupted sessions

WWW provides:

- previous progress
- current task
- decisions made
- unfinished work
- recommended next actions

---

# Don't Forget

Don't Forget creates a continuity capture point.

It records:

- session state
- current work
- recovery marker
- WWW preparation data

---

# Guardian Recovery Authority

Guardian remains separate from Nexus98.

Guardian owns:

- Git operations
- recovery
- integrity validation
- known-good states
- checkpoints

Nexus98 communicates with Guardian but does not replace it.

---

# Memory Lifecycle

Nexus98 memory must prioritize knowledge preservation while minimizing storage.

Avoid:

- checkpoint sprawl
- duplicate history
- unnecessary archive growth

Prefer:

- database storage
- indexing
- compression
- lifecycle management

---

# Code Memory

Code Memory tracks understanding of:

- Python modules
- JSON
- YAML
- configuration
- dependencies
- relationships

Purpose:

Enable fast understanding and safe modification.

---

# Adaptive Interface

Nexus98 must remain functional when resized.

Requirements:

- responsive layouts
- scrollable areas
- collapsible optional panels
- preserved default accessibility

---

# Internal Development Environment

Future Nexus98 may include:

- integrated VS Code
- internal shell
- coding workspace
- AI development workflows

Self modification requires:

1. Analysis
2. Proposal
3. Checkpoint
4. Controlled change
5. Testing
6. Validation

---

