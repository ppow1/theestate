. (Join-Path $PSScriptRoot "Estate-Service-Lib.ps1")
$canonicalOpenWebUiPreflight = "A:\theestate\tools\start_openwebui_canonical.ps1"
if (-not (Test-Path -LiteralPath $canonicalOpenWebUiPreflight -PathType Leaf)) {
    throw "Canonical Open WebUI preflight is missing: $canonicalOpenWebUiPreflight"
}
& $canonicalOpenWebUiPreflight -ValidateOnly | Out-Null
$provider = Get-EstateServiceRuntimeStatus -Service (Get-EstateService -ServiceId "ollama")
$gateway = Get-EstateServiceRuntimeStatus -Service (Get-EstateService -ServiceId "resident_gateway")
if (-not $provider.healthy) { Write-Warning "Ollama/provider is unavailable." }
if (-not $gateway.healthy) { Write-Warning "Resident Gateway is unavailable." }
$result = Start-EstateServiceProcess -Service (Get-EstateService -ServiceId "open_webui")
$result | ConvertTo-Json -Depth 8
