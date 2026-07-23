[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$PluginSourceRoot = 'A:\AI\Tools\EstateStreamDeckPlugin',
    [string]$InstalledPluginRoot = (Join-Path $env:APPDATA 'Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin'),
    [string]$CommandRoot = 'A:\AI\Tools\EstateStreamDeckMVP\OperatorDeck\Cycle'
)

$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { Write-Error 'Windows is required.'; exit 2 }

$slots = @(
'M1_TOP_LEFT','M1_TOP_RIGHT','M1_BOTTOM_LEFT','M1_BOTTOM_RIGHT',
'M2_TOP_LEFT','M2_TOP_RIGHT','M2_BOTTOM_LEFT','M2_BOTTOM_RIGHT',
'M3_TOP_LEFT','M3_TOP_RIGHT','M3_BOTTOM_LEFT','M3_BOTTOM_RIGHT',
'M4_TOP_LEFT','M4_TOP_RIGHT','M4_BOTTOM_LEFT','M4_BOTTOM_RIGHT'
)

$paths = [ordered]@{
    sourceActions = Join-Path $PluginSourceRoot 'src\actions.js'
    sourceStatus = Join-Path $PluginSourceRoot 'src\status.js'
    sourcePlugin = Join-Path $PluginSourceRoot 'src\plugin.js'
    installedActions = Join-Path $InstalledPluginRoot 'bin\actions.js'
    installedStatus = Join-Path $InstalledPluginRoot 'bin\status.js'
    installedPlugin = Join-Path $InstalledPluginRoot 'bin\plugin.js'
}

function Assert-File([string]$Path) { if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Missing: $Path" } }
function Get-Sha256([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }

function Assert-Baseline {
    foreach ($path in $paths.Values) { Assert-File $path }
    foreach ($pair in @(
        @($paths.sourceActions,$paths.installedActions),
        @($paths.sourceStatus,$paths.installedStatus),
        @($paths.sourcePlugin,$paths.installedPlugin)
    )) {
        if ((Get-Sha256 $pair[0]) -ne (Get-Sha256 $pair[1])) { throw "Source/installed drift: $($pair[0])" }
    }
    $actionsText = Get-Content $paths.sourceActions -Raw
    $present = @($slots | Where-Object { $actionsText.Contains('operator_deck.slot.' + $_.ToLowerInvariant()) }).Count
    if ($present -ne 16) { throw "Expected 16 quadrant actions; found $present." }
    $longPresent = ([regex]::Matches($actionsText,'longPressCommandPath:.*OperatorDeck.*Cycle')).Count
    if ($longPresent -notin @(0,16)) { throw "Partial cycle command set: $longPresent of 16." }
}

function Add-CycleCommands([string]$Text) {
    $root = $CommandRoot.Replace('\','\\')
    foreach ($slot in $slots) {
        $uuid = 'com.estate.statusbridge.operator_deck.slot.' + $slot.ToLowerInvariant()
        $blockPattern = '(?s)(uuid:\s*"' + [regex]::Escape($uuid) + '".*?slot:\s*"' + [regex]::Escape($slot) + '",\s*\r?\n\s*commandPath:\s*"[^"]+",)'
        $matches = [regex]::Matches($Text,$blockPattern)
        if ($matches.Count -ne 1) { throw "Expected one action block for $slot; found $($matches.Count)." }
        if ($matches[0].Value.Contains('longPressCommandPath')) { continue }
        $replacement = $matches[0].Value + "`r`n    longPressCommandPath: `"$root\\$slot.cmd`,"
        $Text = $Text.Remove($matches[0].Index,$matches[0].Length).Insert($matches[0].Index,$replacement)
    }
    return $Text
}

function Add-CycleStatus([string]$Text) {
    $pattern = '(?s)export async function getOperatorDeckSlotStatus\(action, config\) \{.*?\r?\n\}\r?\n\r?\n'
    $matches = [regex]::Matches($Text,$pattern)
    if ($matches.Count -ne 1) { throw "Expected one quadrant status provider; found $($matches.Count)." }
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
    return [regex]::Replace($Text,$pattern,[System.Text.RegularExpressions.MatchEvaluator]{ param($m) $replacement },1)
}

function Add-CycleTransient([string]$Text) {
    if ($Text.Contains('action.kind === "operatorDeckSlot" ? "CYCLE"')) { return $Text }
    $old = @'
      showTransient(context, action, "STOPPING", "orange", `Stopping ${action.name}`);
      runCommand(action.longPressCommandPath);
'@
    $new = @'
      const longValue = action.kind === "operatorDeckSlot" ? "CYCLE" : "STOPPING";
      const longColor = action.kind === "operatorDeckSlot" ? "yellow" : "orange";
      const longDetail = action.kind === "operatorDeckSlot" ? "Entering or completing quadrant cycle mode" : `Stopping ${action.name}`;
      showTransient(context, action, longValue, longColor, longDetail);
      runCommand(action.longPressCommandPath);
'@
    if (-not $Text.Contains($old)) { throw 'Plugin long-press execution anchor is missing.' }
    return $Text.Replace($old,$new)
}

function Write-Wrappers {
    New-Item -ItemType Directory -Path $CommandRoot -Force | Out-Null
    foreach ($slot in $slots) {
@"
@echo off
start "" "A:\theestate\tools\operator-deck\OperatorDeck.ahk" cycle-slot $slot
exit /b %ERRORLEVEL%
"@ | Set-Content -LiteralPath (Join-Path $CommandRoot ($slot + '.cmd')) -Encoding ascii
    }
}

function Test-Candidate([string]$Actions,[string]$Status,[string]$Plugin) {
    $actionsText = Get-Content $Actions -Raw
    if (([regex]::Matches($actionsText,'longPressCommandPath:.*OperatorDeck.*Cycle')).Count -ne 16) { throw 'Expected 16 cycle long-press commands.' }
    $statusText = Get-Content $Status -Raw
    if (-not $statusText.Contains('cycle.index')) { throw 'Cycle status publishing is missing.' }
    $pluginText = Get-Content $Plugin -Raw
    if (-not $pluginText.Contains('action.kind === "operatorDeckSlot" ? "CYCLE"')) { throw 'Cycle transient behavior is missing.' }
    $node=Get-Command node.exe -ErrorAction Stop
    foreach($file in @($Actions,$Status,$Plugin)){& $node.Source --check $file;if($LASTEXITCODE -ne 0){throw "Node validation failed: $file"}}
}

$temp=Join-Path $env:TEMP ('operator-deck-cycle-'+[guid]::NewGuid().ToString('N'))
$backup=$null
try {
    Assert-Baseline
    New-Item -ItemType Directory $temp -Force|Out-Null
    $a=Join-Path $temp 'actions.js';$s=Join-Path $temp 'status.js';$p=Join-Path $temp 'plugin.js'
    Add-CycleCommands (Get-Content $paths.sourceActions -Raw)|Set-Content $a -Encoding utf8
    Add-CycleStatus (Get-Content $paths.sourceStatus -Raw)|Set-Content $s -Encoding utf8
    Add-CycleTransient (Get-Content $paths.sourcePlugin -Raw)|Set-Content $p -Encoding utf8
    Test-Candidate $a $s $p
    $installed=(Get-Content $paths.sourceActions -Raw).Contains('longPressCommandPath') -and (([regex]::Matches((Get-Content $paths.sourceActions -Raw),'longPressCommandPath:.*OperatorDeck.*Cycle')).Count -eq 16)
    if(-not $Apply){
        $report=@('OPERATOR DECK QUADRANT CYCLING PREFLIGHT: PASS',"Already installed: $installed",'Quadrant long-hold actions: 16','Normal second tap still aligns in place; long hold enters cycle mode.','No files were changed. Re-run with -Apply only after reviewing this result.')-join"`n"
        $report|Tee-Object -Variable clip;$clip|Set-Clipboard;exit 0
    }
    $backup=Join-Path $PluginSourceRoot ('backups\operator-deck-cycle-'+(Get-Date -Format 'yyyyMMdd-HHmmss'));New-Item -ItemType Directory $backup -Force|Out-Null
    foreach($name in $paths.Keys){Copy-Item $paths[$name] (Join-Path $backup ($name+[IO.Path]::GetExtension($paths[$name])))}
    Copy-Item $a $paths.sourceActions -Force;Copy-Item $a $paths.installedActions -Force
    Copy-Item $s $paths.sourceStatus -Force;Copy-Item $s $paths.installedStatus -Force
    Copy-Item $p $paths.sourcePlugin -Force;Copy-Item $p $paths.installedPlugin -Force
    Write-Wrappers;Assert-Baseline;Test-Candidate $paths.sourceActions $paths.sourceStatus $paths.sourcePlugin
    $report=@('OPERATOR DECK QUADRANT CYCLING: VALIDATED',"Backup: $backup",'Quadrant long-hold actions: 16','Cycle state display and release suppression validated.','Source and installed files match; Node validation passed.','Stream Deck was not restarted automatically.')-join"`n";$report|Tee-Object -Variable clip;$clip|Set-Clipboard
} catch {
    if($backup -and (Test-Path $backup)){foreach($name in $paths.Keys){$saved=Join-Path $backup ($name+[IO.Path]::GetExtension($paths[$name]));if(Test-Path $saved){Copy-Item $saved $paths[$name] -Force}}}
    Write-Error "Operator Deck quadrant cycling patch failed: $($_.Exception.Message)";exit 1
} finally {if(Test-Path $temp){Remove-Item $temp -Recurse -Force}}
