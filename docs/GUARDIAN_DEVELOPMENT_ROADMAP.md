# Guardian Development Roadmap

> Documentation-only. Derived from `docs/GUARDIAN_ARCHITECTURE_AUDIT.md`.
> No Guardian, Nexus98, config, or test files were modified.
> Guardian location: `D:\Nexus98_Guardian` (separate project; remains separate).

---

## 1. Guardian End-State Architecture

The end state is a **standalone, request-driven recovery & integrity authority** for the Nexus98
ecosystem. Nexus98 never owns Git, recovery, or backup; it only *requests* those actions and observes
results.

### Logical components
- **API/Interface Layer** — versioned request/response contract (CLI or local socket) consumed by the
  Nexus98 Guardian client. Replaces today's ad-hoc file artifacts.
- **Snapshot Engine** (exists, harden) — captures system inventory + SHA256 file-hash inventory of
  declared targets; emits verifiable manifests.
- **Verification Engine** (exists, expand) — validates not just Guardian file existence but the
  *health of the Nexus98 application and its data*.
- **Recovery Engine** (stub → real) — actually restores from a validated snapshot and validates the
  restore.
- **Known-Good Manager** (new) — scores, promotes, and rotates recovery points into a rolling
  "last known good" state.
- **Safety / Approval Engine** (stub → real) — an enforcing authorization gate that can return
  `denied` with logged rationale; no pass-through.
- **Git Authority** (new) — the sole owner of commits, pushes, branch management for Nexus98.
- **State Store** (new) — single consolidated source of truth replacing the fragmented per-asset JSON.
- **Logging / Audit** (exists partial, consolidate) — correlated, structured logs tied to requests,
  approvals, and outcomes.

### Non-goals
- No autonomy logic for Nexus98.
- No modification of Nexus98 application code or autonomy state.
- No UI beyond the read-only status/recovery-request surface exposed to Nexus98.

---

## 2. Service Model

### Runtime
- Guardian runs as a **long-lived local service** (Windows service or supervised background process),
  replacing the current one-shot `Nexus98.ps1` launcher that exits immediately.
- Exposes a **versioned local interface** (recommended: a small HTTP/Unix-socket API bound to
  localhost only, or a documented CLI-with-JSON contract). No remote exposure by default.
- Lifecycle: start → load state store → register assets → begin health monitor → accept requests →
  on shutdown, flush state and write a clean exit marker.

### Process isolation
- Runs under its own service account with least-privilege filesystem scope.
- External tools (`git`, `ollama`, `python`) invoked via the existing safe-runner pattern
  (`Invoke-SafeCommand`) with timeouts, but now gated by the approval engine.

### Interaction style
- **Pull (Guardian → Nexus98):** none autonomously. Guardian only responds to explicit requests.
- **Push (Nexus98 → Guardian):** checkpoint, save session, Don't Forget, health report, recovery request.

---

## 3. Health Monitoring Design

### Scope
Replace `Test-Nexus98System` (which only checks 3 Guardian files exist) with **application-level**
health checks of Nexus98.

### Checks
- Nexus98 process / launch integrity.
- Core file hashes vs. last known-good inventory.
- Database / state-file readability and schema sanity.
- Config validity (parse + schema, not content mutation).
- Autonomy/governor state readability (read-only) and consistency.

### Behavior
- Scheduled interval + on-demand trigger from Nexus98.
- Results written to the state store and returned via the interface.
- Degraded health → logged + surfaced to Nexus98 status panel; **no automatic remediation** unless
  explicitly approved per the safety engine.
- No alerts outside the local log/status contract (no external notification in v1).

---

## 4. Recovery Point Design

### Creation
- `New-Nexus98RecoveryPoint` evolves from a metadata-only write (`latest_recovery.json`) into a
  **full, restorable capture**:
  - System inventory (CIM) — exists.
  - SHA256 file-hash inventory of declared targets — exists (`inventory.txt`).
  - Manifest (`manifest.json`) — exists.
  - Self-verification (`verification.json`) — exists.
  - **Actual file payload copy** of critical, small-footprint targets (configs, state) so restore
    does not depend on the live (possibly corrupted) source.

### Restore (new, real)
- `Invoke-Nexus98Recovery` performs an actual restore from a selected recovery point.
- Post-restore **validation**: re-hash restored files and compare against the point's `inventory.txt`;
  report `[PASS]/[FAIL]` per file.
- Restore is **user-initiated / approval-gated only** — never automatic.

### Metadata
- Each recovery point records: reason, time, source state hash, files captured, validation status,
  and a health score at creation time.

---

## 5. Rolling Known-Good State Design

### Concept
A single, authoritative "last known good" pointer that Guardian maintains and promotes only when a
recovery point is **validated healthy**.

### Mechanism
- **Known-Good Manager** stores recovery points with a health score (from verification + health check).
- A point is promoted to "known-good" only after:
  1. Creation succeeded,
  2. Self-verification passed,
  3. Application health check passed against it.
- **Rotation:** keep N known-good points (e.g. last 5); retire oldest beyond the cap. Never auto-retire
  the sole healthy point.
- Exposes `get_last_known_good()` via the interface for status display and as the default restore target.

### Storage
- Consolidated in the state store (not the current single `latest_recovery.json` pointer).

---

## 6. Git Ownership Architecture

### Principle
Guardian is the **sole Git authority** for Nexus98. Nexus98 must never perform Git writes.

### Responsibilities
- Commits (structured, atomic, message-templated).
- Pushes (only after local validation + approval).
- Branch management and tagging for checkpoints.
- Detecting and reporting uncommitted/diverged state to Nexus98 (read-only observation).

### Safety
- All Git actions gated by the approval engine.
- Pre-push validation: health check + known-good reference.
- Failed push → rolled back locally, logged, surfaced to Nexus98; no partial remote state.

---

## 7. Nexus98 Communication Interface

### Contract
A stable, versioned **request/response** interface. Recommended shape (implementation-agnostic):

```
request:  { "action": "<name>", "payload": { ... } }
response: { "status": "ok|denied|error", "result": { ... }, "request_id": "..." }
```

### Supported actions (minimum v1)
- `create_checkpoint` — capture + register a recovery point.
- `save_session` — persist current Nexus98 session state via Guardian.
- `create_dont_forget` — create a Don't Forget marker/checkpoint.
- `report_health` — Nexus98 pushes a health snapshot to Guardian.
- `request_recovery` — user-initiated restore request (approval-gated).
- `get_status` — read-only: last checkpoint, last recovery, known-good, health.

### Client
- A thin Nexus98 **Guardian client** module (read-only status first) that calls the interface and
  parses the JSON result. No Git, no recovery writes live in Nexus98.
- Nexus98 UI exposes only: status panel + user-initiated recovery-request panel.

---

## 8. Permission Boundaries

### Guardian may modify
- Its own tree: `config/`, `data/`, `snapshots/`, `logs/`, `reports/` under `D:\Nexus98_Guardian`.
- Git repositories it owns (Nexus98 repo) via the Git Authority — commits/pushes/branches only.
- Restored file payloads during an approved recovery operation.

### Guardian must NOT modify
- Nexus98 autonomy state or governor logic.
- Nexus98 application source beyond Git-owned version control.
- Any non-Nexus98 user data outside declared recovery targets.

### Required privileges
- Filesystem read of declared snapshot targets (`D:\Nexus98_Toolkit`, `D:\AI_Model_Hub\*`,
  `%USERPROFILE%\.continue`, `%USERPROFILE%\.vscode`) and Nexus98 repo.
- Git write to the Nexus98 repo (scoped, approval-gated).
- Local service account with least privilege.

### Risk containment
- The stub safety engine (currently `approved=True` always) must be replaced by an enforcing gate
  **before** any autonomous or push capability is enabled. No privilege expansion until then.

---

## 9. Implementation Phases

### Phase A — Foundation (no autonomy)
1. Define and document the request/response interface contract (versioned).
2. Replace fragmented per-asset JSON with a single **state store**.
3. Harden `snapshot_engine.ps1` (already mostly real) to emit validated manifests.

### Phase B — Real Recovery
4. Implement actual `Invoke-Nexus98Recovery` restore + post-restore validation.
5. Add `get_status` / `get_last_known_good` read paths.

### Phase C — Known-Good & Health
6. Build the **Known-Good Manager** (scoring, promotion, rotation).
7. Expand `verification_engine.ps1` to application-level health checks.

### Phase D — Safety & Git
8. Replace the stub safety engine with an **enforcing approval gate** (`denied` capable, logged).
9. Implement the **Git Authority** (commit/push/branch), gated and validated.

### Phase E — Service & Integration
10. Convert the one-shot launcher into a **long-lived local service**.
11. Build the Nexus98 **Guardian client** (read-only status first).
12. Wire user-initiated **checkpoint / recovery-request / session / Don't Forget / health report**.

### Phase F — Supervised Automation (only after A–E)
13. Consider approval-gated, logged, non-destructive automation — never before safety + restore
    validation are real.

---

## 10. Testing Strategy

### Unit
- Each engine function tested in isolation (snapshot manifest generation, hash inventory, recovery
  restore + validation, known-good promotion/rotation, approval gate decisions).
- `tests/` directory (currently empty) populated with PowerShell Pester or equivalent.

### Integration
- Simulated request/response cycles against the interface contract.
- Recovery round-trip: create point → corrupt a target → restore → validate hashes match.

### Safety / Negative
- Approval gate returns `denied` for out-of-policy requests.
- Restore validation fails loudly on mismatch; no silent partial restore.
- Git push aborts and rolls back on failed pre-push validation.

### Nexus98-side
- Nexus98 client tests are **read-only**: confirm status parsing, confirm no Git/recovery writes occur
  from Nexus98, confirm UI remains observational.
- No production Nexus98 code changes required for Guardian testing.

### Acceptance gate
- No phase proceeds until the previous phase's tests pass and the safety engine enforces (not
  pass-through) before any privileged/autonomous capability is enabled.

---

*Roadmap derived from the read-only Guardian audit. No production files modified.*
