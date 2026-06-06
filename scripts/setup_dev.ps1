$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv is required. Install uv first: https://docs.astral.sh/uv/"
}

uv venv .venv --python 3.14
uv pip install --python .venv\Scripts\python.exe -r requirements-dev.txt
.venv\Scripts\python.exe -m unittest discover -s tests

Write-Host ""
Write-Host "Dev environment ready: .venv"

