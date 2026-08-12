[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$SourceRoot = (Join-Path $PSScriptRoot "Core"),
    [string]$TargetRoot = "A:\AI\Tools\EstateStreamDeckMVP\Core"
)

$ErrorActionPreference = "Stop"
$files = @(
    "Estate-Service-Lib.ps1",
    "Estate-Service-Config.ps1",
    "Get-EstateServiceStatus.ps1",
    "Start-EstateCore.ps1",
    "Start-OpenWebUI.ps1",
    "Start-ResidentGateway.ps1",
    "Stop-EstateCore.ps1",
    "Restart-EstateCore.ps1"
)

if (-not (Test-Path -LiteralPath $TargetRoot)) {
    throw "Target Estate MVP Core directory is unavailable: $TargetRoot"
}

foreach ($name in $files) {
    $source = Join-Path $SourceRoot $name
    $target = Join-Path $TargetRoot $name
    if (-not (Test-Path -LiteralPath $source)) { throw "Canonical runtime source is missing: $source" }
    if ($PSCmdlet.ShouldProcess($target, "Deploy canonical Estate service runtime file")) {
        Copy-Item -LiteralPath $source -Destination $target -Force
    }
}

Write-Output ([pscustomobject]@{ SourceRoot = $SourceRoot; TargetRoot = $TargetRoot; Files = $files })
