Exit code: 0
Wall time: 0.5 seconds
Output:
. (Join-Path $PSScriptRoot "Estate-Service-Lib.ps1")
$result = Start-EstateServiceProcess -Service (Get-EstateService -ServiceId "resident_gateway")
$result | ConvertTo-Json -Depth 8


