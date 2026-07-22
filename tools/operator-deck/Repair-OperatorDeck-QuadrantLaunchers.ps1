[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$PluginSourceRoot = 'A:\AI\Tools\EstateStreamDeckPlugin',
    [string]$InstalledPluginRoot = (Join-Path $env:APPDATA 'Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin'),
    [string]$CommandRoot = 'A:\AI\Tools\EstateStreamDeckMVP\OperatorDeck\Slots'
)

$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    Write-Error 'Repair-OperatorDeck-QuadrantLaunchers.ps1 requires Windows.'
    exit 2
}

$slotNames = @(
    'M1_TOP_LEFT', 'M1_TOP_RIGHT', 'M1_BOTTOM_LEFT', 'M1_BOTTOM_RIGHT',
    'M2_TOP_LEFT', 'M2_TOP_RIGHT', 'M2_BOTTOM_LEFT', 'M2_BOTTOM_RIGHT',
    'M3_TOP_LEFT', 'M3_TOP_RIGHT', 'M3_BOTTOM_LEFT', 'M3_BOTTOM_RIGHT',
    'M4_TOP_LEFT', 'M4_TOP_RIGHT', 'M4_BOTTOM_LEFT', 'M4_BOTTOM_RIGHT'
)

$sourceActions = Join-Path $PluginSourceRoot 'src\actions.js'
$installedActions = Join-Path $InstalledPluginRoot 'bin\actions.js'
$sourceManifest = Join-Path $PluginSourceRoot 'manifest.json'
$installedManifest = Join-Path $InstalledPluginRoot 'manifest.json'

function Assert-File([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required file not found: $Path" }
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Get-JsPath([string]$Slot, [string]$Extension) {
    return $CommandRoot.Replace('\', '\\') + '\\' + $Slot + $Extension
}

function Convert-LauncherPaths([string]$Text) {
    foreach ($slot in $slotNames) {
        $cmdPath = Get-JsPath $slot '.cmd'
        $vbsPath = Get-JsPath $slot '.vbs'
        if ($Text.Contains($cmdPath)) {
            $Text = $Text.Replace($cmdPath, $vbsPath)
        } elseif (-not $Text.Contains($vbsPath)) {
            throw "Quadrant launcher path not found for $slot."
        }
    }
    return $Text
}

function Write-HiddenLaunchers {
    New-Item -ItemType Directory -Path $CommandRoot -Force | Out-Null
    foreach ($slot in $slotNames) {
        $content = @"
Set shell = CreateObject("WScript.Shell")
shell.Run """A:\theestate\tools\operator-deck\OperatorDeck.ahk"" slot $slot", 0, False
"@
        $content | Set-Content -LiteralPath (Join-Path $CommandRoot ($slot + '.vbs')) -Encoding ascii
    }
}

function Assert-Baseline {
    foreach ($path in @($sourceActions, $installedActions, $sourceManifest, $installedManifest)) { Assert-File $path }
    if ((Get-Sha256 $sourceActions) -ne (Get-Sha256 $installedActions)) { throw 'Source and installed actions.js differ.' }
    if ((Get-Sha256 $sourceManifest) -ne (Get-Sha256 $installedManifest)) { throw 'Source and installed manifests differ.' }
    $manifest = Get-Content -LiteralPath $sourceManifest -Raw | ConvertFrom-Json
    if ($manifest.Actions.Count -ne 35) { throw "Expected the installed 35-action baseline; found $($manifest.Actions.Count)." }
    foreach ($slot in $slotNames) {
        $uuid = 'com.estate.statusbridge.operator_deck.slot.' + $slot.ToLowerInvariant()
        if (@($manifest.Actions | Where-Object UUID -eq $uuid).Count -ne 1) { throw "Missing or duplicated quadrant UUID: $uuid" }
    }
}

function Test-Candidate([string]$Path) {
    $text = Get-Content -LiteralPath $Path -Raw
    foreach ($slot in $slotNames) {
        if (-not $text.Contains((Get-JsPath $slot '.vbs'))) { throw "Hidden launcher path missing for $slot." }
        if ($text.Contains((Get-JsPath $slot '.cmd'))) { throw "Console launcher path remains for $slot." }
    }
    $node = Get-Command node.exe -ErrorAction Stop
    & $node.Source --check $Path
    if ($LASTEXITCODE -ne 0) { throw "Node syntax validation failed: $Path" }
}

$temporaryRoot = Join-Path $env:TEMP ('operator-deck-launcher-repair-' + [guid]::NewGuid().ToString('N'))
$backupRoot = $null
$commandRootExisted = Test-Path -LiteralPath $CommandRoot

try {
    Assert-Baseline
    New-Item -ItemType Directory -Path $temporaryRoot -Force | Out-Null
    $candidate = Join-Path $temporaryRoot 'actions.js'
    Convert-LauncherPaths (Get-Content -LiteralPath $sourceActions -Raw) | Set-Content -LiteralPath $candidate -Encoding utf8
    Test-Candidate $candidate

    $actionsText = Get-Content -LiteralPath $sourceActions -Raw
    $alreadyRepaired = @($slotNames | Where-Object { $actionsText.Contains((Get-JsPath $_ '.vbs')) }).Count -eq 16
    if (-not $Apply) {
        $report = @(
            'OPERATOR DECK QUADRANT LAUNCHER REPAIR PREFLIGHT: PASS'
            "Already repaired: $alreadyRepaired"
            'Candidate uses 16 hidden VBS launchers; no quadrant CMD launcher paths remain.'
            'Source and installed baselines match; candidate Node validation passed.'
            'No files were changed. Re-run with -Apply only after reviewing this result.'
        ) -join "`n"
        $report | Write-Output
        $report | Set-Clipboard
        exit 0
    }

    $backupRoot = Join-Path $PluginSourceRoot ('backups\operator-deck-launchers-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    Copy-Item -LiteralPath $sourceActions -Destination (Join-Path $backupRoot 'sourceActions.js')
    Copy-Item -LiteralPath $installedActions -Destination (Join-Path $backupRoot 'installedActions.js')
    if ($commandRootExisted) { Copy-Item -LiteralPath $CommandRoot -Destination (Join-Path $backupRoot 'Slots') -Recurse }

    Copy-Item -LiteralPath $candidate -Destination $sourceActions -Force
    Copy-Item -LiteralPath $candidate -Destination $installedActions -Force
    Write-HiddenLaunchers

    Assert-Baseline
    Test-Candidate $sourceActions
    foreach ($slot in $slotNames) { Assert-File (Join-Path $CommandRoot ($slot + '.vbs')) }

    $report = @(
        'OPERATOR DECK QUADRANT LAUNCHER REPAIR: VALIDATED'
        "Backup: $backupRoot"
        'Quadrant launchers: 16 hidden VBS adapters'
        'Source and installed actions.js match; Node validation passed.'
        'Stream Deck was not restarted automatically.'
    ) -join "`n"
    $report | Write-Output
    $report | Set-Clipboard
} catch {
    if ($backupRoot -and (Test-Path -LiteralPath $backupRoot)) {
        Copy-Item -LiteralPath (Join-Path $backupRoot 'sourceActions.js') -Destination $sourceActions -Force
        Copy-Item -LiteralPath (Join-Path $backupRoot 'installedActions.js') -Destination $installedActions -Force
        if (Test-Path -LiteralPath $CommandRoot) { Remove-Item -LiteralPath $CommandRoot -Recurse -Force }
        $slotBackup = Join-Path $backupRoot 'Slots'
        if ($commandRootExisted -and (Test-Path -LiteralPath $slotBackup)) { Copy-Item -LiteralPath $slotBackup -Destination $CommandRoot -Recurse }
    }
    Write-Error "Operator Deck quadrant launcher repair failed: $($_.Exception.Message)"
    exit 1
} finally {
    if (Test-Path -LiteralPath $temporaryRoot) { Remove-Item -LiteralPath $temporaryRoot -Recurse -Force }
}
