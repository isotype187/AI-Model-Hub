# Guardian Architecture Audit

> Read-only audit of the separate Guardian project.
> No Guardian or Nexus98 production files were modified.
> Guardian location inspected: `D:\Nexus98_Guardian`
> Related D:\ folders inspected: `Nexus98_Recovery_System`, `Nexus98_Recovery_Tools_PRO`, `Nexus98_Scan_Reports`, `Nexus98_Toolkit`, plus legacy `Nexus98_*_Checkpoint_*` dirs.

---

## 1. Guardian Project Overview

### Purpose
The Nexus98 Guardian is intended to be a separate backup, checkpoint, verification, and recovery
authority for the Nexus98 ecosystem. It is explicitly separated from Nexus98 itself (per the master
handoff): Nexus98 may request recovery/checkpoint/session/health actions, but Guardian owns Git,
recovery, and backup authority.

### Current Role
Today the Guardian is a **PowerShell-based toolkit/recovery scaffold**. It is not a running service.
The main launcher performs a one-shot verification + snapshot + recovery-point-record and exits.
Most "engine" modules are stubs or thin wrappers; the only substantive, working logic is the
snapshot/inventory engine.

### Folder Structure (D:\Nexus98_Guardian)
- `core/`           — engine scripts: `snapshot_engine.ps1`, `verification_engine.ps1`, `recovery_engine.ps1`
- `scripts/`        — many `Nexus98_*_Manager.ps1` / `*_Upgrade.ps1` modules (mostly stubs/scaffolding)
- `config/`         — `assets.json` + ~30 declarative `nexus98_*_state.json` files
- `data/`           — `latest_recovery.json` (single pointer file)
- `snapshots/`      — `Emergency_Test_*`, `Guardian_Test_*`, `permanent`, `recovery`, `temp`, and one dated full copy
- `logs/`           — many small stub logs; `execution_history.log` is the most substantive
- `reports/`        — generated `.txt` reports
- `plugins/`        — plugin placeholders
- `tests/`          — **empty**
- `.venv/`          — Python virtualenv (present but launcher is PowerShell-only)

### Entry Points
- `Nexus98.ps1` — top-level launcher (v3.0.0). Dot-sources the three `core/*_engine.ps1` files,
  runs `Test-Nexus98System`, prints registered assets, calls `New-Nexus98RecoveryPoint`, prints "Guardian Ready", exits.

### Runtime Processes
- None persistent. Runs as a foreground PowerShell script and terminates.
- No scheduler, no daemon, no long-running monitor.

### Required Services
- PowerShell 5.1+ (Windows).
- Optional external tools used opportunistically: `ollama`, `python`/`pip`, `git` (all wrapped in try/catch).
- No internal database or server.

---

## 2. Guardian Capabilities

| Capability            | Status            | Evidence |
|-----------------------|-------------------|----------|
| Git management (commit/push) | Not implemented | No Git write commands anywhere; `git status` is read-only capture only |
| Commits / pushes      | Not implemented   | None found |
| Backups               | Partial           | `New-Nexus98Snapshot` inventories file hashes (read-only capture), not full backups |
| Checkpoints           | Partial           | Snapshot dirs created; no semantic checkpoint rotation |
| Recovery points       | Partial (metadata only) | `New-Nexus98RecoveryPoint` writes `latest_recovery.json` (reason/time) |
| Rolling known-good states | Not implemented | No known-good tracking or rotation |
| Health checks         | Minimal           | `Test-Nexus98System` checks 3 Guardian files exist |
| Monitoring            | Not implemented   | No loop, no watcher |
| Alerts                | Not implemented   | No notification path |
| Automatic fixes       | Not implemented   | No remediation logic |
| Logging               | Partial           | `Safety_*.log`, `execution_history.log`, many stub logs |

### Working pieces
- **snapshot_engine.ps1 → `New-Nexus98Snapshot`**: captures system inventory (CIM), a SHA256 file-hash
  inventory of a hard-coded `$Targets` list (`D:\Nexus98_Toolkit`, `D:\AI_Model_Hub\config|core|scripts`,
  `%USERPROFILE%\.continue`, `%USERPROFILE%\.vscode`), `ollama list`, `python --version`/`pip list`,
  `git status`, then writes `system.json`, `inventory.txt`, `manifest.json`, `ollama.txt`,
  `python.txt`, `git.txt`, and a self-verification `verification.json`. This is the strongest real component.

### Stub / declarative pieces
- **recovery_engine.ps1 → `New-Nexus98RecoveryPoint`**: writes only `data/latest_recovery.json`.
  **No file-restore logic.**
- **verification_engine.ps1 → `Test-Nexus98System`**: existence checks of 3 Guardian files only.
- **scripts/Nexus98_Recovery_Manager.ps1 → `Invoke-Nexus98Recovery`**: returns a stub hashtable;
  `Get-Nexus98RecoveryStatus` reads a `D:\Nexus98_Toolkit\logs\...` path (Toolkit, not Guardian).
- **scripts/Nexus98_Safety_Module.ps1**: provides `Invoke-SafeCommand` (job runner with timeout) and
  `Test-NexusPath`; this is a generic safe-runner, not an approval authority.
- **config/*.json state files**: ~30 `nexus98_*_state.json` files declare states such as
  recovery_state "active/rollback enabled", safety_state "installed/enabled", automation_state
  "queue ready" — these are **declarative state descriptors, not executing logic**.

---

## 3. Storage and Data Layout

| Location | Contents |
|----------|----------|
| `D:\Nexus98_Guardian\config\` | `assets.json` + ~30 `nexus98_*_state.json` + `python_config.json` |
| `D:\Nexus98_Guardian\data\` | `latest_recovery.json` (single pointer) |
| `D:\Nexus98_Guardian\snapshots\` | `Emergency_Test_*`, `Guardian_Test_*`, `permanent`, `recovery`, `temp`, and one dated full copy `Nexus98_20260714_065227` (scripts only) |
| `D:\Nexus98_Guardian\logs\` | many small stub logs + `execution_history.log` |
| `D:\Nexus98_Guardian\reports\` | generated `.txt` reports |
| `D:\Nexus98_Toolkit\logs\` | `Safety_*.log` (written by Safety Module; Toolkit, not Guardian-owned) |
| Related D:\ dirs | `Nexus98_Recovery_System`, `Nexus98_Recovery_Tools_PRO`, `Nexus98_Scan_Reports`, `Nexus98_Toolkit`, legacy `Nexus98_*_Checkpoint_*` |

### Centralized vs Fragmented
**Fragmented.** Guardian state is spread across:
- per-asset JSON state files in `config/`,
- a single pointer file in `data/`,
- ad-hoc snapshot directories,
- logs split between Guardian and the separate `Nexus98_Toolkit`,
- and recovery/scan artifacts living in entirely separate D:\ projects.

There is no unified database or single source of truth for Guardian state.

---

## 4. Recovery Capability Assessment

- **Can Guardian create recovery points?** Yes (partial). It records metadata (`latest_recovery.json`)
  and creates snapshot directories via `New-Nexus98Snapshot`.
- **Can Guardian restore from them?** **No.** `New-Nexus98RecoveryPoint` performs no restore;
  `Invoke-Nexus98Recovery` is a stub returning a placeholder hashtable.
- **Are restores validated?** No — there is no restore path to validate.
- **Does Guardian know when a checkpoint is healthy?** Only self-existence checks of Guardian files
  (`Test-Nexus98System`). It does **not** validate the health of the Nexus98 application or its data.
- **Can it maintain a rolling "last known good" state?** No. Only a single `latest_recovery.json`
  pointer exists; there is no known-good rotation, scoring, or promotion logic.

**Conclusion:** Guardian currently has inventory/checkpoint *capture* capability but **no real recovery
or known-good-state management**.

---

## 5. Automation Safety Assessment

- **Current autonomous actions:** None execute autonomously. The launcher is manual/one-shot and exits.
  The safety module is a generic command runner, and the "safety_state" is declaratively "enabled" but
  there is no enforcing approval engine (no function returns anything but a pass-through; the audit found
  no `approved=False` path).
- **Approval requirements:** Not enforced. The only "safety" artifact is `Invoke-SafeCommand` (timeout job
  runner), not an authorization gate.
- **Failure handling:** `try/catch` around optional external tools (ollama/python/git) only. No rollback
  on Guardian-internal failure.
- **Rollback mechanisms:** None implemented.
- **Logging:** Present (Safety logs, execution history) but not correlated to approvals or outcomes.
- **User notification:** None (no alerts, no UI).

### Is Guardian currently safe to run unattended?
**No.** It is not currently autonomous (it exits after one run), but *if* automation were enabled, the
safety layer is a stub (no real approval gates, no rollback, no restore validation). There is no
authorization boundary, no known-good tracking, and no failure containment. Guardian is therefore **not
safe to run unattended** in its current state.

---

## 6. Nexus98 Integration Readiness

The intended design is **request/response**: Nexus98 asks; Guardian acts (and only on Git/recovery/backup).

### Future Nexus98 → Guardian request examples
- `create checkpoint`
- `save session`
- `create Don't Forget point`
- `report health`
- `request recovery`

### Responsibility boundary (per master handoff)
Guardian remains the sole authority for:
- **Git** (commits, pushes, branch management)
- **Recovery** (restore, rollback)
- **Backup authority** (snapshots, checkpoints)

Nexus98 must **never** own Git or perform recovery writes itself. Nexus98's role is limited to
observability and *requesting* Guardian actions.

### Readiness verdict
The communication contract is **not yet implemented** on either side. Nexus98 has no Guardian client
interface, and Guardian exposes no stable API — only file artifacts and a manual launcher. Integration
requires a defined request/response interface before any Nexus98 code can safely depend on it.

---

## 7. Security and Authority Boundaries

### What Guardian can modify
- Its own folders (`config/`, `data/`, `snapshots/`, `logs/`, `reports/` under `D:\Nexus98_Guardian`).
- Via `New-Nexus98Snapshot`, it **reads** (hashes/inventory) targets in `D:\Nexus98_Toolkit`,
  `D:\AI_Model_Hub\*`, `%USERPROFILE%\.continue`, `%USERPROFILE%\.vscode`.

### What Guardian cannot modify
- No write access to Nexus98 application code or state is implemented.
- It does **not** modify Nexus98 Git history, autonomy state, or config.

### Permissions required
- Filesystem read/write within its own tree and the read targets listed above.
- Invocation of `git`/`ollama`/`python` (read-only uses today).

### Risks from expanded privileges
- If granted autonomous Git push or file-restore authority without an approval gate, a stub safety
  engine (`approved=True` always) would let unintended changes propagate. This is the primary risk to
  contain before any unattended operation.

---

## 8. Recommendations

### Required improvements before autonomous operation
1. **Real restore logic** — implement `Invoke-Nexus98Recovery` to actually restore from a validated snapshot.
2. **Restore validation** — verify post-restore integrity (hash compare against `inventory.txt`).
3. **Known-good tracking** — maintain a rolling "last known good" pointer with health scoring.
4. **Enforcing safety/approval engine** — replace the stub pass-through with a real authorization gate
   that can return `denied`, with logged rationale.
5. **Health validation of Nexus98** — `Test-Nexus98System` must validate the *application* (not just
   Guardian file existence).
6. **Centralized state store** — consolidate the fragmented per-asset JSON into a single source of truth.

### Required API / interface
- A stable **request/response Guardian client** (e.g. a small Python client in Nexus98 that calls a
  Guardian service or script and parses a defined JSON result), supporting at minimum:
  `create_checkpoint`, `save_session`, `create_dont_forget`, `report_health`, `request_recovery`.
- Guardian should expose a versioned CLI/JSON contract, not ad-hoc files.

### Required GUI elements (in Nexus98)
- Guardian **status** panel (read-only: last checkpoint, last recovery, health).
- **Recovery-request** panel (user-initiated requests only; no autonomous triggers from the UI).
- Clear indication that Guardian owns Git/recovery and Nexus98 is request-only.

### Recommended integration order
1. Define the Guardian request/response **interface/contract**.
2. Add Nexus98 **Guardian client** (read-only status first).
3. Wire **checkpoint / recovery-request** actions (user-initiated).
4. Add **session / Don't Forget** request support.
5. Add **health reporting** from Nexus98 to Guardian.
6. Only after all of the above: consider any supervised, approval-gated automation — never before the
   safety engine and restore validation are real.

---

*Audit completed as read-only documentation. No Guardian or Nexus98 production files were modified.*
