[CmdletBinding()]
param([switch]$OpenBrowser)

$ErrorActionPreference = "Stop"
$root = "A:\theestate"
$config = Join-Path $root "config\local_ai\p100_background_lane.json"
$startLane = Join-Path $root "tools\Start-P100BackgroundLane.ps1"
$serviceLib = "A:\AI\Tools\EstateStreamDeckMVP\Core\Estate-Service-Lib.ps1"
$env:PYTHONPATH = "A:\theestate\src"
Push-Location $root
try {

function Get-Owner([int]$port) {
    $connection = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $connection) { return $null }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($connection.OwningProcess)" -ErrorAction SilentlyContinue
    if (-not $process) { throw "Port $port is occupied by an uninspectable process." }
    return [pscustomobject]@{ port = $port; pid = [int]$process.ProcessId; name = $process.Name; executable = $process.ExecutablePath; commandLine = $process.CommandLine }
}

function Test-GovernedLane($owner) {
    if (-not $owner) { return $false }
    $backend = "A:\AI\Tools\llama.cpp\cuda\llama-server.exe"
    $model = "A:\AI\Models\GGUF\qwen3-32b-vl-instruct-polaris-hi16-heretic-uncensored-q5_k_m.gguf"
    $mmproj = "A:\AI\Models\MMProj\mmproj-F16.gguf"
    return $owner.name -ieq "llama-server.exe" -and $owner.executable -ieq $backend -and
        $owner.commandLine.Contains($model) -and $owner.commandLine.Contains($mmproj) -and
        $owner.commandLine.Contains("--port 18080") -and $owner.commandLine.Contains("--gpu-layers 42") -and
        $owner.commandLine.Contains("--ctx-size 4096") -and $owner.commandLine.Contains("--no-mmproj-offload")
}

function Get-Json([string]$url) {
    try { return Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 4 -ErrorAction Stop } catch { return $null }
}

$plan = & python -m estate.cli.main p100-lane-plan --config $config --json 2>&1
if ($LASTEXITCODE -ne 0) { throw "P100 preflight failed: $($plan -join ' ')" }
$preflight = $plan | ConvertFrom-Json
if (-not $preflight.ready -or -not $preflight.no_fallback -or $preflight.target.physical_uuid -ne "GPU-6785b322-899d-8eec-e817-31d83279a414") {
    throw "P100 preflight did not authorize the physical Tesla P100 lane."
}

$owner = Get-Owner 18080
if ($owner -and -not (Test-GovernedLane $owner)) {
    throw "Refusing SILLY start: port 18080 is owned by an unrecognized process (PID $($owner.pid), $($owner.name))."
}

$models = if ($owner) { Get-Json "http://127.0.0.1:18080/v1/models" } else { $null }
$ready = $models -and @($models.models)[0].capabilities -contains "multimodal"
if ($owner -and -not $ready) { throw "Recognized P100 lane process is active but multimodal endpoint readiness failed." }
if (-not $owner) {
    & $startLane -Config $config
    $deadline = (Get-Date).AddSeconds(150)
    do {
        Start-Sleep -Seconds 2
        $owner = Get-Owner 18080
        $models = if ($owner -and (Test-GovernedLane $owner)) { Get-Json "http://127.0.0.1:18080/v1/models" } else { $null }
        $ready = $models -and @($models.models)[0].capabilities -contains "multimodal"
    } while (-not $ready -and (Get-Date) -lt $deadline)
    if (-not $ready) { throw "P100 multimodal endpoint did not become ready." }
}

. $serviceLib
$silly = Get-EstateService -ServiceId sillytavern
$sillyStatus = Get-EstateServiceRuntimeStatus -Service $silly
if ($sillyStatus.foreignPortProcesses.Count -gt 0) { throw "Refusing SILLY start: port 8000 is owned by a foreign process." }
if (-not $sillyStatus.healthy) { [void](Start-EstateServiceProcess -Service $silly) }
if ($OpenBrowser) { Start-Process "http://127.0.0.1:8000/" }

[pscustomobject]@{ action = if ($OpenBrowser) { "start_and_open" } else { "start" }; state = "READY"; p100 = "READY"; sillytavern = "READY"; endpoint = "http://127.0.0.1:18080" } | ConvertTo-Json -Depth 6
} finally { Pop-Location }
