$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$MonaiPython = ".monai-venv\Scripts\python.exe"
if (-not (Test-Path $MonaiPython)) {
    throw "Missing .monai-venv. Run scripts\setup_monai.ps1 first."
}

$Prefix = & $MonaiPython -c "import pathlib, sysconfig; root = pathlib.Path(sysconfig.get_paths()['purelib']); matches = list(root.glob('monailabel-*.data/data')); print(matches[0] if matches else pathlib.Path(''))"
if (-not $Prefix -or -not (Test-Path $Prefix)) {
    throw "Could not locate MONAI Label bundled sample-apps prefix."
}

& $MonaiPython -m monailabel.main apps --download --name radiology --output monai_app --prefix $Prefix
if ($LASTEXITCODE -ne 0) {
    throw "MONAI radiology app download failed."
}

Write-Host ""
Write-Host "MONAI radiology app downloaded under monai_app\radiology"
