<#
.SYNOPSIS
    Launch the Nexus98 workspace with the Codex CLI using the existing HY3/nexus98 profile.

.DESCRIPTION
    Performs preflight validation, then starts the Codex CLI connected to the Nexus98
    workspace using the existing HY3 configuration. It reuses the current working setup:
      - OpenRouter API key (OPENROUTER_API_KEY from environment)
      - HY3 profile (nexus98.config.toml -> model tencent/hy3:free via OpenRouter)
      - Codex CLI configuration (~/.codex/config.toml)
    It does NOT modify Nexus98 source, dependencies, or API keys, and does NOT print secrets.

    The current session launches Codex with the "nexus98" profile (which itself routes to
    the HY3 model tencent/hy3:free through OpenRouter). This launcher reproduces that exactly.

    Requirements (Windows PowerShell):
      - D:\Nexus98 workspace
      - D:\Nexus98\.venv Python environment
      - Codex CLI on PATH (or in ~/.codex/.sandbox-bin)
      - Codex config:  ~/.codex/config.toml
      - Profile config: ~/.codex/nexus98.config.toml (HY3 routing)
      - OPENROUTER_API_KEY environment variable (used by HY3/OpenRouter routing)
#>

[CmdletBinding()]
param(
    [string]$Workspace = 'D:\Nexus98',
    [string]$VenvPath  = 'D:\Nexus98\.venv',
    [string]$Profile   = 'nexus98'
)

$ErrorActionPreference = 'Stop'

function Write-Step($Message) { Write-Host "[*] $Message" -ForegroundColor Cyan }
function Write-Ok($Message)   { Write-Host "    [OK] $Message" -ForegroundColor Green }
function Write-Fail($Message) { Write-Host "    [FAIL] $Message" -ForegroundColor Red }

# ---------------------------------------------------------------------------
# 1. Locate Codex CLI
# ---------------------------------------------------------------------------
Write-Step 'Locating Codex CLI'
$codexCmd = $null
if (Get-Command codex.exe -ErrorAction SilentlyContinue) {
    $codexCmd = (Get-Command codex.exe).Source
}
if (-not $codexCmd) {
    $sandboxBin = Join-Path $env:USERPROFILE '.codex\.sandbox-bin\codex.exe'
    if (Test-Path $sandboxBin) { $codexCmd = $sandboxBin }
}
if ($codexCmd) {
    Write-Ok "Codex CLI: $codexCmd"
} else {
    Write-Fail 'Codex CLI not found on PATH or in ~/.codex/.sandbox-bin.'
    throw 'Codex CLI is required but was not found.'
}

# ---------------------------------------------------------------------------
# 2. Validate workspace
# ---------------------------------------------------------------------------
Write-Step "Validating Nexus98 workspace: $Workspace"
if (Test-Path $Workspace) { Write-Ok "Workspace exists: $Workspace" }
else { Write-Fail "Workspace not found: $Workspace"; throw 'Nexus98 workspace path is missing.' }

# ---------------------------------------------------------------------------
# 3. Validate venv
# ---------------------------------------------------------------------------
Write-Step 'Validating Python virtual environment'
$venvActivate = Join-Path $VenvPath 'Scripts\Activate.ps1'
if (Test-Path $venvActivate) {
    Write-Ok "venv activate script: $venvActivate"
} else {
    Write-Fail "venv not found: $venvActivate"
    throw 'Python virtual environment (.venv) is required but was not found.'
}

# ---------------------------------------------------------------------------
# 4. Validate Codex configuration files
# ---------------------------------------------------------------------------
Write-Step 'Validating Codex configuration files'
$codexHome   = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$codexConfig = Join-Path $codexHome 'config.toml'
$profileCfg  = Join-Path $codexHome ("{0}.config.toml" -f $Profile)

$codexConfigFound = Test-Path $codexConfig
$profileFound     = Test-Path $profileCfg

if ($codexConfigFound) { Write-Ok "Codex config: $codexConfig" } else { Write-Fail "Codex config missing: $codexConfig" }
if ($profileFound)     { Write-Ok "Profile config ($Profile): $profileCfg" } else { Write-Fail "Profile config missing: $profileCfg" }

if (-not $codexConfigFound) { throw 'Codex CLI configuration (config.toml) is required.' }
if (-not $profileFound)     { throw "Profile configuration ($Profile.config.toml) is required." }

# ---------------------------------------------------------------------------
# 5. Validate required environment variables
# ---------------------------------------------------------------------------
Write-Step 'Validating required environment variables'
$requiredEnv = @('OPENROUTER_API_KEY')
$envMissing  = @()
foreach ($name in $requiredEnv) {
    $val = [Environment]::GetEnvironmentVariable($name)
    if ($val -and $val.Length -gt 0) {
        Write-Ok "$name is set (length $($val.Length))"
    } else {
        Write-Fail "$name is NOT set"
        $envMissing += $name
    }
}
if ($envMissing.Count -gt 0) {
    throw ("Missing required environment variable(s): {0}. HY3/OpenRouter routing requires these." -f ($envMissing -join ', '))
}

# ---------------------------------------------------------------------------
# 6. Startup summary
# ---------------------------------------------------------------------------
Write-Host ''
Write-Host '============================================' -ForegroundColor Yellow
Write-Host ' Nexus98 Codex Launcher - Startup Summary' -ForegroundColor Yellow
Write-Host '============================================' -ForegroundColor Yellow
Write-Host ("  Workspace         : {0}" -f $Workspace)
Write-Host ("  Python venv       : {0}" -f $venvActivate)
Write-Host ("  Codex CLI         : {0}" -f $codexCmd)
Write-Host ("  Codex config      : {0}" -f $codexConfig)
Write-Host ("  HY3/Profile config: {0}" -f $profileCfg)
Write-Host ("  Model routing     : OpenRouter (tencent/hy3:free) via profile '$Profile'")
Write-Host ("  OPENROUTER_API_KEY: set (reused, not printed)")
Write-Host ("  Tailscale/network : no hard dependency detected; workspace uses local paths")
Write-Host '--------------------------------------------' -ForegroundColor Yellow
Write-Host '  HY3 status        : READY (profile + API key present)' -ForegroundColor Green
Write-Host '  Codex status      : READY (CLI + config present)' -ForegroundColor Green
Write-Host '============================================' -ForegroundColor Yellow
Write-Host ''

# ---------------------------------------------------------------------------
# 7. Launch (activate venv, then start Codex in the workspace)
# ---------------------------------------------------------------------------
Write-Step "Activating venv and launching Codex CLI with profile '$Profile' in $Workspace"
Push-Location $Workspace
try {
    & $venvActivate
    & $codexCmd --profile $Profile
    $exitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

if ($exitCode -and $exitCode -ne 0) {
    Write-Host "Codex CLI exited with code $exitCode" -ForegroundColor Red
    exit $exitCode
}
