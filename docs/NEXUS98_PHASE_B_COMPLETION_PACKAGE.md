# Nexus98 — Phase B Completion Package

> Onboarding + architecture handoff for new developers. This document is the
> single entry point for understanding Nexus98 after Phase B. It consolidates
> the architecture summary, module map, dependency graph, startup sequence,
> agent interaction flow, configuration, directory structure, technical debt,
> and Phase C recommendations.
>
> Scope: documentation only. No implementation code was changed to produce this
> package. Where this document references prior phase docs, it names them so you
> can drill in. Canonical phase-state snapshot remains `docs/PROJECT_STATE.md`.

## 0. Reader's Map

| If you need… | Read section |
|---|---|
| The 10,000-ft view | 1. Architecture Summary |
| Where code lives | 2. Module Map, 7. Directory Structure |
| How pieces depend on each other | 3. Component Dependency Graph |
| What happens on launch | 4. Startup Sequence |
| How a task flows through agents | 5. Agent Interaction Flow |
| What to edit for behavior | 6. Configuration Files |
| Known limitations | 8. Technical Debt |
| What to build next | 9. Phase C Recommendations |

---

## 1. Architecture Summary

Nexus98 is an autonomy-governed AI workstation. A **Tkinter "Command Center"**
UI (`ui/main_window.py`) is the primary user surface; beneath it sits a layered
backend organized around clear **authority boundaries**:

- **Execution authority** — `core/supervisor.py` runs tasks. It owns the task
  lifecycle (`detect_intent` → `run_task` / `run_action_task`) and never acts
  autonomously beyond its level.
- **Routing authority** — `core/router.py` selects the agent role for a task.
- **Autonomy authority** — `core/autonomy/governor.py` is the *sole* writer of
  autonomy state (current level, level-change requests, emergency stop).
  Nothing else flips `auto_execute` or mutates `config/system_config.json`.
- **Coordination glue** — `core/coordination.py` and `core/integration.py`
  connect the verified frameworks (Strategy, Model Intelligence, Planning,
  Workspace Continuity, Code/Knowledge Memory, Review) into a single advisory
  context. These layers are **read-only with respect to autonomy**; they advise,
  they do not decide.
- **Cognitive layer** — `core/cognitive/*` composes ten advisory frameworks
  (intent, context, planning, decision, execution, review, learning, goals,
  knowledge, comms) into one `CognitiveCycle` per task via
  `CognitiveOrchestrator`. It prepares and analyzes; it never executes.
- **Validation/observability** — `core/frameworks/validation.py`
  (read-only health check) and `ui/autonomy_dashboard.py` (read-only snapshot
  of the Governor) make the system's state inspectable without mutation.

### Layering (top → bottom)

```
ui/ (Command Center, Tkinter, read-only views)
  └─ core.integration.FrameworkIntegrator   (advisory coordination facade)
       ├─ core.framework_hooks.SupervisorHooks (wraps Supervisor lifecycle)
       ├─ core.coordination.AgentCoordinator
       ├─ core.cognitive.orchestrator.CognitiveOrchestrator
       └─ frameworks: strategy / model / planning / workspace / memory / review
core.supervisor (execution) ── core.router (routing)
core.autonomy.governor (autonomy authority, sole writer)
core.bridge_controller + api/ + bridge/ (VSCode bridge)
core.config + config/*.json (single config authority)
```

### Design invariants (hard rules)

1. Only the Governor may change autonomy state. No UI, integration, or hook
   layer may call `request_level_change` / `emergency_stop` or write
   `config/system_config.json`.
2. The integration/coordination/cognitive layers are advisory only; they never
   execute and never escalate autonomy.
3. Validators and dashboards are read-only diagnostics; a failing diagnostic
   must never crash the app — it degrades gracefully.

---

## 2. Current Module Map

### Entry points
- `main.py` — prints banner, imports `ui.main_window.launch_ui()`, crash-logged
  to `logs/startup_crash.log`.
- `debug_launch.py` — dev harness calling `launch_ui()`.
- `api/vscode_bridge.py` — Flask bridge (`health`, `models`, `chat`).
- `bridge/vscode_listener.py`, `bridge/worker.py` — file-drop task processors.
- `core/api_server.py`, `core/server.py` — additional server entry points.
- `runtime/generate_models.py` — model catalog generation.

### `ui/` (Tkinter Command Center)
- `main_window.py` — shell: builds themed `ttk.Notebook`, hosts view builders,
  owns `refresh()` coordination. Exposes `launch_ui()`.
- `theme.py` — theme application.
- `autonomy_dashboard.py` — **read-only** snapshot of Governor state
  (`snapshot()`), 8 approved fields. Never mutates.
- `autonomy_panel.py` — request-capable autonomy panel.
- `views/` — `dashboard_view.py` (overview + live boot report + live cognitive
  cycle), `models_view.py`, `supervisor_view.py`, `agents_view.py`,
  `bridge_view.py`, `autonomy_view.py` (read-only observability),
  `system_view.py` (logs).

### `core/` (backend)
- **Execution/routing**: `supervisor.py`, `router.py`, `orchestrator.py`
  (Supervisor's agent orchestrator), `project_engine.py`, `agent_factory.py`,
  `agent_registry.py`, `command.py`, `queue.py`, `workers.py`.
- **Autonomy (authority)**: `autonomy/governor.py`, `autonomy/levels.py`,
  `autonomy/audit.py`, `autonomy/policies.py`.
- **Cognitive (advisory)**: `cognitive/bootstrap.py` (`BootReport`,
  `CognitiveBootstrap`), `cognitive/orchestrator.py` (`CognitiveOrchestrator`,
  `CognitiveCycle`), plus `intent`, `context`, `planning`, `decision`,
  `execution`, `review`, `learning`, `goals`, `knowledge`, `comms`.
- **Integration/coordination**: `integration.py` (`FrameworkIntegrator`,
  `default_integrator`), `framework_hooks.py` (`SupervisorHooks`),
  `coordination.py` (`AgentCoordinator`, `TaskHandoff`),
  `capability_awareness.py` (`CapabilityDiscoverer`).
- **Frameworks**: `frameworks/strategy.py`, `frameworks/model.py`
  (`ModelIntelligence`), `frameworks/workspace.py` (`WorkspaceReality`),
  `frameworks/planning.py` (`PlanningEngine`), `frameworks/knowledge.py`
  (`KnowledgeArchitecture`), `frameworks/review.py` (`ReviewSystem`),
  `frameworks/extension.py` (`ExtensionRegistry`), `frameworks/validation.py`
  (`FrameworkValidator`).
- **State/memory**: `memory.py`, `memory_service.py`, `code_memory.py`,
  `continuity.py`, `identity.py`, `state_manager/`, `config_manager/`.
- **Bridge/integration surfaces**: `bridge_controller.py`, `bridge.py`,
  `vscode_bridge.py` (mirror in `api/`), `integrations/vscode_connector.py`.
- **Config/runtime**: `config.py` (`load_config`, single authority),
  `boot.py` (`verify_environment`), `autostart.py`.
- **Scaffold packages** (present, partially built): `event_bus/`,
  `rule_engine/`, `supervisor/` (note: `supervisor/__init__.py` carries a
  cosmetic `SyntaxWarning`).

### `api/`, `bridge/`, `integrations/`, `tools/`, `runtime/`, `scripts/`
- `api/vscode_bridge.py` — Flask HTTP surface (health/models/chat).
- `bridge/` — file-drop listener + worker (VSCode task handoff).
- `integrations/vscode_connector.py` — HTTP client to bridge/API.
- `tools/` — file/git/model tools, agent runner/selector, model_router,
  continue_sync, ollama_manager.
- `runtime/generate_models.py` (+ `run-ai.ps1`).
- `scripts/` — PowerShell launch/setup helpers.

---

## 3. Component Dependency Graph

Arrows mean "depends on / calls into". Solid = hard runtime dependency,
dotted = advisory/read-only observation.

```
                         ui/main_window.launch_ui()
                                   |
              +--------------------+--------------------+
              |                    |                    |
        ui/views/dashboard   ui/autonomy_dashboard   other ui/views/*
              |                    |                    |
              v                    v                    v
   core.integration           core.autonomy           core.bridge_controller
   .default_integrator        .governor (AUTHORITY)   core.agent_registry
        |  |  |                                          |
        |  |  +-- core.cognitive.orchestrator ----------+ (advisory cycle)
        |  |         (CognitiveOrchestrator)
        |  +---- core.framework_hooks (SupervisorHooks)
        |            |
        |            v
        |      core.supervisor  <----- core.router (routing authority)
        |            |
        +---- core.coordination (AgentCoordinator)
                  |
   +--------------+--------------+--------------+--------------+
   v              v              v              v              v
frameworks/    frameworks/    frameworks/    frameworks/    frameworks/
strategy       model          planning       workspace      memory
                                                |             |
                                                v             v
                                          core.continuity  core.code_memory
                                                          core.knowledge

core.frameworks.validation  --> reads all of the above (read-only diagnostics)
core.config.load_config     --> config/*.json (single authority)
```

Key boundaries:
- `ui/*` and `core.integration` observe the Governor via `autonomy_dashboard`
  and `snapshot()`; they never call Governor mutators.
- `core.integration` and `core.framework_hooks` are **advisory**: they call the
  Supervisor's existing functions and record context; failures are re-raised.
- `core.supervisor` is the only executor; `core.router` is the only role picker.
- `core.cognitive.orchestrator` composes the ten cognitive frameworks but
  executes nothing. Its output is surfaced live in the Dashboard.

---

## 4. Startup Sequence

1. **`main.py`** prints `"Starting AI Model Hub..."`, sets crash-log path
   (`logs/startup_crash.log`), and calls `ui.main_window.launch_ui()` inside a
   try/except that writes any traceback to the crash log and waits for Enter.
2. **`launch_ui()`** creates the Tk root (`Nexus98 Command Center`, 1600×950),
   applies `ui.theme`, and builds a `ttk.Notebook` with tabs:
   Dashboard, Models, Supervisor, Agents, Bridge, Autonomy, Logs/System.
3. **View builders run** (each read-only where noted):
   - `dashboard_view.build` → renders overview + **live cognitive boot report**
     + **live cognitive cycle** (timer-driven refresh, 5s).
   - `models_view.build` → model search/list + inspector.
   - `supervisor_view.build` → task console; footer buttons drive shared
     `refresh()`.
   - `agents_view.build`, `bridge_view.build`, `autonomy_view.build`
     (read-only `snapshot()`), `system_view.build` (log tail).
4. **Backend wiring at import time** (no UI coupling):
   - `core.integration.default_integrator` is constructed **with a wired
     `CognitiveOrchestrator`** so `cognitive_cycle()` returns live data.
   - `core.capability_awareness`, `core.frameworks.validation`, and
     `core.cognitive.bootstrap` are importable and used by the boot report.
5. **Live refresh begins**: the Dashboard's `_schedule_cycle()` uses
   `parent.after(5000, …)` to re-run `default_integrator.cognitive_cycle(...)`
   so the cognitive cycle updates without user action. The manual
   "Refresh Overview" button re-pulls the overview + boot report.
6. **`app.mainloop()`** runs the Tk event loop until the window closes.

> Note: `core/boot.py:verify_environment()` and `core/autostart.py` exist as
> environment/startup hooks but are not invoked by `main.py` today; they are
> available for Phase C first-run seeding (see §9).

---

## 5. Agent Interaction Flow

Nexus98 models agents in two complementary ways: a **registry of roles**
(`core/agent_registry.AGENTS`) and a **runtime orchestrator**
(`core/orchestrator.Orchestrator`) that loads agent instances and dispatches
tasks. The Supervisor is the execution authority that drives the flow.

### 5.1 Registry (`core/agent_registry.py`)
A static `AGENTS` dict describing known agents: `Supervisor` (controller,
ONLINE), `Coding Agent` (llm, `qwen3-coder:30b`), `Reasoning Agent`
(llm, `deepseek-r1:32b`), `Vision Agent` (vision, `llava:latest`),
`Mouse Agent` (automation, DEVELOPMENT), `Memory Agent` (embedding,
`nomic-embed-text:latest`, WAITING). `list_agents()` is the read-only accessor
used by the Dashboard.

### 5.2 Task lifecycle (advisory → execute)
```
User / VSCode bridge submits a task
        |
        v
core.router.detect_intent(task)        # routing authority: picks role
        |
        v
core.supervisor.run_task / run_action_task
        |  (execution authority; respects current autonomy level)
        |
        +-- core.framework_hooks.SupervisorHooks wraps the lifecycle:
        |     on_task_start -> integrator.build_task_context()  (advisory)
        |                     + orchestrator.run_cycle(task)     (advisory)
        |     on_task_plan / on_task_execute / on_task_complete / on_failure_recovery
        |     (records strategy guidance, workspace reality, model pick,
        |      memory recall, review verdict; re-raises on failure)
        |
        v
core.coordination.AgentCoordinator      # glue: strategy->role hint, memory, continuity, tools
        |
        v
core.orchestrator.Orchestrator.load_agents() / get_agent(role)
        |  dispatches to the selected agent instance
        v
Agent executes (LLM call / tool use / vision / automation)
        |
        v
results recorded to memory/continuity/review; UI refreshes
```

### 5.3 Advisory cognitive cycle (parallel, non-blocking)
For each task start, `CognitiveOrchestrator.run_cycle(task)` composes
`intent → context → plan → decision → execution-prep → review → learning` and
publishes lifecycle messages on `core/cognitive/comms.CommunicationBus`. The
Dashboard subscribes by polling `default_integrator.cognitive_cycle(...)` on a
timer. The cycle never executes and never changes autonomy.

### 5.4 Autonomy gating
Every autonomous action is bounded by `core/autonomy/governor.current_level()`.
The Governor is the sole writer of level/emergency-stop state; UI and
integration layers only read it via `ui.autonomy_dashboard.snapshot()`.

---

## 6. Configuration Files

Config lives under `config/` and is loaded through `core/config.load_config()`,
which is the **single config authority** (consolidated in `config/runtime.json`;
legacy root `D:\Nexus98\config.json` is no longer the source of truth — see
`docs/CONFIG_AUTHORITY.md`).

| File | Authority for | Notes |
|---|---|---|
| `config/runtime.json` | Paths/limits (`base_path`, `hf_dir`, `gguf_dir`, `max_workers`, `ui_mode`, `cache_ttl`) | Read by `core/boot.py:verify_environment()` to create dirs. |
| `config/system_config.json` | **Autonomy authority** (`autonomy_level`, `mode`, `safety.*`) | Governor intent; only the Governor writes it. |
| `config/models.json` / `models.yaml` | Model catalog | Validated by `FrameworkValidator` (`config:models_json_valid`). |
| `config/providers.json` | Model/provider endpoints | HuggingFace/Ollama provider config. |
| `config/settings.json` | App settings | General runtime toggles. |
| `config/system_context.json` | Project context/phase | May lag actual phase (cosmetic; see §8). |
| `config/mouse_agent.json` | Mouse automation config | Used by Mouse Agent (DEVELOPMENT). |
| `config/vscode.json` / `vscode_workflow.json` | VSCode bridge/workflow roles | Bridge connector + desktop/laptop roles. |

### Data stores (created lazily on first write)
These are **expected-empty on a clean install** and are not defects:
- `data/workspace.json` — `WorkspaceReality` store.
- `data/reviews.json` — `ReviewSystem` store.
- `data/extensions.json` — `ExtensionRegistry` store.
- `data/continuity.json`, `data/plans.json`, `data/resume.json`,
  `data/system_state.json`, `data/db/memory.db` — continuity/memory/planning.

> Editing `config/system_config.json` by hand is **not** the supported path for
> autonomy changes; use the Governor's request/approval flow. UI and integration
> layers must never write it.

---

## 7. Directory Structure

```
Nexus98/
├── main.py                  # launcher -> launch_ui()
├── debug_launch.py          # dev harness
├── core/                    # backend (authoritative logic)
│   ├── supervisor.py        # execution authority
│   ├── router.py            # routing authority
│   ├── orchestrator.py      # Supervisor agent orchestrator
│   ├── project_engine.py
│   ├── agent_registry.py    # AGENTS role registry (read-only)
│   ├── agent_factory.py
│   ├── autonomy/            # governor (autonomy authority), levels, audit, policies
│   ├── cognitive/           # bootstrap + orchestrator + 10 advisory frameworks
│   ├── frameworks/          # strategy, model, workspace, planning, knowledge, review, extension, validation
│   ├── integration.py       # FrameworkIntegrator (advisory facade)
│   ├── framework_hooks.py   # SupervisorHooks (advisory lifecycle)
│   ├── coordination.py      # AgentCoordinator (glue)
│   ├── capability_awareness.py
│   ├── bridge_controller.py # bridge status
│   ├── config.py            # single config authority (load_config)
│   ├── boot.py / autostart.py
│   ├── event_bus/ rule_engine/ state_manager/ config_manager/ supervisor/  # scaffold packages
│   └── ... (memory, catalog, ollama, search, installer, etc.)
├── ui/                      # Tkinter Command Center
│   ├── main_window.py       # launch_ui() entry
│   ├── theme.py autonomy_dashboard.py autonomy_panel.py
│   └── views/               # dashboard, models, supervisor, agents, bridge, autonomy, system
├── api/                     # Flask VSCode bridge (vscode_bridge.py)
├── bridge/                  # file-drop listener + worker
├── integrations/            # vscode_connector.py (HTTP client)
├── tools/                   # file/git/model tools, agent runner/selector, model_router
├── runtime/                 # generate_models.py, run-ai.ps1
├── scripts/                 # PowerShell launch/setup
├── config/                  # runtime.json, system_config.json, models.*, providers.json, ...
├── data/                    # db/, models/, *.json state stores
├── tests/                   # 50 pytest modules, 284 tests
├── docs/                    # architecture/phase handoffs (this package + many)
├── handoffs/                # phase handoff notes
├── logs/ startup_crash.log # crash log
├── checkpoints/ snapshots/ backups/ agent_logs/ history/ reports/  # recoverable state
├── vscode_extension/        # JS extension (extension.js)
└── agents/ agent_logs/      # agent run artifacts
```

> Source vs. state: `core/`, `ui/`, `api/`, `bridge/`, `tools/`, `runtime/`,
> `scripts/`, `config/`, `tests/` are source. `data/`, `logs/`, `checkpoints/`,
> `snapshots/`, `backups/`, `history/`, `reports/`, `agent_logs/` are recoverable
> runtime state. `AI_Model_Hub_archive/`, `archive/`, `diagnostic_parts/`,
> `.venv_broken_*` are superseded and not current architecture.

---

## 8. Remaining Technical Debt

Carried over from `docs/PROJECT_STATE.md` and `docs/TECHNICAL_DEBT_REPORT.md`,
plus items confirmed during Phase B wiring. None block launch; all are
documented so a new developer is not surprised.

1. **Three expected-empty data stores** (`data/workspace.json`,
   `data/reviews.json`, `data/extensions.json`) report as `failed` in
   `FrameworkValidator`. These are **expected warnings**, not defects: each
   framework's `_load()` degrades to an empty store when the file is absent, and
   the file is created on first write. They are recorded in
   `validation._EXPECTED_EMPTY_STORES` and surfaced via
   `validate()["expected_failures"]`. The boot report therefore shows
   `failed=3` on a clean install until first use — intentional.
2. **`core/supervisor/__init__.py` SyntaxWarning** — invalid escape sequence;
   cosmetic, non-fatal.
3. **`config/system_context.json.current_phase` lag** — still reads an older
   phase label; does not reflect current state. Cosmetic; fix in a config pass.
4. **Branding mismatch** — `core/identity.py` says "AI Model Hub Agent" while
   Operating Rules say "Nexus98 Agent". Cosmetic; unify in a branding pass.
5. **`main.py` hardcoded crash-log path** — `D:\Nexus98\logs\startup_crash.log`
   is absolute; acceptable for this single-machine workstation but not portable.
6. **Locked pytest temp** — a prior interrupted session can lock the system
   `Temp/pytest-of-*` dir; re-run tests with `TMPDIR` pointed at a writable root
   (e.g. `D:\Nexus98\.pytest_temp_alt`). Not a code defect.
7. **`core/boot.py` / `core/autostart.py` not wired into `main.py`** — available
   first-run hooks that are not yet invoked at startup. Opportunity, not a bug.
8. **Scaffold packages** (`event_bus/`, `rule_engine/`, `state_manager/`,
   `config_manager/`) are present but partially built; the live path uses
   `core.event_bus` / `core.config` directly. Treat scaffold dirs as
   experimental.
9. **`supervisor/` subpackage duplicate** — `core/supervisor.py` (active) vs.
   `core/supervisor/` (scaffold); do not confuse them.

---

## 9. Phase C Recommendations

Prioritized for a new developer picking up Nexus98 after Phase B. Ordered by
value-to-risk; all preserve the authority boundaries in §1.

### 9.1 First-run seeding (low risk, high polish)
Wire `core/boot.py:verify_environment()` / `core/autostart.py` into `main.py`
so a clean install writes empty-but-valid `workspace.json`, `reviews.json`,
`extensions.json` (plus continuity/plans). This flips the boot report to
`healthy=True` on first launch and removes the only "noise" in validation.
Pure additive; no authority change.

### 9.2 Autonomy observability depth (medium)
The Autonomy tab (`ui/views/autonomy_view.py`) already renders the Governor
`snapshot()`. Consider adding a timer-driven refresh (like the Dashboard) and a
live "last audit event" ticker, keeping it strictly read-only via
`autonomy_dashboard.snapshot()`.

### 9.3 Real task flow end-to-end (medium)
Today the advisory cycle runs on a synthetic "live cycle" task. Wire
`SupervisorHooks` (already built in `core/framework_hooks.py`) into the real
Supervisor lifecycle (`run_task`/`run_action_task`) so cognitive cycles attach
to actual user tasks. Hooks are non-blocking and re-raise on failure — safe.

### 9.4 Bridge/VSCode hardening (medium)
`api/vscode_bridge.py` + `bridge/` + `integrations/vscode_connector.py` form a
complete loop but are not exercised by `launch_ui()`. Add a smoke test that
submits a task via the bridge and asserts the Supervisor picks it up.

### 9.5 Scaffold packages decision (low/medium)
Decide the fate of `event_bus/`, `rule_engine/`, `state_manager/`,
`config_manager/` (and the `supervisor/` subpackage): either promote them to the
live path or mark them explicitly experimental/legacy to avoid confusion (debt
item #8/#9).

### 9.6 Cosmetic cleanups (low)
- Fix the `SyntaxWarning` in `core/supervisor/__init__.py`.
- Unify branding ("AI Model Hub Agent" → "Nexus98 Agent") in `core/identity.py`.
- Sync `config/system_context.json.current_phase` to the real phase.
- Make `main.py`'s crash-log path relative/configurable.

### 9.7 Validation gate before Phase 7/8/9 promotion
Keep `pytest` green (currently **284 passed**) and the `FrameworkValidator`
report truthful. Before any autonomy-level promotion, follow the existing
Phase 7 Level-2 checklists in `docs/`. The Governor remains the sole writer of
autonomy state — no Phase C work should bypass that.

---
*End of Phase B Completion Package. For deeper dives, consult the named docs in
`docs/` (architecture map, framework integration, cognitive architecture,
autonomy governor design, UI spec) and `docs/PROJECT_STATE.md` for live status.*


---

## 10. Phase C Milestone 1 (delivered 2026-07-18)

First useful Phase C milestone implemented and validated (306 tests green).

* **First-run init (obj 1):** already wired. `core/frameworks/seed.py` seeds
  the expected-empty stores and `core.boot.verify_environment()` is invoked
  from `ui.main_window.launch_ui()`. Boot validation now reports
  `healthy=True, failed=0` on a clean install (no behavior change).
* **Real task pipeline (obj 2):** new `core/workflow.py` (`TaskWorkflow`)
  advisory pipeline: goal intake + intent -> decompose (PlanningEngine) ->
  agent assignment (Router role -> registered agent) -> execution tracking
  (delegated to Supervisor) -> review cycle (ReviewSystem) -> memory/state
  update (CognitiveOrchestrator.learn_outcome + continuity). No autonomy
  writes; Governor untouched.
* **Autonomy visibility (obj 3):** new `ui/views/operations_view.py`
  "Operations" tab (read-only) surfaces current goal/phase, active tasks,
  agent state, cognitive cycle, decisions, blockers, and provider status.
  No duplicate dashboard; reuses existing views + a new notebook tab.
* **Provider boundary (obj 4):** new `core/providers.py` (`ProviderRegistry`,
  `ModelProvider`/`TaskProvider` interfaces, Ollama/OpenRouter/VS Code
  adapters). Vendor logic stays behind a clean interface; future providers
  register without core edits. Core execution/autonomy systems unchanged.

New tests: `tests/test_workflow_pipeline.py`, `tests/test_providers_boundary.py`,
`tests/test_operations_view.py`.
