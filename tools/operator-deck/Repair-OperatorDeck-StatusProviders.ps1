[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$PluginSourceRoot = 'A:\AI\Tools\EstateStreamDeckPlugin',
    [string]$InstalledPluginRoot = (Join-Path $env:APPDATA 'Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin')
)

$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { Write-Error 'Windows is required.'; exit 2 }

$sourceStatus = Join-Path $PluginSourceRoot 'src\status.js'
$installedStatus = Join-Path $InstalledPluginRoot 'bin\status.js'
$installedBin = Join-Path $InstalledPluginRoot 'bin'

function Assert-File([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing: $Path" }
}

function Get-Sha256([string]$Path) {
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Restore-Providers([string]$Text) {
    $anchor = 'export async function getActionStatus(action, config) {'
    if (-not $Text.Contains($anchor)) { throw 'getActionStatus insertion anchor is missing.' }

    if (-not $Text.Contains('export async function getOperatorDeckControlStatus(action, config) {')) {
        $controlProvider = @'
export async function getOperatorDeckControlStatus(action, config) {
  if (action.operation === "undo") {
    return statusResult({ value: "UNDO", color: "blue", detail: "Restore the most recent Operator Deck move or swap." });
  }
  if (action.operation === "selectActive") {
    return statusResult({ value: "SELECT", color: "blue", detail: "Arm the currently active window for placement." });
  }
  try {
    const { state, statePath } = await getCachedOperatorDeckState(config);
    const armed = Boolean(state?.selection?.armed && state?.selection?.valid);
    return statusResult({ value: armed ? "CANCEL" : "CLEAR", color: armed ? "yellow" : "off", detail: armed ? "Cancel the armed window selection." : "No window selection is armed.", source: statePath });
  } catch (error) {
    return statusResult({ value: "ERR", color: "red", detail: error.stderr || error.message });
  }
}

'@
        $Text = $Text.Replace($anchor, $controlProvider + $anchor)
    }

    if (-not $Text.Contains('export async function getOperatorDeckPlacementStatus(action, config) {')) {
        $placementProvider = @'
export async function getOperatorDeckPlacementStatus(action, config) {
  try {
    const { state, statePath } = await getCachedOperatorDeckState(config);
    const placement = state?.placement || {};
    const promotion = state?.promotion || {};
    if (action.placementType === "return") {
      const available = Boolean(promotion.available && promotion.valid);
      return statusResult({ value: available ? "RETURN" : "EMPTY", color: available ? "green" : "off", detail: available ? "Return the promoted window to its original rectangle." : "No promoted window is available.", source: statePath });
    }
    if (action.placementType === "monitor") {
      const selected = placement.monitor === action.placementValue;
      const hasShape = Boolean(placement.shape);
      return statusResult({ value: selected ? "ARMED" : (hasShape ? "PLACE" : action.label), color: selected ? "yellow" : (hasShape ? "blue" : "off"), detail: hasShape ? `Place the selected window on ${action.placementValue} using ${placement.shape}.` : `Place the selected window full-screen on ${action.placementValue}.`, source: statePath });
    }
    const selected = placement.shape === action.placementValue;
    const hasMonitor = Boolean(placement.monitor);
    return statusResult({ value: selected ? "ARMED" : (hasMonitor ? "PLACE" : action.label), color: selected ? "yellow" : (hasMonitor ? "blue" : "off"), detail: hasMonitor ? `Place the selected window on ${placement.monitor} using ${action.placementValue}.` : `Arm the ${action.placementValue} destination shape.`, source: statePath });
  } catch (error) {
    return statusResult({ value: "ERR", color: "red", detail: error.stderr || error.message });
  }
}

'@
        $Text = $Text.Replace($anchor, $placementProvider + $anchor)
    }

    return $Text
}

function Test-StatusModule([string]$CandidatePath) {
    $text = Get-Content -LiteralPath $CandidatePath -Raw
    foreach ($required in @(
        'export async function getOperatorDeckSlotStatus',
        'export async function getOperatorDeckControlStatus',
        'export async function getOperatorDeckPlacementStatus',
        'export async function getActionStatus'
    )) {
        $count = ([regex]::Matches($text, [regex]::Escape($required))).Count
        if ($count -ne 1) { throw "Expected one '$required'; found $count." }
    }

    foreach ($routing in @(
        'case "operatorDeckSlot":',
        'case "operatorDeckControl":',
        'case "operatorDeckPlacement":'
    )) {
        if (-not $text.Contains($routing)) { throw "Missing routing case: $routing" }
    }

    $node = Get-Command node.exe -ErrorAction Stop
    & $node.Source --check $CandidatePath
    if ($LASTEXITCODE -ne 0) { throw 'Node syntax validation failed.' }

    $probe = @'
const { pathToFileURL } = await import("node:url");
const candidate = await import(pathToFileURL(process.argv[1]).href + "?validation=" + Date.now());
for (const name of [
  "getOperatorDeckSlotStatus",
  "getOperatorDeckControlStatus",
  "getOperatorDeckPlacementStatus",
  "getActionStatus"
]) {
  if (typeof candidate[name] !== "function") throw new Error("Missing export: " + name);
}
const undo = await candidate.getOperatorDeckControlStatus({ operation: "undo" }, {});
if (undo?.value !== "UNDO") throw new Error("UNDO provider smoke test failed.");
const select = await candidate.getOperatorDeckControlStatus({ operation: "selectActive" }, {});
if (select?.value !== "SELECT") throw new Error("SELECT provider smoke test failed.");
'@
    & $node.Source --input-type=module --eval $probe $CandidatePath
    if ($LASTEXITCODE -ne 0) { throw 'Node ESM provider validation failed.' }
}

$temp = Join-Path $env:TEMP ('operator-deck-provider-repair-' + [guid]::NewGuid().ToString('N'))
$backup = $null

try {
    Assert-File $sourceStatus
    Assert-File $installedStatus
    if ((Get-Sha256 $sourceStatus) -ne (Get-Sha256 $installedStatus)) {
        throw 'Source and installed status.js differ; nothing was changed.'
    }

    New-Item -ItemType Directory -Path $temp -Force | Out-Null
    $tempBin = Join-Path $temp 'bin'
    Copy-Item -LiteralPath $installedBin -Destination $tempBin -Recurse -Force
    $candidateStatus = Join-Path $tempBin 'status.js'

    $candidate = Restore-Providers -Text (Get-Content -LiteralPath $sourceStatus -Raw)
    $candidate | Set-Content -LiteralPath $candidateStatus -Encoding utf8
    Test-StatusModule -CandidatePath $candidateStatus

    if (-not $Apply) {
        @(
            'OPERATOR DECK STATUS PROVIDER REPAIR PREFLIGHT: PASS'
            'Quadrant provider: preserved'
            'Control provider: restored and smoke-tested'
            'Placement provider: restored'
            'getActionStatus routing: preserved'
            'No files were changed. Re-run with -Apply only after reviewing this result.'
        ) -join "`n" | Tee-Object -Variable report
        $report | Set-Clipboard
        exit 0
    }

    $backup = Join-Path $PluginSourceRoot ('backups\operator-deck-provider-repair-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    New-Item -ItemType Directory -Path $backup -Force | Out-Null
    Copy-Item -LiteralPath $sourceStatus -Destination (Join-Path $backup 'sourceStatus.js')
    Copy-Item -LiteralPath $installedStatus -Destination (Join-Path $backup 'installedStatus.js')

    Copy-Item -LiteralPath $candidateStatus -Destination $sourceStatus -Force
    Copy-Item -LiteralPath $candidateStatus -Destination $installedStatus -Force

    if ((Get-Sha256 $sourceStatus) -ne (Get-Sha256 $installedStatus)) {
        throw 'Source and installed repaired status.js do not match.'
    }
    Test-StatusModule -CandidatePath $installedStatus

    @(
        'OPERATOR DECK STATUS PROVIDER REPAIR: VALIDATED'
        "Backup: $backup"
        'Quadrant, control, placement, and action-router exports validated.'
        'UNDO and SELECT provider smoke tests passed.'
        'Node syntax and ESM validation passed.'
        'Stream Deck was not restarted automatically.'
    ) -join "`n" | Tee-Object -Variable report
    $report | Set-Clipboard
} catch {
    if ($backup -and (Test-Path -LiteralPath $backup)) {
        $savedSource = Join-Path $backup 'sourceStatus.js'
        $savedInstalled = Join-Path $backup 'installedStatus.js'
        if (Test-Path -LiteralPath $savedSource) { Copy-Item -LiteralPath $savedSource -Destination $sourceStatus -Force }
        if (Test-Path -LiteralPath $savedInstalled) { Copy-Item -LiteralPath $savedInstalled -Destination $installedStatus -Force }
    }
    Write-Error "Operator Deck status provider repair failed: $($_.Exception.Message)"
    exit 1
} finally {
    if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
}
