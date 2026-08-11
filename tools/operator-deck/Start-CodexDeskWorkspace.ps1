[CmdletBinding()]
param(
    [ValidateSet('Top', 'Middle', 'Bottom', 'All')]
    [string]$Mode = 'All',
    [switch]$PlanOnly,
    [switch]$NoLaunch,
    [switch]$NoMove,
    [switch]$RestartChromium,
    [switch]$StopChromium,
    [switch]$StopAll
)

$ErrorActionPreference = 'Stop'

# The Stream Deck process is intentionally not an interactive PowerShell
# session. Log the process boundary and all bootstrap inputs before any
# helper/configuration call can fail. This log is the durable cold-start
# evidence; the transient console is not.
$coldStartLog = Join-Path $PSScriptRoot 'runtime\codex-desk-cold-start.log'
$resolvedPowerShell = Join-Path $PSHOME 'pwsh.exe'
if (-not (Test-Path -LiteralPath $resolvedPowerShell)) { $resolvedPowerShell = (Get-Process -Id $PID -ErrorAction SilentlyContinue).Path }
function Write-ColdStartLog([string]$Message) {
    try {
        $directory = Split-Path -Parent $coldStartLog
        New-Item -ItemType Directory -Force -Path $directory -ErrorAction SilentlyContinue | Out-Null
        $now = Get-Date
        Add-Content -LiteralPath $coldStartLog -Value ("[local={0};utc={1}] {2}" -f $now.ToString('o'), $now.ToUniversalTime().ToString('o'), $Message) -Encoding utf8 -ErrorAction SilentlyContinue
    } catch { }
}
function Get-ProcessChainForLog {
    try {
        $all = @(Get-CimInstance Win32_Process -ErrorAction Stop)
        $current = $all | Where-Object ProcessId -eq $PID | Select-Object -First 1
        $chain = @()
        while ($current) {
            $chain += ("pid={0};parent_pid={1};name={2};command_line={3}" -f $current.ProcessId, $current.ParentProcessId, $current.Name, $current.CommandLine)
            $current = $all | Where-Object ProcessId -eq $current.ParentProcessId | Select-Object -First 1
        }
        return ($chain -join ' || ')
    } catch { return "process_chain_error=$($_.Exception.Message)" }
}
function Resolve-ExistingPathForLog([string[]]$Candidates) {
    foreach ($candidate in $Candidates) { if ($candidate -and (Test-Path -LiteralPath $candidate)) { return $candidate } }
    return '<unresolved>'
}
try {
    $self = Get-Process -Id $PID -ErrorAction SilentlyContinue
    $selfCommand = (Get-CimInstance Win32_Process -Filter "ProcessId = $PID" -ErrorAction SilentlyContinue).CommandLine
    $codexLogCandidates = @((Join-Path $env:APPDATA 'npm\codex.cmd'), (Join-Path $env:APPDATA 'npm\codex.ps1'))
    $chromeLogCandidates = @(
        (Join-Path $env:ProgramFiles 'Google\Chrome\Application\chrome.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Google\Chrome\Application\chrome.exe')
    )
    $chromiumLogCandidates = @(
        (Join-Path $env:ProgramFiles 'Chromium\Application\chrome.exe'),
        (Join-Path $env:ProgramFiles 'Chromium\chrome.exe'),
        (Join-Path ${env:ProgramFiles(x86)} 'Chromium\Application\chrome.exe')
    )
    Write-ColdStartLog '[PS-BEGIN]'
    Write-ColdStartLog ("pid={0};process={1};parent_chain={2}" -f $PID, $self.Path, (Get-ProcessChainForLog))
    Write-ColdStartLog ("cwd={0};command_line={1};arguments={2}" -f (Get-Location).Path, $selfCommand, (($args | ForEach-Object { $_ }) -join ' '))
    foreach ($name in @('PATH','PATHEXT','USERPROFILE','LOCALAPPDATA','APPDATA','ProgramFiles','ProgramFiles(x86)','CODEX_HOME')) {
        Write-ColdStartLog ("env_{0}={1}" -f $name, [Environment]::GetEnvironmentVariable($name))
    }
    Write-ColdStartLog ("resolved_powershell={0};resolved_script={1};resolved_codex={2};resolved_chrome={3};resolved_chromium={4}" -f $self.Path, $PSCommandPath, (Resolve-ExistingPathForLog $codexLogCandidates), (Resolve-ExistingPathForLog $chromeLogCandidates), (Resolve-ExistingPathForLog $chromiumLogCandidates))
    Write-ColdStartLog ("files_cmd={0};files_script={1};files_monitor_helper={2};files_status_helper={3};files_seat_helper={4}" -f (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'Start-CodexDeskWorkspace.cmd')), (Test-Path -LiteralPath $PSCommandPath), (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'Get-OperatorDeckMonitorLayout.ps1')), (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'Send-CodexStatus.ps1')), (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'Get-CodexSeatConfiguration.ps1')))
} catch { Write-ColdStartLog ("[PS-EARLY-DIAGNOSTIC-ERROR] {0}`n{1}" -f $_.Exception.Message, $_.ScriptStackTrace) }
trap {
    Write-ColdStartLog ("[PS-FAIL] exception={0}`nposition={1}`nstack={2}" -f $_.Exception.ToString(), $_.InvocationInfo.PositionMessage, $_.ScriptStackTrace)
    exit 1
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$seatHelper = Join-Path $PSScriptRoot 'Get-CodexSeatConfiguration.ps1'
$monitorHelper = Join-Path $PSScriptRoot 'Get-OperatorDeckMonitorLayout.ps1'
$operatorDeck = Join-Path $PSScriptRoot 'OperatorDeck.ahk'
$ahkCandidates = @(
    'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe',
    'C:\Program Files\AutoHotkey\v2\AutoHotkey.exe'
)
$ahk = $ahkCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (-not ('EstateCodexDeskDpiV1' -as [type])) {
    Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class EstateCodexDeskDpiV1 {
    [DllImport("user32.dll")] public static extern bool SetProcessDpiAwarenessContext(IntPtr dpiContext);
    [DllImport("user32.dll")] public static extern IntPtr SetThreadDpiAwarenessContext(IntPtr dpiContext);
}
'@
}
# Diagnostic/native context surface used before any workspace window placement.
if (-not ('EstateCodexDeskDiagnosticsV1' -as [type])) {
    Add-Type @'
using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
public static class EstateCodexDeskDiagnosticsV1 {
    [DllImport("shcore.dll")] public static extern int GetProcessDpiAwareness(IntPtr process, out int awareness);
    [DllImport("user32.dll")] public static extern IntPtr GetThreadDpiAwarenessContext();
    [DllImport("user32.dll")] public static extern int GetAwarenessFromDpiAwarenessContext(IntPtr context);
    [DllImport("user32.dll")] public static extern int GetSystemMetrics(int index);
}
'@
}
# The Stream Deck child is launched through hidden cmd.exe and can otherwise
# inherit a system-DPI context. Establish the workspace process context before
# monitor identity/cell geometry is read.
try { [EstateCodexDeskDpiV1]::SetProcessDpiAwarenessContext([IntPtr](-4)) | Out-Null } catch { }
try { [EstateCodexDeskDpiV1]::SetThreadDpiAwarenessContext([IntPtr](-4)) | Out-Null } catch { }

function Get-WindowByMarker([string]$Marker) {
    Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like "*$Marker*" } |
        Select-Object -First 1
}

function Get-SeatLauncherProcess([string]$Seat) {
    $needle = "Start-CodexInteractive.ps1' -Seat '$Seat'"
    $candidate = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine.Contains($needle) } |
        Sort-Object @{Expression={
            if ($_.Name -eq 'pwsh.exe' -and $_.ProcessId -and (Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue).MainWindowHandle -ne 0) { 0 }
            elseif ($_.Name -eq 'pwsh.exe') { 1 }
            else { 2 }
        }} |
        Select-Object -First 1
    if ($candidate) { return Get-Process -Id $candidate.ProcessId -ErrorAction SilentlyContinue }
}

function Invoke-MoveMarker([string]$Marker, $Cell) {
    if ($NoMove) { return }
    if (-not $ahk) { throw 'AutoHotkey v2 is required by the existing Operator Deck placement engine.' }
    $args = @($operatorDeck, 'move-marker', $Marker, $Cell.x, $Cell.y, $Cell.width, $Cell.height)
    $p = Start-Process -FilePath $ahk -ArgumentList $args -Wait -PassThru -WindowStyle Hidden
    if ($p.ExitCode -ne 0) { throw "Operator Deck placement failed for $Marker (exit $($p.ExitCode))." }
}

function Invoke-MovePid([int]$ProcessId, $Cell) {
    if ($NoMove) { return }
    if (-not ('EstateCodexDeskWindowV1' -as [type])) {
        Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class EstateCodexDeskWindowV1 {
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint flags);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern bool SetWindowText(IntPtr hWnd, string text);
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr hWnd);
    delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    public static IntPtr FindWindow(uint pid) {
        IntPtr found = IntPtr.Zero;
        EnumWindows((h, l) => { uint p; GetWindowThreadProcessId(h, out p); if (p == pid && IsWindowVisible(h) && found == IntPtr.Zero) found = h; return true; }, IntPtr.Zero);
        return found;
    }
}
'@
    }
    $windowProcess = Get-Process -Id $ProcessId -ErrorAction Stop
    $hwnd = $windowProcess.MainWindowHandle
    if ($hwnd -eq 0) { $hwnd = [EstateCodexDeskWindowV1]::FindWindow([uint32]$ProcessId) }
    if ($hwnd -eq 0) { Write-Warning "No independently movable console window found for process $ProcessId (Windows Terminal host); leaving its current geometry."; return $false }
    $previousDpiContext = [EstateCodexDeskDpiV1]::SetThreadDpiAwarenessContext([IntPtr](-4))
    try {
        [EstateCodexDeskWindowV1]::ShowWindow($hwnd, 9) | Out-Null
        $ok = [EstateCodexDeskWindowV1]::SetWindowPos($hwnd, [IntPtr]::Zero, $Cell.x, $Cell.y, $Cell.width, $Cell.height, 0x0014)
    } finally {
        if ($previousDpiContext -ne [IntPtr]::Zero) { [EstateCodexDeskDpiV1]::SetThreadDpiAwarenessContext($previousDpiContext) | Out-Null }
    }
    if (-not $ok) { Write-Warning "Native window placement failed for process $ProcessId."; return $false }
    return $true
}

function Set-SeatWindowTitle([int]$ProcessId, [string]$Title) {
    if (-not ('EstateCodexDeskTitleV1' -as [type])) {
        Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class EstateCodexDeskTitleV1 {
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern bool SetWindowText(IntPtr hWnd, string text);
}
'@
    }
    $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if (-not $process) { return }
    $hwnd = $process.MainWindowHandle
    if ($hwnd -ne 0) { [EstateCodexDeskTitleV1]::SetWindowText($hwnd, $Title) | Out-Null }
}

function Get-ConsoleWindowProcessId([int]$ProcessId) {
    $child = Get-CimInstance Win32_Process -Filter "name='pwsh.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.ParentProcessId -eq $ProcessId } | Select-Object -First 1
    if ($child) { return [int]$child.ProcessId }
    return $ProcessId
}

function Start-SeatCodex($Seat) {
    $marker = "$Seat-CODEX"
    $existing = Get-WindowByMarker $marker
    if (-not $existing) { $existing = Get-SeatLauncherProcess $Seat }
    if ($existing) { return $existing }
    if ($codexWindowMap.Contains($Seat)) {
        $saved = $codexWindowMap[$Seat]
        $savedProcess = Get-Process -Id ([int]$saved.window_pid) -ErrorAction SilentlyContinue
        $savedCommand = (Get-CimInstance Win32_Process -Filter "ProcessId = $([int]$saved.window_pid)" -ErrorAction SilentlyContinue).CommandLine
        if ($savedProcess -and $savedCommand -and $savedCommand.Contains("Start-CodexInteractive.ps1' -Seat '$Seat'")) {
            return $savedProcess
        }
        $codexWindowMap.Remove($Seat)
    }
    if ($NoLaunch) { return $null }
    $interactive = Join-Path $PSScriptRoot 'Start-CodexInteractive.ps1'
    $statusHelper = Join-Path $PSScriptRoot 'Send-CodexStatus.ps1'
    $command = "`$host.UI.RawUI.WindowTitle = '$marker'; Start-Process -FilePath 'pwsh.exe' -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-File','$statusHelper','-Seat','$Seat','-ConsolePid',`$PID) -WindowStyle Hidden; Set-Location -LiteralPath '$repoRoot'; & '$interactive' -Seat '$Seat'"
    $conhost = Join-Path $env:SystemRoot 'System32\conhost.exe'
    $started = Start-Process -FilePath $conhost -Verb RunAs -ArgumentList @('pwsh.exe','-NoProfile','-ExecutionPolicy','Bypass','-NoExit','-Command',$command) -PassThru
    Start-Sleep -Seconds 2
    return $started
}

function Test-WorkspaceReadiness {
    $checks = [ordered]@{
        powershell = [bool]($resolvedPowerShell -and (Test-Path -LiteralPath $resolvedPowerShell))
        codex_config = [bool]($config -and @($config.seats).Count -eq 3)
        codex_executable = [bool]((Get-Command codex.cmd -ErrorAction SilentlyContinue) -or (Test-Path -LiteralPath (Join-Path $env:APPDATA 'npm\codex.cmd')))
        elevation_host = [bool](Test-Path -LiteralPath (Join-Path $env:SystemRoot 'System32\conhost.exe'))
    }
    Write-ColdStartLog ("readiness={0}" -f (($checks.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join ','))
    if (-not $checks.powershell -or -not $checks.codex_config -or -not $checks.codex_executable -or -not $checks.elevation_host) {
        throw ('CODEX DESK not ready: ' + (($checks.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join ', '))
    }
    return $checks
}

function Close-SeatCodex([string]$Seat) {
    for ($attempt = 0; $attempt -lt 3; $attempt++) {
        $window = Get-Process -ErrorAction SilentlyContinue |
            Where-Object { $_.MainWindowTitle -eq "$Seat-CODEX" } |
            Select-Object -First 1
        if (-not $window) { $window = Get-WindowByMarker "$Seat-CODEX" }
        if (-not $window) { $window = Get-SeatLauncherProcess $Seat }
        if (-not $window) { return }
        $window.CloseMainWindow() | Out-Null
        $window.WaitForExit(5000) | Out-Null
        Start-Sleep -Milliseconds 250
    }
    if (Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -eq "$Seat-CODEX" }) {
        throw "Codex Desk terminal $Seat did not close gracefully."
    }
}

function Request-SeatCodexClose([string]$Seat) {
    $windows = @(Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -eq "$Seat-CODEX" })
    if ($windows.Count -eq 0) {
        $windows = @(Get-Process -ErrorAction SilentlyContinue |
            Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like "*$Seat-CODEX*" })
    }
    if ($windows.Count -eq 0) {
        $launcher = Get-SeatLauncherProcess $Seat
        if ($launcher) { $windows = @($launcher) }
    }
    foreach ($window in $windows) {
        try { $window.CloseMainWindow() | Out-Null } catch { }
    }
    return ($windows.Count -gt 0)
}

function Test-SeatCodexClosed([string]$Seat) {
    $windows = @(Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like "*$Seat-CODEX*" })
    if ($windows.Count -gt 0) { return $false }
    return (-not (Get-SeatLauncherProcess $Seat))
}

function Get-SeatConfig {
    $json = & $resolvedPowerShell -NoLogo -NoProfile -ExecutionPolicy Bypass -File $seatHelper
    if ($LASTEXITCODE -ne 0) { throw 'Codex seat configuration helper failed.' }
    return ($json -join "`n" | ConvertFrom-Json)
}

function Get-TargetMonitor {
    $json = & $resolvedPowerShell -NoLogo -NoProfile -ExecutionPolicy Bypass -File $monitorHelper -NoClipboard
    if ($LASTEXITCODE -ne 0) { throw 'Operator Deck monitor identity helper failed.' }
    $raw = $json -join "`n"
    $jsonStart = $raw.IndexOf('{')
    if ($jsonStart -lt 0) { throw 'Monitor identity helper did not return JSON.' }
    $jsonEnd = $raw.LastIndexOf('}')
    $layout = $raw.Substring($jsonStart, $jsonEnd - $jsonStart + 1) | ConvertFrom-Json
    $script:CodexDeskRawMonitorLayout = $layout
    # The monitor helper is PMv2-aware and returns physical desktop rectangles.
    # Keep those rectangles unchanged: placement also runs PMv2-aware, and the
    # independent physical screenshot demonstrated that 96-DPI normalization
    # moved the desk into the wrong desktop region.
    $physicalMonitors = @($layout.monitors | ForEach-Object {
        [pscustomobject]@{
            index=$_.index; device=$_.device; primary=$_.primary
            bounds=$_.bounds; work_area=$_.work_area
            reserved_edges=$_.reserved_edges; dpi=$_.dpi; slot_prefix=$_.slot_prefix
        }
    })
    $layout.monitors = $physicalMonitors
    $script:CodexDeskMonitorLayout = $layout
    $topRow = @($physicalMonitors | Sort-Object { ($_.bounds.top + $_.bounds.bottom) / 2 } | Select-Object -First 2)
    $script:CodexDeskMonitorCandidates = @($topRow)
    return $topRow | Sort-Object { $_.bounds.left } -Descending | Select-Object -First 1
}

function New-WorkspaceCells($Monitor) {
    $x = [int]$Monitor.work_area.left
    $y = [int]$Monitor.work_area.top
    $width = [int]$Monitor.work_area.width
    $height = [int]$Monitor.work_area.height
    $col = [math]::Floor($width / 3)
    $rowTop = [math]::Floor($height * 0.25)
    $rowMiddle = [math]::Floor($height * 0.25)
    $cells = [ordered]@{}
    foreach ($seatIndex in 0..2) {
        $seat = "C$($seatIndex + 1)"
        $cx = $x + ($seatIndex * $col)
        $cw = if ($seatIndex -eq 2) { $width - ($col * 2) } else { $col }
        $cells["$seat-CODEX"] = [pscustomobject]@{ x=$cx; y=$y; width=$cw; height=$rowTop }
        $cells["$seat-CHROMIUM"] = [pscustomobject]@{ x=$cx; y=$y+$rowTop; width=$cw; height=$rowMiddle }
        $cells["$seat-CHROME"] = [pscustomobject]@{ x=$cx; y=$y+$rowTop+$rowMiddle; width=$cw; height=$height-$rowTop-$rowMiddle }
    }
    return $cells
}

$config = Get-SeatConfig
Write-ColdStartLog ("seat_configuration=resolved;seat_count={0};homes={1}" -f @($config.seats).Count, ((@($config.seats) | ForEach-Object { "$($_.seat_id)=$($_.codex_home)" }) -join ','))
$monitor = Get-TargetMonitor
$cells = New-WorkspaceCells $monitor
$chromium = @(
    'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
    'C:\Users\wille\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe'
    'C:\Program Files\Chromium\Application\chrome.exe'
    'C:\Program Files\Chromium\chrome.exe'
    'C:\Program Files (x86)\Chromium\Application\chrome.exe'
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
Write-ColdStartLog ("runtime_resolved_chromium={0};runtime_resolved_chrome={1}" -f $chromium, (Resolve-ExistingPathForLog $chromeLogCandidates))
$chromeUserData = Join-Path $env:LOCALAPPDATA 'Google\Chrome\User Data'
$seatBrowserMappings = @($config.seats | Where-Object {
    $_.interactive_chrome_profile -and
    (Test-Path -LiteralPath (Join-Path $chromeUserData $_.interactive_chrome_profile))
})
$seatChromiumMappings = @($config.seats | Where-Object {
    $_.automation_chromium_profile -and (Test-Path -LiteralPath $_.automation_chromium_profile)
})

$report = [ordered]@{
    schema_version = 'codex_desk_workspace_v1'
    observed_at = (Get-Date).ToUniversalTime().ToString('o')
    target_monitor = $monitor
    cells = $cells
    codex_seats = @($config.seats | ForEach-Object { [ordered]@{ seat_id=$_.seat_id; codex_home=$_.codex_home; mode='interactive'; status='configured' } })
    chromium = [ordered]@{ executable=$chromium; configured_seats=@($seatChromiumMappings | ForEach-Object seat_id); status=if($chromium -and $seatChromiumMappings.Count -eq 3){'configured'}else{'unavailable/not configured'} }
    chrome = [ordered]@{ configured_seats=@($seatBrowserMappings | ForEach-Object seat_id); status=if($seatBrowserMappings.Count -eq 3){'configured'}else{'unavailable/not configured'} }
}
$reportPath = Join-Path $PSScriptRoot 'runtime\codex-desk-workspace.json'
$diagnosticPath = Join-Path $PSScriptRoot 'runtime\codex-desk-launch-diagnostics.json'
$batchPath = Join-Path $PSScriptRoot 'runtime\codex-desk-last-batch.json'
$chromeMapPath = Join-Path $PSScriptRoot 'runtime\codex-desk-chrome-windows.json'
$chromiumMapPath = Join-Path $PSScriptRoot 'runtime\codex-desk-chromium-windows.json'
$codexMapPath = Join-Path $PSScriptRoot 'runtime\codex-desk-codex-windows.json'
try {
    $runtimeDirectory = Split-Path -Parent $reportPath
    New-Item -ItemType Directory -Force -Path $runtimeDirectory | Out-Null
    $writeProbe = Join-Path $runtimeDirectory ('.codex-desk-write-probe-{0}.tmp' -f $PID)
    'probe' | Set-Content -LiteralPath $writeProbe -Encoding utf8
    Remove-Item -LiteralPath $writeProbe -Force
    Write-ColdStartLog ("runtime_directory={0};runtime_writable=True" -f $runtimeDirectory)
} catch {
    Write-ColdStartLog ("runtime_directory={0};runtime_writable=False;error={1}" -f (Split-Path -Parent $reportPath), $_.Exception.ToString())
    throw
}

function Get-WorkspaceProcessChain {
    $all = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
    $chain = @()
    $current = $all | Where-Object ProcessId -eq $PID | Select-Object -First 1
    while ($current) {
        $chain += [ordered]@{ pid=[int]$current.ProcessId; parent_pid=[int]$current.ParentProcessId; name=$current.Name; command_line=$current.CommandLine }
        $current = $all | Where-Object ProcessId -eq $current.ParentProcessId | Select-Object -First 1
    }
    return $chain
}

function Write-WorkspaceLaunchDiagnostics($Monitor, $Cells) {
    $process = Get-Process -Id $PID -ErrorAction SilentlyContinue
    $processAwareness = -1
    try { [void][EstateCodexDeskDiagnosticsV1]::GetProcessDpiAwareness($process.Handle, [ref]$processAwareness) } catch { }
    $threadContext = [EstateCodexDeskDiagnosticsV1]::GetThreadDpiAwarenessContext()
    $threadAwareness = -1
    try { $threadAwareness = [EstateCodexDeskDiagnosticsV1]::GetAwarenessFromDpiAwarenessContext($threadContext) } catch { }
    $sm = [ordered]@{
        x=[EstateCodexDeskDiagnosticsV1]::GetSystemMetrics(76)
        y=[EstateCodexDeskDiagnosticsV1]::GetSystemMetrics(77)
        width=[EstateCodexDeskDiagnosticsV1]::GetSystemMetrics(78)
        height=[EstateCodexDeskDiagnosticsV1]::GetSystemMetrics(79)
    }
    $diagnostic = [ordered]@{
        observed_at=(Get-Date).ToUniversalTime().ToString('o')
        launcher_pid=$PID
        powershell_path=$process.Path
        powershell_is_64_bit=[Environment]::Is64BitProcess
        process_dpi_awareness=$processAwareness
        thread_dpi_awareness_context=('0x{0:x}' -f $threadContext.ToInt64())
        thread_dpi_awareness=$threadAwareness
        virtual_screen=$sm
        process_chain=(Get-WorkspaceProcessChain)
        raw_monitor_map=$script:CodexDeskRawMonitorLayout.monitors
        monitor_candidates=$script:CodexDeskMonitorCandidates
        monitor_map=$script:CodexDeskMonitorLayout.monitors
        selected_monitor=$Monitor
        calculated_cells=$Cells
    }
    $diagnostic | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $diagnosticPath -Encoding utf8
}

Write-WorkspaceLaunchDiagnostics $monitor $cells
$chromeExe = 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
$readiness = Test-WorkspaceReadiness
# Runtime HWND/PID files are evidence only. They are intentionally not loaded
# as live state: after reboot PIDs and HWNDs may be recycled. Every invocation
# discovers live windows/processes again and writes a fresh map after identity
# validation.
$codexWindowMap = [ordered]@{}
$chromeWindowMap = [ordered]@{}
$chromiumWindowMap = [ordered]@{}

function Get-ChromeWindows {
    if (-not ('EstateCodexDeskChromeV1' -as [type])) {
        Add-Type @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public static class EstateCodexDeskChromeV1 {
    public class WindowRecord { public IntPtr Hwnd; public uint Pid; public string Title; public string ClassName; }
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowsProc callback, IntPtr state);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr hwnd);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr hwnd, StringBuilder text, int count);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetClassName(IntPtr hwnd, StringBuilder text, int count);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern bool SetWindowText(IntPtr hwnd, string text);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hwnd, IntPtr after, int x, int y, int w, int h, uint flags);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hwnd, out RECT rect);
    [DllImport("user32.dll")] public static extern IntPtr SetThreadDpiAwarenessContext(IntPtr dpiContext);
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hwnd, int command);
    [DllImport("user32.dll")] public static extern uint GetDpiForWindow(IntPtr hwnd);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hwnd, uint message, IntPtr wParam, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr hwnd);
    delegate bool EnumWindowsProc(IntPtr hwnd, IntPtr state);
    public static WindowRecord[] Windows() {
        var rows = new List<WindowRecord>();
        EnumWindows((hwnd, state) => {
            if (!IsWindowVisible(hwnd)) return true;
            uint pid; GetWindowThreadProcessId(hwnd, out pid);
            var title = new StringBuilder(512); GetWindowText(hwnd, title, title.Capacity);
            var cls = new StringBuilder(256); GetClassName(hwnd, cls, cls.Capacity);
            if (cls.ToString().StartsWith("Chrome_WidgetWin_")) rows.Add(new WindowRecord { Hwnd=hwnd, Pid=pid, Title=title.ToString(), ClassName=cls.ToString() });
            return true;
        }, IntPtr.Zero);
        return rows.ToArray();
    }
}
'@
    }
    return [EstateCodexDeskChromeV1]::Windows() | ForEach-Object {
        [pscustomobject]@{ hwnd=[int64]$_.Hwnd; pid=$_.Pid; title=$_.Title; class_name=$_.ClassName }
    }
}

function Move-ChromeWindow($Window, $Cell) {
    if ($NoMove) { return }
    # The existing placement process calls SetWindowPos with physical desktop
    # coordinates. Scaling again by GetDpiForWindow double-scales Chrome app
    # windows (for example 853x720 becomes 1280x1080 and spills monitors).
    $targetX = [int]$Cell.x
    $targetY = [int]$Cell.y
    $targetWidth = [int]$Cell.width
    $targetHeight = [int]$Cell.height
    $commandX = $targetX
    $commandY = $targetY
    $commandWidth = $targetWidth
    $commandHeight = $targetHeight
    # All rows use the canonical Estate 96-DPI desktop coordinate space. Keep
    # SetWindowPos in the matching system-DPI context regardless of caller.
    $previousDpiContext = [EstateCodexDeskChromeV1]::SetThreadDpiAwarenessContext([IntPtr](-4))
    try {
        [EstateCodexDeskChromeV1]::ShowWindow([IntPtr]$Window.hwnd, 9) | Out-Null
        for ($attempt = 0; $attempt -lt 2; $attempt++) {
            if (-not [EstateCodexDeskChromeV1]::SetWindowPos([IntPtr]$Window.hwnd, [IntPtr]::Zero, $commandX, $commandY, $commandWidth, $commandHeight, 0x0014)) {
                throw "Chrome window placement failed for HWND $($Window.hwnd)."
            }
            # Chrome can apply its startup/app-window bounds after the first
            # SetWindowPos. Read back the physical rectangle and correct once.
            Start-Sleep -Milliseconds 350
            $rect = New-Object EstateCodexDeskChromeV1+RECT
            if (-not [EstateCodexDeskChromeV1]::GetWindowRect([IntPtr]$Window.hwnd, [ref]$rect)) {
                throw "Chrome window rectangle could not be read for HWND $($Window.hwnd)."
            }
            if ($rect.Left -eq $targetX -and $rect.Top -eq $targetY -and
                ($rect.Right - $rect.Left) -eq $targetWidth -and
                ($rect.Bottom - $rect.Top) -eq $targetHeight) {
                return
            }
            if ($attempt -eq 0) {
                # Derive the next SetWindowPos arguments from the observed
                # physical/API scale. This handles a newly created DPI-
                # virtualized app window without hard-coded offsets.
                $actualWidth = $rect.Right - $rect.Left
                $actualHeight = $rect.Bottom - $rect.Top
                if ($actualWidth -le 0 -or $actualHeight -le 0) { break }
                $scaleX = $actualWidth / [double]$targetWidth
                $scaleY = $actualHeight / [double]$targetHeight
                if ($scaleX -le 0 -or $scaleY -le 0) { break }
                $commandX = [int][math]::Round($targetX / $scaleX)
                $commandY = [int][math]::Round($targetY / $scaleY)
                $commandWidth = [int][math]::Round($targetWidth / $scaleX)
                $commandHeight = [int][math]::Round($targetHeight / $scaleY)
            }
        }
    } finally {
        if ($previousDpiContext -ne [IntPtr]::Zero) {
            [EstateCodexDeskChromeV1]::SetThreadDpiAwarenessContext($previousDpiContext) | Out-Null
        }
    }
    throw "Chrome window HWND $($Window.hwnd) did not stabilize at $targetX,$targetY ${targetWidth}x${targetHeight}."
}

function Close-ManagedChromeWindow($Window) {
    if ($Window -and [EstateCodexDeskChromeV1]::IsWindow([IntPtr]$Window.hwnd)) {
        [EstateCodexDeskChromeV1]::PostMessage([IntPtr]$Window.hwnd, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null
        Start-Sleep -Milliseconds 500
    }
}

function Close-SeatChrome([string]$Seat) {
    if (-not $chromeWindowMap.Contains($Seat)) { return }
    $hwnd = [int64]$chromeWindowMap.$Seat.hwnd
    for ($attempt = 0; $attempt -lt 10; $attempt++) {
        $window = Get-ChromeWindows | Where-Object { $_.hwnd -eq $hwnd } | Select-Object -First 1
        if (-not $window) { break }
        Close-ManagedChromeWindow $window
        Start-Sleep -Milliseconds 250
    }
    if (Get-ChromeWindows | Where-Object { $_.hwnd -eq $hwnd }) {
        throw "Codex Desk Chrome window $Seat did not close gracefully."
    }
    $chromeWindowMap.Remove($Seat)
}

function Request-SeatChromeClose([string]$Seat) {
    if (-not $chromeWindowMap.Contains($Seat)) { return $false }
    $hwnd = [int64]$chromeWindowMap.$Seat.hwnd
    $window = Get-ChromeWindows | Where-Object { $_.hwnd -eq $hwnd } | Select-Object -First 1
    if ($window) {
        [EstateCodexDeskChromeV1]::PostMessage([IntPtr]$window.hwnd, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null
        return $true
    }
    return $false
}

function Test-SeatChromeClosed([string]$Seat) {
    if (-not $chromeWindowMap.Contains($Seat)) { return $true }
    $hwnd = [int64]$chromeWindowMap.$Seat.hwnd
    return (@(Get-ChromeWindows | Where-Object { $_.hwnd -eq $hwnd }).Count -eq 0)
}

function Get-ChromeProfilePathFromUi($Window) {
    Add-Type -AssemblyName UIAutomationClient -ErrorAction Stop
    Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
    $root = [System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$Window.hwnd)
    $condition = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::AutomationIdProperty, 'view_1012'
    )
    $address = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $condition)
    if (-not $address) { throw "Chrome verification window has no address control for HWND $($Window.hwnd)." }
    $value = $address.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
    $value.SetValue('chrome://version/')
    [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
    Start-Sleep -Seconds 2
    $root = [System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$Window.hwnd)
    $all = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
    for ($index = 0; $index -lt $all.Count; $index++) {
        $name = $all.Item($index).Current.Name
        if ($name -match '(?i)Google\\Chrome\\User Data\\Profile \d+$') {
            try {
                $root = [System.Windows.Automation.AutomationElement]::FromHandle([IntPtr]$Window.hwnd)
                $address = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $condition)
                $value = $address.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
                $value.SetValue('https://chatgpt.com/')
                [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
            } catch { }
            return $name
        }
    }
    throw "Chrome did not expose a profile path for HWND $($Window.hwnd)."
}

function Get-ChromeWindowCommandLine($Window) {
    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $($Window.pid)" -ErrorAction SilentlyContinue
    if ($process) { return [string]$process.CommandLine }
    return ''
}

function Test-ChromeWindowProfile($Window, [string]$ProfilePath, [string]$ProfileName, $VerifiedRecord = $null) {
    if (-not $Window) { return $false }
    # Chrome app windows in an existing browser process do not retain the
    # profile-launch switches on their owner process. A persisted record is
    # accepted only when it was written after the chrome://version proof and
    # the HWND is still the same visible ChatGPT app window. This prevents a
    # stale HWND from being treated as a seat merely because it exists.
    if ($VerifiedRecord -and
        $VerifiedRecord.profile_path_verified -eq $true -and
        $VerifiedRecord.app_mode -eq $true -and
        [string]$VerifiedRecord.profile -eq $ProfileName -and
        [string]$VerifiedRecord.user_data_dir -eq $chromeUserData -and
        $Window.title -eq 'ChatGPT') {
        return $true
    }
    $commandLine = Get-ChromeWindowCommandLine $Window
    $rootNeedle = '--user-data-dir="?' + [regex]::Escape($chromeUserData) + '"?'
    $profileNeedle = '--profile-directory="?' + [regex]::Escape($ProfileName) + '"?'
    return $commandLine -match $rootNeedle -and
        $commandLine -match $profileNeedle -and
        $ProfilePath -eq (Join-Path $chromeUserData $ProfileName)
}

function Find-ChromeWindowForProfile([string]$ProfilePath, [string]$ProfileName) {
    foreach ($window in @(Get-ChromeWindows)) {
        if (Test-ChromeWindowProfile $window $ProfilePath $ProfileName) { return $window }
    }
    return $null
}

function Start-SeatChrome([string]$Seat, $SeatRecord, $Cell) {
    $profileName = [string]$SeatRecord.interactive_chrome_profile
    $profilePath = Join-Path $chromeUserData $profileName
    if (-not (Test-Path -LiteralPath $profilePath)) { throw "Configured Chrome profile is missing for $Seat`: $profilePath" }
    $saved = $null
    if ($chromeWindowMap.Contains($Seat)) {
        if ($chromeWindowMap.$Seat.app_mode -ne $true) {
            $old = Get-ChromeWindows | Where-Object { $_.hwnd -eq [int64]$chromeWindowMap.$Seat.hwnd } | Select-Object -First 1
            Close-ManagedChromeWindow $old
            $chromeWindowMap.Remove($Seat)
        }
    }
    if ($chromeWindowMap.Contains($Seat)) {
        if ($chromeWindowMap.$Seat.profile_path_verified -eq $true) {
            $candidate = Get-ChromeWindows | Where-Object { $_.hwnd -eq [int64]$chromeWindowMap.$Seat.hwnd } | Select-Object -First 1
            if (Test-ChromeWindowProfile $candidate $profilePath $profileName $chromeWindowMap.$Seat) { $saved = $candidate }
        }
        # The persisted record is written only after chrome://version proved the
        # exact profile path. Do not infer identity from a page title or profile
        # menu label on reuse; those are not stable window metadata.
    }
    if (-not $saved) { $saved = Find-ChromeWindowForProfile $profilePath $profileName }
    $profilePathVerified = $false
    if (-not $saved) {
        # App windows do not expose a writable omnibox. Verify the exact
        # profile first in a disposable normal chrome://version window, then
        # launch the operating ChatGPT app with the identical profile args.
        $probeBefore = @(Get-ChromeWindows | ForEach-Object hwnd)
        $probeArguments = @(
            "--user-data-dir=`"$chromeUserData`""
            "--profile-directory=`"$profileName`""
            '--new-window'
            'https://chatgpt.com/'
        )
        Start-Process -FilePath $chromeExe -ArgumentList $probeArguments | Out-Null
        $probe = $null
        for ($i=0; $i -lt 15; $i++) {
            Start-Sleep -Milliseconds 500
            $probe = Get-ChromeWindows | Where-Object { $probeBefore -notcontains $_.hwnd } | Select-Object -First 1
            if ($probe) { break }
        }
        if (-not $probe) { throw "Chrome did not expose a profile verification app window for $Seat." }
        $actualProfilePath = Get-ChromeProfilePathFromUi $probe
        if ($actualProfilePath -ne $profilePath) {
            Close-ManagedChromeWindow $probe
            throw "Chrome profile mismatch for $Seat`: expected $profilePath, observed $actualProfilePath."
        }
        Close-ManagedChromeWindow $probe
        $before = @(Get-ChromeWindows | ForEach-Object hwnd)
        $launchArguments = @(
            "--user-data-dir=`"$chromeUserData`""
            "--profile-directory=`"$profileName`""
            '--app=https://chatgpt.com/'
        )
        Start-Process -FilePath $chromeExe -ArgumentList $launchArguments | Out-Null
        for ($i=0; $i -lt 15; $i++) {
            Start-Sleep -Milliseconds 500
            $saved = Get-ChromeWindows | Where-Object { $before -notcontains $_.hwnd } | Select-Object -First 1
            if ($saved) { break }
        }
        if (-not $saved) { throw "Chrome did not expose a new top-level window for $Seat." }
        $profilePathVerified = $true
    } else {
        $profilePathVerified = $chromeWindowMap.$Seat.profile_path_verified
    }
    Move-ChromeWindow $saved $Cell
    $chromeWindowMap[$Seat] = [ordered]@{
        hwnd=$saved.hwnd
        pid=$saved.pid
        profile=$profileName
        user_data_dir=$chromeUserData
        app_mode=$true
        profile_path_verified=$profilePathVerified
        launch_arguments=@("--user-data-dir=`"$chromeUserData`"", "--profile-directory=`"$profileName`"", '--app=https://chatgpt.com/')
    }
}

function Get-ChromiumWindows {
    if (-not ('EstateCodexDeskChromiumV1' -as [type])) {
        Add-Type @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public static class EstateCodexDeskChromiumV1 {
    public class WindowRecord { public IntPtr Hwnd; public uint Pid; public string Title; public string ClassName; }
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowsProc callback, IntPtr state);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr hwnd);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr hwnd, StringBuilder text, int count);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetClassName(IntPtr hwnd, StringBuilder text, int count);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern bool SetWindowText(IntPtr hwnd, string text);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr hwnd, IntPtr after, int x, int y, int w, int h, uint flags);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hwnd, int command);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr hwnd, uint message, IntPtr wParam, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr hwnd);
    delegate bool EnumWindowsProc(IntPtr hwnd, IntPtr state);
    public static WindowRecord[] Windows() {
        var rows = new List<WindowRecord>();
        EnumWindows((hwnd, state) => {
            if (!IsWindowVisible(hwnd)) return true;
            uint pid; GetWindowThreadProcessId(hwnd, out pid);
            var title = new StringBuilder(512); GetWindowText(hwnd, title, title.Capacity);
            var cls = new StringBuilder(256); GetClassName(hwnd, cls, cls.Capacity);
            if (cls.ToString().StartsWith("Chrome_WidgetWin_")) rows.Add(new WindowRecord { Hwnd=hwnd, Pid=pid, Title=title.ToString(), ClassName=cls.ToString() });
            return true;
        }, IntPtr.Zero);
        return rows.ToArray();
    }
    public static WindowRecord[] AllWindows() {
        var rows = new List<WindowRecord>();
        EnumWindows((hwnd, state) => {
            uint pid; GetWindowThreadProcessId(hwnd, out pid);
            var title = new StringBuilder(512); GetWindowText(hwnd, title, title.Capacity);
            var cls = new StringBuilder(256); GetClassName(hwnd, cls, cls.Capacity);
            if (cls.ToString().StartsWith("Chrome_WidgetWin_")) rows.Add(new WindowRecord { Hwnd=hwnd, Pid=pid, Title=title.ToString(), ClassName=cls.ToString() });
            return true;
        }, IntPtr.Zero);
        return rows.ToArray();
    }
}

'@
    }
    return [EstateCodexDeskChromiumV1]::Windows() | ForEach-Object {
        [pscustomobject]@{ hwnd=[int64]$_.Hwnd; pid=$_.Pid; title=$_.Title; class_name=$_.ClassName }
    }
}

function Move-ChromiumWindow($Window, $Cell) {
    if ($NoMove) { return }
    $previousDpiContext = [EstateCodexDeskDpiV1]::SetThreadDpiAwarenessContext([IntPtr](-4))
    try {
        [EstateCodexDeskChromiumV1]::ShowWindow([IntPtr]$Window.hwnd, 9) | Out-Null
        if (-not [EstateCodexDeskChromiumV1]::SetWindowPos([IntPtr]$Window.hwnd, [IntPtr]::Zero, $Cell.x, $Cell.y, $Cell.width, $Cell.height, 0x0014)) {
            throw "Chromium window placement failed for HWND $($Window.hwnd)."
        }
    } finally {
        if ($previousDpiContext -ne [IntPtr]::Zero) { [EstateCodexDeskDpiV1]::SetThreadDpiAwarenessContext($previousDpiContext) | Out-Null }
    }
}

function Get-AllChromiumWindows {
    return [EstateCodexDeskChromiumV1]::AllWindows() | ForEach-Object {
        [pscustomobject]@{ hwnd=[int64]$_.Hwnd; pid=$_.Pid; title=$_.Title; class_name=$_.ClassName }
    }
}

function Get-ChromiumSeatProcesses([string]$ProfilePath) {
    $needle = $ProfilePath.Replace('/', '\')
    return @(Get-CimInstance Win32_Process -Filter "Name = 'chrome.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine.IndexOf($needle, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 })
}

function Find-ChromiumWindowForProfile([string]$ProfilePath) {
    $processes = @(Get-ChromiumSeatProcesses $ProfilePath | ForEach-Object ProcessId)
    if ($processes.Count -eq 0) { return $null }
    return Get-ChromiumWindows | Where-Object { $processes -contains $_.pid } | Select-Object -First 1
}

function Request-SeatChromiumClose([string]$Seat) {
    $record = $chromiumWindowMap[$Seat]
    if (-not $record) { return $null }
    $processes = Get-ChromiumSeatProcesses $record.profile_path
    $pids = @($processes | ForEach-Object ProcessId)
    foreach ($window in @(Get-AllChromiumWindows | Where-Object { $pids -contains $_.pid })) {
        [EstateCodexDeskChromiumV1]::PostMessage([IntPtr]$window.hwnd, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null
    }
    return [pscustomobject]@{ seat=$Seat; hwnd=[int64]$record.hwnd; profile_path=$record.profile_path }
}

function Test-SeatChromiumClosed($Request) {
    if (-not $Request) { return $true }
    $windowAlive = Get-ChromiumWindows | Where-Object { $_.hwnd -eq $Request.hwnd }
    $processes = Get-ChromiumSeatProcesses $Request.profile_path
    return (-not $windowAlive -and $processes.Count -eq 0)
}

function Close-SeatChromium([string]$Seat) {
    $request = Request-SeatChromiumClose $Seat
    if (-not $request) { return }
    for ($i=0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        if (Test-SeatChromiumClosed $request) { return }
    }
    throw "Chromium $Seat did not complete graceful shutdown; no forced termination was attempted."
}

function Start-SeatChromium([string]$Seat, $SeatRecord, $Cell) {
    if (-not $chromium) { throw 'Playwright Chromium executable is unavailable.' }
    $profilePath = [string]$SeatRecord.automation_chromium_profile
    if (-not $profilePath) { throw "Chromium automation profile is unset for $Seat." }
    New-Item -ItemType Directory -Force -Path $profilePath | Out-Null

    function Repair-IsolatedChromiumExitState([string]$Path) {
        $preferences = Join-Path $Path 'Default\Preferences'
        if (-not (Test-Path -LiteralPath $preferences)) { return 'not_present' }
        try {
            $json = Get-Content -Raw -LiteralPath $preferences | ConvertFrom-Json
            $exitType = [string]$json.profile.exit_type
            if ($exitType -and $exitType -ne 'Normal') {
                $json.profile.exit_type = 'Normal'
                $tmp = "$preferences.codex-desk.tmp"
                $json | ConvertTo-Json -Depth 100 -Compress | Set-Content -LiteralPath $tmp -Encoding utf8
                Move-Item -LiteralPath $tmp -Destination $preferences -Force
                return "repaired_$exitType"
            }
            return "already_$exitType"
        } catch {
            throw "Could not inspect isolated Chromium exit state for $Seat`: $($_.Exception.Message)"
        }
    }
    $saved = $null
    if ($chromiumWindowMap.Contains($Seat) -and $chromiumWindowMap.$Seat.profile_path_verified -eq $true) {
        $saved = Get-ChromiumWindows | Where-Object { $_.hwnd -eq [int64]$chromiumWindowMap.$Seat.hwnd } | Select-Object -First 1
    }
    if (-not $saved) {
        # Cold-start discovery is based on the live process command line, never
        # on an HWND/PID saved before reboot.
        $saved = Find-ChromiumWindowForProfile $profilePath
    }
    if (-not $saved) {
        # Only touch the isolated Preferences file after proving that no live
        # Chromium process owns this profile.
        if ((Get-ChromiumSeatProcesses $profilePath).Count -eq 0) {
            $exitState = Repair-IsolatedChromiumExitState $profilePath
        }
        $before = @(Get-ChromiumWindows | ForEach-Object hwnd)
        $launchArguments = @(
            "--user-data-dir=`"$profilePath`""
            '--profile-directory="Default"'
            '--disable-background-mode'
            '--disable-session-crashed-bubble'
            '--app=data:text/html,%3Ctitle%3ECodex%20Desk%20Chromium%3C%2Ftitle%3E'
        )
        Start-Process -FilePath $chromium -ArgumentList $launchArguments | Out-Null
        for ($i=0; $i -lt 20; $i++) {
            Start-Sleep -Milliseconds 500
            $saved = Get-ChromiumWindows | Where-Object { $before -notcontains $_.hwnd } | Select-Object -First 1
            if ($saved) { break }
        }
        if (-not $saved) { throw "Chromium did not expose a new top-level window for $Seat." }
    }
    [EstateCodexDeskChromiumV1]::SetWindowText([IntPtr]$saved.hwnd, "$Seat CHROMIUM") | Out-Null
    Move-ChromiumWindow $saved $Cell
    $chromiumWindowMap[$Seat] = [ordered]@{
        hwnd=$saved.hwnd
        profile_path=$profilePath
        profile_path_verified=$true
        persistent=$true
        app_mode=$true
        launch_arguments=@("--user-data-dir=`"$profilePath`"", '--profile-directory="Default"', '--disable-background-mode', '--app=data:text/html,%3Ctitle%3ECodex%20Desk%20Chromium%3C%2Ftitle%3E')
    }
}

function Import-ValidatedRuntimeMaps {
    foreach ($pathAndMap in @(
        [pscustomobject]@{ path=$codexMapPath; map=$codexWindowMap; kind='codex' },
        [pscustomobject]@{ path=$chromiumMapPath; map=$chromiumWindowMap; kind='chromium' },
        [pscustomobject]@{ path=$chromeMapPath; map=$chromeWindowMap; kind='chrome' }
    )) {
        if (-not (Test-Path -LiteralPath $pathAndMap.path)) { continue }
        try { $savedSeats = (Get-Content -Raw -LiteralPath $pathAndMap.path | ConvertFrom-Json).seats } catch { continue }
        foreach ($property in $savedSeats.PSObject.Properties) {
            $seat = $property.Name; $record = $property.Value
            if ($pathAndMap.kind -eq 'codex') {
                $process = Get-Process -Id ([int]$record.window_pid) -ErrorAction SilentlyContinue
                $command = if ($process) { (Get-CimInstance Win32_Process -Filter "ProcessId = $([int]$record.window_pid)" -ErrorAction SilentlyContinue).CommandLine } else { '' }
                if ($process -and $command -and $command.Contains("Start-CodexInteractive.ps1' -Seat '$seat'")) { $pathAndMap.map[$seat] = $record }
            } elseif ($pathAndMap.kind -eq 'chromium') {
                $live = Get-ChromiumWindows | Where-Object { $_.hwnd -eq [int64]$record.hwnd } | Select-Object -First 1
                $command = if ($live) { (Get-CimInstance Win32_Process -Filter "ProcessId = $([int]$live.pid)" -ErrorAction SilentlyContinue).CommandLine } else { '' }
                if ($live -and $command -and $command.IndexOf([string]$record.profile_path, [StringComparison]::OrdinalIgnoreCase) -ge 0) { $pathAndMap.map[$seat] = $record }
            } else {
                $live = Get-ChromeWindows | Where-Object { $_.hwnd -eq [int64]$record.hwnd } | Select-Object -First 1
                $profilePath = Join-Path $chromeUserData ([string]$record.profile)
                if (Test-ChromeWindowProfile $live $profilePath ([string]$record.profile) $record) { $pathAndMap.map[$seat] = $record }
            }
        }
    }
}

Import-ValidatedRuntimeMaps

$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $reportPath -Encoding utf8

if ($PlanOnly) { $report | ConvertTo-Json -Depth 12; exit 0 }

if ($RestartChromium) {
    Get-ChromiumWindows | Out-Null
    foreach ($seat in @('C1','C2','C3')) {
        Close-SeatChromium $seat
        $chromiumWindowMap.Remove($seat)
    }
}

if ($StopChromium) {
    Get-ChromiumWindows | Out-Null
    foreach ($seat in @('C1','C2','C3')) {
        Close-SeatChromium $seat
        $chromiumWindowMap.Remove($seat)
    }
    ([ordered]@{ seats=$chromiumWindowMap } | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $chromiumMapPath -Encoding utf8
    Write-Host 'Chromium automation seats stopped cleanly.'
    exit 0
}

if ($StopAll) {
    Get-ChromiumWindows | Out-Null
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $codexSeats = @()
    $chromiumRequests = @()
    $chromeSeats = @()
    foreach ($seat in @('C1','C2','C3')) {
        if (Request-SeatCodexClose $seat) { $codexSeats += $seat }
        $chromiumRequest = Request-SeatChromiumClose $seat
        if ($chromiumRequest) { $chromiumRequests += $chromiumRequest }
        if (Request-SeatChromeClose $seat) { $chromeSeats += $seat }
    }
    $codexDone = ($codexSeats.Count -eq 0)
    $chromiumDone = ($chromiumRequests.Count -eq 0)
    $chromeDone = ($chromeSeats.Count -eq 0)
    $codexMs = if ($codexDone) { 0 } else { $null }
    $chromiumMs = if ($chromiumDone) { 0 } else { $null }
    $chromeMs = if ($chromeDone) { 0 } else { $null }
    for ($i = 0; $i -lt 60 -and -not ($codexDone -and $chromiumDone -and $chromeDone); $i++) {
        if (-not $codexDone) {
            $codexDone = (@($codexSeats | Where-Object { -not (Test-SeatCodexClosed $_) }).Count -eq 0)
            if ($codexDone) { $codexMs = $stopwatch.ElapsedMilliseconds }
        }
        if (-not $chromiumDone) {
            $chromiumDone = (@($chromiumRequests | Where-Object { -not (Test-SeatChromiumClosed $_) }).Count -eq 0)
            if ($chromiumDone) { $chromiumMs = $stopwatch.ElapsedMilliseconds }
        }
        if (-not $chromeDone) {
            $chromeDone = (@($chromeSeats | Where-Object { -not (Test-SeatChromeClosed $_) }).Count -eq 0)
            if ($chromeDone) { $chromeMs = $stopwatch.ElapsedMilliseconds }
        }
        if (-not ($codexDone -and $chromiumDone -and $chromeDone)) {
            Start-Sleep -Milliseconds 250
        }
    }
    $totalMs = $stopwatch.ElapsedMilliseconds
    $remainingChromium = @(
        foreach ($seatRecord in @($config.seats)) {
            if ($seatRecord.automation_chromium_profile) {
                @(Get-ChromiumSeatProcesses $seatRecord.automation_chromium_profile)
            }
        }
    )
    $remainingCodex = @($codexSeats | Where-Object { -not (Test-SeatCodexClosed $_) })
    $remainingChrome = @($chromeSeats | Where-Object { -not (Test-SeatChromeClosed $_) })
    if ($remainingCodex.Count -gt 0) { throw "Codex Desk terminals remain after StopAll: $($remainingCodex -join ', ')." }
    if ($remainingChromium.Count -gt 0) { throw 'Codex Desk Chromium processes remain after graceful StopAll.' }
    if ($remainingChrome.Count -gt 0) { throw "Codex Desk Chrome windows remain after StopAll: $($remainingChrome -join ', ')." }
    foreach ($seat in @('C1','C2','C3')) {
        $codexWindowMap.Remove($seat)
        $chromiumWindowMap.Remove($seat)
        $chromeWindowMap.Remove($seat)
    }
    ([ordered]@{ seats=$codexWindowMap } | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $codexMapPath -Encoding utf8
    ([ordered]@{ seats=$chromiumWindowMap } | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $chromiumMapPath -Encoding utf8
    ([ordered]@{ seats=$chromeWindowMap } | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $chromeMapPath -Encoding utf8
    Write-Host ("Codex Desk StopAll timings: Codex={0}ms Chromium={1}ms Chrome={2}ms Total={3}ms" -f $codexMs, $chromiumMs, $chromeMs, $totalMs)
    Write-Host 'Codex Desk windows stopped cleanly.'
    exit 0
}

$runTop = $Mode -in @('Top', 'All')
$runMiddle = $Mode -in @('Middle', 'All')
$runBottom = $Mode -in @('Bottom', 'All')
$batchResults = [ordered]@{}

function Invoke-SeatBatch([string]$Kind, [scriptblock]$Action) {
    foreach ($seat in @('C1','C2','C3')) {
        try {
            & $Action $seat
            $batchResults["$Kind-$seat"] = [ordered]@{ seat=$seat; kind=$Kind; status='success' }
        } catch {
            $batchResults["$Kind-$seat"] = [ordered]@{ seat=$seat; kind=$Kind; status='failure'; error=$_.Exception.Message }
            Write-Warning "$Kind $seat failed; continuing remaining seats: $($_.Exception.Message)"
        }
    }
}

if ($runTop) {
    Invoke-SeatBatch 'codex' {
        param($seat)
        $window = Start-SeatCodex $seat
        if (-not $window) { throw "Codex launcher returned no process for $seat." }
        $windowPid = Get-ConsoleWindowProcessId $window.Id
        Invoke-MovePid $windowPid $cells["$seat-CODEX"]
        Set-SeatWindowTitle $windowPid $seat-CODEX
        $codexWindowMap[$seat] = [ordered]@{ window_pid=[int]$windowPid; seat=$seat; title="$seat-CODEX" }
    }
    ([ordered]@{ seats=$codexWindowMap } | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $codexMapPath -Encoding utf8
}

if (-not $PlanOnly -and $runMiddle) {
    Invoke-SeatBatch 'chromium' {
        param($seat)
        $seatRecord = @($config.seats) | Where-Object seat_id -eq $seat | Select-Object -First 1
        Start-SeatChromium $seat $seatRecord $cells["$seat-CHROMIUM"]
    }
    ([ordered]@{ seats=$chromiumWindowMap } | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $chromiumMapPath -Encoding utf8
}

if (-not $PlanOnly -and $runBottom) {
    Invoke-SeatBatch 'chrome' {
        param($seat)
        $seatRecord = @($config.seats) | Where-Object seat_id -eq $seat | Select-Object -First 1
        Start-SeatChrome $seat $seatRecord $cells["$seat-CHROME"]
    }
    ([ordered]@{ seats=$chromeWindowMap } | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $chromeMapPath -Encoding utf8
}

([ordered]@{ schema_version='codex_desk_batch_v1'; observed_at=(Get-Date).ToUniversalTime().ToString('o'); mode=$Mode; readiness=$readiness; results=$batchResults } | ConvertTo-Json -Depth 12) | Set-Content -LiteralPath $batchPath -Encoding utf8

Write-Host "Codex Desk target: $($monitor.device) / logical top-right ($($monitor.work_area.width)x$($monitor.work_area.height))"
Write-Host "Workspace plan: $reportPath"
Write-Host "Chromium: $($report.chromium.status)"
Write-Host "Chrome: $($report.chrome.status)"
$report | ConvertTo-Json -Depth 12
