<#
.SYNOPSIS
    Create a desktop shortcut for the Nexus98 Codex launcher.

.DESCRIPTION
    MUST be run from an Administrator PowerShell window.
    Creates "Nexus98 Codex Launcher.lnk" on the current user's Desktop that runs:

        powershell.exe -ExecutionPolicy Bypass -File "D:\Nexus98\tools\Launch-Nexus98-Codex.ps1"

    Working directory: D:\Nexus98

    Does NOT modify Nexus98 files; only creates the shortcut.
    Verifies the shortcut exists after creation and prints success/failure.

    NOTE: This script targets the launcher at D:\Nexus98\tools\Launch-Nexus98-Codex.ps1.
    If your launcher lives elsewhere, update $LauncherPath below.
#>

$ErrorActionPreference = 'Stop'

$LauncherPath = 'D:\Nexus98\tools\Launch-Nexus98-Codex.ps1'
$ShortcutName = 'Nexus98 Codex Launcher.lnk'
$DesktopDir   = [Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $DesktopDir $ShortcutName

Write-Host ("Creating desktop shortcut: {0}" -f $ShortcutPath) -ForegroundColor Cyan

if (-not (Test-Path $LauncherPath)) {
    Write-Host ("[FAIL] Launcher not found: {0}" -f $LauncherPath) -ForegroundColor Red
    Write-Host '       Place the launcher at that path (Administrator shell) before creating the shortcut.' -ForegroundColor Yellow
    exit 1
}

try {
    $wsShell = New-Object -ComObject WScript.Shell
    $shortcut = $wsShell.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath       = 'powershell.exe'
    $shortcut.Arguments        = '-ExecutionPolicy Bypass -File "{0}"' -f $LauncherPath
    $shortcut.WorkingDirectory = 'D:\Nexus98'
    $shortcut.Description      = 'Launch Nexus98 workspace with Codex CLI (HY3 profile)'
    $shortcut.WindowStyle      = 1
    $shortcut.Save()
    Write-Host '[OK] Shortcut object saved.' -ForegroundColor Green
} catch {
    Write-Host ("[FAIL] Could not create shortcut: {0}" -f $_.Exception.Message) -ForegroundColor Red
    exit 1
}

# Verification
Start-Sleep -Milliseconds 300
if (Test-Path $ShortcutPath) {
    $props = Get-Item $ShortcutPath
    Write-Host ('[SUCCESS] Shortcut verified: {0} ({1} bytes)' -f $ShortcutPath, $props.Length) -ForegroundColor Green
    exit 0
} else {
    Write-Host ('[FAIL] Shortcut was not found after creation: {0}' -f $ShortcutPath) -ForegroundColor Red
    exit 1
}
