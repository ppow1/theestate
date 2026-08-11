param([int]$ProcessId)
$ErrorActionPreference = "Stop"
if ($ProcessId -le 0) { throw "Provide the exact llama-server lane PID with -ProcessId." }
$process = Get-Process -Id $ProcessId -ErrorAction Stop
if ($process.Path -and ((Resolve-Path $process.Path).Path -ne (Resolve-Path "A:\AI\Tools\llama.cpp\cuda\llama-server.exe").Path)) {
    throw "Refusing to stop PID $ProcessId because it is not llama-server.exe."
}
Stop-Process -Id $ProcessId -ErrorAction Stop
Write-Output "Stopped P100 lane PID $ProcessId."
