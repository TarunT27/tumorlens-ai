$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "Running TumorLens AI tests..."
powershell -ExecutionPolicy Bypass -File scripts\run_tests.ps1

Write-Host ""
Write-Host "Checking development environment..."
if (Test-Path ".venv\Scripts\python.exe") {
    .venv\Scripts\python.exe scripts\check_environment.py
} else {
    python scripts\check_environment.py
}

Write-Host ""
Write-Host "Checking MONAI environment..."
if (-not (Test-Path ".monai-venv\Scripts\python.exe")) {
    throw "Missing .monai-venv. Run scripts\setup_monai.ps1 first."
}
.monai-venv\Scripts\python.exe -m monailabel.main --version
.monai-venv\Scripts\python.exe scripts\check_environment.py

Write-Host ""
Write-Host "Checking 3D Slicer..."
powershell -ExecutionPolicy Bypass -File scripts\find_slicer.ps1

Write-Host ""
Write-Host "Checking MONAI server configuration with synthetic study and BraTS bundle..."
$SyntheticStudy = "sample_data\synthetic_brain_mri\imagesTr"
if (-not (Test-Path $SyntheticStudy)) {
    powershell -ExecutionPolicy Bypass -File scripts\create_synthetic_study.ps1
}
powershell -ExecutionPolicy Bypass -File scripts\start_monai_server.ps1 `
    -StudiesPath $SyntheticStudy `
    -UseBrainTumorBundle `
    -DryRun

Write-Host ""
Write-Host "Setup check complete."
