# Nexus98 - UI Design Specification

Status: DESIGN SPECIFICATION (documentation only; no implementation)
Source of truth: docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md (v2)
Related: docs/PHASE9_GUI_BEHAVIOR_SPEC.md (frozen behavior contract),
docs/CURRENT_ARCHITECTURE_MAP.md, docs/FUTURE_ARCHITECTURE_GAP_ANALYSIS.md,
docs/EXTENSION_POINT_MAP.md.

This document defines the FUTURE Nexus98 UI architecture. It supersedes nothing
and changes no code. All state-changing behavior remains governed by the
Autonomy Governor; observability remains read-only. Every implementation step
must follow the handoff Development Rule:
checkpoint -> analyze -> document -> approve -> implement -> validate.

Framework constraint: continue on Tkinter/ttk (no new dependencies) unless a
future, separately approved decision changes the toolkit. Preserve the
launch_ui() entry contract.

---

## 1. UI Philosophy

### 1.1 Hybrid AI companion + command center
Nexus98's UI is a single window that behaves as two things at once:
- an AI companion (conversational, helpful, context-aware), and
- a command center (models, agents, tools, system, autonomy, recovery).
The companion is the front door; the command center is always one click away.

### 1.2 Chat-first default experience
- Default startup surface is a Chat workspace with a large central conversation
  area (input, output, execution results, summaries), per handoff #10.
- New/casual sessions never need to touch command-center complexity to be useful.

### 1.3 Expandable complexity (progressive disclosure)
- Simple by default; power on demand. Advanced panels (diagnostics, autonomy,
  tools, control panel) are collapsed/secondary until summoned.
- Complexity expands via the workspace model (Section 3) and toolbar (Section 2),
  never by cluttering the default chat view.
- Consistent visual identity: dark theme, ttk styling, text-first legibility,
  semantic status colors (OK green / warn amber / error-stop red).

---

## 2. Navigation

### 2.1 Top toolbar
A persistent top toolbar hosts six primary controls (grouping the handoff #12
requirements). Each is a labeled menu/selector with hover explanations
(handoff #13).

- Mode: selects the active experience/autonomy posture surface
  (e.g., Assistant / Coding / Research / Nexus Development). Mode influences the
  default workspace layout and strategy hints. Mode never bypasses the Governor.
- Project: selects/creates the active project; scopes conversations, documents,
  and code memory to that project (Section 4, 7).
- AI: opens the Smart AI dashboard (model/provider/strategy/agent selection with
  automatic selection + override) (Section 5).
- Workspace: switches/pins/collapses workspace layouts (Section 3).
- Tools: tool discovery, GitHub search, installed tools, custom tool generation
  (Section 6).
- System: system status, logs/diagnostics, Control Panel, Guardian client,
  session controls, settings (Sections 8-11).

### 2.2 Toolbar behavior
- Always visible, compact, labeled; icons optional and never the sole signal.
- Selecting a toolbar item opens a panel/overlay, not a full-page nav change,
  preserving the chat context underneath where sensible.
- Session controls (Save Session / Don't Forget) are reachable from System and
  optionally surfaced as quick actions (Section 9).

---

## 3. Workspace Model

### 3.1 Adaptive workspace
- The central region is an adaptive workspace whose layout adapts to the current
  Mode and Project. Chat is the anchor; supporting panels arrange around it.
- Switching Mode proposes a matching layout; the user's explicit pin/collapse
  choices always win and persist per Mode/Project.

### 3.2 Dynamic panels
- Panels are modular, dockable regions (conversation, results, diagnostics,
  autonomy read-only, documents, tools). Panels can be shown, hidden, pinned, or
  collapsed independently.
- Panels are data-driven views (reusing the existing ui/views builder pattern);
  each declares a refresh contract and degrades gracefully on backend failure.

### 3.3 Named workspaces
- Coding workspace: chat + code/results panel + code memory + tools; optimized
  for implementation and review. Integrates with VS Code bridge (Section 11).
- Research workspace: chat + documents + web/GitHub search results + notes;
  optimized for gathering and synthesis.
- Assistant workspace: chat-forward, minimal panels; the default companion
  experience with optional status strip.
- (Nexus Development / other Modes may define additional workspaces later.)

### 3.4 User-controlled pin/collapse behavior
- Every panel supports pin (keep visible), collapse (minimize to a header), and
  hide. Layout state is saved per workspace and restored on return.
- No panel auto-expands in a way that hides the conversation without user intent.
- Resizing: the conversation area is the primary expander; fixed-purpose controls
  keep their size.

---

## 4. Conversation Architecture

### 4.1 Separate conversations
- Multiple independent conversations exist concurrently (handoff #9), e.g.,
  Personal Assistant, Coding, Nexus Development, Research, Planning, Guardian,
  Custom. Each has its own history and settings (model/strategy defaults).

### 4.2 Shared memory / context
- Conversations can share APPROVED context only. Context sharing is explicit and
  user-controlled; nothing is shared silently.
- Shared context is sourced from the Memory Layer (Active/Knowledge/Code memory)
  and gated so a personal conversation does not leak into project work unless
  approved.

### 4.3 Project-linked conversations
- A conversation may be linked to a Project, inheriting that project's documents,
  code memory, and default strategy. Project switching updates linked context.

### 4.4 Personal standalone conversations
- Personal conversations are standalone by default (not project-linked) and do
  not auto-share context. They are the safe default for general assistant use.

### 4.5 Continuity
- Conversation state participates in the Session System (Section 9): Save Session
  and Don't Forget capture active conversation context for WWW restore.

---

## 5. AI Control Design

### 5.1 Smart AI dashboard
- A dedicated panel (opened from the AI toolbar item) shows the current effective
  selection: provider, model, strategy set, and active agents, plus why it was
  chosen (automatic) and controls to override.

### 5.2 Model selection
- Model dropdowns show model information, strengths, weaknesses, compatible
  agents, and recommended use cases (handoff #7), sourced from the model catalog
  + future Model Router metadata.

### 5.3 Provider selection
- Provider selector lists available providers (Ollama local, future cloud) with
  availability/health indicators. Local-first is the default.

### 5.4 Local / cloud switching
- A clear local/cloud switch, configuration-driven and opt-in for cloud. Cloud
  use is surfaced explicitly (cost/latency hints per strategy).

### 5.5 Agent selection
- Users can view and select agents/teams; the UI reflects agent status
  (from the agent registry) and compatibility with the chosen model.

### 5.6 Strategy combinations
- Multiple strategies may be active simultaneously (handoff #8): Fast, Accurate,
  Coding, Research, Creative, Safety First, Cost Efficient. The UI shows the
  active combination and its trade-offs.

### 5.7 Automatic selection with user override
- By default the Model Router auto-selects provider/model/local-cloud/strategy;
  the UI always exposes a visible, one-action override. Overrides persist per
  conversation/mode until changed.
- All selection is non-mutating to autonomy state; execution remains
  Governor-gated.

---

## 6. Tools System

### 6.1 Tool discovery
- A Tools panel lists discoverable tools with capability metadata (from a future
  tools registry). Discovery is read-only; enabling a tool for an agent is an
  explicit, governed action.

### 6.2 GitHub search
- Search GitHub for tools/repositories (Nexus98 may search, download, inspect
  per handoff #5). Results show repo metadata and a safe inspect action.
- Nexus98 does NOT perform Git ownership operations (commit/push/history) - those
  belong to Guardian (Section 8).

### 6.3 Installed tools
- View installed/available tools, their status, and which agents/workspaces use
  them. Provide enable/disable behind clear labels and, where risky, confirmation.

### 6.4 Custom tool generation
- Generate custom tools via the governed action path (proposals -> Project Engine
  backup/write/validate). Tool generation is Medium/High risk: requires approval,
  checkpointing, and Governor authorization; never bypasses Project Engine.

---

## 7. Documents System

### 7.1 Project documents
- Per-project documents view (architecture, decisions, changelog, notes) scoped
  to the active Project and linkable to conversations.

### 7.2 Global Nexus knowledge library
- A global library aggregating Nexus-wide documentation (handoff #18):
  architecture, roadmap, decisions, changelog, Guardian docs, memory docs, tool
  library. Read-first; edits (if any) go through the governed write path.

### 7.3 Interactive roadmap
- An interactive roadmap view (milestones, status, origin tracking) rendered from
  the roadmap/handoff documents; navigable and filterable, read-only by default.

### 7.4 Generated documentation
- Surface auto-generated documentation (e.g., architecture inventories, handoffs)
  produced by the documentation pipeline; clearly marked as generated with source
  provenance. Generation is a governed action.

---

## 8. Guardian Integration

### 8.1 Guardian remains a separate project
- Per handoff #4-5, Guardian is NOT merged into Nexus98. The UI treats Guardian
  as an external service reached through controlled interfaces (External Guardian
  model preferred initially).

### 8.2 Nexus98 Guardian client interface
- A read-first Guardian client panel/button (toolbar System + Control Panel)
  communicates with Guardian via a defined client interface. No Guardian internals
  are embedded in Nexus98.

### 8.3 Status access
- Display Guardian health/status (reachable, last check, health summary) as
  read-only indicators. Unreachable Guardian degrades gracefully (offline state),
  never blocks the UI.

### 8.4 Recovery requests
- The UI may REQUEST recovery actions (e.g., restore a recovery point) from
  Guardian through the client, with explicit confirmation. Guardian owns and
  executes recovery; Nexus98 only requests.

### 8.5 No Git ownership inside Nexus98
- The UI exposes NO Git commit/push/history/rollback controls. GitHub search and
  repo inspection (Section 6) are the only repository-facing actions. Git
  ownership stays with Guardian.

---

## 9. Session System

### 9.1 Save Session
- Explicit "Save Session" persists the current workspace layout, active
  conversation(s), Mode/Project, and AI selection so the session can be resumed.

### 9.2 Don't Forget
- A manual emergency context save (handoff #15) that creates: a recovery point
  (requested via Guardian where applicable), a memory update, and a WWW summary.
- Reachable as a prominent quick action; confirms what was captured.

### 9.3 WWW startup summary
- On startup after a proper shutdown or a Don't Forget event, show a
  "Where Were We" summary (handoff #14): current task, recent decisions, system
  status, unfinished work, and user intent - to restore context before the user
  resumes. Dismissible; read-only.

---

## 10. Control Panel

A consolidated Control Panel (opened from System) presents labeled controls with
hover explanations, avoiding clutter (handoff #13). Toggles reflect real backend
state and confirm risky changes.

- AI toggle: enable/disable AI execution surface (reflects, and requests through,
  the governed path; never writes autonomy state directly).
- Bridge toggle: enable/disable the VS Code bridge (reuses existing bridge status
  + safe-fallback behavior).
- Mouse tool toggle: start/stop the desktop mouse agent with status.
- Memory controls: view memory status; request maintenance is delegated to
  Guardian (cleanup/compression/dedup are Guardian-owned).
- Recovery controls: request recovery points / restore via the Guardian client
  (with confirmation); Nexus98 does not own recovery execution.
- Guardian: Guardian status indicator + open Guardian client panel.
- Status indicators: autonomy level, bridge online/enabled, agent status,
  Guardian status, emergency-stop state - text + semantic color; emergency-stop
  engaged is unmistakable (red + explicit label).

Autonomy invariant: the Control Panel observes via
ui.autonomy_dashboard.snapshot() and requests changes only through the Governor.
No control writes supervisor.auto_execute or config directly.

---

## 11. Future Expansion

Highest-privilege capabilities are deferred and, where applicable, sit in the
handoff High Risk tier (Guardian-protected).

### 11.1 Voice integration
- Optional STT/TTS as an input/output modality routed like text to the supervisor.
  Local-first preferred; opt-in; surfaced as a toolbar/control-panel control. No
  dependency additions without approval.

### 11.2 Internal shell
- An in-app shell for running commands (handoff #11). HIGH risk: approval-gated,
  checkpointed, Governor-authorized, and audited. Implemented last.

### 11.3 VS Code integration
- Deeper in-app VS Code functionality building on the existing bridge/connector/
  extension and the vscode_task_send governed workflow. New actions become new
  governed workflows, not new permissions; preserve L2 vscode_task_send.

### 11.4 Self-modification capability
- Nexus98 editing its own code (handoff #11) via the governed action path
  (Project Engine proposals -> backup/write/validate) under Governor authorization
  and, for High Risk changes, Guardian protection. The riskiest capability;
  implemented only after foundations, memory, Guardian client, and the UI shell
  are approved and validated.

---

## Cross-Cutting UI Invariants (must hold in all future UI work)
- Governor is the sole authority/writer of autonomy state; the UI requests, it
  never writes autonomy state directly.
- All passive autonomy displays use ui.autonomy_dashboard.snapshot() only; no
  Governor imports in observability views.
- Guardian stays separate; Nexus98 is a client. No Git ownership in Nexus98.
- Configuration-driven and path-abstracted (avoid hardcoded paths) as the UI
  grows; preserve launch_ui() and existing view-builder patterns.
- No new autonomy levels, no workflow expansion, and no new permissions are
  introduced by the UI.
- Every implementation step: checkpoint -> analyze -> document -> approve ->
  implement -> validate.
