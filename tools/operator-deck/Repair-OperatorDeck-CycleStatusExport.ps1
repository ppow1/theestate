[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$PluginSourceRoot = 'A:\AI\Tools\EstateStreamDeckPlugin',
    [string]$InstalledPluginRoot = (Join-Path $env:APPDATA 'Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin'),
    [string]$BackupRoot = 'A:\AI\Tools\EstateStreamDeckPlugin\backups\operator-deck-cycle-20260723-160500'
)

$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { Write-Error 'Windows is required.'; exit 2 }

$sourceStatus = Join-Path $PluginSourceRoot 'src\status.js'
$installedStatus = Join-Path $InstalledPluginRoot 'bin\status.js'
$backupSourceStatus = Join-Path $BackupRoot 'sourceStatus.js'
$installedBin = Join-Path $InstalledPluginRoot 'bin'

function Assert-File([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing: $Path" }
}

function Get-Sha256([string]$Path) {
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Set-QuadrantStatusProvider([string]$Text) {
    $startAnchor = 'export async function getOperatorDeckSlotStatus(action, config) {'
    $endAnchor = 'export async function getActionStatus(action, config) {'
    $start = $Text.IndexOf($startAnchor, [StringComparison]::Ordinal)
    $end = $Text.IndexOf($endAnchor, [StringComparison]::Ordinal)

    if ($start -lt 0) { throw 'The backup status module is missing getOperatorDeckSlotStatus.' }
    if ($end -lt 0) { throw 'The backup status module is missing getActionStatus.' }
    if ($end -le $start) { throw 'The status-provider anchors are out of order.' }
    if ($Text.IndexOf($startAnchor, $start + 1, [StringComparison]::Ordinal) -ge 0) {
        throw 'The backup contains more than one quadrant status provider.'
    }
    if ($Text.IndexOf($endAnchor, $end + 1, [StringComparison]::Ordinal) -ge 0) {
        throw 'The backup contains more than one getActionStatus export.'
    }

    $replacement = @'
export async function getOperatorDeckSlotStatus(action, config) {
  try {
    const { state, statePath } = await getCachedOperatorDeckState(config);
    const selection = state?.selection || {};
    const cycle = state?.cycle || {};
    if (!selection.armed || !selection.valid) {
      return statusResult({ value: "READY", color: "off", detail: `${action.name}: press to select the occupying window.`, source: statePath, raw: { selection, cycle } });
    }
    if (selection.source_slot === action.slot) {
      if (cycle.active && cycle.slot === action.slot) {
        return statusResult({ value: `${cycle.index}/${cycle.count}`, color: "yellow", detail: "Tap to cycle; hold to align the selected window in this quadrant.", source: statePath, raw: { selection, cycle } });
      }
      return statusResult({ value: "SELECT", color: "green", detail: "Tap again to align here; hold to enter window cycling.", source: statePath, raw: { selection, cycle } });
    }
    return statusResult({ value: "PLACE", color: "blue", detail: `Press to move the selected window to ${action.name}.`, source: statePath, raw: { selection, cycle } });
  } catch (error) {
    return statusResult({ value: "ERR", color: "red", detail: error.stderr || error.message });
  }
}

'@

    return $Text.Substring(0, $start) + $replacement + $Text.Substring($end)
}

function Test-StatusModule([string]$CandidatePath) {
    $text = Get-Content -LiteralPath $CandidatePath -Raw
    foreach ($required in @(
        'export async function getOperatorDeckSlotStatus',
        'export async function getActionStatus',
        'cycle.index',
        'cycle.count'
    )) {
        if (-not $text.Contains($required)) { throw "Candidate status module is missing: $required" }
    }

    $node = Get-Command node.exe -ErrorAction Stop
    & $node.Source --check $CandidatePath
    if ($LASTEXITCODE -ne 0) { throw 'Node syntax validation failed for repaired status.js.' }

    $probe = @'
const { pathToFileURL } = await import("node:url");
const modulePath = pathToFileURL(process.argv[1]).href + "?validation=" + Date.now();
const candidate = await import(modulePath);
for (const name of ["getOperatorDeckSlotStatus", "getActionStatus"]) {
  if (typeof candidate[name] !== "function") {
    throw new Error("Missing named function export: " + name);
  }
}
'@
    & $node.Source --input-type=module --eval $probe $CandidatePath
    if ($LASTEXITCODE -ne 0) { throw 'Node ESM import validation failed for repaired status.js.' }
}

$temp = Join-Path $env:TEMP ('operator-deck-status-repair-' + [guid]::NewGuid().ToString('N'))
$repairBackup = $null

try {
    foreach ($path in @($sourceStatus, $installedStatus, $backupSourceStatus)) { Assert-File $path }
    if ((Get-Sha256 $sourceStatus) -ne (Get-Sha256 $installedStatus)) {
        throw 'Source and installed status.js differ; nothing was changed.'
    }

    New-Item -ItemType Directory -Path $temp -Force | Out-Null
    $tempBin = Join-Path $temp 'bin'
    Copy-Item -LiteralPath $installedBin -Destination $tempBin -Recurse -Force
    $candidateStatus = Join-Path $tempBin 'status.js'

    $baseline = Get-Content -LiteralPath $backupSourceStatus -Raw
    $candidate = Set-QuadrantStatusProvider -Text $baseline
    $candidate | Set-Content -LiteralPath $candidateStatus -Encoding utf8
    Test-StatusModule -CandidatePath $candidateStatus

    if (-not $Apply) {
        @(
            'OPERATOR DECK CYCLE STATUS EXPORT REPAIR PREFLIGHT: PASS'
            'Observed defect: getActionStatus was removed from status.js.'
            'Recovery source: automatic pre-cycle backup.'
            'Named exports validated through the Node ESM loader.'
            'No files were changed. Re-run with -Apply only after reviewing this result.'
        ) -join "`n" | Tee-Object -Variable report
        $report | Set-Clipboard
        exit 0
    }

    $repairBackup = Join-Path $PluginSourceRoot ('backups\operator-deck-cycle-status-repair-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    New-Item -ItemType Directory -Path $repairBackup -Force | Out-Null
    Copy-Item -LiteralPath $sourceStatus -Destination (Join-Path $repairBackup 'sourceStatus.js')
    Copy-Item -LiteralPath $installedStatus -Destination (Join-Path $repairBackup 'installedStatus.js')

    Copy-Item -LiteralPath $candidateStatus -Destination $sourceStatus -Force
    Copy-Item -LiteralPath $candidateStatus -Destination $installedStatus -Force

    if ((Get-Sha256 $sourceStatus) -ne (Get-Sha256 $installedStatus)) {
        throw 'Source and installed repaired status.js do not match.'
    }
    Test-StatusModule -CandidatePath $installedStatus

    @(
        'OPERATOR DECK CYCLE STATUS EXPORT REPAIR: VALIDATED'
        "Backup: $repairBackup"
        'getOperatorDeckSlotStatus: exported'
        'getActionStatus: exported'
        'Node syntax and ESM import validation passed.'
        'Stream Deck was not restarted automatically.'
    ) -join "`n" | Tee-Object -Variable report
    $report | Set-Clipboard
} catch {
    if ($repairBackup -and (Test-Path -LiteralPath $repairBackup)) {
        $savedSource = Join-Path $repairBackup 'sourceStatus.js'
        $savedInstalled = Join-Path $repairBackup 'installedStatus.js'
        if (Test-Path -LiteralPath $savedSource) { Copy-Item -LiteralPath $savedSource -Destination $sourceStatus -Force }
        if (Test-Path -LiteralPath $savedInstalled) { Copy-Item -LiteralPath $savedInstalled -Destination $installedStatus -Force }
    }
    Write-Error "Operator Deck cycle status export repair failed: $($_.Exception.Message)"
    exit 1
} finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}
