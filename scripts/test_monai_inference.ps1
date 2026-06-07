param(
    [string]$ServerUrl = "http://127.0.0.1:8000",
    [string]$ModelName = "brats_mri_segmentation",
    [string]$ImageId = "synthetic_brats_001",
    [string]$OutputDir = "reports/monai_smoke",
    [double]$TimeoutSec = 300
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$Python = ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

& $Python scripts\test_monai_inference.py `
    --server-url $ServerUrl `
    --model $ModelName `
    --image $ImageId `
    --output-dir $OutputDir `
    --timeout $TimeoutSec

if ($LASTEXITCODE -ne 0) {
    throw "MONAI inference smoke test failed."
}
