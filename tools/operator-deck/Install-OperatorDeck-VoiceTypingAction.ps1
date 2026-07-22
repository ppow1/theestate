[CmdletBinding()]
param(
    [string]$PluginSourceRoot = 'A:\AI\Tools\EstateStreamDeckPlugin',
    [string]$InstalledPluginRoot = (Join-Path $env:APPDATA 'Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin'),
    [string]$EstateRoot = 'A:\theestate',
    [switch]$Apply
)

CLS
$ErrorActionPreference = 'Stop'

$actionUuid = 'com.estate.statusbridge.operator_deck.dictation'
$expected = @{
    actions = '1d9e694f3d50f1ed391bd8caea3d805d4e8d3fe25907fd6b668428c505c42f49'
    status = '02fe3e267387565e7e41ad074c7270e4d8f49904f31dee9e5398cb43cbd08d60'
    manifest = '646c28cee047e5832738db7e7de34788dd53aaf976a5514807e85be0a8a94e82'
}

$paths = [ordered]@{
    sourceActions = Join-Path $PluginSourceRoot 'src\actions.js'
    sourceStatus = Join-Path $PluginSourceRoot 'src\status.js'
    sourceManifest = Join-Path $PluginSourceRoot 'manifest.json'
    installedActions = Join-Path $InstalledPluginRoot 'bin\actions.js'
    installedStatus = Join-Path $InstalledPluginRoot 'bin\status.js'
    installedManifest = Join-Path $InstalledPluginRoot 'manifest.json'
    wrapper = 'A:\AI\Tools\EstateStreamDeckMVP\OperatorDeck\Toggle-VoiceTyping.cmd'
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Assert-File([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { throw "Required file not found: $Path" }
}

function Add-ActionDefinition([string]$Text) {
    if ($Text.Contains($actionUuid)) { return $Text }
    $closing = $Text.LastIndexOf('];')
    if ($closing -lt 0) { throw 'Could not locate ACTION_LIST closing marker.' }
    $prefix = $Text.Substring(0, $closing).TrimEnd()
    $suffix = $Text.Substring($closing + 2)
    if (-not $prefix.EndsWith('}')) { throw 'ACTION_LIST did not end with an action object.' }
    $block = @'
  {
    key: "operatorDeckDictation",
    uuid: "com.estate.statusbridge.operator_deck.dictation",
    label: "VOICE",
    name: "Operator Deck Voice Typing",
    kind: "operatorDeckDictation",
    commandPath: "A:\\AI\\Tools\\EstateStreamDeckMVP\\OperatorDeck\\Toggle-VoiceTyping.cmd",
    icon: "images/health"
  }
'@
    return $prefix + ",`r`n" + $block.TrimEnd() + "`r`n];" + $suffix
}

function Add-StatusProvider([string]$Text) {
    if ($Text.Contains('getOperatorDeckDictationStatus')) { return $Text }
    $anchor = 'export async function getActionStatus(action, config) {'
    if (-not $Text.Contains($anchor)) { throw 'Could not locate getActionStatus insertion point.' }
    $provider = @'
export async function getOperatorDeckDictationStatus(config) {
  const scriptPath = path.join(config.estateRepo, "tools", "operator-deck", "Get-OperatorDeckState.ps1");
  const statePath = path.join(config.estateRepo, "tools", "operator-deck", "runtime", "operator-deck-state.json");
  if (!existsSync(scriptPath)) {
    return statusResult({ value: "ERR", color: "red", detail: `Operator Deck state publisher not found: ${scriptPath}`, source: scriptPath });
  }
  try {
    await run("pwsh.exe", ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", scriptPath, "-NoClipboard", "-Quiet"], { timeoutMs: config.commandTimeoutMs });
    const state = await readJson(statePath);
    const dictation = state?.dictation || {};
    if (dictation.state === "listening") {
      return statusResult({ value: "ON", color: "green", detail: "Windows Voice Typing is listening.", source: statePath, raw: { dictation } });
    }
    if (dictation.state === "off") {
      return statusResult({ value: "OFF", color: "off", detail: "Windows Voice Typing is not listening.", source: statePath, raw: { dictation } });
    }
    return statusResult({ value: "UNK", color: "yellow", detail: "Voice Typing state is unknown.", source: statePath, raw: { dictation } });
  } catch (error) {
    return statusResult({ value: "ERR", color: "red", detail: error.stderr || error.message, source: statePath });
  }
}

'@
    $Text = $Text.Replace($anchor, $provider + $anchor)
    $caseAnchor = '    case "commandStatus":'
    if (-not $Text.Contains($caseAnchor)) { throw 'Could not locate getActionStatus switch insertion point.' }
    return $Text.Replace($caseAnchor, "    case `"operatorDeckDictation`":`r`n      return getOperatorDeckDictationStatus(config);`r`n$caseAnchor")
}

function Add-ManifestAction([string]$Text) {
    $manifest = $Text | ConvertFrom-Json
    if ($manifest.Actions.UUID -contains $actionUuid) { return $Text }
    $manifest.Actions += [pscustomobject]@{
        UUID = $actionUuid
        Name = 'Operator Deck Voice Typing'
        Tooltip = 'Tap to toggle Windows Voice Typing. Status shows ON or OFF.'
        Icon = 'images/health'
        States = @([pscustomobject]@{ Image = 'images/health'; TitleAlignment = 'middle'; FontSize = '16' })
        SupportedInMultiActions = $false
    }
    $manifest.Version = '0.2.1'
    return $manifest | ConvertTo-Json -Depth 20
}

function Test-PatchedFiles {
    foreach ($path in $paths.Values) { Assert-File $path }
    $sourceManifest = Get-Content -LiteralPath $paths.sourceManifest -Raw | ConvertFrom-Json
    $installedManifest = Get-Content -LiteralPath $paths.installedManifest -Raw | ConvertFrom-Json
    foreach ($manifest in @($sourceManifest, $installedManifest)) {
        if (@($manifest.Actions | Where-Object UUID -eq $actionUuid).Count -ne 1) { throw 'Voice Typing action UUID is missing or duplicated.' }
        if ($manifest.Actions.Count -ne 19) { throw "Expected 19 manifest actions; found $($manifest.Actions.Count)." }
    }
    if ((Get-Sha256 $paths.sourceActions) -ne (Get-Sha256 $paths.installedActions)) { throw 'Source and installed actions.js differ.' }
    if ((Get-Sha256 $paths.sourceStatus) -ne (Get-Sha256 $paths.installedStatus)) { throw 'Source and installed status.js differ.' }
    if ((Get-Sha256 $paths.sourceManifest) -ne (Get-Sha256 $paths.installedManifest)) { throw 'Source and installed manifests differ.' }
    $node = Get-Command node.exe -ErrorAction Stop
    foreach ($path in @($paths.sourceActions, $paths.sourceStatus, $paths.installedActions, $paths.installedStatus)) {
        & $node.Source --check $path
        if ($LASTEXITCODE -ne 0) { throw "Node syntax validation failed: $path" }
    }
}

$backupRoot = $null
$wrapperExisted = Test-Path -LiteralPath $paths.wrapper

try {
    foreach ($path in @($paths.sourceActions, $paths.sourceStatus, $paths.sourceManifest, $paths.installedActions, $paths.installedStatus, $paths.installedManifest)) {
        Assert-File $path
    }

    $alreadyInstalled = (Get-Content -LiteralPath $paths.sourceActions -Raw).Contains($actionUuid)
    if (-not $alreadyInstalled) {
        if ((Get-Sha256 $paths.sourceActions) -ne $expected.actions -or (Get-Sha256 $paths.installedActions) -ne $expected.actions) { throw 'actions.js SHA precondition failed.' }
        if ((Get-Sha256 $paths.sourceStatus) -ne $expected.status -or (Get-Sha256 $paths.installedStatus) -ne $expected.status) { throw 'status.js SHA precondition failed.' }
        if ((Get-Sha256 $paths.sourceManifest) -ne $expected.manifest -or (Get-Sha256 $paths.installedManifest) -ne $expected.manifest) { throw 'manifest SHA precondition failed.' }
    }

    if (-not $Apply) {
        @(
            'OPERATOR DECK VOICE TYPING PATCH PREFLIGHT: PASS'
            "Already installed: $alreadyInstalled"
            'No files were changed. Re-run with -Apply only after reviewing this result.'
        ) -join "`n" | Tee-Object -Variable Report | Write-Output
        $Report | Set-Clipboard
        exit 0
    }

    $backupRoot = Join-Path $PluginSourceRoot ('backups\operator-deck-voice-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    foreach ($name in @('sourceActions','sourceStatus','sourceManifest','installedActions','installedStatus','installedManifest')) {
        Copy-Item -LiteralPath $paths[$name] -Destination (Join-Path $backupRoot ($name + [System.IO.Path]::GetExtension($paths[$name])))
    }
    if ($wrapperExisted) { Copy-Item -LiteralPath $paths.wrapper -Destination (Join-Path $backupRoot 'wrapper.cmd') }

    if (-not $alreadyInstalled) {
        $actions = Add-ActionDefinition (Get-Content -LiteralPath $paths.sourceActions -Raw)
        $status = Add-StatusProvider (Get-Content -LiteralPath $paths.sourceStatus -Raw)
        $manifest = Add-ManifestAction (Get-Content -LiteralPath $paths.sourceManifest -Raw)
        $actions | Set-Content -LiteralPath $paths.sourceActions -Encoding utf8
        $actions | Set-Content -LiteralPath $paths.installedActions -Encoding utf8
        $status | Set-Content -LiteralPath $paths.sourceStatus -Encoding utf8
        $status | Set-Content -LiteralPath $paths.installedStatus -Encoding utf8
        $manifest | Set-Content -LiteralPath $paths.sourceManifest -Encoding utf8
        $manifest | Set-Content -LiteralPath $paths.installedManifest -Encoding utf8
    }

    New-Item -ItemType Directory -Path (Split-Path -Parent $paths.wrapper) -Force | Out-Null
    @'
@echo off
start "" "A:\theestate\tools\operator-deck\OperatorDeck.ahk" dictation-toggle
exit /b %ERRORLEVEL%
'@ | Set-Content -LiteralPath $paths.wrapper -Encoding ascii

    Test-PatchedFiles
    $report = @(
        'OPERATOR DECK VOICE TYPING PATCH: VALIDATED'
        "Backup: $backupRoot"
        'Manifest actions: 19'
        "Action UUID: $actionUuid"
        'Source and installed files match; Node and JSON validation passed.'
        'Stream Deck was not restarted automatically.'
    ) -join "`n"
    $report | Write-Output
    $report | Set-Clipboard
    exit 0
} catch {
    if ($backupRoot -and (Test-Path -LiteralPath $backupRoot)) {
        foreach ($name in @('sourceActions','sourceStatus','sourceManifest','installedActions','installedStatus','installedManifest')) {
            $backup = Join-Path $backupRoot ($name + [System.IO.Path]::GetExtension($paths[$name]))
            if (Test-Path -LiteralPath $backup) { Copy-Item -LiteralPath $backup -Destination $paths[$name] -Force }
        }
        $wrapperBackup = Join-Path $backupRoot 'wrapper.cmd'
        if ($wrapperExisted -and (Test-Path -LiteralPath $wrapperBackup)) {
            Copy-Item -LiteralPath $wrapperBackup -Destination $paths.wrapper -Force
        } elseif (-not $wrapperExisted -and (Test-Path -LiteralPath $paths.wrapper)) {
            Remove-Item -LiteralPath $paths.wrapper -Force
        }
    }
    Write-Error "Operator Deck Voice Typing patch failed: $($_.Exception.Message)"
    exit 1
}
