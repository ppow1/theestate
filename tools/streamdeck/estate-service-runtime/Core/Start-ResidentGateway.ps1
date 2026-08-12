. (Join-Path $PSScriptRoot "Estate-Service-Lib.ps1")
$result = Start-EstateServiceProcess -Service (Get-EstateService -ServiceId "resident_gateway")
$result | ConvertTo-Json -Depth 8
