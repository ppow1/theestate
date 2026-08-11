[CmdletBinding()]
param(
    [switch]$PlanOnly,
    [switch]$NoLaunch,
    [switch]$NoMove
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
$chromium = @('C:\Program Files\Chromium\Application\chrome.exe','C:\Program Files\Chromium\chrome.exe','C:\Program Files (x86)\Chromium\Application\chrome.exe') | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
$seatBrowserMappings = @($config.seats | Where-Object { $_.interactive_chrome_profile -and (Test-Path -LiteralPath $_.interactive_chrome_profile) })

$report = [ordered]@{
    schema_version = 'codex_desk_workspace_v1'
    observed_at = (Get-Date).ToUniversalTime().ToString('o')
    target_monitor = $monitor
    cells = $cells
    codex_seats = @($config.seats | ForEach-Object { [ordered]@{ seat_id=$_.seat_id; codex_home=$_.codex_home; mode='interactive'; status='configured' } })
    chromium = [ordered]@{ executable=$chromium; configured_seats=@($seatBrowserMappings | ForEach-Object seat_id); status=if($chromium -and $seatBrowserMappings.Count -eq 3){'configured'}else{'unavailable/not configured'} }
    chrome = [ordered]@{ configured_seats=@($seatBrowserMappings | ForEach-Object seat_id); status=if($seatBrowserMappings.Count -eq 3){'configured'}else{'unavailable/not configured'} }
}
$reportPath = Join-Path $PSScriptRoot 'runtime\codex-desk-workspace.json'
$report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $reportPath -Encoding utf8

if ($PlanOnly) { $report | ConvertTo-Json -Depth 12; exit 0 }

foreach ($seat in @('C1','C2','C3')) {
    $window = Start-SeatCodex $seat
    if ($window) {
        $windowPid = Get-ConsoleWindowProcessId $window.Id
        Invoke-MovePid $windowPid $cells["$seat-CODEX"]
        Set-SeatWindowTitle $windowPid $seat-CODEX
    }
}

Write-Host "Codex Desk target: $($monitor.device) / logical top-right ($($monitor.work_area.width)x$($monitor.work_area.height))"
Write-Host "Workspace plan: $reportPath"
Write-Host "Chromium: $($report.chromium.status)"
Write-Host "Chrome: $($report.chrome.status)"
$report | ConvertTo-Json -Depth 12
