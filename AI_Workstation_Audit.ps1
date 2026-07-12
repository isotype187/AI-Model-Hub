# AI Workstation Audit
# READ ONLY - NO CHANGES MADE

$ErrorActionPreference = "SilentlyContinue"

$ComputerName = $env:COMPUTERNAME
$UserName = $env:USERNAME
$TimeStamp = Get-Date -Format "yyyy-MM-dd_HHmmss"

$ReportPath = Join-Path $PWD "AI_Workstation_Audit_$ComputerName`_$TimeStamp.txt"

Start-Transcript -Path $ReportPath

function Section {
    param($Title)
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host $Title -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
}

function CheckCommand {
    param($Command)

    $result = Get-Command $Command

    if ($result) {
        Write-Host "[FOUND] $Command"
        Write-Host "Path: $($result.Source)"
    }
    else {
        Write-Host "[MISSING] $Command"
    }
}

function CheckService {
    param($Name)

    $svc = Get-Service $Name

    if ($svc) {
        Write-Host ""
        Write-Host "Service: $Name"
        Write-Host "Status: $($svc.Status)"
        Write-Host "Startup: $((Get-CimInstance Win32_Service -Filter "Name='$Name'").StartMode)"
    }
    else {
        Write-Host "Service $Name not found"
    }
}


Section "SYSTEM INFORMATION"

hostname
whoami

Get-ComputerInfo |
Select WindowsProductName,WindowsVersion,OsArchitecture |
Format-List


Section "NETWORK INFORMATION"

Get-NetIPAddress |
Where-Object {
    $_.IPAddress -notlike "127*" -and
    $_.IPAddress -notlike "::1"
} |
Select InterfaceAlias,IPAddress,AddressFamily |
Format-Table


Section "TAILSCALE"

CheckCommand "tailscale"

CheckService "Tailscale"

if (Get-Command tailscale) {

    tailscale version

    Write-Host "`nTailscale IP:"
    tailscale ip

    Write-Host "`nStatus:"
    tailscale status

    Write-Host "`nNetcheck:"
    tailscale netcheck

    Write-Host "`nDNS:"
    tailscale dns status

    Write-Host "`nPrefs:"
    tailscale debug prefs
}


Section "OLLAMA"

CheckCommand "ollama"

CheckService "Ollama"

if (Get-Command ollama) {

    ollama --version

    Write-Host "`nModels:"
    ollama list

    Write-Host "`nAPI:"
    
    try {
        Invoke-WebRequest `
        http://localhost:11434/api/tags `
        -UseBasicParsing `
        -TimeoutSec 5

        Write-Host "Ollama API ONLINE"
    }
    catch {
        Write-Host "Ollama API FAILED"
    }
}


Section "OPENSSH"

Get-WindowsCapability -Online |
Where-Object Name -like "OpenSSH*" |
Format-Table

CheckService "sshd"

netstat -ano | findstr ":22"

Get-NetFirewallRule |
Where-Object DisplayName -like "*SSH*" |
Select DisplayName,Enabled,Direction,Action |
Format-Table


Section "SUNSHINE"

Get-Process sunshine |
Select Name,Id,Path |
Format-Table

netstat -ano | findstr ":479"


Section "VS CODE"

CheckCommand "code"

if (Get-Command code) {

    code --version

    Write-Host "`nExtensions:"
    code --list-extensions
}


Section "PYTHON"

CheckCommand "python"

if (Get-Command python) {

    python --version

    python -c "import sys; print(sys.executable)"
}


Section "GIT"

CheckCommand "git"

if (Get-Command git) {

    git --version
    git config --list
}


Section "AI MODEL HUB"

$Paths = @(
"D:\AI_Model_Hub",
"$env:USERPROFILE\AI_Model_Hub"
)

foreach ($Path in $Paths) {

    if (Test-Path $Path) {

        Write-Host "FOUND $Path"

        if (Test-Path "$Path\.git") {
            Write-Host "Git repository detected"
        }

        if (Test-Path "$Path\venv") {
            Write-Host "Python venv detected"
        }

        if (Test-Path "$Path\main.py") {
            Write-Host "main.py detected"
        }
    }
}


Section "COMPLETE"

Write-Host "Computer: $ComputerName"
Write-Host "User: $UserName"
Write-Host "Report: $ReportPath"

Stop-Transcript
