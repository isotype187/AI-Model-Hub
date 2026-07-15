# VS Code workflow setup

This automation is meant to restore a stable two-machine VS Code workflow:

- Desktop machine: host role, heavy development setup.
- Laptop machine: client role, minimal remote entrypoint setup.

## Quick commands

From the repository root on the desktop:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_vscode_workflow.ps1 -Role desktop
powershell -ExecutionPolicy Bypass -File .\scripts\validate_vscode_workflow.ps1 -Role desktop
```

From the repository root on the laptop:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_vscode_workflow.ps1 -Role laptop
powershell -ExecutionPolicy Bypass -File .\scripts\validate_vscode_workflow.ps1 -Role laptop
powershell -ExecutionPolicy Bypass -File .\scripts\launch_vscode_laptop.ps1
```

## Laptop auto-open behavior

The laptop launcher script opens the shared workspace automatically when VS Code starts. The setup script prepares that launcher for the laptop role so it can be used as a simple startup entrypoint for the remote workspace.

## What this automates

- Applies a role-based extension list from config/vscode_workflow.json.
- Writes role-specific settings into the user VS Code settings file.
- Validates that the expected extensions and workspace file are present.

## Notes

The desktop should be the machine that hosts the tunnel and the workspace. The laptop should connect to that host rather than acting as an independent local development host.
