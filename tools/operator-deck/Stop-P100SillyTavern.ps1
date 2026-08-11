[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$serviceLib = "A:\AI\Tools\EstateStreamDeckMVP\Core\Estate-Service-Lib.ps1"
$stopLane = "A:\theestate\tools\Stop-P100BackgroundLane.ps1"

function Get-Owner([int]$port) {
    $connection = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $connection) { return $null }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($connection.OwningProcess)" -ErrorAction SilentlyContinue
    if (-not $process) { throw "Port $port is occupied by an uninspectable process." }
    return [pscustomobject]@{ port = $port; pid = [int]$process.ProcessId; name = $process.Name; executable = $process.ExecutablePath; commandLine = $process.CommandLine }
}
function Test-GovernedLane($owner) {
    return $owner -and $owner.name -ieq "llama-server.exe" -and $owner.executable -ieq "A:\AI\Tools\llama.cpp\cuda\llama-server.exe" -and
        $owner.commandLine.Contains("--port 18080") -and $owner.commandLine.Contains("qwen3-32b-vl-instruct-polaris-hi16-heretic-uncensored-q5_k_m.gguf") -and
        $owner.commandLine.Contains("mmproj-F16.gguf") -and $owner.commandLine.Contains("--gpu-layers 42")
}

. $serviceLib
$silly = Get-EstateService -ServiceId sillytavern
$sillyStatus = Get-EstateServiceRuntimeStatus -Service $silly
if ($sillyStatus.foreignPortProcesses.Count -gt 0) { throw "Refusing SILLY stop: port 8000 is owned by a foreign process." }
if ($sillyStatus.ownedPortProcesses.Count -gt 0 -or $sillyStatus.matchingProcesses.Count -gt 0) {
    [void](Stop-EstateServiceProcess -Service $silly -AllOwnedInstances)
}

$owner = Get-Owner 18080
if ($owner) {
    if (-not (Test-GovernedLane $owner)) { throw "Refusing P100 stop: port 18080 is owned by an unrecognized process." }
    & $stopLane -ProcessId $owner.pid
}
[pscustomobject]@{ action = "stop"; state = "OFF"; p100 = "OFF"; sillytavern = "OFF" } | ConvertTo-Json -Depth 6
