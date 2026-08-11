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
}
'@
}
# The Stream Deck child is launched through hidden cmd.exe and can otherwise
# inherit a system-DPI context. Establish the workspace process context before
# monitor identity/cell geometry is read.
try { [EstateCodexDeskDpiV1]::SetProcessDpiAwarenessContext([IntPtr](-4)) | Out-Null } catch { }

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
    [EstateCodexDeskWindowV1]::ShowWindow($hwnd, 9) | Out-Null
    $ok = [EstateCodexDeskWindowV1]::SetWindowPos($hwnd, [IntPtr]::Zero, $Cell.x, $Cell.y, $Cell.width, $Cell.height, 0x0014)
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

function Wait-SeatCodexReady([int]$ConsoleProcessId) {
    $deadline = [DateTime]::UtcNow.AddSeconds(15)
    while ([DateTime]::UtcNow -lt $deadline) {
        $processes = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
        $owned = [System.Collections.Generic.HashSet[int]]::new()
        [void]$owned.Add($ConsoleProcessId)
        $changed = $true
        while ($changed) {
            $changed = $false
            foreach ($process in $processes) {
                if ($owned.Contains([int]$process.ParentProcessId) -and $owned.Add([int]$process.ProcessId)) { $changed = $true }
            }
        }
        $codex = $processes |
            Where-Object { $_.Name -eq 'codex.exe' -and $owned.Contains([int]$_.ProcessId) } |
            Select-Object -First 1
        $console = Get-Process -Id $ConsoleProcessId -ErrorAction SilentlyContinue
        if ($codex -and $console -and $console.MainWindowHandle -ne 0) {
            # The codex process is the strongest local readiness signal
            # available; allow its TUI one bounded render interval to settle.
            Start-Sleep -Milliseconds 750
            return $console
        }
        Start-Sleep -Milliseconds 250
    }
    throw "Codex TUI for process $ConsoleProcessId did not reach an input-ready process state."
}

function Send-NewSeatCodexStatus([string]$Seat, [int]$ConsoleProcessId) {
    if (-not ('EstateCodexDeskInputV1' -as [type])) {
        Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class EstateCodexDeskInputV1 {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr hWnd);
}
'@
    }
    Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
    $console = Wait-SeatCodexReady $ConsoleProcessId
    $target = [IntPtr]$console.MainWindowHandle
    $previous = [EstateCodexDeskInputV1]::GetForegroundWindow()
    [EstateCodexDeskInputV1]::BringWindowToTop($target) | Out-Null
    [EstateCodexDeskInputV1]::SetForegroundWindow($target) | Out-Null
    Start-Sleep -Milliseconds 150
    if ([EstateCodexDeskInputV1]::GetForegroundWindow() -ne $target) {
        throw "Could not focus the exact $Seat Codex console for /status input."
    }
    [System.Windows.Forms.SendKeys]::SendWait('/status{ENTER}')
    Start-Sleep -Milliseconds 300
    if ($previous -ne [IntPtr]::Zero) { [EstateCodexDeskInputV1]::SetForegroundWindow($previous) | Out-Null }
    Write-Host "Codex /status sent once to new $Seat session (PID $ConsoleProcessId)." -ForegroundColor Cyan
}

function Start-SeatCodex($Seat) {
    $script:CodexDeskSeatCreated = $false
    $marker = "$Seat-CODEX"
    $existing = Get-WindowByMarker $marker
    if (-not $existing) { $existing = Get-SeatLauncherProcess $Seat }
    if ($existing) { return $existing }
    if ($NoLaunch) { return $null }
    $interactive = Join-Path $PSScriptRoot 'Start-CodexInteractive.ps1'
    $command = "`$host.UI.RawUI.WindowTitle = '$marker'; Set-Location -LiteralPath '$repoRoot'; & '$interactive' -Seat '$Seat'"
    $conhost = Join-Path $env:SystemRoot 'System32\conhost.exe'
    $started = Start-Process -FilePath $conhost -Verb RunAs -ArgumentList @('pwsh.exe','-NoProfile','-ExecutionPolicy','Bypass','-NoExit','-Command',$command) -PassThru
    $script:CodexDeskSeatCreated = $true
    Start-Sleep -Seconds 2
    return $started
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
    $json = & pwsh -NoProfile -File $seatHelper
    if ($LASTEXITCODE -ne 0) { throw 'Codex seat configuration helper failed.' }
    return ($json -join "`n" | ConvertFrom-Json)
}

function Get-TargetMonitor {
    $json = & pwsh -NoProfile -File $monitorHelper -NoClipboard
    if ($LASTEXITCODE -ne 0) { throw 'Operator Deck monitor identity helper failed.' }
    $raw = $json -join "`n"
    $jsonStart = $raw.IndexOf('{')
    if ($jsonStart -lt 0) { throw 'Monitor identity helper did not return JSON.' }
    $jsonEnd = $raw.LastIndexOf('}')
    $layout = $raw.Substring($jsonStart, $jsonEnd - $jsonStart + 1) | ConvertFrom-Json
    $topRow = @($layout.monitors | Sort-Object { ($_.bounds.top + $_.bounds.bottom) / 2 } | Select-Object -First 2)
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
$monitor = Get-TargetMonitor
$cells = New-WorkspaceCells $monitor
$chromium = @(
    'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
    'C:\Users\wille\AppData\Local\ms-playwright\chromium-1234\chrome-win64\chrome.exe'
    'C:\Program Files\Chromium\Application\chrome.exe'
    'C:\Program Files\Chromium\chrome.exe'
    'C:\Program Files (x86)\Chromium\Application\chrome.exe'
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
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
$chromeMapPath = Join-Path $PSScriptRoot 'runtime\codex-desk-chrome-windows.json'
$chromiumMapPath = Join-Path $PSScriptRoot 'runtime\codex-desk-chromium-windows.json'
$chromeExe = 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
$chromeWindowMap = [ordered]@{}
$chromiumWindowMap = [ordered]@{}
if (Test-Path -LiteralPath $chromeMapPath) {
    try {
        $savedMap = (Get-Content -Raw -LiteralPath $chromeMapPath | ConvertFrom-Json).seats
        foreach ($property in $savedMap.PSObject.Properties) { $chromeWindowMap[$property.Name] = $property.Value }
    } catch { $chromeWindowMap = [ordered]@{} }
}
if (Test-Path -LiteralPath $chromiumMapPath) {
    try {
        $savedChromiumMap = (Get-Content -Raw -LiteralPath $chromiumMapPath | ConvertFrom-Json).seats
        foreach ($property in $savedChromiumMap.PSObject.Properties) { $chromiumWindowMap[$property.Name] = $property.Value }
    } catch { $chromiumWindowMap = [ordered]@{} }
}

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
    # SetWindowPos otherwise virtualizes coordinates for this PowerShell host
    # while a new Chrome app window is DPI 144. Use one explicit per-monitor
    # context so target cells always mean physical desktop pixels.
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
    [EstateCodexDeskChromiumV1]::ShowWindow([IntPtr]$Window.hwnd, 9) | Out-Null
    if (-not [EstateCodexDeskChromiumV1]::SetWindowPos([IntPtr]$Window.hwnd, [IntPtr]::Zero, $Cell.x, $Cell.y, $Cell.width, $Cell.height, 0x0014)) {
        throw "Chromium window placement failed for HWND $($Window.hwnd)."
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
    $saved = $null
    if ($chromiumWindowMap.Contains($Seat) -and $chromiumWindowMap.$Seat.profile_path_verified -eq $true) {
        $saved = Get-ChromiumWindows | Where-Object { $_.hwnd -eq [int64]$chromiumWindowMap.$Seat.hwnd } | Select-Object -First 1
    }
    if (-not $saved) {
        $before = @(Get-ChromiumWindows | ForEach-Object hwnd)
        $launchArguments = @(
            "--user-data-dir=`"$profilePath`""
            '--profile-directory="Default"'
            '--disable-background-mode'
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
        $chromiumWindowMap.Remove($seat)
        $chromeWindowMap.Remove($seat)
    }
    ([ordered]@{ seats=$chromiumWindowMap } | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $chromiumMapPath -Encoding utf8
    ([ordered]@{ seats=$chromeWindowMap } | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $chromeMapPath -Encoding utf8
    Write-Host ("Codex Desk StopAll timings: Codex={0}ms Chromium={1}ms Chrome={2}ms Total={3}ms" -f $codexMs, $chromiumMs, $chromeMs, $totalMs)
    Write-Host 'Codex Desk windows stopped cleanly.'
    exit 0
}

$runTop = $Mode -in @('Top', 'All')
$runMiddle = $Mode -in @('Middle', 'All')
$runBottom = $Mode -in @('Bottom', 'All')

if ($runTop) {
    foreach ($seat in @('C1','C2','C3')) {
        $window = Start-SeatCodex $seat
        if ($window) {
            $windowPid = Get-ConsoleWindowProcessId $window.Id
            Invoke-MovePid $windowPid $cells["$seat-CODEX"]
            Set-SeatWindowTitle $windowPid $seat-CODEX
            if ($script:CodexDeskSeatCreated) {
                Send-NewSeatCodexStatus $seat $windowPid
                Set-SeatWindowTitle $windowPid $seat-CODEX
            }
        }
    }
}

if (-not $PlanOnly -and $runMiddle) {
    foreach ($seatRecord in @($config.seats)) {
        Start-SeatChromium $seatRecord.seat_id $seatRecord $cells["$($seatRecord.seat_id)-CHROMIUM"]
    }
    ([ordered]@{ seats=$chromiumWindowMap } | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $chromiumMapPath -Encoding utf8
}

if (-not $PlanOnly -and $runBottom) {
    foreach ($seatRecord in @($config.seats)) {
        Start-SeatChrome $seatRecord.seat_id $seatRecord $cells["$($seatRecord.seat_id)-CHROME"]
    }
    ([ordered]@{ seats=$chromeWindowMap } | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $chromeMapPath -Encoding utf8
}

Write-Host "Codex Desk target: $($monitor.device) / logical top-right ($($monitor.work_area.width)x$($monitor.work_area.height))"
Write-Host "Workspace plan: $reportPath"
Write-Host "Chromium: $($report.chromium.status)"
Write-Host "Chrome: $($report.chrome.status)"
$report | ConvertTo-Json -Depth 12
