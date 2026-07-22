[CmdletBinding()]
param(
    [string]$OutputPath = (Join-Path $PSScriptRoot 'runtime\window-inventory.json'),
    [switch]$IncludeMinimized,
    [switch]$NoClipboard
)

CLS
$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    Write-Error 'Get-OperatorDeckWindowInventory.ps1 requires Windows.'
    exit 2
}

$nativeSource = @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public static class EstateTopLevelWindowsV1 {
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    [StructLayout(LayoutKind.Sequential)] public struct WINDOWPLACEMENT {
        public int length; public int flags; public int showCmd;
        public int minX; public int minY; public int maxX; public int maxY;
        public RECT normalPosition;
    }
    public sealed class WindowRecord {
        public long Hwnd; public uint ProcessId; public string Title; public string ClassName;
        public bool Visible; public bool Cloaked; public RECT Rect; public int ShowCommand;
    }
    private delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr data);
    [DllImport("user32.dll")] private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr data);
    [DllImport("user32.dll")] private static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] private static extern int GetWindowTextLength(IntPtr hWnd);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetClassName(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll")] private static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")] private static extern bool GetWindowPlacement(IntPtr hWnd, ref WINDOWPLACEMENT placement);
    [DllImport("dwmapi.dll")] private static extern int DwmGetWindowAttribute(IntPtr hWnd, int attribute, out int value, int size);

    public static WindowRecord[] Enumerate() {
        var records = new List<WindowRecord>();
        EnumWindows(delegate(IntPtr hWnd, IntPtr data) {
            int titleLength = GetWindowTextLength(hWnd);
            var title = new StringBuilder(titleLength + 1);
            GetWindowText(hWnd, title, title.Capacity);
            var className = new StringBuilder(256);
            GetClassName(hWnd, className, className.Capacity);
            uint processId; GetWindowThreadProcessId(hWnd, out processId);
            RECT rect; GetWindowRect(hWnd, out rect);
            int cloaked = 0; bool isCloaked = DwmGetWindowAttribute(hWnd, 14, out cloaked, 4) == 0 && cloaked != 0;
            var placement = new WINDOWPLACEMENT(); placement.length = Marshal.SizeOf(typeof(WINDOWPLACEMENT));
            GetWindowPlacement(hWnd, ref placement);
            records.Add(new WindowRecord {
                Hwnd = hWnd.ToInt64(), ProcessId = processId, Title = title.ToString(),
                ClassName = className.ToString(), Visible = IsWindowVisible(hWnd), Cloaked = isCloaked,
                Rect = rect, ShowCommand = placement.showCmd
            });
            return true;
        }, IntPtr.Zero);
        return records.ToArray();
    }
}
'@

try {
    if (-not ('EstateTopLevelWindowsV1' -as [type])) {
        Add-Type -TypeDefinition $nativeSource -ErrorAction Stop
    }

    Write-Host 'Inventorying visible top-level application windows (read-only)...'
    $windows = foreach ($window in [EstateTopLevelWindowsV1]::Enumerate()) {
        if (-not $window.Visible -or $window.Cloaked -or [string]::IsNullOrWhiteSpace($window.Title)) { continue }
        if (-not $IncludeMinimized -and $window.ShowCommand -eq 2) { continue }
        $process = Get-Process -Id $window.ProcessId -ErrorAction SilentlyContinue
        if (-not $process) { continue }
        $width = $window.Rect.Right - $window.Rect.Left
        $height = $window.Rect.Bottom - $window.Rect.Top
        if ($width -le 0 -or $height -le 0) { continue }
        $executablePath = try { $process.Path } catch { $null }

        [ordered]@{
            hwnd = ('0x{0:X}' -f $window.Hwnd)
            process_id = $window.ProcessId
            process_name = $process.ProcessName
            executable_path = $executablePath
            title = $window.Title
            class_name = $window.ClassName
            window_state = switch ($window.ShowCommand) { 2 { 'minimized' } 3 { 'maximized' } default { 'normal' } }
            rect = [ordered]@{
                left = $window.Rect.Left; top = $window.Rect.Top
                right = $window.Rect.Right; bottom = $window.Rect.Bottom
                width = $width; height = $height
            }
            suggested_match_rules = @(
                "ahk_exe $($process.ProcessName).exe"
                "$($window.Title) ahk_exe $($process.ProcessName).exe"
                "ahk_class $($window.ClassName) ahk_exe $($process.ProcessName).exe"
            )
        }
    }

    $windows = @($windows | Sort-Object process_name, title)
    $report = [ordered]@{
        schema_version = 'operator_deck_window_inventory_v1'
        observed_at = (Get-Date).ToUniversalTime().ToString('o')
        window_count = $windows.Count
        windows = $windows
    }

    $directory = Split-Path -Parent $OutputPath
    if ($directory) { New-Item -ItemType Directory -Path $directory -Force | Out-Null }
    $json = $report | ConvertTo-Json -Depth 7
    $json | Set-Content -LiteralPath $OutputPath -Encoding utf8
    $json | Write-Output
    Write-Host "Report written to: $OutputPath"
    if (-not $NoClipboard) {
        $json | Set-Clipboard
        Write-Host 'The JSON window inventory is on the clipboard.'
    }
    exit 0
} catch {
    Write-Error "Window inventory failed: $($_.Exception.Message)"
    exit 1
}
