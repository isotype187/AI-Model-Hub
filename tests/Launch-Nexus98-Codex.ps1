<#
.SYNOPSIS
    Launch the Nexus98 development environment and start Codex (nexus98 profile)
    against D:\Nexus98. Recreates the current session environment exactly:
    same venv, same OpenRouter key (detected, never created/printed),
    same Codex profile/model routing, same workspace.

.DESCRIPTION
    - Starts in D:\Nexus98
    - Activates the Python venv (bare venv: no Activate.ps1, so PATH is set directly)
    - Detects OPENROUTER_API_KEY from environment or a local .env (does NOT create or print it)
    - Launches `codex` with the `nexus98` profile (model tencent/hy3:free via OpenRouter)
    - Performs preflight checks and fails with clear errors
    - Prints a startup summary (no secrets)

.NOTES
    Windows PowerShell only. Does not modify Nexus98 source, deps, or install anything.
#>

[CmdletBinding()]
param(
    [string]$Workspace = 'D:\Nexus98',
    [string]$Profile = 'nexus98',
    [switch]$NoLaunch
)

$ErrorActionPreference = 'Stop'

function Write-Step($msg) { Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "[+] $msg" -ForegroundColor Green }
function Write-Fail($msg) { Write-Host "[!] $msg" -ForegroundColor Red; throw $msg }

# ---------------------------------------------------------------------------
# 1. Workspace
# ---------------------------------------------------------------------------
Write-Step "Validating workspace: $Workspace"
if (-not (Test-Path $Workspace)) { Write-Fail "Workspace not found: $Workspace" }
Write-Ok "Workspace present"

# ---------------------------------------------------------------------------
# 2. Python venv (bare venv: no Activate.ps1 expected)
# ---------------------------------------------------------------------------
Write-Step "Locating Python venv"
$venvPython = Join-Path $Workspace '.venv\Scripts\python.exe'
$venvScripts = Join-Path $Workspace '.venv\Scripts'
if (-not (Test-Path $venvPython)) { Write-Fail "Venv python not found: $venvPython" }
Write-Ok "Venv python: $venvPython"

# Activate by manipulating PATH/VIRTUAL_ENV (no Activate.ps1 dependency)
$env:VIRTUAL_ENV = Join-Path $Workspace '.venv'
$env:PATH = "$venvScripts" + [System.IO.Path]::PathSeparator + $env:PATH
$pyVersion = & $venvPython --version 2>&1
Write-Ok "Active Python: $pyVersion"

# ---------------------------------------------------------------------------
# 3. Detect OpenRouter API key (NEVER create, NEVER print)
# ---------------------------------------------------------------------------
Write-Step "Detecting OpenRouter API configuration"
$apiKey = $env:OPENROUTER_API_KEY
if (-not $apiKey) {
    $envFile = Join-Path $Workspace '.env'
    if (Test-Path $envFile) {
        $envContent = Get-Content $envFile -ErrorAction SilentlyContinue
        foreach ($line in $envContent) {
            if ($line -match '^\s*OPENROUTER_API_KEY\s*=\s*(.+)\s*$') {
                $apiKey = $Matches[1].Trim().Trim('"').Trim("'")
                break
            }
        }
    }
}
if ($apiKey) {
    Write-Ok "OPENROUTER_API_KEY detected (length $($apiKey.Length), value hidden)"
    $env:OPENROUTER_API_KEY = $apiKey
} else {
    Write-Fail "OPENROUTER_API_KEY not found in environment or $Workspace\.env. Cannot launch OpenRouter-routed profile. Set the variable or add it to .env (value will not be printed or created)."
}

# ---------------------------------------------------------------------------
# 4. Locate codex / hy3 binary
# ---------------------------------------------------------------------------
Write-Step "Locating codex / hy3 launcher"
$codexCmd = $null
foreach ($candidate in @('codex', 'hy3')) {
    try { $found = Get-Command $candidate -ErrorAction SilentlyContinue; if ($found) { $codexCmd = $found.Source; break } } catch { }
}
if (-not $codexCmd) {
    $fallbacks = @(
        "$env:LOCALAPPDATA\Programs\codex\codex.exe",
        "$env:APPDATA\npm\codex.cmd",
        "$env:LOCALAPPDATA\Microsoft\WinGet\Links\codex.exe",
        "C:\Users\isoty\.codex\codex.exe"
    )
    foreach ($f in $fallbacks) { if (Test-Path $f) { $codexCmd = $f; break } }
}
if (-not $codexCmd) {
    Write-Fail "codex/hy3 binary not found on PATH or in common locations. Install/link it or call this script from a shell where it is available."
}
Write-Ok "Launcher: $codexCmd"

# ---------------------------------------------------------------------------
# 5. Verify Codex config profile exists (without printing secrets)
# ---------------------------------------------------------------------------
Write-Step "Verifying Codex profile: $Profile"
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$profileFile = Join-Path $codexHome "$Profile.config.toml"
if (-not (Test-Path $profileFile)) {
    Write-Fail "Codex profile config not found: $profileFile"
}
Write-Ok "Profile config present: $profileFile"

# ---------------------------------------------------------------------------
# 6. Startup summary (no secrets)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "==================== Nexus98 Launch Summary ====================" -ForegroundColor Yellow
Write-Host "Workspace     : $Workspace"
Write-Host "Venv Python   : $venvPython ($pyVersion)"
Write-Host "OpenRouter    : key detected (len $($apiKey.Length), hidden)"
Write-Host "Codex launcher: $codexCmd"
Write-Host "Profile       : $Profile (model tencent/hy3:free via OpenRouter)"
Write-Host "Codex home    : $codexHome"
Write-Host "Tailscale/net : inherited from current environment (no changes made)"
Write-Host "===============================================================" -ForegroundColor Yellow
Write-Host ""

if ($NoLaunch) {
    Write-Ok "NoLaunch specified; environment prepared, not starting Codex."
    return
}

# ---------------------------------------------------------------------------
# 7. Launch Codex with the nexus98 profile, in the workspace
# ---------------------------------------------------------------------------
Write-Step "Launching Codex (profile=$Profile) in $Workspace"
Set-Location $Workspace
& $codexCmd --profile $Profile
