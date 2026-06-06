$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$MonaiPython = ".monai-venv\Scripts\python.exe"
if (-not (Test-Path $MonaiPython)) {
    throw "Missing .monai-venv. Run scripts\setup_monai.ps1 first."
}

& $MonaiPython scripts\create_synthetic_study.py
if ($LASTEXITCODE -ne 0) {
    throw "Synthetic study generation failed."
}
