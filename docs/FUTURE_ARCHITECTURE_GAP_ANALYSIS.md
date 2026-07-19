# Nexus98 - Future Architecture Gap Analysis

Status: READ-ONLY ANALYSIS (no code changes)
Compared against: docs/NEXUS98_MASTER_ARCHITECTURE_HANDOFF.md (v2) and
docs/Nexus98_Vision_Architecture.md.

This compares the current implementation (see docs/CURRENT_ARCHITECTURE_MAP.md)
to the design handoff and identifies what exists, what is missing, required
future modules, migration risks, and a recommended order.

---

## 1. Existing Pieces Already Implemented

| Handoff element | Status | Evidence |
|-----------------|--------|----------|
| Execution Layer (tasks/tools/coding) | Implemented | supervisor.py + project_engine.py (Phase 5) |
| Governor (autonomy levels/permissions/safety) | Implemented | core/autonomy/* (Phase 8) |
| Autonomy dashboard (read-only) | Implemented | ui/autonomy_dashboard.py + views |
| UI refactor foundation / view separation | Implemented | ui/main_window.py shell + ui/views/* (Phase 9 Step 1-2) |
| Local model runtime (Ollama) | Implemented | agent_factory, ollama.py, vscode_bridge |
| Agent selection (basic) | Partial | router.py (keyword rules), orchestrator, agent_factory |
| Model catalog + recommender | Implemented | catalog.py, discovery.py, recommender.py, db.py |
| Memory (DB-backed) | Implemented (foundation) | memory_service.py (SQLite) + migration |
| VS Code integration | Implemented | api/bridge, bridge/, connector, extension.js |
| Control-panel primitives (AI/Bridge/Mouse toggles, agent status) | Partial | bridge toggle + agents view; mouse_agent; no unified panel |
| Test stabilization | Implemented | 96 tests passing |
| Checkpoint/recovery surfaces | Implemented (file-based) | checkpoints/, history/, backups/, snapshots/ |

---

## 2. Missing Systems (in handoff, not yet built)

- Model Router (handoff #7): automatic provider/model/local-cloud/strategy
  selection with user override and rich dropdown metadata. Only keyword routing
  + a helper (tools/model_router.py) exist; no unified router abstraction.
- Local/Cloud switching: no cloud provider layer; system is local-only today.
- Strategy System (#8): Fast/Accurate/Coding/Research/etc. simultaneous
  strategies - not present.
- Conversation System (#9): separate, context-sharing conversations - not
  present (supervisor is task-oriented, not conversation-oriented).
- Chat-first UI (#10): default startup is the Dashboard/Command Center, not a
  large central chat interface. No conversation area.
- Toolbar (#12): mode/dashboard/Guardian/model/provider/strategy selectors,
  documents/memory/settings/session controls - not present.
- Unified Control Panel (#13): consolidated toggles + Guardian/recovery/memory
  controls with hover explanations - only partial (bridge tab).
- WWW "Where Were We" (#14) + Don't Forget (#15): context restore + manual
  emergency context save - not present.
- Code Memory (#17): module/function/class/dependency understanding with
  hashes/summaries - not present (memory_service is generic records).
- Documents section (#18): architecture/roadmap/decisions/changelog browser -
  docs exist on disk but no in-app Documents view.
- Guardian communication layer (#4-5): external Guardian connectors, Git
  ownership boundary, recovery/health interfaces - not present.
- Internal development surface (#11): self-edit, internal shell, in-app VS Code
  functionality - not present.
- Tool discovery / custom tool generation: tool registry doc exists; dynamic
  discovery + generation not implemented.
- Provider metadata for dropdowns (strengths/weaknesses/compatible agents) -
  not modeled.

---

## 3. Required Future Modules (proposed placement)

- `core/model_router/` - provider+model+strategy selection, override API,
  metadata catalog (feeds UI dropdowns).
- `core/providers/` - provider adapters (ollama, cloud_*) behind one interface;
  enables local/cloud switching.
- `core/strategy/` - strategy definitions + selection (compose with router).
- `core/conversations/` - conversation store + context-sharing policy.
- `core/code_memory/` - AST/hash-based code understanding index (built on
  memory_service or a sibling DB).
- `core/guardian/` (client only) - controlled interface to the external
  Guardian project (health/recovery/git/memory-maintenance requests).
- `core/context/` - WWW + Don't Forget (recovery point + memory update + summary).
- `core/tools_registry/` + `core/tool_gen/` - tool discovery + custom tool
  generation (governed).
- UI: `ui/views/chat_view.py`, `ui/views/documents_view.py`,
  `ui/toolbar.py`, `ui/control_panel.py` (consolidated).
- Fill existing scaffolds: `core/event_bus/`, `core/rule_engine/`,
  `core/state_manager/`, `core/config_manager/`, `core/supervisor/` (currently
  empty packages reserved for these roles).

---

## 4. Migration Risks

- AI_Model_Hub -> Nexus98 naming: handoff forbids blind replacement. Window
  title and some strings still say "AI Model Hub" in legacy files; intentional,
  verified migration only.
- Hardcoded absolute paths (D:\Nexus98, D:\AI\Nexus98_Bridge) pervade core/ -
  any relocation, Docker, or multi-node plan (handoff future) breaks without a
  path/config abstraction first. High risk for portability goals.
- Duplicate/legacy modules (supervisor_STATUS_BEFORE.py,
  supervisor_before_final_autogen_fix.py, api/*.backup.py,
  ui/main_window_BEFORE_STATUS.py) risk accidental import/edit of the wrong file.
- Governor authority must be preserved: any new control surfaces (toolbar,
  control panel, chat actions) must route through the Governor; risk of adding a
  mutation path that bypasses it.
- Chat-first UI pivot is a large UX change from the current tabbed Command
  Center; risk of regressing the validated read-only autonomy behavior.
- Memory clutter: 54 checkpoint dirs + snapshots/backups conflict with handoff
  #16 ("avoid thousands of checkpoint files; use databases/indexes").
- Guardian boundary: Git ownership belongs to Guardian; adding Git actions in
  Nexus98 would violate the handoff separation.
- Multiple server entry points (api_server.py, server.py, vscode_bridge.py,
  bridge/*) risk port/role confusion during consolidation.

---

## 5. Recommended Implementation Order

Follow the handoff Development Rule for every step:
checkpoint -> analyze -> document -> approve -> implement -> validate.

1. Foundation hardening (enables everything else, low UX risk):
   - Path/config abstraction (remove hardcoded D:\ paths behind config_manager).
   - Retire/relocate duplicate legacy modules (with checkpoints).
   - Consolidate server/entry roles and document ports.
2. Model Router + Providers (handoff #7): unified selection + local/cloud seam,
   with metadata to drive future dropdowns. User override first-class.
3. Strategy System (#8) composed with the router.
4. Memory maturation (#16-17): code_memory index + checkpoint/DB consolidation;
   align with MEMORY_ARCHITECTURE_DESIGN.md.
5. Guardian communication layer (#4-5): external client only; no merge, no Git
   ownership transfer.
6. Context continuity: WWW + Don't Forget (#14-15) on top of memory + Guardian.
7. UI evolution (#9-13): conversation system + chat-first shell, toolbar, and
   consolidated control panel - only after the design spec
   (docs/PHASE9_GUI_BEHAVIOR_SPEC.md) is finalized and approved.
8. Internal development surface (#11) and tool discovery/generation - last, as
   the highest-risk, highest-privilege capabilities (High Risk tier).

Sequencing rationale: infrastructure (paths/router/memory) unblocks the UI and
Guardian work; the chat-first UI pivot and self-editing capabilities are
deferred until foundations and the frozen GUI spec are approved.
