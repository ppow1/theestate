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

$profileManifest = Get-ChildItem -LiteralPath $ProfileRoot -Recurse -File -Filter 'manifest.json' |
    Where-Object {
        try { (Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json).Name -eq 'Estate Operations v0.5 Plugin' }
        catch { $false }
    } |
    Select-Object -First 1

if ($null -eq $profileManifest) { throw "Active Estate Operations v0.5 Plugin profile was not found under $ProfileRoot" }
$profile = Get-Content -LiteralPath $profileManifest.FullName -Raw | ConvertFrom-Json
$currentPage = [string]$profile.Pages.Current
$pageManifest = Join-Path $profileManifest.DirectoryName "Profiles\$currentPage\manifest.json"
if (-not (Test-Path -LiteralPath $pageManifest -PathType Leaf)) { throw "Current Stream Deck page manifest was not found: $pageManifest" }

$generated = Get-ChildItem -LiteralPath (Join-Path $PluginRoot 'deploy-wp0535\profile-src') -Recurse -File -Filter 'manifest.json' |
    Where-Object { $_.FullName -match '\\Profiles\\[^\\]+\.sdProfile\\Profiles\\[^\\]+\\manifest\.json$' } |
    Select-Object -First 1
if ($null -eq $generated) { throw 'Generated WP-0535 profile page manifest was not found.' }

$activePage = Get-Content -LiteralPath $pageManifest -Raw | ConvertFrom-Json
$generatedPage = Get-Content -LiteralPath $generated.FullName -Raw | ConvertFrom-Json
$activeActions = $activePage.Controllers[0].Actions
$generatedActions = $generatedPage.Controllers[0].Actions

if ($activeActions.'6,2'.UUID -ne 'com.estate.statusbridge.operator_deck.dictation' -or
    $activeActions.'7,2'.UUID -ne 'com.elgato.streamdeck.profile.rotate') {
    throw 'Refusing to overwrite unexpected active Stream Deck controls at 6,2 or 7,2.'
}
if ($activeActions.'3,2'.UUID -ne 'com.ez.sho-metrics.cpu' -or
    $activeActions.'3,3'.UUID -ne 'com.ez.sho-metrics.memory') {
    throw 'Refusing to modify a profile whose CPU/RAM layout does not match the accepted Estate profile.'
}
if ($generatedActions.'6,2'.UUID -ne 'com.estate.statusbridge.gpu.gpu1' -or
    $generatedActions.'7,2'.UUID -ne 'com.estate.statusbridge.gpu.gpu2') {
    throw 'Generated profile does not contain the expected GPU1/GPU2 actions.'
}

if ([string]::IsNullOrWhiteSpace($BackupRoot)) {
    $BackupRoot = Join-Path $PluginRoot ('backups\wp0535-gpu-profile-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
}
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
Copy-Item -LiteralPath $pageManifest -Destination (Join-Path $BackupRoot 'active-page-manifest.json') -Force

$activeActions.'6,2' = $generatedActions.'6,2'
$activeActions.'7,2' = $generatedActions.'7,2'
$tempManifest = "$pageManifest.wp0535.tmp"
Write-Utf8NoBom -Path $tempManifest -Content ($activePage | ConvertTo-Json -Depth 40)
Move-Item -LiteralPath $tempManifest -Destination $pageManifest -Force

Get-Process StreamDeck -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3
Start-Process 'C:\Program Files\Elgato\StreamDeck\StreamDeck.exe' | Out-Null

[pscustomobject]@{
    Profile = $profileManifest.FullName
    Page = $pageManifest
    Backup = (Join-Path $BackupRoot 'active-page-manifest.json')
    GPU1 = '6,2'
    GPU2 = '7,2'
    StreamDeckRestarted = $true
}
