[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$PluginSourceRoot = 'A:\AI\Tools\EstateStreamDeckPlugin',
    [string]$InstalledPluginRoot = (Join-Path $env:APPDATA 'Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin')
)

$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    Write-Error 'Repair-OperatorDeck-SharedStatePolling.ps1 requires Windows.'
    exit 2
}

$sourceStatus = Join-Path $PluginSourceRoot 'src\status.js'
$installedStatus = Join-Path $InstalledPluginRoot 'bin\status.js'
$legacyMarker = 'await run("pwsh.exe", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", scriptPath, "-NoClipboard", "-Quiet"], { timeoutMs: config.commandTimeoutMs });'
$sharedMarker = 'const observation = await getCachedOperatorDeckState(config);'

function Assert-File([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required file not found: $Path" }
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Assert-Baseline {
    Assert-File $sourceStatus
    Assert-File $installedStatus
    if ((Get-Sha256 $sourceStatus) -ne (Get-Sha256 $installedStatus)) { throw 'Source and installed status.js differ.' }
    $text = Get-Content -LiteralPath $sourceStatus -Raw
    if (-not $text.Contains('getOperatorDeckDictationStatus')) { throw 'Voice Typing status provider is missing.' }
    if (-not $text.Contains('getCachedOperatorDeckState')) { throw 'Shared Operator Deck state cache is missing.' }
    $legacyCount = ([regex]::Matches($text, [regex]::Escape($legacyMarker))).Count
    $sharedCount = ([regex]::Matches($text, [regex]::Escape($sharedMarker))).Count
    if (($legacyCount -eq 2 -and $sharedCount -eq 0) -or ($legacyCount -eq 1 -and $sharedCount -eq 1)) { return }
    throw "Unexpected polling posture: direct publisher calls=$legacyCount, shared Voice Typing calls=$sharedCount."
}

function Convert-VoiceTypingPolling([string]$Text) {
    if ($Text.Contains($sharedMarker)) { return $Text }
    $pattern = '(?s)export async function getOperatorDeckDictationStatus\(config\) \{\s+const scriptPath.*?\s+try \{\s+await run\("pwsh\.exe".*?\);\s+const state = await readJson\(statePath\);'
    $replacement = @'
export async function getOperatorDeckDictationStatus(config) {
  let statePath = "";
  try {
    const observation = await getCachedOperatorDeckState(config);
    statePath = observation.statePath;
    const state = observation.state;
'@.TrimEnd()
    $matches = [regex]::Matches($Text, $pattern)
    if ($matches.Count -ne 1) { throw "Expected one Voice Typing polling block; found $($matches.Count)." }
    return [regex]::Replace($Text, $pattern, $replacement, 1)
}

function Test-Candidate([string]$Path) {
    $text = Get-Content -LiteralPath $Path -Raw
    if (-not $text.Contains($sharedMarker)) { throw 'Voice Typing does not use the shared state cache.' }
    if (([regex]::Matches($text, [regex]::Escape($legacyMarker))).Count -ne 1) { throw 'Expected exactly one publisher call owned by the shared cache.' }
    $node = Get-Command node.exe -ErrorAction Stop
    & $node.Source --check $Path
    if ($LASTEXITCODE -ne 0) { throw "Node syntax validation failed: $Path" }
}

$temporaryRoot = Join-Path $env:TEMP ('operator-deck-state-polling-' + [guid]::NewGuid().ToString('N'))
$backupRoot = $null

try {
    Assert-Baseline
    New-Item -ItemType Directory -Path $temporaryRoot -Force | Out-Null
    $candidate = Join-Path $temporaryRoot 'status.js'
    Convert-VoiceTypingPolling (Get-Content -LiteralPath $sourceStatus -Raw) | Set-Content -LiteralPath $candidate -Encoding utf8
    Test-Candidate $candidate

    $alreadyRepaired = (Get-Content -LiteralPath $sourceStatus -Raw).Contains($sharedMarker)
    if (-not $Apply) {
        $report = @(
            'OPERATOR DECK SHARED STATE POLLING PREFLIGHT: PASS'
            "Already repaired: $alreadyRepaired"
            'Voice Typing and quadrant actions share one cached state publication.'
            'Candidate contains one publisher call; Node validation passed.'
            'No files were changed. Re-run with -Apply only after reviewing this result.'
        ) -join "`n"
        $report | Write-Output
        $report | Set-Clipboard
        exit 0
    }

    $backupRoot = Join-Path $PluginSourceRoot ('backups\operator-deck-state-polling-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    Copy-Item -LiteralPath $sourceStatus -Destination (Join-Path $backupRoot 'source-status.js')
    Copy-Item -LiteralPath $installedStatus -Destination (Join-Path $backupRoot 'installed-status.js')

    Copy-Item -LiteralPath $candidate -Destination $sourceStatus -Force
    Copy-Item -LiteralPath $candidate -Destination $installedStatus -Force

    Assert-Baseline
    Test-Candidate $sourceStatus

    $report = @(
        'OPERATOR DECK SHARED STATE POLLING: VALIDATED'
        "Backup: $backupRoot"
        'Voice Typing and quadrant actions now share one cached state publication.'
        'Source and installed status.js match; Node validation passed.'
        'Stream Deck was not restarted automatically.'
    ) -join "`n"
    $report | Write-Output
    $report | Set-Clipboard
} catch {
    if ($backupRoot -and (Test-Path -LiteralPath $backupRoot)) {
        Copy-Item -LiteralPath (Join-Path $backupRoot 'source-status.js') -Destination $sourceStatus -Force
        Copy-Item -LiteralPath (Join-Path $backupRoot 'installed-status.js') -Destination $installedStatus -Force
    }
    Write-Error "Operator Deck shared state polling repair failed: $($_.Exception.Message)"
    exit 1
} finally {
    if (Test-Path -LiteralPath $temporaryRoot) { Remove-Item -LiteralPath $temporaryRoot -Recurse -Force }
}
