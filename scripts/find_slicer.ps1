$ErrorActionPreference = "Stop"

$Candidates = @()

$PathHits = @()
$SlicerCommand = Get-Command Slicer -ErrorAction SilentlyContinue
if ($SlicerCommand) {
    $PathHits += $SlicerCommand.Source
}
foreach ($Hit in $PathHits) {
    if ($Hit -and (Test-Path $Hit)) {
        $Candidates += (Resolve-Path -LiteralPath $Hit).Path
    }
}

$Roots = @("C:\Program Files", "C:\Program Files (x86)", $env:LOCALAPPDATA, $env:APPDATA)
foreach ($Root in $Roots) {
    if (-not $Root -or -not (Test-Path $Root)) {
        continue
    }
    $Candidates += Get-ChildItem -Path $Root -Recurse -File -Filter Slicer.exe -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty FullName
}

$SlicerPath = $Candidates | Sort-Object -Unique | Select-Object -First 1
if (-not $SlicerPath) {
    throw "3D Slicer was not found. Install it from https://download.slicer.org/ and rerun this script."
}

Write-Output $SlicerPath
