param([string]$task = "")

if ($task -match "bug|error|fix|crash|exception") {
    "deepseek-coder:latest"
}
elseif ($task -match "design|architecture|system|plan") {
    "mistral:latest"
}
elseif ($task -match "image|ui|screenshot|vision") {
    "llava:latest"
}
elseif ($task -match "simple|quick|what|explain") {
    "phi3:latest"
}
else {
    "deepseek-coder:latest"
}
