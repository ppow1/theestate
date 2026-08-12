param([switch]$OpenBrowser)
. (Join-Path $PSScriptRoot "Estate-Service-Lib.ps1")
$canonicalOpenWebUiPreflight = "A:\theestate\tools\start_openwebui_canonical.ps1"
if (-not (Test-Path -LiteralPath $canonicalOpenWebUiPreflight -PathType Leaf)) {
    throw "Canonical Open WebUI preflight is missing: $canonicalOpenWebUiPreflight"
}
& $canonicalOpenWebUiPreflight -ValidateOnly | Out-Null
(Start-EstateCore -OpenBrowser:$OpenBrowser) | ConvertTo-Json -Depth 8
