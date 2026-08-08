$ErrorActionPreference = 'Stop'
$canonicalExe = 'A:\AI\OpenWebUI\.venv\Scripts\open-webui.exe'
$listener = Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    $ownerPid = $listener[0].OwningProcess
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$ownerPid"
    if (-not $process -or $process.CommandLine -notlike "*$canonicalExe*") {
        throw "Refusing to stop unexpected port 8080 owner PID $ownerPid."
    }
    Stop-Process -Id $ownerPid -Force
    $deadline = (Get-Date).AddSeconds(30)
    do {
        Start-Sleep -Milliseconds 250
        $stillListening = Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
    } while ($stillListening -and (Get-Date) -lt $deadline)
    if ($stillListening) { throw 'Canonical Open WebUI listener did not stop.' }
}
& "$PSScriptRoot\start_openwebui_canonical.ps1"
$deadline = (Get-Date).AddSeconds(60)
do {
    Start-Sleep -Seconds 1
    $ready = Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
} while (-not $ready -and (Get-Date) -lt $deadline)
if (-not $ready) { throw 'Canonical Open WebUI listener did not return.' }
Write-Output (@{status='RESTARTED'; pid=$ready[0].OwningProcess; executable=$canonicalExe} | ConvertTo-Json -Compress)
