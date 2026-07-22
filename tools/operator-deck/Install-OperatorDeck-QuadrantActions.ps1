[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$PluginSourceRoot = 'A:\AI\Tools\EstateStreamDeckPlugin',
    [string]$InstalledPluginRoot = (Join-Path $env:APPDATA 'Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin'),
    [string]$CommandRoot = 'A:\AI\Tools\EstateStreamDeckMVP\OperatorDeck\Slots'
)

$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    Write-Error 'Install-OperatorDeck-QuadrantActions.ps1 requires Windows.'
    exit 2
}

$slots = @(
    [ordered]@{ Name = 'M1_TOP_LEFT'; Label = 'M1 TL'; Display = 'M1 Top Left' },
    [ordered]@{ Name = 'M1_TOP_RIGHT'; Label = 'M1 TR'; Display = 'M1 Top Right' },
    [ordered]@{ Name = 'M1_BOTTOM_LEFT'; Label = 'M1 BL'; Display = 'M1 Bottom Left' },
    [ordered]@{ Name = 'M1_BOTTOM_RIGHT'; Label = 'M1 BR'; Display = 'M1 Bottom Right' },
    [ordered]@{ Name = 'M2_TOP_LEFT'; Label = 'M2 TL'; Display = 'M2 Top Left' },
    [ordered]@{ Name = 'M2_TOP_RIGHT'; Label = 'M2 TR'; Display = 'M2 Top Right' },
    [ordered]@{ Name = 'M2_BOTTOM_LEFT'; Label = 'M2 BL'; Display = 'M2 Bottom Left' },
    [ordered]@{ Name = 'M2_BOTTOM_RIGHT'; Label = 'M2 BR'; Display = 'M2 Bottom Right' },
    [ordered]@{ Name = 'M3_TOP_LEFT'; Label = 'M3 TL'; Display = 'M3 Top Left' },
    [ordered]@{ Name = 'M3_TOP_RIGHT'; Label = 'M3 TR'; Display = 'M3 Top Right' },
    [ordered]@{ Name = 'M3_BOTTOM_LEFT'; Label = 'M3 BL'; Display = 'M3 Bottom Left' },
    [ordered]@{ Name = 'M3_BOTTOM_RIGHT'; Label = 'M3 BR'; Display = 'M3 Bottom Right' },
    [ordered]@{ Name = 'M4_TOP_LEFT'; Label = 'M4 TL'; Display = 'M4 Top Left' },
    [ordered]@{ Name = 'M4_TOP_RIGHT'; Label = 'M4 TR'; Display = 'M4 Top Right' },
    [ordered]@{ Name = 'M4_BOTTOM_LEFT'; Label = 'M4 BL'; Display = 'M4 Bottom Left' },
    [ordered]@{ Name = 'M4_BOTTOM_RIGHT'; Label = 'M4 BR'; Display = 'M4 Bottom Right' }
)

$paths = [ordered]@{
    sourceActions = Join-Path $PluginSourceRoot 'src\actions.js'
    sourceStatus = Join-Path $PluginSourceRoot 'src\status.js'
    sourceManifest = Join-Path $PluginSourceRoot 'manifest.json'
    installedActions = Join-Path $InstalledPluginRoot 'bin\actions.js'
    installedStatus = Join-Path $InstalledPluginRoot 'bin\status.js'
    installedManifest = Join-Path $InstalledPluginRoot 'manifest.json'
}

function Assert-File([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required file not found: $Path" }
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Get-ActionUuid([string]$SlotName) {
    return 'com.estate.statusbridge.operator_deck.slot.' + $SlotName.ToLowerInvariant()
}

function Assert-CurrentBaseline {
    foreach ($path in $paths.Values) { Assert-File $path }
    foreach ($pair in @(
        @($paths.sourceActions, $paths.installedActions),
        @($paths.sourceStatus, $paths.installedStatus),
        @($paths.sourceManifest, $paths.installedManifest)
    )) {
        if ((Get-Sha256 $pair[0]) -ne (Get-Sha256 $pair[1])) {
            throw "Source and installed files differ: $($pair[0]) <> $($pair[1])"
        }
    }

    $manifest = Get-Content -LiteralPath $paths.sourceManifest -Raw | ConvertFrom-Json
    if ($manifest.Actions.Count -notin @(19, 35)) { throw "Expected 19 or 35 manifest actions; found $($manifest.Actions.Count)." }
    if (@($manifest.Actions | Where-Object UUID -eq 'com.estate.statusbridge.operator_deck.dictation').Count -ne 1) {
        throw 'The validated Operator Deck Voice Typing action is missing or duplicated.'
    }
    $actionsText = Get-Content -LiteralPath $paths.sourceActions -Raw
    $statusText = Get-Content -LiteralPath $paths.sourceStatus -Raw
    if (-not $actionsText.Contains('com.estate.statusbridge.operator_deck.dictation')) { throw 'Voice Typing action definition is missing.' }
    if (-not $statusText.Contains('getOperatorDeckDictationStatus')) { throw 'Voice Typing status provider is missing.' }

    $present = @($slots | Where-Object { $actionsText.Contains((Get-ActionUuid $_.Name)) }).Count
    if ($present -notin @(0, 16)) { throw "Partial quadrant installation detected in actions.js: $present of 16 actions." }
}

function Add-ActionDefinitions([string]$Text) {
    $present = @($slots | Where-Object { $Text.Contains((Get-ActionUuid $_.Name)) }).Count
    if ($present -eq 16) { return $Text }
    if ($present -ne 0) { throw "Partial quadrant action set detected: $present of 16." }
    $closing = $Text.LastIndexOf('];')
    if ($closing -lt 0) { throw 'Could not locate ACTION_LIST closing marker.' }
    $prefix = $Text.Substring(0, $closing).TrimEnd()
    $suffix = $Text.Substring($closing + 2)
    $blocks = foreach ($slot in $slots) {
        $uuid = Get-ActionUuid $slot.Name
        $key = 'operatorDeckSlot' + ($slot.Name -replace '_', '')
        @"
  {
    key: "$key",
    uuid: "$uuid",
    label: "$($slot.Label)",
    name: "Operator Deck $($slot.Display)",
    kind: "operatorDeckSlot",
    slot: "$($slot.Name)",
    commandPath: "$($CommandRoot.Replace('\', '\\'))\\$($slot.Name).cmd",
    icon: "images/health"
  }
"@.TrimEnd()
    }
    return $prefix + ",`r`n" + ($blocks -join ",`r`n") + "`r`n];" + $suffix
}

function Add-StatusProvider([string]$Text) {
    if ($Text.Contains('getOperatorDeckSlotStatus')) { return $Text }
    $anchor = 'export async function getActionStatus(action, config) {'
    if (-not $Text.Contains($anchor)) { throw 'Could not locate getActionStatus insertion point.' }
    $provider = @'
let operatorDeckStateCache = { expiresAt: 0, promise: null };

async function getCachedOperatorDeckState(config) {
  const now = Date.now();
  if (operatorDeckStateCache.promise && now < operatorDeckStateCache.expiresAt) {
    return operatorDeckStateCache.promise;
  }
  const scriptPath = path.join(config.estateRepo, "tools", "operator-deck", "Get-OperatorDeckState.ps1");
  const statePath = path.join(config.estateRepo, "tools", "operator-deck", "runtime", "operator-deck-state.json");
  if (!existsSync(scriptPath)) throw new Error(`Operator Deck state publisher not found: ${scriptPath}`);
  operatorDeckStateCache.expiresAt = now + 750;
  operatorDeckStateCache.promise = (async () => {
    await run("pwsh.exe", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", scriptPath, "-NoClipboard", "-Quiet"], { timeoutMs: config.commandTimeoutMs });
    return { state: await readJson(statePath), statePath };
  })();
  try {
    return await operatorDeckStateCache.promise;
  } catch (error) {
    operatorDeckStateCache = { expiresAt: 0, promise: null };
    throw error;
  }
}

export async function getOperatorDeckSlotStatus(action, config) {
  try {
    const { state, statePath } = await getCachedOperatorDeckState(config);
    const selection = state?.selection || {};
    if (!selection.armed || !selection.valid) {
      return statusResult({ value: "READY", color: "off", detail: `${action.name}: press to select the occupying window.`, source: statePath, raw: { selection } });
    }
    if (selection.source_slot === action.slot) {
      return statusResult({ value: "SELECT", color: "green", detail: `${action.name} is the selected source.`, source: statePath, raw: { selection } });
    }
    return statusResult({ value: "PLACE", color: "blue", detail: `Press to move the selected window to ${action.name}.`, source: statePath, raw: { selection } });
  } catch (error) {
    return statusResult({ value: "ERR", color: "red", detail: error.stderr || error.message });
  }
}

'@
    $Text = $Text.Replace($anchor, $provider + $anchor)
    $caseAnchor = '    case "commandStatus":'
    if (-not $Text.Contains($caseAnchor)) { throw 'Could not locate getActionStatus switch insertion point.' }
    return $Text.Replace($caseAnchor, "    case `"operatorDeckSlot`":`r`n      return getOperatorDeckSlotStatus(action, config);`r`n$caseAnchor")
}

function Add-ManifestActions([string]$Text) {
    $manifest = $Text | ConvertFrom-Json
    $present = @($slots | Where-Object { $manifest.Actions.UUID -contains (Get-ActionUuid $_.Name) }).Count
    if ($present -eq 16) { return $Text }
    if ($present -ne 0) { throw "Partial quadrant manifest set detected: $present of 16." }
    foreach ($slot in $slots) {
        $manifest.Actions += [pscustomobject]@{
            UUID = Get-ActionUuid $slot.Name
            Name = "Operator Deck $($slot.Display)"
            Tooltip = "Select the window in $($slot.Name), or place the armed selection there."
            Icon = 'images/health'
            States = @([pscustomobject]@{ Image = 'images/health'; TitleAlignment = 'middle'; FontSize = '13' })
            SupportedInMultiActions = $false
        }
    }
    $manifest.Version = '0.3.0'
    return $manifest | ConvertTo-Json -Depth 20
}

function Write-Wrappers([string]$Root) {
    New-Item -ItemType Directory -Path $Root -Force | Out-Null
    foreach ($slot in $slots) {
        $content = @"
@echo off
start "" "A:\theestate\tools\operator-deck\OperatorDeck.ahk" slot $($slot.Name)
exit /b %ERRORLEVEL%
"@
        $content | Set-Content -LiteralPath (Join-Path $Root ($slot.Name + '.cmd')) -Encoding ascii
    }
}

function Test-Candidate([string]$ActionsPath, [string]$StatusPath, [string]$ManifestPath) {
    $manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
    if ($manifest.Actions.Count -ne 35) { throw "Expected 35 manifest actions; found $($manifest.Actions.Count)." }
    foreach ($slot in $slots) {
        $uuid = Get-ActionUuid $slot.Name
        if (@($manifest.Actions | Where-Object UUID -eq $uuid).Count -ne 1) { throw "Missing or duplicated action UUID: $uuid" }
    }
    $node = Get-Command node.exe -ErrorAction Stop
    foreach ($path in @($ActionsPath, $StatusPath)) {
        & $node.Source --check $path
        if ($LASTEXITCODE -ne 0) { throw "Node syntax validation failed: $path" }
    }
}

$temporaryRoot = Join-Path $env:TEMP ('operator-deck-quadrants-' + [guid]::NewGuid().ToString('N'))
$backupRoot = $null
$commandRootExisted = Test-Path -LiteralPath $CommandRoot

try {
    Assert-CurrentBaseline
    New-Item -ItemType Directory -Path $temporaryRoot -Force | Out-Null
    $candidateActions = Join-Path $temporaryRoot 'actions.js'
    $candidateStatus = Join-Path $temporaryRoot 'status.js'
    $candidateManifest = Join-Path $temporaryRoot 'manifest.json'
    Add-ActionDefinitions (Get-Content -LiteralPath $paths.sourceActions -Raw) | Set-Content -LiteralPath $candidateActions -Encoding utf8
    Add-StatusProvider (Get-Content -LiteralPath $paths.sourceStatus -Raw) | Set-Content -LiteralPath $candidateStatus -Encoding utf8
    Add-ManifestActions (Get-Content -LiteralPath $paths.sourceManifest -Raw) | Set-Content -LiteralPath $candidateManifest -Encoding utf8
    Test-Candidate $candidateActions $candidateStatus $candidateManifest

    $alreadyInstalled = (Get-Content -LiteralPath $paths.sourceActions -Raw).Contains((Get-ActionUuid $slots[0].Name))
    if (-not $Apply) {
        $report = @(
            'OPERATOR DECK QUADRANT PATCH PREFLIGHT: PASS'
            "Already installed: $alreadyInstalled"
            'Candidate manifest actions: 35'
            'Quadrant actions: 16'
            'Source and installed baselines match; candidate Node and JSON validation passed.'
            'No files were changed. Re-run with -Apply only after reviewing this result.'
        ) -join "`n"
        $report | Write-Output
        $report | Set-Clipboard
        exit 0
    }

    $backupRoot = Join-Path $PluginSourceRoot ('backups\operator-deck-quadrants-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    foreach ($name in $paths.Keys) {
        Copy-Item -LiteralPath $paths[$name] -Destination (Join-Path $backupRoot ($name + [System.IO.Path]::GetExtension($paths[$name])))
    }
    if ($commandRootExisted) {
        Copy-Item -LiteralPath $CommandRoot -Destination (Join-Path $backupRoot 'Slots') -Recurse
    }

    Copy-Item -LiteralPath $candidateActions -Destination $paths.sourceActions -Force
    Copy-Item -LiteralPath $candidateActions -Destination $paths.installedActions -Force
    Copy-Item -LiteralPath $candidateStatus -Destination $paths.sourceStatus -Force
    Copy-Item -LiteralPath $candidateStatus -Destination $paths.installedStatus -Force
    Copy-Item -LiteralPath $candidateManifest -Destination $paths.sourceManifest -Force
    Copy-Item -LiteralPath $candidateManifest -Destination $paths.installedManifest -Force
    Write-Wrappers $CommandRoot

    Assert-CurrentBaseline
    Test-Candidate $paths.sourceActions $paths.sourceStatus $paths.sourceManifest
    foreach ($slot in $slots) { Assert-File (Join-Path $CommandRoot ($slot.Name + '.cmd')) }

    $report = @(
        'OPERATOR DECK QUADRANT PATCH: VALIDATED'
        "Backup: $backupRoot"
        'Manifest actions: 35'
        'Quadrant actions: 16'
        'Source and installed files match; Node and JSON validation passed.'
        'Stream Deck was not restarted automatically.'
    ) -join "`n"
    $report | Write-Output
    $report | Set-Clipboard
} catch {
    if ($backupRoot -and (Test-Path -LiteralPath $backupRoot)) {
        foreach ($name in $paths.Keys) {
            $backup = Join-Path $backupRoot ($name + [System.IO.Path]::GetExtension($paths[$name]))
            if (Test-Path -LiteralPath $backup) { Copy-Item -LiteralPath $backup -Destination $paths[$name] -Force }
        }
        if (Test-Path -LiteralPath $CommandRoot) { Remove-Item -LiteralPath $CommandRoot -Recurse -Force }
        $wrapperBackup = Join-Path $backupRoot 'Slots'
        if ($commandRootExisted -and (Test-Path -LiteralPath $wrapperBackup)) {
            Copy-Item -LiteralPath $wrapperBackup -Destination $CommandRoot -Recurse
        }
    }
    Write-Error "Operator Deck quadrant patch failed: $($_.Exception.Message)"
    exit 1
} finally {
    if (Test-Path -LiteralPath $temporaryRoot) { Remove-Item -LiteralPath $temporaryRoot -Recurse -Force }
}
