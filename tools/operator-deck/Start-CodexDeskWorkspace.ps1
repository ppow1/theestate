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

function Get-WindowByMarker([string]$Marker) {
    Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like "*$Marker*" } |
        Select-Object -First 1
}

function Get-SeatLauncherProcess([string]$Seat) {
    $needle = "Start-CodexInteractive.ps1' -Seat '$Seat'"
    $candidate = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine.Contains($needle) } |
        Sort-Object @{Expression={ if ($_.Name -eq 'conhost.exe') { 0 } else { 1 } }} |
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

function Start-SeatCodex($Seat) {
    $marker = "$Seat-CODEX"
    $existing = Get-WindowByMarker $marker
    if (-not $existing) { $existing = Get-SeatLauncherProcess $Seat }
    if ($existing) { return $existing }
    if ($NoLaunch) { return $null }
    $interactive = Join-Path $PSScriptRoot 'Start-CodexInteractive.ps1'
    $command = "`$host.UI.RawUI.WindowTitle = '$marker'; Set-Location -LiteralPath '$repoRoot'; & '$interactive' -Seat '$Seat'"
    $conhost = Join-Path $env:SystemRoot 'System32\conhost.exe'
    $started = Start-Process -FilePath $conhost -Verb RunAs -ArgumentList @('pwsh.exe','-NoProfile','-ExecutionPolicy','Bypass','-NoExit','-Command',$command) -PassThru
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
    $targetDpi = [int]$monitor.dpi.x
    if ($targetDpi -le 0) { $targetDpi = 96 }
    $windowDpi = [int][EstateCodexDeskChromeV1]::GetDpiForWindow([IntPtr]$Window.hwnd)
    if ($windowDpi -le 0) { $windowDpi = $targetDpi }
    $scale = $windowDpi / $targetDpi
    $x = [int][math]::Round($Cell.x * $scale)
    $y = [int][math]::Round($Cell.y * $scale)
    $width = [int][math]::Round($Cell.width * $scale)
    $height = [int][math]::Round($Cell.height * $scale)
    [EstateCodexDeskChromeV1]::ShowWindow([IntPtr]$Window.hwnd, 9) | Out-Null
    if (-not [EstateCodexDeskChromeV1]::SetWindowPos([IntPtr]$Window.hwnd, [IntPtr]::Zero, $x, $y, $width, $height, 0x0014)) {
        throw "Chrome window placement failed for HWND $($Window.hwnd)."
    }
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
            $saved = Get-ChromeWindows | Where-Object { $_.hwnd -eq [int64]$chromeWindowMap.$Seat.hwnd } | Select-Object -First 1
        }
        # The persisted record is written only after chrome://version proved the
        # exact profile path. Do not infer identity from a page title or profile
        # menu label on reuse; those are not stable window metadata.
    }
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

function Close-SeatChromium([string]$Seat) {
    $record = $chromiumWindowMap[$Seat]
    if (-not $record) { return }
    $processes = Get-ChromiumSeatProcesses $record.profile_path
    $pids = @($processes | ForEach-Object ProcessId)
    foreach ($window in @(Get-AllChromiumWindows | Where-Object { $pids -contains $_.pid })) {
        [EstateCodexDeskChromiumV1]::PostMessage([IntPtr]$window.hwnd, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null
    }
    for ($i=0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        $windowAlive = Get-ChromiumWindows | Where-Object { $_.hwnd -eq [int64]$record.hwnd }
        $processes = Get-ChromiumSeatProcesses $record.profile_path
        if (-not $windowAlive -and $processes.Count -eq 0) { return }
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
    foreach ($seat in @('C1','C2','C3')) {
        Close-SeatChromium $seat
        $chromiumWindowMap.Remove($seat)
        Close-SeatCodex $seat
        Close-SeatChrome $seat
    }
    $remainingChromium = @(
        foreach ($seatRecord in @($config.seats)) {
            if ($seatRecord.automation_chromium_profile) {
                Get-ChromiumSeatProcesses $seatRecord.automation_chromium_profile
            }
        }
    )
    if ($remainingChromium.Count -gt 0) { throw 'Codex Desk Chromium processes remain after graceful StopAll.' }
    ([ordered]@{ seats=$chromiumWindowMap } | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $chromiumMapPath -Encoding utf8
    ([ordered]@{ seats=$chromeWindowMap } | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $chromeMapPath -Encoding utf8
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
