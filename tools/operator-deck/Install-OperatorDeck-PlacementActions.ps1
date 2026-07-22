[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$PluginSourceRoot = 'A:\AI\Tools\EstateStreamDeckPlugin',
    [string]$InstalledPluginRoot = (Join-Path $env:APPDATA 'Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin'),
    [string]$CommandRoot = 'A:\AI\Tools\EstateStreamDeckMVP\OperatorDeck\Placement'
)

$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { Write-Error 'Windows is required.'; exit 2 }

$actions = @(
    [ordered]@{ Key='operatorDeckMonitorM1'; UUID='com.estate.statusbridge.operator_deck.monitor.m1'; Label='M1'; Name='Operator Deck Destination M1'; Type='monitor'; Value='M1'; File='Monitor-M1.cmd' },
    [ordered]@{ Key='operatorDeckMonitorM2'; UUID='com.estate.statusbridge.operator_deck.monitor.m2'; Label='M2'; Name='Operator Deck Destination M2'; Type='monitor'; Value='M2'; File='Monitor-M2.cmd' },
    [ordered]@{ Key='operatorDeckMonitorM3'; UUID='com.estate.statusbridge.operator_deck.monitor.m3'; Label='M3'; Name='Operator Deck Destination M3'; Type='monitor'; Value='M3'; File='Monitor-M3.cmd' },
    [ordered]@{ Key='operatorDeckMonitorM4'; UUID='com.estate.statusbridge.operator_deck.monitor.m4'; Label='M4'; Name='Operator Deck Destination M4'; Type='monitor'; Value='M4'; File='Monitor-M4.cmd' },
    [ordered]@{ Key='operatorDeckShapeFull'; UUID='com.estate.statusbridge.operator_deck.shape.full'; Label='FULL'; Name='Operator Deck Shape Full'; Type='shape'; Value='full'; File='Shape-Full.cmd' },
    [ordered]@{ Key='operatorDeckShapeLeft'; UUID='com.estate.statusbridge.operator_deck.shape.left'; Label='LEFT'; Name='Operator Deck Shape Left'; Type='shape'; Value='left'; File='Shape-Left.cmd' },
    [ordered]@{ Key='operatorDeckShapeRight'; UUID='com.estate.statusbridge.operator_deck.shape.right'; Label='RIGHT'; Name='Operator Deck Shape Right'; Type='shape'; Value='right'; File='Shape-Right.cmd' },
    [ordered]@{ Key='operatorDeckShapeTop'; UUID='com.estate.statusbridge.operator_deck.shape.top'; Label='TOP'; Name='Operator Deck Shape Top'; Type='shape'; Value='top'; File='Shape-Top.cmd' },
    [ordered]@{ Key='operatorDeckShapeBottom'; UUID='com.estate.statusbridge.operator_deck.shape.bottom'; Label='BOTTOM'; Name='Operator Deck Shape Bottom'; Type='shape'; Value='bottom'; File='Shape-Bottom.cmd' },
    [ordered]@{ Key='operatorDeckReturn'; UUID='com.estate.statusbridge.operator_deck.return'; Label='RETURN'; Name='Operator Deck Return Promoted Window'; Type='return'; Value='return'; File='Return.cmd' }
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
    if ($manifest.Actions.Count -notin @(38,48)) { throw "Expected 38 or 48 actions; found $($manifest.Actions.Count)." }
    $text = Get-Content $paths.sourceActions -Raw
    $present = @($actions | Where-Object { $text.Contains($_.UUID) }).Count
    if ($present -notin @(0,10)) { throw "Partial placement action set: $present of 10." }
}

function Add-Actions([string]$Text) {
    $present = @($actions | Where-Object { $Text.Contains($_.UUID) }).Count
    if ($present -eq 10) { return $Text }
    if ($present -ne 0) { throw "Partial placement action set: $present of 10." }
    $closing = $Text.LastIndexOf('];')
    if ($closing -lt 0) { throw 'ACTION_LIST closing marker not found.' }
    $root = $CommandRoot.Replace('\','\\')
    $blocks = foreach ($item in $actions) {
@"
  {
    key: "$($item.Key)",
    uuid: "$($item.UUID)",
    label: "$($item.Label)",
    name: "$($item.Name)",
    kind: "operatorDeckPlacement",
    placementType: "$($item.Type)",
    placementValue: "$($item.Value)",
    commandPath: "$root\\$($item.File)",
    icon: "images/health"
  }
"@.TrimEnd()
    }
    return $Text.Substring(0,$closing).TrimEnd() + ",`r`n" + ($blocks -join ",`r`n") + "`r`n];" + $Text.Substring($closing+2)
}

function Add-Status([string]$Text) {
    if ($Text.Contains('getOperatorDeckPlacementStatus')) { return $Text }
    $anchor = 'export async function getActionStatus(action, config) {'
    if (-not $Text.Contains($anchor)) { throw 'Status insertion anchor missing.' }
    $provider = @'
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
    $Text = $Text.Replace($anchor,$provider+$anchor)
    $caseAnchor = '    case "commandStatus":'
    if (-not $Text.Contains($caseAnchor)) { throw 'Status switch anchor missing.' }
    return $Text.Replace($caseAnchor,"    case `"operatorDeckPlacement`":`r`n      return getOperatorDeckPlacementStatus(action, config);`r`n$caseAnchor")
}

function Add-Manifest([string]$Text) {
    $manifest = $Text | ConvertFrom-Json
    $present = @($actions | Where-Object { $manifest.Actions.UUID -contains $_.UUID }).Count
    if ($present -eq 10) { return $Text }
    if ($present -ne 0) { throw "Partial placement manifest set: $present of 10." }
    foreach ($item in $actions) {
        $manifest.Actions += [pscustomobject]@{ UUID=$item.UUID; Name=$item.Name; Tooltip=$item.Name; Icon='images/health'; States=@([pscustomobject]@{Image='images/health';TitleAlignment='middle';FontSize='13'}); SupportedInMultiActions=$false }
    }
    $manifest.Version='0.5.0'
    $manifest | ConvertTo-Json -Depth 20
}

function Write-Wrappers {
    New-Item -ItemType Directory -Path $CommandRoot -Force | Out-Null
    foreach ($item in $actions) {
        $command = switch ($item.Type) {
            'monitor' { "destination-monitor $($item.Value)" }
            'shape' { "destination-shape $($item.Value)" }
            'return' { 'return-promoted' }
        }
@"
@echo off
start "" "A:\theestate\tools\operator-deck\OperatorDeck.ahk" $command
exit /b %ERRORLEVEL%
"@ | Set-Content -LiteralPath (Join-Path $CommandRoot $item.File) -Encoding ascii
    }
}

function Test-Candidate([string]$ActionsPath,[string]$StatusPath,[string]$ManifestPath) {
    $manifest=Get-Content $ManifestPath -Raw|ConvertFrom-Json
    if ($manifest.Actions.Count -ne 48) { throw "Expected 48 actions; found $($manifest.Actions.Count)." }
    foreach($item in $actions){if(@($manifest.Actions|Where-Object UUID -eq $item.UUID).Count -ne 1){throw "Bad UUID: $($item.UUID)"}}
    $node=Get-Command node.exe -ErrorAction Stop
    foreach($file in @($ActionsPath,$StatusPath)){& $node.Source --check $file;if($LASTEXITCODE -ne 0){throw "Node validation failed: $file"}}
}

$temp=Join-Path $env:TEMP ('operator-deck-placement-'+[guid]::NewGuid().ToString('N'))
$backup=$null
try {
    Assert-Baseline
    New-Item -ItemType Directory $temp -Force|Out-Null
    $a=Join-Path $temp 'actions.js';$s=Join-Path $temp 'status.js';$m=Join-Path $temp 'manifest.json'
    Add-Actions (Get-Content $paths.sourceActions -Raw)|Set-Content $a -Encoding utf8
    Add-Status (Get-Content $paths.sourceStatus -Raw)|Set-Content $s -Encoding utf8
    Add-Manifest (Get-Content $paths.sourceManifest -Raw)|Set-Content $m -Encoding utf8
    Test-Candidate $a $s $m
    $installed=(Get-Content $paths.sourceActions -Raw).Contains($actions[0].UUID)
    if(-not $Apply){
        $report=@('OPERATOR DECK PLACEMENT ACTIONS PREFLIGHT: PASS',"Already installed: $installed",'Candidate manifest actions: 48','Placement actions: M1-M4, FULL, LEFT, RIGHT, TOP, BOTTOM, RETURN','No files were changed. Re-run with -Apply only after reviewing this result.')-join"`n"
        $report|Tee-Object -Variable clip; $clip|Set-Clipboard;exit 0
    }
    $backup=Join-Path $PluginSourceRoot ('backups\operator-deck-placement-'+(Get-Date -Format 'yyyyMMdd-HHmmss'));New-Item -ItemType Directory $backup -Force|Out-Null
    foreach($name in $paths.Keys){Copy-Item $paths[$name] (Join-Path $backup ($name+[IO.Path]::GetExtension($paths[$name])))}
    Copy-Item $a $paths.sourceActions -Force;Copy-Item $a $paths.installedActions -Force;Copy-Item $s $paths.sourceStatus -Force;Copy-Item $s $paths.installedStatus -Force;Copy-Item $m $paths.sourceManifest -Force;Copy-Item $m $paths.installedManifest -Force
    Write-Wrappers;Assert-Baseline;Test-Candidate $paths.sourceActions $paths.sourceStatus $paths.sourceManifest
    $report=@('OPERATOR DECK PLACEMENT ACTIONS: VALIDATED',"Backup: $backup",'Manifest actions: 48','Placement actions installed: M1-M4, FULL, LEFT, RIGHT, TOP, BOTTOM, RETURN','Source and installed files match; Node and JSON validation passed.','Stream Deck was not restarted automatically.')-join"`n";$report|Tee-Object -Variable clip;$clip|Set-Clipboard
} catch {
    if($backup -and (Test-Path $backup)){
        foreach($name in $paths.Keys){$saved=Join-Path $backup ($name+[IO.Path]::GetExtension($paths[$name]));if(Test-Path $saved){Copy-Item $saved $paths[$name] -Force}}
    }
    Write-Error "Operator Deck placement patch failed: $($_.Exception.Message)";exit 1
} finally {if(Test-Path $temp){Remove-Item $temp -Recurse -Force}}
