param(
    [Parameter(Mandatory=$true)][string]$WorkPackageId
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
Push-Location $RepoRoot
try {
    $env:PYTHONPATH = "src" + [IO.Path]::PathSeparator + $env:PYTHONPATH
    python -m estate.cli.main validate-work-package --id $WorkPackageId --json
} finally {
    Pop-Location
}
