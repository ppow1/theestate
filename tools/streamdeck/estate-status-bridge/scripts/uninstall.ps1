[CmdletBinding()]
param(
    [string]$BuildRoot = "A:\AI\Tools\EstateStreamDeckPlugin"
)

$ErrorActionPreference = "Stop"
$PluginId = "com.estate.statusbridge.sdPlugin"
$BuildRootFull = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($BuildRoot)
$PluginsRoot = Join-Path $env:APPDATA "Elgato\StreamDeck\Plugins"
$Destination = Join-Path $PluginsRoot $PluginId
$UninstallReport = Join-Path $BuildRootFull "UNINSTALL_REPORT.md"

$Removed = $false
if (Test-Path -LiteralPath $Destination) {
    if ((Split-Path -Leaf $Destination) -ne $PluginId) {
        throw "Refusing to remove unexpected plugin path: $Destination"
    }
    Remove-Item -LiteralPath $Destination -Recurse -Force
    $Removed = $true
}

@(
    "# Estate Status Bridge Uninstall Report"
    ""
    "Generated: $(Get-Date -Format o)"
    "Target plugin path: $Destination"
    "Removed: $Removed"
    ""
    "The uninstaller removes only $PluginId."
) | Set-Content -LiteralPath $UninstallReport -Encoding UTF8

Write-Output ([pscustomobject]@{
    TargetPluginPath = $Destination
    Removed = $Removed
    UninstallReport = $UninstallReport
})


