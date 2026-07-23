CLS
[CmdletBinding()]
param(
    [ValidateSet("inspect", "prepare", "validate-profiles", "generate-front-tpose")]
    [string]$Command = "inspect",
    [string]$Root = "A:\theestate",
    [string]$Endpoint = "http://127.0.0.1:8188",
    [int]$SamplesPerProfile = 0
)

$ErrorActionPreference = "Stop"
$env:PYTHONPATH = Join-Path $Root "src"
$python = "python"
$argsList = @(
    "-m", "estate.visual_bible.evelyn_turnaround",
    "--root", $Root,
    "--endpoint", $Endpoint,
    $Command
)
if ($Command -eq "generate-front-tpose" -and $SamplesPerProfile -gt 0) {
    $argsList += @("--samples-per-profile", $SamplesPerProfile)
}

Write-Host "Evelyn turnaround pipeline: $Command"
& $python @argsList
exit $LASTEXITCODE
