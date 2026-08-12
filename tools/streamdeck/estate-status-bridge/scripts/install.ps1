[CmdletBinding()]
param(
    [string]$BuildRoot = "A:\AI\Tools\EstateStreamDeckPlugin",
    [string]$PluginSource = "",
    [switch]$RestartStreamDeck
)

$ErrorActionPreference = "Stop"
$PluginId = "com.estate.statusbridge.sdPlugin"
$BuildRootFull = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($BuildRoot)
$Source = if ($PluginSource) { $PluginSource } else { Join-Path (Join-Path $BuildRootFull "dist") $PluginId }
$SourceFull = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Source)
$PluginsRoot = Join-Path $env:APPDATA "Elgato\StreamDeck\Plugins"
$Destination = Join-Path $PluginsRoot $PluginId
$InstallReport = Join-Path $BuildRootFull "INSTALL_REPORT.md"

if (-not (Test-Path -LiteralPath $SourceFull)) {
    throw "Plugin source not found: $SourceFull"
}
if (-not (Test-Path -LiteralPath (Join-Path $SourceFull "manifest.json"))) {
    throw "Plugin source does not contain manifest.json: $SourceFull"
}

New-Item -ItemType Directory -Path $PluginsRoot -Force | Out-Null
if (Test-Path -LiteralPath $Destination) {
    if ((Split-Path -Leaf $Destination) -ne $PluginId) {
        throw "Refusing to remove unexpected plugin path: $Destination"
    }
    Remove-Item -LiteralPath $Destination -Recurse -Force
}
Copy-Item -LiteralPath $SourceFull -Destination $Destination -Recurse -Force

$Manifest = Get-Content -Raw -LiteralPath (Join-Path $Destination "manifest.json") | ConvertFrom-Json
$Hash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Destination "manifest.json")).Hash

@(
    "# Estate Status Bridge Install Report"
    ""
    "Generated: $(Get-Date -Format o)"
    "Source: $SourceFull"
    "Installed plugin path: $Destination"
    "Manifest SHA-256: $Hash"
    "Actions exposed: $($Manifest.Actions.Count)"
    "Stream Deck restart requested: $([bool]$RestartStreamDeck)"
    ""
    "The installer copies only $PluginId."
) | Set-Content -LiteralPath $InstallReport -Encoding UTF8

if ($RestartStreamDeck) {
    Write-Warning "Automatic Stream Deck restart is intentionally not performed by this installer. Restart manually after confirming profile backup state."
}

Write-Output ([pscustomobject]@{
    InstalledPluginPath = $Destination
    Actions = $Manifest.Actions.Count
    ManifestSha256 = $Hash
    InstallReport = $InstallReport
})


