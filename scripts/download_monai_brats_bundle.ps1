param(
    [string]$RepoId = "MONAI/brats_mri_segmentation",
    [string]$Revision = "main",
    [string]$OutputPath = "monai_app/bundles/brats_mri_segmentation"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$MonaiPython = ".monai-venv\Scripts\python.exe"
if (-not (Test-Path $MonaiPython)) {
    throw "Missing .monai-venv. Run scripts\setup_monai.ps1 first."
}

& $MonaiPython -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('huggingface_hub') else 1)"
if ($LASTEXITCODE -ne 0) {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        throw "huggingface_hub is missing and uv is unavailable. Install uv or rerun scripts\setup_monai.ps1."
    }

    uv pip install --python $MonaiPython "huggingface_hub[hf_xet]>=1.17.0"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install huggingface_hub into .monai-venv."
    }
}

$ResolvedOutput = Join-Path $RepoRoot $OutputPath
New-Item -ItemType Directory -Path $ResolvedOutput -Force | Out-Null

& $MonaiPython -c "import sys; from huggingface_hub import snapshot_download; path = snapshot_download(repo_id=sys.argv[1], revision=sys.argv[2], local_dir=sys.argv[3]); print(path)" $RepoId $Revision $ResolvedOutput
if ($LASTEXITCODE -ne 0) {
    throw "Failed to download Hugging Face repo: $RepoId"
}

Write-Host ""
Write-Host "MONAI BraTS bundle installed at:"
Write-Host "  $ResolvedOutput"
