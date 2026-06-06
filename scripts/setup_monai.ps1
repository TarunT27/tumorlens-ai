$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is required. Install uv first: https://docs.astral.sh/uv/"
}

uv venv .monai-venv --python 3.10
uv pip install --python .monai-venv\Scripts\python.exe -r monai_app\requirements-monai.txt

Write-Host ""
Write-Host "MONAI environment ready: .monai-venv"
Write-Host "Activate it with:"
Write-Host "  .\.monai-venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "Then start a MONAI Label server after downloading an app/dataset:"
Write-Host "  monailabel start_server --app apps/radiology --studies datasets/Task01_BrainTumour/imagesTr --conf models deepedit"

