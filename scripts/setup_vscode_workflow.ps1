param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('desktop', 'laptop')]
    [string]$Role,

    [string]$MachineName = '',
    [string]$WorkspaceRoot = 'D:/Nexus98',
    [string]$WorkspaceFile = 'D:/Nexus98/Nexus98_Workspace.code-workspace'
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $repoRoot 'config/vscode_workflow.json'
if (-not (Test-Path $configPath)) {
    throw "Missing workflow config at $configPath"
}

$config = Get-Content $configPath -Raw | ConvertFrom-Json
$roleConfig = $config.roles.$Role
if (-not $roleConfig) {
    throw "Unsupported role: $Role"
}

if ($MachineName -eq '') {
    $MachineName = $roleConfig.machineName
}

Write-Host "Configuring VS Code workflow role '$Role' on machine '$MachineName'" -ForegroundColor Cyan

$codeCmd = Get-Command code -ErrorAction SilentlyContinue
if (-not $codeCmd) {
    Write-Warning 'VS Code CLI not found on PATH. Install VS Code and re-run the script.'
    return
}

$extensionsToInstall = @($roleConfig.extensions)
foreach ($extension in $extensionsToInstall) {
    Write-Host "Installing extension $extension" -ForegroundColor Yellow
    & code --install-extension $extension --force
}

$settingsDir = Join-Path $HOME '.vscode'
if (-not (Test-Path $settingsDir)) {
    New-Item -ItemType Directory -Path $settingsDir -Force | Out-Null
}

$settingsPath = Join-Path $settingsDir 'settings.json'
$settings = @{}
if (Test-Path $settingsPath) {
    try {
        $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json -AsHashtable
    }
    catch {
        $settings = @{}
    }
}

foreach ($key in $roleConfig.workspaceSettings.PSObject.Properties.Name) {
    $settings[$key] = $roleConfig.workspaceSettings.$key
}

$settings | ConvertTo-Json -Depth 20 | Set-Content $settingsPath -Encoding UTF8

$workspaceSettingsPath = Join-Path $repoRoot '.vscode/settings.json'
if (Test-Path $workspaceSettingsPath) {
    Copy-Item $workspaceSettingsPath (Join-Path $settingsDir 'settings.json') -Force
}

if (Test-Path $WorkspaceFile) {
    Write-Host "Workspace file detected at $WorkspaceFile" -ForegroundColor Green
}
else {
    Write-Warning "Workspace file not found at $WorkspaceFile"
}

if ($Role -eq 'desktop') {
    Write-Host 'Desktop role: enabling host-side workspace settings and tunnel readiness.' -ForegroundColor Green
    & code --list-extensions | Out-Null
}
else {
    Write-Host 'Laptop role: configured as client-side remote workspace entrypoint.' -ForegroundColor Green

    $launcherPath = Join-Path $repoRoot 'scripts/launch_vscode_laptop.ps1'
    if (-not (Test-Path $launcherPath)) {
        @'
param(
    [string]$WorkspaceFile = 'D:/Nexus98/Nexus98_Workspace.code-workspace'
)

$ErrorActionPreference = 'Stop'

if (Get-Command code -ErrorAction SilentlyContinue) {
    Start-Process code -ArgumentList @('--reuse-window', $WorkspaceFile) -WindowStyle Normal
}
else {
    throw 'VS Code CLI not found on PATH.'
}
'@ | Set-Content $launcherPath -Encoding UTF8
    }

    $startupScript = Join-Path $HOME 'AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Open_Nexus98_Workspace.lnk'
    Write-Host "Laptop startup launcher prepared at $launcherPath" -ForegroundColor Green
}

Write-Host 'VS Code workflow setup completed.' -ForegroundColor Green

