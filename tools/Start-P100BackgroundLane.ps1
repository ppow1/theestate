param(
    [string]$Config = "A:\theestate\config\local_ai\p100_background_lane.json",
    [string]$Log = "A:\theestate\runtime\local_ai\p100_background_lane.log",
    [string]$ErrorLog = "A:\theestate\runtime\local_ai\p100_background_lane.error.log"
)
$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "A:\theestate\src"
$plan = python -m estate.cli.main p100-lane-plan --config $Config --json | ConvertFrom-Json
if (-not $plan.ready) { throw ("P100 lane refused to start: " + ($plan.errors -join "; ")) }
$args = @("-m", "estate.cli.main", "p100-lane-run", "--config", $Config)
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Log) | Out-Null
Start-Process -FilePath "python" -ArgumentList $args -WorkingDirectory "A:\theestate" -RedirectStandardOutput $Log -RedirectStandardError $ErrorLog -PassThru
