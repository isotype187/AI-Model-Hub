param([string]$prompt)

$model = & "D:\Nexus98\core\router.ps1" $prompt

Write-Host "Using Model: $model"

$response = Invoke-RestMethod http://localhost:11434/api/generate -Method Post -Body (@{
    model = $model
    prompt = $prompt
    stream = $false
} | ConvertTo-Json -Depth 3)

$response.response

