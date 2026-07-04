Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "../../..")).Path
Push-Location $RepoRoot
try {
    python -m estate.cli.main validation-production-readiness --json
    Write-Host "Production readiness report: operations/validation/production_readiness_report.md"
    Write-Host "Production readiness JSON: runtime/validation/production_readiness_report.json"
    Write-Host "Coverage manifest: operations/validation/validation_coverage_manifest.md"
    Write-Host "Coverage manifest JSON: runtime/validation/validation_coverage_manifest.json"
}
finally {
    Pop-Location
}
