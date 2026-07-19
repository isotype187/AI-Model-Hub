# Phase 7.5 — Autonomy Control Interface (Design)

> **Design document only.** No implementation. No source, config, test, or autonomy
> changes. `supervisor.auto_execute` remains `False`. This document designs the
> user-facing **Autonomy Control Interface** — the UI half of the Phase 8
> Autonomy Governor (`docs/PHASE8_AUTONOMY_GOVERNOR_DESIGN.md`). It mirrors the
> existing bridge pattern: the UI is a **client that requests**; the Governor
> (backend authority) **acts**. The UI never grants permissions directly.

## 1. Nexus98 Autonomy Dial Concept

A single, always-visible control that reflects and requests the autonomy level.

- **Dial positions:** L0 (Manual) — L1 (Assisted) — L2 (Trusted workflows) —
  L3 (Expanded autonomous) — L4 (Experimental/restricted).
- **Two states per position:** *current* (what is live, read from the Governor)
  and *requested* (what the user has queued, not yet approved).
- **Invariant:** turning the dial only creates a `governor.request_level_change(...)`
  call. It never writes `auto_execute` or `system_config.json`. The dial is a
  request surface, not an authority.
- **Visual cue:** the current level is shown solid; a pending request is shown
  as an outlined/"pending" marker until approval resolves.

## 2. Level 0–4 Display

- **L0 Manual only:** read-only; dial disabled from requesting above L0 unless an
  explicit promote flow is opened.
- **L1 Assisted:** propose + checkpoint; human approves before execution.
- **L2 Trusted workflows:** the pre-approved workflow set (e.g.
  `vscode_task_send`) may auto-execute, scoped + monitored.
- **L3 Expanded autonomous workflows:** broader, still checkpointed/validated set.
- **L4 Experimental / restricted:** opt-in, time-boxed, sandbox + full audit.
- The display reads level definitions from `core/autonomy/levels.py` (declarative),
  so labels/permissions stay in one source of truth and the UI cannot invent levels.

## 3. Promotion Request Flow

1. User selects a target level on the dial (or clicks "Promote").
2. UI collects **scope** (which workflow set) + **justification** text.
3. UI calls `governor.request_level_change(target, scope, justification)`.
4. Governor validates via `policies.py` (who may request, what needs sign-off,
   per-workflow allow/deny) and returns a **request id** + pending state.
5. UI shows "Requested: L<n> (pending approval)" and locks further changes
   until the request resolves.
6. On approval, Governor applies the change (through `supervisor.auto_execute` +
   `system_config.json` intent) and the dial's *current* marker moves; the
   *requested* marker clears.

## 4. Approval Workflow

- **Human approver:** the request surfaces an in-UI approval card (approve /
  reject) bound to a recorded approver identity + timestamp.
- **Approval record:** persisted by `core/autonomy/audit.py` (and mirrored to
  `history/`), satisfying the human-approval boundary from the safety model.
- **No self-approval for risky promotion:** L(n)→L(n+1) above L1 requires an
  explicit human sign-off; the UI cannot mark its own request approved.
- **Rejection:** clears the pending *requested* marker; current level unchanged.

## 5. Checkpoint Verification

- Before any promotion request can be submitted, the UI queries the Governor for
  checkpoint status.
- The Governor requires a fresh `checkpoints/NEXUS98_BEFORE_PHASE*_*` snapshot +
  `MANIFEST.txt` (reusing the Phase 7 convention) as a promotion precondition.
- The UI displays: *"Pre-promotion checkpoint: present / missing"* and blocks
  submit when missing, with a "Create checkpoint" action that asks the Governor
  (it performs the snapshot, not the UI).
- This preserves `require_snapshots = true` and the Phase 7 checkpoint contract.

## 6. Rollback Integration

- The interface exposes a **Rollback** control that is request-only: it calls
  `governor.initiate_rollback()` (or `emergency_stop()` for the kill-switch).
- Governor performs the actual restore via the existing path:
  `ProjectEngine.restore_backup()` (auto on validate fail), restore the matching
  `checkpoints/` tree, or `git checkout` affected files.
- UI shows **rollback availability** (reachable roots: Phase 5 stable baseline,
  pre-alignment, HARD_BACKUPs, config-repair snapshots, `history/`) and the last
  successful checkpoint reference.
- The primary "Emergency Stop" button maps to `governor.emergency_stop()`,
  forcing `auto_execute = False` and downgrade to L0/L1 immediately.

## 7. Audit History Display

- Read-only feed from `core/autonomy/audit.py` (and `history/operations`):
  every request, decision, level transition, checkpoint reference, and approver.
- Columns: timestamp, request id, from→to level, scope, approver, outcome.
- No write actions from this view; it is the transparency surface that makes the
  human-approval boundary auditable after the fact.

## 8. UI / Backend Separation

- **UI (client):** renders state, collects requests, displays approval/checkpoint/
  rollback/audit. **Has no code path that writes `auto_execute`,
  `autonomy_level`, or `system_config.json` directly.**
- **Backend (Governor authority):** the **sole** writer of autonomy state; applies
  changes only after `policies` marks a request approved. This is the same
  client-request / server-authority split as `integrations/vscode_connector.py`
  (request) vs `api/vscode_bridge.py` + `bridge/vscode_listener.py` (act).
- **Transport:** the UI talks to the Governor through a defined request API
  (e.g. a local bridge/endpoint or in-process call), never touching `supervisor`
  internals except via the Governor.
- **Security boundary:** if the UI is compromised, the worst it can do is *request*;
  the Governor's `policies` + human approval still gate any actual change.

## 9. Migration from Manual `supervisor.auto_execute` Control

- **Today:** `auto_execute` is a code constant flipped by a human through the
  approved, checkpointed Phase 7 procedure. No UI touches it.
- **Phase 7.5 → 8:** the Autonomy Control Interface becomes the **only**
  supported way to *request* a level change; the Governor wraps the same
  `auto_execute` + `system_config` writes so the hard floor is preserved.
- **No behavior regression:** the Phase 7 `vscode_task_send` L2 promotion is
  migrated in as the Governor's first governed workflow; the manual procedure
  remains valid as the fallback path.
- **Cutover:** keep the manual procedure documented alongside the UI until the
  Governor + interface are validated; then the UI is the primary surface and the
  manual path is the recovery fallback. The UI does not remove or bypass the
  human-approval gate — it surfaces it.

> This design changes no autonomy state. `supervisor.auto_execute` stays `False`
> until a human-signed activation occurs through the Governor/approval flow.
