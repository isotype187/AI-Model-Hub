param(
    [string]$WorkspaceFile = 'D:/AI_Model_Hub/Nexus98_Workspace.code-workspace'
)

$ErrorActionPreference = 'Stop'

if (Get-Command code -ErrorAction SilentlyContinue) {
    Start-Process code -ArgumentList @('--reuse-window', $WorkspaceFile) -WindowStyle Normal
}
else {
    throw 'VS Code CLI not found on PATH.'
}
