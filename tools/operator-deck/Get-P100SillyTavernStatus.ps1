[CmdletBinding()]
param()
$ErrorActionPreference = "Stop"
$root = "A:\theestate"
$config = Join-Path $root "config\local_ai\p100_background_lane.json"
$env:PYTHONPATH = "A:\theestate\src"
Push-Location $root
$plan = & python -m estate.cli.main p100-lane-plan --config $config --json 2>&1
if ($LASTEXITCODE -ne 0) { [pscustomobject]@{ state = "ERR"; detail = "P100 preflight failed." } | ConvertTo-Json; exit 0 }
$preflight = $plan | ConvertFrom-Json
$models = $null
try { $models = Invoke-RestMethod http://127.0.0.1:18080/v1/models -TimeoutSec 3 -ErrorAction Stop } catch {}
$p100Ready = $preflight.ready -and $preflight.target.physical_uuid -eq "GPU-6785b322-899d-8eec-e817-31d83279a414" -and $models -and @($models.models)[0].capabilities -contains "multimodal"
. "A:\AI\Tools\EstateStreamDeckMVP\Core\Estate-Service-Lib.ps1"
$silly = Get-EstateServiceRuntimeStatus -Service (Get-EstateService -ServiceId sillytavern)
if ($p100Ready -and $silly.healthy) { [pscustomobject]@{ state = "READY"; detail = "P100 multimodal lane and SillyTavern are ready." } | ConvertTo-Json; exit 0 }
if (-not $p100Ready -and -not $silly.healthy) { [pscustomobject]@{ state = "OFF"; detail = "P100 multimodal lane and SillyTavern are stopped." } | ConvertTo-Json; exit 0 }
[pscustomobject]@{ state = "ERR"; detail = "P100 or SillyTavern is not ready." } | ConvertTo-Json
Pop-Location
