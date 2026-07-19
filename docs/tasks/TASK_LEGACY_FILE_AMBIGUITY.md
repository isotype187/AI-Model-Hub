# Task: Authority / Source-of-Truth Ambiguity (Legacy File Proliferation)

> **Type:** Repository hygiene / governance clarity
> **Severity:** MEDIUM (enabler for safe engineering)
> **Status:** OPEN — can begin with non-destructive quarantine (no source/config edit)
> **Source report:** `docs/NEXUS98_ENGINEERING_READINESS_REPORT.md` (section 5.4 / Technical Debt 2)
> **Created:** 2026-07-18 (America/Chicago)
> **Constraint:** Documentation only. No source, config, test, Guardian, or dependency files modified here. Moves/quarantine are non-source file relocations only.

---

## 1. Problem Statement

The repository contains a large number of legacy/backup copies (>=368 files matching
`.backup`/`.bak`/`before`/`STATUS_BEFORE`) spread across the working tree plus
parallel `archive/`, `snapshots/`, `backups/`, and `checkpoints/` trees. This makes
it ambiguous which file is the authoritative source, risking edits to stale copies
and confusion during recovery.

## 2. Current Behavior

- `Get-ChildItem` (2026-07-18) found >=368 files matching backup/legacy name patterns
  inside `core/`, `api/`, `ui/`, `tests/`, `backups/`, `snapshots/`, `archive/`, etc.
- Examples: `api/vscode_bridge.backup.py`, `ui/main_window_BEFORE_STATUS.py`,
  `core/supervisor_before_final_autogen_fix.py`, `tests/test_vscode_workflow_config.py.bak`.
- Guardian is the intended authority for recovery/Git/integrity, but the sheer
  volume of in-tree copies competes with that authority and obscures the live source.
- During routine edits, an engineer could modify a `*_before_*` or `.backup` copy
  instead of the real module.

## 3. Expected Behavior

- A single, indexed legacy location (e.g., `archive/legacy_inventory/`) holds all
  non-authoritative copies, with a manifest mapping each to its original path/date.
- The active source tree contains only live, authoritative files (no `*_before_*`,
  `.backup`, `.bak` copies alongside live modules).
- Guardian remains the recovery authority; Nexus98 does not duplicate that role.

## 4. Files Involved

| Scope | Role | Change? |
|-------|------|---------|
| `~368` legacy files across `core/`, `api/`, `ui/`, `tests/`, `backups/`, `snapshots/`, `archive/` | Non-authoritative copies | Quarantine/move (non-source) |
| `archive/legacy_inventory/MANIFEST.csv` (new) | Index of relocated copies | Create (doc/index only) |
| `docs/NEXUS98_ENGINEERING_READINESS_REPORT.md` | Records the risk | Already documents it |

> No live source/config/test/Guardian files are modified. Moves are relocations of
> already-dead copies into an indexed archive.

## 5. Risk Assessment

- **Severity:** MEDIUM. Not a runtime defect, but a real governance/error risk.
- **Likelihood of harm if unchanged:** Medium over time — accidental edits to stale copies.
- **Risk of the fix:** Low. Pure relocation + manifest; no behavior change.
  Must avoid moving live files or Guardian-owned recovery artifacts.
- **Blast radius:** Repository layout only; zero runtime impact.

## 6. Required Checkpoint Before Modification

1. **Inspect** and enumerate all legacy matches (done via inventory scan).
2. **Create a Guardian checkpoint / snapshot** of the repo before any relocation.
3. **Explain intended change**: move only `*_before_*`/`.backup`/`.bak` copies (not
   live modules, not Guardian recovery artifacts) into `archive/legacy_inventory/`
   with a manifest; do not delete.
4. **Obtain human approval** for the relocation scope.
5. **Apply controlled relocation** + write the manifest.
6. **Validate** (section 7) and **report**.

## 7. Validation Steps After Change

- [ ] Live source directories (`core/`, `api/`, `ui/`, `tests/`) contain no `*_before_*`/`.backup`/`.bak` copies of active modules.
- [ ] `archive/legacy_inventory/MANIFEST.csv` lists each relocated file with original path + date.
- [ ] `git status` (via Guardian) shows only additions to the archive index, no deletion of live files.
- [ ] Application still imports and runs (`tests/test_import_smoke.py` green).
- [ ] Guardian checkpoint confirmed recoverable (relocation is reversible).

---

*End of task document. No files outside `docs/tasks/` were modified.*
