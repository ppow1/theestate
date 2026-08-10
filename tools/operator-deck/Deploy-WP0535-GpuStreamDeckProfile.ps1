param(
    [string]$PluginRoot = 'A:\AI\Tools\EstateStreamDeckPlugin',
    [string]$ProfileRoot = (Join-Path $env:APPDATA 'Elgato\StreamDeck\ProfilesV3'),
    [string]$BackupRoot = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Utf8NoBom {
    param([string]$Path, [string]$Content)
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.UTF8Encoding]::new($false))
}

function Copy-Action {
    param($Action)
    if ($null -eq $Action) { return $null }
    return (ConvertFrom-Json (ConvertTo-Json $Action -Depth 40))
}

function Get-Action {
    param($Actions, [string]$Slot)
    $property = $Actions.PSObject.Properties[$Slot]
    if ($null -eq $property) { return $null }
    return $property.Value
}

function Remove-Action {
    param($Actions, [string]$Slot)
    $property = $Actions.PSObject.Properties[$Slot]
    if ($null -ne $property) { $Actions.PSObject.Properties.Remove($Slot) }
}

function Set-Action {
    param($Actions, [string]$Slot, $Action)
    $property = $Actions.PSObject.Properties[$Slot]
    if ($null -ne $property) { $property.Value = $Action }
    else { $Actions | Add-Member -NotePropertyName $Slot -NotePropertyValue $Action }
}

$profileManifest = Get-ChildItem -LiteralPath $ProfileRoot -Recurse -File -Filter 'manifest.json' |
    Where-Object {
        try { (Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json).Name -eq 'Estate Operations v0.5 Plugin' }
        catch { $false }
    } |
    Select-Object -First 1
if ($null -eq $profileManifest) { throw "Estate Operations v0.5 Plugin profile was not found under $ProfileRoot" }

$profile = Get-Content -LiteralPath $profileManifest.FullName -Raw | ConvertFrom-Json
$currentPage = [string]$profile.Pages.Current
$pageManifest = Join-Path $profileManifest.DirectoryName "Profiles\$currentPage\manifest.json"
if (-not (Test-Path -LiteralPath $pageManifest -PathType Leaf)) { throw "Current page manifest was not found: $pageManifest" }

$generated = Get-ChildItem -LiteralPath (Join-Path $PluginRoot 'deploy-wp0535\profile-src') -Recurse -File -Filter 'manifest.json' |
    Where-Object { $_.FullName -match '\\Profiles\\[^\\]+\.sdProfile\\Profiles\\[^\\]+\\manifest\.json$' } |
    Select-Object -First 1
if ($null -eq $generated) { throw 'Generated WP-0535 profile page manifest was not found.' }

$activePage = Get-Content -LiteralPath $pageManifest -Raw | ConvertFrom-Json
$generatedPage = Get-Content -LiteralPath $generated.FullName -Raw | ConvertFrom-Json
$actions = $activePage.Controllers[0].Actions
$generatedActions = $generatedPage.Controllers[0].Actions

$legacyBackup = Get-ChildItem -LiteralPath (Join-Path $PluginRoot 'backups') -Recurse -File -Filter 'active-page-manifest.json' |
    Where-Object { $_.FullName -match 'wp0535-gpu-profile-' } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
$legacyPage = if ($null -ne $legacyBackup) { Get-Content -LiteralPath $legacyBackup.FullName -Raw | ConvertFrom-Json } else { $null }
$legacyActions = if ($null -ne $legacyPage) { $legacyPage.Controllers[0].Actions } else { $null }

$cpu = Get-Action $actions '0,2'; if ($null -eq $cpu -or $cpu.UUID -ne 'com.ez.sho-metrics.cpu') { $cpu = Get-Action $actions '3,2' }
$ram = Get-Action $actions '0,3'; if ($null -eq $ram -or $ram.UUID -ne 'com.ez.sho-metrics.memory') { $ram = Get-Action $actions '3,3' }
$stop = Get-Action $actions '3,2'; if ($null -eq $stop -or $stop.UUID -ne 'com.estate.statusbridge.surfaces.stop') { $stop = Get-Action $actions '0,2' }
$restart = Get-Action $actions '4,2'; if ($null -eq $restart -or $restart.UUID -ne 'com.estate.statusbridge.surfaces.restart') { $restart = Get-Action $actions '1,2' }
$health = Get-Action $actions '5,2'; if ($null -eq $health -or $health.UUID -ne 'com.estate.statusbridge.health') { $health = Get-Action $actions '2,2' }
$voice = Get-Action $actions '6,2'; if ($null -eq $voice -or $voice.UUID -ne 'com.estate.statusbridge.operator_deck.dictation') { $voice = Get-Action $legacyActions '6,2' }
$profileReverse = Get-Action $actions '7,2'; if ($null -eq $profileReverse -or $profileReverse.UUID -ne 'com.elgato.streamdeck.profile.rotate') { $profileReverse = Get-Action $legacyActions '7,2' }
$gpu1 = Get-Action $generatedActions '1,2'
$gpu2 = Get-Action $generatedActions '1,3'

foreach ($item in @(@{n='CPU';v=$cpu},@{n='RAM';v=$ram},@{n='CORE STOP';v=$stop},@{n='CORE RESTART';v=$restart},@{n='CORE HEALTH';v=$health},@{n='VOICE';v=$voice},@{n='PROFILE';v=$profileReverse},@{n='GPU1';v=$gpu1},@{n='GPU2';v=$gpu2})) {
    if ($null -eq $item.v) { throw "Required action is unavailable: $($item.n)" }
}
if ($gpu1.UUID -ne 'com.estate.statusbridge.gpu.gpu1' -or $gpu2.UUID -ne 'com.estate.statusbridge.gpu.gpu2') { throw 'Generated GPU actions do not match the expected identities.' }

if ([string]::IsNullOrWhiteSpace($BackupRoot)) { $BackupRoot = Join-Path $PluginRoot ('backups\wp0535-gpu-layout-' + (Get-Date -Format 'yyyyMMdd-HHmmss')) }
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
Copy-Item -LiteralPath $pageManifest -Destination (Join-Path $BackupRoot 'active-page-manifest.json') -Force

foreach ($slot in @('0,2','1,2','2,2','3,2','4,2','5,2','6,2','7,2','0,3','1,3','2,3','3,3')) { Remove-Action $actions $slot }
Set-Action $actions '0,2' (Copy-Action $cpu)
Set-Action $actions '1,2' (Copy-Action $gpu1)
Set-Action $actions '3,2' (Copy-Action $stop)
Set-Action $actions '4,2' (Copy-Action $restart)
Set-Action $actions '5,2' (Copy-Action $health)
Set-Action $actions '6,2' (Copy-Action $voice)
Set-Action $actions '7,2' (Copy-Action $profileReverse)
Set-Action $actions '0,3' (Copy-Action $ram)
Set-Action $actions '1,3' (Copy-Action $gpu2)

$tempManifest = "$pageManifest.wp0535.tmp"
Write-Utf8NoBom -Path $tempManifest -Content ($activePage | ConvertTo-Json -Depth 40)
Move-Item -LiteralPath $tempManifest -Destination $pageManifest -Force
Get-Process StreamDeck -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3
Start-Process 'C:\Program Files\Elgato\StreamDeck\StreamDeck.exe' | Out-Null

[pscustomobject]@{ Profile = $profileManifest.FullName; Page = $pageManifest; Backup = (Join-Path $BackupRoot 'active-page-manifest.json'); Mapping = 'CPU 0,2; GPU1 1,2; STOP 3,2; RESTART 4,2; HEALTH 5,2; VOICE 6,2; PROFILE 7,2; RAM 0,3; GPU2 1,3'; StreamDeckRestarted = $true }
