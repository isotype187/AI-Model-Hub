# Task: Bridge Subsystem Cross-Machine Path References

> **Type:** Runtime defect (path/configuration alignment)
> **Severity:** HIGH
> **Status:** OPEN — blocked, awaiting checkpoint + human approval
> **Source report:** `docs/NEXUS98_ENGINEERING_READINESS_REPORT.md` (section 5.2)
> **Created:** 2026-07-18 (America/Chicago)
> **Constraint:** Documentation only. No source, config, test, Guardian, or dependency files modified here.

---

## 1. Problem Statement

The bridge subsystem hardcodes paths to a different machine's install location
(`D:\AI\Nexus98_Bridge\...`), while the current repository root is `D:\Nexus98`.
This means the bridge controller will attempt to launch/inspect a bridge process
that does not exist on this machine, breaking or misrouting VS Code bridge
operations and any continuity features that depend on it.

## 2. Current Behavior

- `core/bridge_controller.py:11` -> `BRIDGE_PYTHON = r"D:\AI\Nexus98_Bridge\.venv\Scripts\python.exe"`
- `core/bridge_controller.py:13` -> `BRIDGE_SCRIPT = r"D:\AI\Nexus98_Bridge\bridge_server.py"`
- `core/bridge_controller.py:77-80` launches/inspects using those hardcoded paths (`cwd=str(Path(BRIDGE_SCRIPT).parent)`).
- On this workstation, the referenced `D:\AI\Nexus98_Bridge` directory is not the
  active install; the actual bridge lives under `D:\Nexus98` (e.g., `bridge/`, `api/vscode_bridge.py`).
- Net effect: `get_status()`, enable/disable, and process discovery can target the
  wrong (or non-existent) bridge, producing failed connections or a silently dead bridge.

## 3. Expected Behavior

- Bridge paths resolve from a single configurable root (e.g., a `ROOT`/`BRIDGE_HOME`
  config key or environment variable), defaulting to the current repo root `D:\Nexus98`.
- `core/bridge_controller.py` locates `bridge_server.py` / its venv relative to that
  root, not a hardcoded foreign path.
- The bridge subsystem starts, reports status, and discovers the correct local
  process on this machine.

## 4. Files Involved

| File | Role | Change? |
|------|------|---------|
| `core/bridge_controller.py` | Hardcodes `D:\AI\Nexus98_Bridge` paths (lines 11, 13, 77-80) | Proposed change (gated) |
| `config/system_config.json` (or new bridge config) | Could host `bridge_home` root | Optional, under checkpoint |
| `bridge/` , `api/vscode_bridge.py` | Actual local bridge implementation | No change (reference only) |
| `docs/NEXUS98_ENGINEERING_READINESS_REPORT.md` | Records the risk | Already documents it |

> Guardian owns Git/recovery; any edit must go through Guardian's checkpoint flow.

## 5. Risk Assessment

- **Severity:** HIGH. Breaks a core integration (VS Code bridge / continuity) on this machine.
- **Likelihood of harm if unchanged:** High for any workflow relying on the bridge
  (task-send, continuity capture, model/provider sync via bridge).
- **Risk of the fix:** Low-Medium. Introducing a configurable root is mechanical;
  main risk is selecting the correct default and not regressing the launch cwd.
- **Blast radius:** Bridge controller + VS Code integration only; contained.

## 6. Required Checkpoint Before Modification

1. **Inspect** current implementation (done — see report §5.2 and this doc).
2. **Create a Guardian checkpoint / known-good snapshot** of `core/bridge_controller.py`
   (and any config touched) before editing.
3. **Explain intended change**: replace hardcoded `D:\AI\Nexus98_Bridge` paths with a
   root-derived path (config or env var), preserving launch behavior.
4. **Obtain human approval** (Constitution development rule step 4).
5. **Apply controlled modification** only after approval.
6. **Validate** (section 7) and **report** results.

> This document covers steps 1 and 3. Steps 2, 4, 5, 6 require a change window + sign-off.

## 7. Validation Steps After Change

- [ ] `core/bridge_controller.py` no longer references `D:\AI\Nexus98_Bridge`.
- [ ] Bridge paths resolve to the current repo root (`D:\Nexus98`) by default.
- [ ] `bridge_controller.get_status()` returns a valid status against the local bridge (or clearly reports "not running" without crashing).
- [ ] Process discovery (`find_bridge_processes`) finds the actual local `bridge_server.py` if running.
- [ ] Existing bridge tests pass: `tests/test_vscode_bridge.py`, `tests/test_vscode_connection.py`, `tests/test_vscode_workflow_config.py` (with `TMPDIR` redirected).
- [ ] No regression in `api/vscode_bridge.py` behavior.
- [ ] Guardian checkpoint confirmed recoverable.

---

*End of task document. No files outside `docs/tasks/` were modified.*
