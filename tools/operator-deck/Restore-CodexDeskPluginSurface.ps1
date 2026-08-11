[CmdletBinding()]
param(
    [switch]$NoRestart
)

$ErrorActionPreference = 'Stop'
$pluginRoot = 'A:\AI\Tools\EstateStreamDeckPlugin'
$knownGood = Join-Path $pluginRoot 'deploy-wp0535\com.estate.statusbridge.sdPlugin\bin'
$source = Join-Path $pluginRoot 'src'
$dist = Join-Path $pluginRoot 'dist\com.estate.statusbridge.sdPlugin'
$profilesRoot = Join-Path $env:APPDATA 'Elgato\StreamDeck\ProfilesV3'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = Join-Path $pluginRoot "backups\codex-desk-plugin-surface-$stamp"

New-Item -ItemType Directory -Force -Path $backup | Out-Null
foreach ($profile in @(
    'F40CBB56-817F-48C5-908F-A9E5F9EEC0A8.sdProfile',
    'D4ABFFCD-7BDE-4DB7-856B-B26823E1780B.sdProfile'
)) {
    $path = Join-Path $profilesRoot $profile
    if (Test-Path -LiteralPath $path) { Copy-Item -LiteralPath $path -Destination $backup -Recurse -Force }
}

Get-Process StreamDeck -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Keep the Codex gesture action registry from src; restore only the known-good
# status/rendering modules that were lost during the prior plugin reinstall.
foreach ($name in @('status.js', 'icon.js', 'config.js')) {
    Copy-Item -LiteralPath (Join-Path $knownGood $name) -Destination (Join-Path $source $name) -Force
}
New-Item -ItemType Directory -Force -Path (Join-Path $dist 'bin') | Out-Null
Copy-Item -LiteralPath (Join-Path $pluginRoot 'manifest.json') -Destination (Join-Path $dist 'manifest.json') -Force
Copy-Item -Path (Join-Path $source '*.js') -Destination (Join-Path $dist 'bin') -Force
Copy-Item -LiteralPath (Join-Path $pluginRoot 'bin\package.json') -Destination (Join-Path $dist 'bin\package.json') -Force
Copy-Item -LiteralPath (Join-Path $pluginRoot 'bin\EstateStatusBridge.cmd') -Destination (Join-Path $dist 'bin\EstateStatusBridge.cmd') -Force

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $pluginRoot 'install.ps1') | Out-Host
if (-not $NoRestart) { Start-Process 'C:\Program Files\Elgato\StreamDeck\StreamDeck.exe' }
Write-Output "Plugin surface restored; profile backup: $backup"
