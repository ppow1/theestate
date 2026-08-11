[CmdletBinding()]
param(
    [string]$OutputPath = (Join-Path $PSScriptRoot 'runtime\monitor-layout.json'),
    [switch]$NoClipboard
)

$ErrorActionPreference = 'Stop'

if (-not ('EstateMonitorDpiV1' -as [type])) {
    Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class EstateMonitorDpiV1 {
    [DllImport("user32.dll")] public static extern bool SetProcessDpiAwarenessContext(IntPtr dpiContext);
}
'@
}
try { [EstateMonitorDpiV1]::SetProcessDpiAwarenessContext([IntPtr](-4)) | Out-Null } catch { }

if ($env:OS -ne 'Windows_NT') {
    Write-Error 'Get-OperatorDeckMonitorLayout.ps1 requires Windows.'
    exit 2
}

$nativeSource = @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

public static class EstateMonitorInventoryV1 {
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)] public struct MONITORINFOEX {
        public int cbSize;
        public RECT rcMonitor;
        public RECT rcWork;
        public uint dwFlags;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)] public string szDevice;
    }
    public sealed class MonitorRecord {
        public string Device;
        public bool Primary;
        public RECT Bounds;
        public RECT WorkArea;
        public uint DpiX;
        public uint DpiY;
    }
    private delegate bool MonitorEnumProc(IntPtr monitor, IntPtr hdc, ref RECT rect, IntPtr data);
    [DllImport("user32.dll")] private static extern bool EnumDisplayMonitors(IntPtr hdc, IntPtr clip, MonitorEnumProc callback, IntPtr data);
    [DllImport("user32.dll", CharSet = CharSet.Auto)] private static extern bool GetMonitorInfo(IntPtr monitor, ref MONITORINFOEX info);
    [DllImport("shcore.dll")] private static extern int GetDpiForMonitor(IntPtr monitor, int dpiType, out uint dpiX, out uint dpiY);

    public static MonitorRecord[] Enumerate() {
        var records = new List<MonitorRecord>();
        EnumDisplayMonitors(IntPtr.Zero, IntPtr.Zero, delegate(IntPtr monitor, IntPtr hdc, ref RECT rect, IntPtr data) {
            var info = new MONITORINFOEX();
            info.cbSize = Marshal.SizeOf(typeof(MONITORINFOEX));
            if (!GetMonitorInfo(monitor, ref info)) return true;
            uint dpiX = 96, dpiY = 96;
            try { GetDpiForMonitor(monitor, 0, out dpiX, out dpiY); } catch { }
            records.Add(new MonitorRecord {
                Device = info.szDevice,
                Primary = (info.dwFlags & 1) != 0,
                Bounds = info.rcMonitor,
                WorkArea = info.rcWork,
                DpiX = dpiX,
                DpiY = dpiY
            });
            return true;
        }, IntPtr.Zero);
        return records.ToArray();
    }
}
'@

try {
    if (-not ('EstateMonitorInventoryV1' -as [type])) {
        Add-Type -TypeDefinition $nativeSource -ErrorAction Stop
    }

    Write-Host 'Inspecting monitor bounds, work areas, DPI, and quadrant slots...'
    $nativeMonitors = [EstateMonitorInventoryV1]::Enumerate() | Sort-Object { $_.Bounds.Top }, { $_.Bounds.Left }
    $monitors = @()
    $slots = [ordered]@{}
    $index = 0

    foreach ($monitor in $nativeMonitors) {
        $index++
        $boundsWidth = $monitor.Bounds.Right - $monitor.Bounds.Left
        $boundsHeight = $monitor.Bounds.Bottom - $monitor.Bounds.Top
        $workWidth = $monitor.WorkArea.Right - $monitor.WorkArea.Left
        $workHeight = $monitor.WorkArea.Bottom - $monitor.WorkArea.Top
        $leftWidth = [Math]::Floor($workWidth / 2)
        $rightWidth = $workWidth - $leftWidth
        $topHeight = [Math]::Floor($workHeight / 2)
        $bottomHeight = $workHeight - $topHeight
        $slotPrefix = "M$index"

        $slots["${slotPrefix}_TOP_LEFT"] = "$($monitor.WorkArea.Left),$($monitor.WorkArea.Top),$leftWidth,$topHeight"
        $slots["${slotPrefix}_TOP_RIGHT"] = "$($monitor.WorkArea.Left + $leftWidth),$($monitor.WorkArea.Top),$rightWidth,$topHeight"
        $slots["${slotPrefix}_BOTTOM_LEFT"] = "$($monitor.WorkArea.Left),$($monitor.WorkArea.Top + $topHeight),$leftWidth,$bottomHeight"
        $slots["${slotPrefix}_BOTTOM_RIGHT"] = "$($monitor.WorkArea.Left + $leftWidth),$($monitor.WorkArea.Top + $topHeight),$rightWidth,$bottomHeight"

        $monitors += [ordered]@{
            index = $index
            device = $monitor.Device
            primary = $monitor.Primary
            bounds = [ordered]@{
                left = $monitor.Bounds.Left; top = $monitor.Bounds.Top
                right = $monitor.Bounds.Right; bottom = $monitor.Bounds.Bottom
                width = $boundsWidth; height = $boundsHeight
            }
            work_area = [ordered]@{
                left = $monitor.WorkArea.Left; top = $monitor.WorkArea.Top
                right = $monitor.WorkArea.Right; bottom = $monitor.WorkArea.Bottom
                width = $workWidth; height = $workHeight
            }
            reserved_edges = [ordered]@{
                left = $monitor.WorkArea.Left - $monitor.Bounds.Left
                top = $monitor.WorkArea.Top - $monitor.Bounds.Top
                right = $monitor.Bounds.Right - $monitor.WorkArea.Right
                bottom = $monitor.Bounds.Bottom - $monitor.WorkArea.Bottom
            }
            dpi = [ordered]@{
                x = $monitor.DpiX
                y = $monitor.DpiY
                scale_percent = [Math]::Round(($monitor.DpiX / 96.0) * 100)
            }
            slot_prefix = $slotPrefix
        }
    }

    $report = [ordered]@{
        schema_version = 'operator_deck_monitor_layout_v1'
        observed_at = (Get-Date).ToUniversalTime().ToString('o')
        monitor_count = $monitors.Count
        monitors = $monitors
        suggested_slots = $slots
    }

    $directory = Split-Path -Parent $OutputPath
    if ($directory) { New-Item -ItemType Directory -Path $directory -Force | Out-Null }
    $json = $report | ConvertTo-Json -Depth 8
    $json | Set-Content -LiteralPath $OutputPath -Encoding utf8
    $json | Write-Output
    Write-Host "Report written to: $OutputPath"
    if (-not $NoClipboard) {
        $json | Set-Clipboard
        Write-Host 'The JSON monitor report is on the clipboard.'
    }
    exit 0
} catch {
    Write-Error "Monitor layout inspection failed: $($_.Exception.Message)"
    exit 1
}
