# Nexus98 Configuration Authority Map

> Authoritative reference for every major configuration source in Nexus98.
> Supersedes any scattered config notes elsewhere. Verified against the live
> `config/` directory on 2026-07-17. Documentation only; no config was changed.

## 1. Configuration Sources (major)

| File | Authority scope | Status |
|------|----------------|--------|
| `config/system_config.json` | **Primary** runtime config: autonomy level, mode, safety gates, logging, project, version | Authoritative for runtime behavior |
| `config/system_context.json` | Project phase state, available agents, capabilities, milestones, development mode | Authoritative for project-state narrative |
| `config/vscode_workflow.json` | VS Code role/tunnel/workspace mapping | Authoritative for VS Code integration |
| `config/models.json` | Model catalog (`models` array) | Authoritative model list |
| `config/models.yaml` | Model definitions (YAML form) | Alternative model source; may overlap `models.json` |
| `config/providers.json` | External providers: `github`, `huggingface`, `ollama` | Authoritative provider config |
| `config/settings.json` | User prefs: `theme`, `auto_update` | Authoritative user settings |
| `config/mouse_agent.json` | Mouse-agent timing/safety/screenshot tuning | Authoritative for mouse agent |

## 2. Authoritative File / Location

- **Autonomy & safety (the gate):** `config/system_config.json`
  - `autonomy_level`: currently `"controlled"` (corresponds to supervisor
    `auto_execute = False`; action intents are held for approval).
  - `safety.require_approval_for_risky_actions`: `true`.
  - `safety.require_snapshots`: `true`, `safety.require_validation`: `true`.
  - `mode`: `"development"`.
- **Phase/milestone state:** `config/system_context.json` (`current_phase`,
  `next_phase`, `completed_milestones`, `development_mode`).
- **Model selection:** `config/models.json` is authoritative; `models.yaml`
  mirrors/extends it.
- **VS Code:** `config/vscode_workflow.json` only.

## 3. Generated / Derived Configurations

- `*.pre_nexus98_migration_backup`, `*.backup*`, `*_before_*.backup` files in
  `tools/`, `api/`, `scripts/` are **snapshots**, not live config. Ignore them.
- `config/*_before_*.json` / `*_before_*.yaml` (e.g. `system_context_before_autogen.json`,
  `models_before_small_test_models.yaml`) are **historical snapshots**, not live.
- `core/cache.py` / `data/cache/` may hold runtime-derived caches; safe to
  regenerate, not authoritative.
- `history/`, `checkpoints/`, `snapshots/`, `backups/` contain recovery artifacts,
  not configuration sources.

## 4. Override Precedence (most authoritative first)

1. **Runtime code constants** — `core/supervisor.py: auto_execute = False` is the
   hard safety floor and cannot be overridden by config alone. Config may request
   a level, but the supervisor gate stays `False` until explicitly enabled in code.
2. **`config/system_config.json`** — primary runtime authority (autonomy, safety).
3. **`config/system_context.json`** — project/phase state.
4. **Feature-specific config** — `models.json`/`models.yaml` (models),
   `providers.json` (providers), `vscode_workflow.json` (VS Code),
   `mouse_agent.json` (mouse agent), `settings.json` (user prefs).
5. **Environment variables / runtime flags** — e.g. `TMPDIR` for pytest temp;
   these affect execution environment, not stored config.
6. **Generated caches / snapshots** — lowest; always regenerable.

> Note: a config request to raise autonomy (e.g. `autonomy_level: "autonomous"`)
> does NOT by itself enable execution. `supervisor.auto_execute` must also be set
> to `True` via an explicit, checkpointed, human-approved action.

## 5. Files That Should NOT Be Manually Edited

- `core/supervisor.py` `auto_execute` constant — safety floor; change only via
  approved autonomy-promotion procedure.
- Any `*.backup*`, `*.pre_nexus98_migration_backup`, `*_before_*` snapshot.
- `history/`, `checkpoints/`, `snapshots/`, `backups/` contents (recovery data).
- `data/db/` and `data/system_state.json` (runtime state; regenerate if corrupt).
- Generated caches under `core/cache.py` / `data/cache/`.

## 6. Recovery When Configurations Disagree

1. **Identify the conflict** — compare the disagreeing values against the
   precedence list in Section 4. The higher-precedence source wins.
2. **Safety first** — if `system_config.json` safety flags disagree with runtime
   behavior, treat the stricter (safer) value as correct and restore
   `require_approval_for_risky_actions: true`, `require_snapshots: true`,
   `require_validation: true`.
3. **Restore from snapshot** — if a live config file is corrupted or wrong,
   recover from the most recent matching backup:
   - `backups/`, `snapshots/config_repair_baseline_*`, or
   - `checkpoints/HARD_BACKUP_BEFORE_HY3_INTEGRATION_20260716_052637`,
     `checkpoints/HARD_BACKUP_BEFORE_PATH_MIGRATION_20260716_061932`.
4. **Validate** — re-run `tests/test_import_smoke.py` and the full suite; confirm
   `supervisor.auto_execute` remains `False` and `autonomy_level` matches intent.
5. **Record** — log the disagreement and the chosen resolution in the relevant
   checkpoint/history entry.
6. **Stale phase state** — if `system_context.json.current_phase` disagrees with
   reality (e.g. still reads "AutoGen Multi-Agent Foundation" after Phase 5/6),
   update it to reflect the true current phase via a checkpointed edit. (See
   PROJECT_STATE.md for the canonical current phase.)

## 7. Known Inconsistencies (flagged, not yet resolved)

- `config/system_context.json.current_phase` = `"AutoGen Multi-Agent Foundation"`
  is **stale**; the project is actually at the Phase 6 documentation/audit stage.
  Resolution is tracked in PROJECT_STATE.md and should be corrected when config
  edits are permitted.
- Branding mismatch: `core/identity.py` still identifies as "AI Model Hub Agent"
  while Operating Rules use "Nexus98 Agent". Cosmetic; unify during a later
  branding pass (not a safety issue).
