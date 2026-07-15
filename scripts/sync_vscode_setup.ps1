param([switch]$WhatIf)

$extensions = @(
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-toolsai.jupyter",
    "ms-vscode.powershell",
    "github.copilot",
    "github.copilot-chat",
    "github.vscode-pull-request-github",
    "eamodio.gitlens",
    "redhat.vscode-yaml",
    "ms-vscode.makefile-tools",
    "ms-azuretools.vscode-docker",
    "ms-vscode-remote.remote-containers",
    "ms-vscode-remote.remote-ssh"
)

if (-not (Get-Command code -ErrorAction SilentlyContinue)) {
    Write-Host "VS Code CLI was not found on PATH. Install the 'code' command or open VS Code and run the command from the Command Palette." -ForegroundColor Yellow
    exit 1
}

foreach ($extension in $extensions) {
    if ($WhatIf) {
        Write-Host "Would install $extension"
    }
    else {
        Write-Host "Installing $extension..."
        code --install-extension $extension
    }
}

Write-Host "VS Code extension sync script completed." -ForegroundColor Green
