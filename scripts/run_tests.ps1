$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".venv\Scripts\python.exe") {
    .venv\Scripts\python.exe -m unittest discover -s tests
} else {
    python -m unittest discover -s tests
}

