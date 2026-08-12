param([switch]$IncludeProvider)
. (Join-Path $PSScriptRoot "Estate-Service-Lib.ps1")
(Restart-EstateCore -IncludeProvider:$IncludeProvider) | ConvertTo-Json -Depth 8
