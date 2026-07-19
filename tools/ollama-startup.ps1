$env:OLLAMA_MODELS="D:\AI\Models\ollama"

$Log = "D:\Nexus98\ollama_startup.log"

function Write-Log {
    param($Text)
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')  $Text" |
    Add-Content $Log
}

Write-Log "Startup check beginning"

Start-Sleep -Seconds 10

# Check API first
try {

    Invoke-RestMethod `
    "http://127.0.0.1:11434/api/tags" `
    -TimeoutSec 5 | Out-Null

    Write-Log "Ollama already running"

}
catch {

    Write-Log "Ollama API unavailable. Starting server."

    Start-Process `
    "C:\Users\isoty\AppData\Local\Programs\Ollama\ollama.exe" `
    "serve"

    Start-Sleep -Seconds 15

    try {

        Invoke-RestMethod `
        "http://127.0.0.1:11434/api/tags" `
        -TimeoutSec 10 | Out-Null

        Write-Log "Ollama started successfully"

    }
    catch {

        Write-Log "Ollama failed startup check"

    }
}

Write-Log "Startup check complete"

