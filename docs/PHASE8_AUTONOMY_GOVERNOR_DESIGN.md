# Phase 8 — Autonomy Governor / Control Plane (Design)

> **Design document only.** No implementation. No source, config, test, or
> autonomy changes. `supervisor.auto_execute` remains `False`. This design mirrors
> the existing bridge architecture (`integrations/vscode_connector.py` +
> `api/vscode_bridge.py` + `bridge/vscode_listener.py`/`worker.py`): a thin,
> request-only client in front of a server-side authority that performs the actual
> gated action. The Autonomy Governor reuses that same pattern for permission
> changes instead of file edits.

## 1. Autonomy Governor Concept

A central authority that *owns* the current autonomy level and is the only component
permitted to change it. Clients (UI, agent, scheduler) may only **request** a
level change; the Governor validates the request against policy + approval state and
either rejects or applies it through the existing `supervisor.auto_execute` +
`system_config.json` path.

### Autonomy levels

| Level | Name | Definition |
|-------|------|-------------|
| **Level 0** | Manual only | No autonomous action. Read-only queries only (`list_files`, `read_file`, `git_status`, status). No proposals executed. |
| **Level 1** | Assisted operation | Agent creates proposals + `checkpoints/` + `history/` request records; **human approves before execution**. No auto-write. |
| **Level 2** | Trusted workflows | A fixed, pre-approved set of trusted workflows (e.g. `vscode_task_send`) may run with `auto_execute = True`, scoped and monitored. Other actions stay Level 1. |
| **Level 3** | Expanded autonomous workflows | Broader, still checkpointed + validated workflow set (model/agent lifecycle, downloads on trusted workflows). Requires the Phase 7-style promotion per workflow. |
| **Level 4** | Experimental / restricted | Opt-in, time-boxed, heavily monitored sandbox for capability trials. Never the default; explicit on/off. |

### Permissions per level
- **L0:** read-only tools; zero mutations.
- **L1:** propose + checkpoint; writes require human approval (Project Engine
  `approve_request`).
- **L2:** trusted-workflow set auto-executes after checkpoint + validation;
  everything else stays L1.
- **L3:** expanded workflow set auto-executes; risky actions still gated by
  `require_approval_for_risky_actions`.
- **L4:** experimental set only, sandbox + full audit; auto-off on anomaly.

### Promotion requirements (L(n) -> L(n+1))
1. Human sign-off on the target workflow set and scope.
2. Pre-promotion `checkpoints/NEXUS98_BEFORE_PHASE*_*` snapshot + `MANIFEST.txt`.
3. Validation suite green (import smoke + relevant workflow tests, with the
   approved `TMPDIR` redirect).
4. Explicit, logged `governor.promote()` that flips `supervisor.auto_execute`
   (the hard floor) **only** for the approved workflow set.
5. Monitored first run; stop-and-report on any anomaly.

### Downgrade / emergency stop
- **Soft stop:** Governor rejects new autonomous actions; in-flight trusted
  workflows finish or are paused; system falls back to L1 (propose + human
  approve).
- **Hard stop (kill-switch):** any client (UI button, audit rule, supervisor
  anomaly) can call `governor.emergency_stop()` which forces `auto_execute =
  False` and reverts to L0/L1 immediately, then triggers rollback review.
- **Auto-downgrade:** if validation fails, an audit rule trips, or a checkpoint
  write fails, Governor auto-downgrades to L1 and opens a rollback record.

## 2. Architecture

Proposed package: `core/autonomy/` — mirrors the bridge split (client request
vs server authority).

- **`core/autonomy/governor.py`** — the authority. Holds the runtime level
  state, validates promotion/downgrade requests, applies level changes through
  the existing `supervisor.auto_execute` + `system_config.json` path, and emits
  audit events. Single writer of autonomy state.
- **`core/autonomy/levels.py`** — declarative definitions of L0–L4 (names,
  permission sets, allowed workflow lists, promotion/downgrade rules). Pure data +
  helpers; no I/O side effects.
- **`core/autonomy/policies.py`** — approval policy engine: who may request,
  what requires human sign-off, time-boxes, per-workflow allow/deny, and the
  mapping from a request to the concrete gated action.
- **`core/autonomy/audit.py`** — structured, append-only audit log of every
  request, decision, level transition, and checkpoint reference
  (`history/autonomy/` or `history/operations/`); supports the UI audit view.

### Responsibilities / interactions / data flow
- **Request flow:** UI/agent -> `governor.request_level_change(target, scope,
  justification)` -> `policies.py` checks approval + scope -> `levels.py` resolves
  allowed set -> `governor` applies via `supervisor`/`system_config` -> `audit`
  records it.
- **The Governor never grants by itself:** it only *applies* a change that
  `policies` has marked "approved" (human sign-off captured as an approval
  record). This parallels the bridge: the connector *requests*, the server *acts*.
- **Security boundaries:** `governor.py` is the sole mutator of `auto_execute`
  and the `autonomy_level` intent; `levels.py`/`policies.py` are read-only
  config consumers; `audit.py` is append-only. No UI path writes `auto_execute`
  directly — UI only submits requests.

## 3. UI Control Design

A Nexus98 control interface (intended to live inside `ui/main_window.py` as a new
panel; this is design only) that **requests**, never grants.

- **Autonomy level selector / dial:** shows L0–L4; selecting a higher level
  opens a *request*, not an immediate change.
- **Current state display:** live read of `governor` runtime level +
  `supervisor.auto_execute` + `autonomy_level` from `system_config.json`.
- **Requested promotion state:** pending request shown with target level, scope,
  justification, and required approver(s); disabled/locked until approved.
- **Approval workflow:** human approves/rejects in-UI; approval recorded by
  `policies` (and mirrored to `history/`). No button flips `auto_execute`.
- **Checkpoint status:** displays the latest `checkpoints/NEXUS98_BEFORE_PHASE*_*`
  and whether a pre-promotion snapshot exists for the pending request.
- **Rollback availability:** shows reachable rollback roots (Phase 7 inventory:
  stable baseline, pre-alignment, HARD_BACKUPs, snapshots, `history/`) and a
  one-click "initiate rollback" that calls the existing rollback path.
- **Audit history:** read-only feed from `core/autonomy/audit.py` (and
  `history/operations`).

> Invariant: the UI sends `governor.request_level_change(...)`; it has no code
> path that writes `auto_execute` or `system_config.json` directly.

## 4. Integration Points

Existing components the Governor must reuse (not replace):

- **`supervisor.auto_execute`** — the **hard safety floor**. The Governor is the
  *only* sanctioned writer; config alone cannot override it (per
  `docs/CONFIG_AUTHORITY.md` §4). Recommendation: Governor sits **between**
  `supervisor` and any requester, and all level transitions funnel through
  `governor.apply()` -> `supervisor`.
- **Project Engine approval flow** — `create_request` -> `approve_request` ->
  `execute_operation` remains the file-mutation authority. Governor governs the
  *autonomy level*; Project Engine governs the *file writes*. They compose: a
  trusted L2 workflow still routes every write through Project Engine.
- **Checkpoints** — Governor requires a `checkpoints/NEXUS98_BEFORE_PHASE*_*`
  snapshot + `MANIFEST.txt` before any promotion (reuse Phase 7 convention).
- **`history/operations`** — every Governor decision references/extends this
  audit trail.
- **Audit logging** — `core/autonomy/audit.py` appends; the existing
  `logs/supervisor.log` / `logs/vscode_bridge.log` pattern is the model.
- **`system_config.json`** — authoritative runtime config (autonomy_level, mode,
  safety gates). Governor reads gates and writes the *intent* level; the actual
  execution enablement still requires `auto_execute`.
- **`system_context.json`** — project/phase narrative; Governor may record the
  active autonomy posture but must not be the source of truth for the safety floor.

**Recommendation:** place the Autonomy Governor as a first-class authority layer
*adjacent to* `supervisor` (same process, owned by the supervisor wiring), with
the UI/agent as clients. It wraps `auto_execute` and `autonomy_level` so that no
other component can change them except via `governor`.

## 5. Safety Model

Preserved from the current design (Phase 5/6/7):

- **Human approval boundaries:** every L(n)->L(n+1) needs explicit human sign-off
  captured as an approval record; the Governor enforces this, it does not bypass
  it.
- **Checkpoint requirements:** `require_snapshots = true` stays; promotion is
  blocked without a fresh `checkpoints/` snapshot.
- **Rollback capability:** `ProjectEngine.restore_backup()` (auto on validate
  fail) + `checkpoints/` + `git checkout` remain the rollback path; the UI
  "rollback" button invokes this, nothing new required.
- **Validation requirements:** promotion requires the green test suite (with the
  approved `TMPDIR` redirect) and per-operation `validate_file`.
- **Audit logging:** every request/decision/transition is append-only in
  `core/autonomy/audit.py` + `history/`; non-repudiable.

## 6. Migration Plan (Phase 7 -> Governor)

1. **Freeze current state:** the Phase 7 `vscode_task_send` L2 promotion is the
   reference implementation — keep it running as the first *governed* workflow.
2. **Introduce `core/autonomy/`** (governor/levels/policies/audit) wrapping the
   existing `supervisor.auto_execute` + `system_config` writes.
3. **Encode L0–L4 + the `vscode_task_send` trusted set** into `levels.py`;
   port the Phase 7 promotion checklist into `policies.py` as the L1->L2 rule.
4. **Point the UI** at `governor.request_level_change(...)`; remove any direct
   config-write intent from the UI (request-only invariant).
5. **Re-route approvals:** the Phase 7 human sign-off becomes a `policies`
   approval record; the pre-promotion checkpoint becomes a Governor precondition.
6. **Backfill audit:** existing `history/operations` + `checkpoints/` become the
   Governor's audit/rollback backing with no data migration needed.
7. **Expand gradually:** add L3 workflows one at a time using the same governed
   promotion path; L4 only as an explicit experimental toggle.

## 7. Risks

- **Accidental privilege escalation:** a bug or rushed approval could promote to a
  higher level than intended. *Mitigation:* `policies` enforces scope + explicit
  approver; `levels.py` caps allowed sets; every transition is audited and
  reversible via rollback.
- **Config conflicts:** `system_config.json` `autonomy_level` vs Governor
  runtime state vs `supervisor.auto_execute` could diverge. *Mitigation:* Governor
  is the single writer; on read, treat the stricter/safer value as correct
  (consistent with `docs/CONFIG_AUTHORITY.md` §6).
- **UI bypass risks:** a future dev adds a direct `auto_execute = True` button.
  *Mitigation:* the request-only invariant + code review; `supervisor.auto_execute`
  stays the hard floor that config/UI cannot set except via `governor.apply()`.
- **Recovery scenarios:** a promotion goes wrong mid-run. *Mitigation:* existing
  rollback (auto-restore on validate fail + `checkpoints/` + `git`) plus the
  Governor `emergency_stop()` kill-switch forcing L0/L1.

---

### Recommended implementation order
1. `core/autonomy/levels.py` (declarative L0–L4 + trusted workflow sets).
2. `core/autonomy/audit.py` (append-only audit, reusing `history/`).
3. `core/autonomy/policies.py` (approval + scope engine; port Phase 7 rules).
4. `core/autonomy/governor.py` (wraps `supervisor.auto_execute` +
   `system_config`; the sole writer).
5. UI control panel (request-only) in `ui/main_window.py`.
6. Migrate the Phase 7 `vscode_task_send` promotion into the Governor; expand
   to L3 workflows one at a time; add L4 as explicit experimental toggle.

### Should Phase 8 begin after successful Phase 7 activation?
**Yes — conditionally.** Phase 8 design should start (design/planning can begin
now, documentation-only), but the **Autonomy Governor implementation should begin
only after the Phase 7 Level 2 promotion for `vscode_task_send` is successfully
activated, monitored, and validated** (Sections 3–5 of the activation checklist
complete). Phase 7 is the proven reference workflow the Governor will wrap; starting
implementation before that validation would put the safety layer on unproven ground.
This document changes no code, config, or autonomy state.
