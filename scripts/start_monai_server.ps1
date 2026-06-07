param(
    [string]$StudiesPath = "datasets/Task01_BrainTumour/imagesTr",
    [string]$Model = "deepedit",
    [string]$Bundles = "",
    [switch]$UseBrainTumorBundle,
    [switch]$DryRun,
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

function Register-LocalBundle {
    param(
        [string]$BundleName,
        [string]$SourcePath,
        [string]$AppPath
    )

    if (-not (Test-Path $SourcePath)) {
        throw "Missing MONAI bundle: $SourcePath. Run scripts\download_monai_brats_bundle.ps1 first."
    }

    $ModelRoot = Join-Path $AppPath "model"
    $TargetPath = Join-Path $ModelRoot $BundleName
    New-Item -ItemType Directory -Path $ModelRoot -Force | Out-Null

    if (Test-Path $TargetPath) {
        return
    }

    try {
        New-Item -ItemType Junction -Path $TargetPath -Target (Resolve-Path $SourcePath).Path | Out-Null
    } catch {
        Copy-Item -Path $SourcePath -Destination $TargetPath -Recurse
    }
}

if ($UseBrainTumorBundle) {
    $BrainTumorBundleName = "brats_mri_segmentation"
    & $MonaiPython scripts\validate_brats_study.py --studies $StudiesPath
    if ($LASTEXITCODE -ne 0) {
        throw "BraTS study validation failed."
    }

    Register-LocalBundle `
        -BundleName $BrainTumorBundleName `
        -SourcePath "monai_app\bundles\$BrainTumorBundleName" `
        -AppPath $AppPath

    if ($Bundles) {
        $Bundles = "$Bundles,$BrainTumorBundleName"
    } else {
        $Bundles = $BrainTumorBundleName
    }
}

$Arguments = @(
    "-m", "monailabel.main", "start_server",
    "--app", $AppPath,
    "--studies", $StudiesPath,
    "--conf", "models", $Model,
    "--host", $HostAddress,
    "--port", $Port
)

if ($Bundles) {
    $Arguments += @("--conf", "bundles", $Bundles)
}

if ($DryRun) {
    $Arguments += @("--dryrun")
}

& $MonaiPython @Arguments
