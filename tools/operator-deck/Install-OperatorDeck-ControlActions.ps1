[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$PluginSourceRoot = 'A:\AI\Tools\EstateStreamDeckPlugin',
    [string]$InstalledPluginRoot = (Join-Path $env:APPDATA 'Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin'),
    [string]$CommandRoot = 'A:\AI\Tools\EstateStreamDeckMVP\OperatorDeck\Controls'
)

$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { Write-Error 'Windows is required.'; exit 2 }

$controls = @(
    [ordered]@{ Key='operatorDeckUndo'; UUID='com.estate.statusbridge.operator_deck.undo'; Label='UNDO'; Name='Operator Deck Undo'; Operation='undo'; File='Undo.cmd' },
    [ordered]@{ Key='operatorDeckClearSelection'; UUID='com.estate.statusbridge.operator_deck.clear_selection'; Label='CLEAR'; Name='Operator Deck Clear Selection'; Operation='clearSelection'; File='ClearSelection.cmd' },
    [ordered]@{ Key='operatorDeckSelectActive'; UUID='com.estate.statusbridge.operator_deck.select_active'; Label='SELECT'; Name='Operator Deck Select Active'; Operation='selectActive'; File='SelectActive.cmd' }
)

$paths = [ordered]@{
    sourceActions = Join-Path $PluginSourceRoot 'src\actions.js'
    sourceStatus = Join-Path $PluginSourceRoot 'src\status.js'
    sourceManifest = Join-Path $PluginSourceRoot 'manifest.json'
    installedActions = Join-Path $InstalledPluginRoot 'bin\actions.js'
    installedStatus = Join-Path $InstalledPluginRoot 'bin\status.js'
    installedManifest = Join-Path $InstalledPluginRoot 'manifest.json'
}

function Assert-File([string]$Path) { if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing: $Path" } }
function Get-Sha256([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }

function Assert-Baseline {
    foreach ($path in $paths.Values) { Assert-File $path }
    foreach ($pair in @(@($paths.sourceActions,$paths.installedActions),@($paths.sourceStatus,$paths.installedStatus),@($paths.sourceManifest,$paths.installedManifest))) {
        if ((Get-Sha256 $pair[0]) -ne (Get-Sha256 $pair[1])) { throw "Source/installed drift: $($pair[0])" }
    }
    $manifest = Get-Content $paths.sourceManifest -Raw | ConvertFrom-Json
    if ($manifest.Actions.Count -notin @(35,38)) { throw "Expected 35 or 38 actions; found $($manifest.Actions.Count)." }
    $text = Get-Content $paths.sourceActions -Raw
    $present = @($controls | Where-Object { $text.Contains($_.UUID) }).Count
    if ($present -notin @(0,3)) { throw "Partial control action set: $present of 3." }
}

function Add-Actions([string]$Text) {
    $present = @($controls | Where-Object { $Text.Contains($_.UUID) }).Count
    if ($present -eq 3) { return $Text }
    if ($present -ne 0) { throw "Partial action set: $present of 3." }
    $closing = $Text.LastIndexOf('];')
    if ($closing -lt 0) { throw 'ACTION_LIST closing marker not found.' }
    $root = $CommandRoot.Replace('\','\\')
    $blocks = foreach ($item in $controls) {
@"
  {
    key: "$($item.Key)",
    uuid: "$($item.UUID)",
    label: "$($item.Label)",
    name: "$($item.Name)",
    kind: "operatorDeckControl",
    operation: "$($item.Operation)",
    commandPath: "$root\\$($item.File)",
    icon: "images/health"
  }
"@.TrimEnd()
    }
    return $Text.Substring(0,$closing).TrimEnd() + ",`r`n" + ($blocks -join ",`r`n") + "`r`n];" + $Text.Substring($closing+2)
}

function Add-Status([string]$Text) {
    if (-not $Text.Contains('getOperatorDeckControlStatus')) {
        $anchor = 'export async function getActionStatus(action, config) {'
        $provider = @'
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
        if (-not $Text.Contains($anchor)) { throw 'Status insertion anchor missing.' }
        $Text = $Text.Replace($anchor,$provider+$anchor)
        $caseAnchor = '    case "commandStatus":'
        if (-not $Text.Contains($caseAnchor)) { throw 'Status switch anchor missing.' }
        $Text = $Text.Replace($caseAnchor,"    case `"operatorDeckControl`":`r`n      return getOperatorDeckControlStatus(action, config);`r`n$caseAnchor")
    }
    return $Text
}

function Add-Manifest([string]$Text) {
    $manifest = $Text | ConvertFrom-Json
    $present = @($controls | Where-Object { $manifest.Actions.UUID -contains $_.UUID }).Count
    if ($present -eq 3) { return $Text }
    if ($present -ne 0) { throw "Partial manifest control set: $present of 3." }
    foreach ($item in $controls) {
        $manifest.Actions += [pscustomobject]@{ UUID=$item.UUID; Name=$item.Name; Tooltip=$item.Name; Icon='images/health'; States=@([pscustomobject]@{Image='images/health';TitleAlignment='middle';FontSize='14'}); SupportedInMultiActions=$false }
    }
    $manifest.Version='0.4.0'
    $manifest | ConvertTo-Json -Depth 20
}

function Write-Wrappers {
    New-Item -ItemType Directory -Path $CommandRoot -Force | Out-Null
    $commands = [ordered]@{'Undo.cmd'='undo';'ClearSelection.cmd'='clear-selection';'SelectActive.cmd'='select-active'}
    foreach ($name in $commands.Keys) {
@"
@echo off
start "" "A:\theestate\tools\operator-deck\OperatorDeck.ahk" $($commands[$name])
exit /b %ERRORLEVEL%
"@ | Set-Content -LiteralPath (Join-Path $CommandRoot $name) -Encoding ascii
    }
}

function Test-Candidate([string]$Actions,[string]$Status,[string]$Manifest) {
    $m=Get-Content $Manifest -Raw|ConvertFrom-Json
    if ($m.Actions.Count -ne 38) { throw "Expected 38 actions; found $($m.Actions.Count)." }
    foreach($item in $controls){if(@($m.Actions|Where-Object UUID -eq $item.UUID).Count -ne 1){throw "Bad UUID: $($item.UUID)"}}
    $node=Get-Command node.exe -ErrorAction Stop
    foreach($file in @($Actions,$Status)){& $node.Source --check $file;if($LASTEXITCODE -ne 0){throw "Node validation failed: $file"}}
}

$temp=Join-Path $env:TEMP ('operator-deck-controls-'+[guid]::NewGuid().ToString('N'))
$backup=$null
try {
    Assert-Baseline
    New-Item -ItemType Directory $temp -Force|Out-Null
    $a=Join-Path $temp 'actions.js';$s=Join-Path $temp 'status.js';$m=Join-Path $temp 'manifest.json'
    Add-Actions (Get-Content $paths.sourceActions -Raw)|Set-Content $a -Encoding utf8
    Add-Status (Get-Content $paths.sourceStatus -Raw)|Set-Content $s -Encoding utf8
    Add-Manifest (Get-Content $paths.sourceManifest -Raw)|Set-Content $m -Encoding utf8
    Test-Candidate $a $s $m
    $installed=(Get-Content $paths.sourceActions -Raw).Contains($controls[0].UUID)
    if(-not $Apply){$report=@('OPERATOR DECK CONTROL ACTIONS PREFLIGHT: PASS',"Already installed: $installed",'Candidate manifest actions: 38','Controls: UNDO, CLEAR, SELECT','No files were changed. Re-run with -Apply only after reviewing this result.')-join"`n";$report|Tee-Object -Variable clip; $clip|Set-Clipboard;exit 0}
    $backup=Join-Path $PluginSourceRoot ('backups\operator-deck-controls-'+(Get-Date -Format 'yyyyMMdd-HHmmss'));New-Item -ItemType Directory $backup -Force|Out-Null
    foreach($name in $paths.Keys){Copy-Item $paths[$name] (Join-Path $backup ($name+[IO.Path]::GetExtension($paths[$name])))}
    Copy-Item $a $paths.sourceActions -Force;Copy-Item $a $paths.installedActions -Force;Copy-Item $s $paths.sourceStatus -Force;Copy-Item $s $paths.installedStatus -Force;Copy-Item $m $paths.sourceManifest -Force;Copy-Item $m $paths.installedManifest -Force
    Write-Wrappers;Assert-Baseline;Test-Candidate $paths.sourceActions $paths.sourceStatus $paths.sourceManifest
    $report=@('OPERATOR DECK CONTROL ACTIONS: VALIDATED',"Backup: $backup",'Manifest actions: 38','Controls installed: UNDO, CLEAR, SELECT','Source and installed files match; Node and JSON validation passed.','Stream Deck was not restarted automatically.')-join"`n";$report|Tee-Object -Variable clip;$clip|Set-Clipboard
} catch {
    if($backup -and (Test-Path $backup)){
        foreach($name in $paths.Keys){$saved=Join-Path $backup ($name+[IO.Path]::GetExtension($paths[$name]));if(Test-Path $saved){Copy-Item $saved $paths[$name] -Force}}
    }
    Write-Error "Operator Deck control patch failed: $($_.Exception.Message)";exit 1
} finally {if(Test-Path $temp){Remove-Item $temp -Recurse -Force}}
