param(
    [string]$SlicerPath = "",
    [string]$ModulePath = ""
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (-not $SlicerPath) {
    $SlicerPath = powershell -ExecutionPolicy Bypass -File scripts\find_slicer.ps1
}

if (-not (Test-Path $SlicerPath)) {
    throw "Slicer executable not found: $SlicerPath"
}

if (-not $ModulePath) {
    $ModulePath = Join-Path $RepoRoot "TumorLensAI"
}

if (-not (Test-Path $ModulePath)) {
    throw "Module path not found: $ModulePath"
}

Start-Process -FilePath $SlicerPath -ArgumentList @("--additional-module-paths", $ModulePath)
Write-Host "Launched 3D Slicer with TumorLens AI module path:"
Write-Host "  $ModulePath"
