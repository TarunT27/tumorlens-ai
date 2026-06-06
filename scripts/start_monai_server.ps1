param(
    [string]$StudiesPath = "datasets/Task01_BrainTumour/imagesTr",
    [string]$Model = "deepedit",
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$MonaiPython = ".monai-venv\Scripts\python.exe"
if (-not (Test-Path $MonaiPython)) {
    throw "Missing .monai-venv. Run scripts\setup_monai.ps1 first."
}

$AppPath = "monai_app\radiology"
if (-not (Test-Path $AppPath)) {
    throw "Missing MONAI radiology app. Run scripts\download_monai_radiology_app.ps1 first."
}

if (-not (Test-Path $StudiesPath)) {
    throw "Studies path not found: $StudiesPath. Download a public dataset first, or pass -StudiesPath <path>."
}

& $MonaiPython -m monailabel.main start_server `
    --app $AppPath `
    --studies $StudiesPath `
    --conf models $Model `
    --host $HostAddress `
    --port $Port
