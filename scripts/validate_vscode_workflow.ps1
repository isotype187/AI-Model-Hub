param(
    [ValidateSet('desktop', 'laptop')]
    [string]$Role,
    [string]$MachineName = ''
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $repoRoot 'config/vscode_workflow.json'
$config = Get-Content $configPath -Raw | ConvertFrom-Json
$roleConfig = $config.roles.$Role

if ($MachineName -eq '') {
    $MachineName = $roleConfig.machineName
}

Write-Host "Validating VS Code workflow role '$Role' on '$MachineName'" -ForegroundColor Cyan

$codeCmd = Get-Command code -ErrorAction SilentlyContinue
if (-not $codeCmd) {
    Write-Host 'VS Code CLI not found.' -ForegroundColor Red
    exit 1
}

$installedExtensions = & code --list-extensions
foreach ($extension in $roleConfig.extensions) {
    if ($installedExtensions -contains $extension) {
        Write-Host "[OK] $extension" -ForegroundColor Green
    }
    else {
        Write-Host "[MISSING] $extension" -ForegroundColor Yellow
    }
}

$settingsPath = Join-Path $HOME '.vscode/settings.json'
if (Test-Path $settingsPath) {
    Write-Host '[OK] User settings file is present.' -ForegroundColor Green
}
else {
    Write-Host '[MISSING] User settings file.' -ForegroundColor Yellow
}

$expectedSettings = $roleConfig.workspaceSettings.PSObject.Properties.Name
foreach ($key in $expectedSettings) {
    Write-Host "[CHECK] $key" -ForegroundColor DarkCyan
}

$workspaceFile = $config.workspace.workspaceFile
if (Test-Path $workspaceFile) {
    Write-Host '[OK] Workspace file is present.' -ForegroundColor Green
}
else {
    Write-Host '[MISSING] Workspace file.' -ForegroundColor Yellow
}

Write-Host "Role check: expected $($roleConfig.role)" -ForegroundColor Green
