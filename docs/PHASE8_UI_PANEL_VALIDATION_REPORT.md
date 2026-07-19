# Phase 8 — Request-Only Autonomy UI Panel: Validation Report

> **Validation report only.** Implemented `ui/autonomy_panel.py` (request-only)
> + `ui/__init__.py` package marker. No L3 enabled, no workflows expanded,
> no safety gates changed, Project Engine untouched, `auto_execute` scope
> unchanged. Governor remains the sole autonomy-state writer.

## Implemented Surfaces

- **Autonomy status display:** `render()` returns current level + name,
  `auto_execute` (read), config intent, allowed workflows, checkpoint
  status, and audit history — all via read-only accessors.
- **L0–L4 dial / request selector:** `submit_level_request(target_level,
  requested_workflows, approver, checkpoint_present)` — the ONLY
  mutation-capable call the UI exposes.
- **Pending request display:** `render()` includes a `pending_request`
  field (client-side until Governor approval).
- **Approval state display:** `submit_level_request` returns the Governor
  decision (`approved` + reason); the UI surfaces it, it does not self-grant.
- **Checkpoint readiness display:** `checkpoint_status()` reports pre-promotion
  checkpoint dirs present.
- **Audit history viewer:** `audit_history()` reads `history/autonomy/audit.log`.

## Validation Results — PASS

- **UI cannot mutate state directly:** source contains NO `auto_execute =`
  assignment and NO file-write (`def write_file` / `open(...,"w")`); the
  only mutation-capable call is `governor.request_level_change`.
- **Governor approval path works:** `submit_level_request(L2->L2,
  approved+checkpoint)` → `approved=True`; `auto_execute` unchanged
  (True -> True).
- **Rejected path safe:** `submit_level_request(L2->L3, no checkpoint)`
  → `approved=False`; `auto_execute` unchanged (no bypass).
- **Read-only render verified:** current_level=L1 (config intent `trusted`
  via approved L2 promotion), `auto_execute` read=True, checkpoints
  present, audit history populated.
- **Phase 7 regression green:** `integrations.vscode_connector
  .status()` returns a dict; safety gates intact (`require_approval`
  /`require_snapshots`/`require_validation` = true).

## Standing Boundaries (preserved)

- **Governor remains sole authority:** UI only *requests*; the Governor is
  the only writer of `supervisor.auto_execute` / `system_config` intent.
- **No L3 enabled:** `levels.allowed_workflows(3)` only inherits the L2
  set (`vscode_task_send`); no new workflow added.
- **No workflow expansion:** only `vscode_task_send` is trusted.
- **Safety gates unchanged:** all three remain `true`.
- **Project Engine untouched:** the UI / Governor do not reimplement file
  writes; Project Engine stays the file-mutation authority.
- **`auto_execute` scope unchanged:** still `True`, scoped to
  `vscode_task_send` (L2 promotion intact).

## Note on config intent
The Governor's approved L2 promotion legitimately set `autonomy_level =
"trusted"` in `system_config.json` (the intent string). This is expected
and consistent with the promoted state; all safety gates remain `true`.

## Verdict
**UI milestone validated.** The panel is request-only end to end: it reads
state, renders the dial/status/checkpoint/audit views, and submits a
gated request through the Governor. It cannot grant permissions, flip
`auto_execute`, or write `system_config` directly.
