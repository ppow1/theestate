[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('C1','C2','C3')][string]$Seat,
    [Parameter(Mandatory)][int]$ConsolePid
)

$ErrorActionPreference = 'Stop'
$runtimeRoot = Join-Path $PSScriptRoot 'runtime'
$eventPath = Join-Path $runtimeRoot 'codex-desk-status-events.jsonl'

if (-not ('EstateCodexDeskConsoleInputV1' -as [type])) {
    Add-Type @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public static class EstateCodexDeskConsoleInputV1 {
    [StructLayout(LayoutKind.Sequential)] public struct COORD { public short X; public short Y; }
    [StructLayout(LayoutKind.Sequential)] public struct SMALL_RECT { public short Left; public short Top; public short Right; public short Bottom; }
    [StructLayout(LayoutKind.Sequential)] public struct CSBI { public COORD Size; public COORD Cursor; public short Attributes; public SMALL_RECT Window; public COORD Max; }
    [StructLayout(LayoutKind.Explicit, Size=16)] public struct KEY_EVENT_RECORD {
        [FieldOffset(0)] public int KeyDown;
        [FieldOffset(4)] public ushort Repeat;
        [FieldOffset(6)] public ushort VirtualKey;
        [FieldOffset(8)] public ushort ScanCode;
        [FieldOffset(10)] public char UnicodeChar;
        [FieldOffset(12)] public uint ControlState;
    }
    [StructLayout(LayoutKind.Explicit, Size=20)] public struct INPUT_RECORD {
        [FieldOffset(0)] public ushort EventType;
        [FieldOffset(4)] public KEY_EVENT_RECORD KeyEvent;
    }
    [StructLayout(LayoutKind.Sequential)] struct KEYBDINPUT { public ushort Vk; public ushort Scan; public uint Flags; public uint Time; public IntPtr Extra; }
    [StructLayout(LayoutKind.Explicit, Size=40)] struct INPUT { [FieldOffset(0)] public uint Type; [FieldOffset(8)] public KEYBDINPUT Keyboard; }
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool FreeConsole();
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool AttachConsole(uint processId);
    [DllImport("kernel32.dll")] static extern IntPtr GetStdHandle(int handle);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool WriteConsoleInputW(IntPtr input, INPUT_RECORD[] records, uint length, out uint written);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool GetConsoleScreenBufferInfo(IntPtr output, out CSBI info);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool ReadConsoleOutputCharacterW(IntPtr output, StringBuilder buffer, uint length, COORD coordinate, out uint read);
    [DllImport("user32.dll")] static extern bool ShowWindow(IntPtr hwnd, int command);
    [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr hwnd);
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    public static bool Attach(uint processId) { FreeConsole(); return AttachConsole(processId); }
    public static void Detach() { FreeConsole(); }
    public static bool Focus(IntPtr hwnd) {
        ShowWindow(hwnd, 9);
        SetForegroundWindow(hwnd);
        return GetForegroundWindow() == hwnd;
    }
    public static bool WriteText() {
        var records = new List<INPUT_RECORD>();
        foreach (var ch in "/status") {
            records.Add(Key(ch, true)); records.Add(Key(ch, false));
        }
        uint written; var input = GetStdHandle(-10);
        return WriteConsoleInputW(input, records.ToArray(), (uint)records.Count, out written) && written == records.Count;
    }
    public static bool WriteEnter() {
        var records = new[] { Enter(true), Enter(false) };
        uint written; var input = GetStdHandle(-10);
        return WriteConsoleInputW(input, records, 2, out written) && written == 2;
    }
    [DllImport("user32.dll", SetLastError=true)] static extern uint SendInput(uint count, INPUT[] inputs, int size);
    public static bool SendUnicodeText(string text) {
        var inputs = new List<INPUT>();
        foreach (var ch in text) {
            inputs.Add(new INPUT { Type=1, Keyboard=new KEYBDINPUT { Scan=ch, Flags=4 } });
            inputs.Add(new INPUT { Type=1, Keyboard=new KEYBDINPUT { Scan=ch, Flags=6 } });
        }
        return SendInput((uint)inputs.Count, inputs.ToArray(), Marshal.SizeOf(typeof(INPUT))) == inputs.Count;
    }
    public static bool SendReturn() {
        var inputs = new[] {
            new INPUT { Type=1, Keyboard=new KEYBDINPUT { Vk=13 } },
            new INPUT { Type=1, Keyboard=new KEYBDINPUT { Vk=13, Flags=2 } }
        };
        return SendInput(2, inputs, Marshal.SizeOf(typeof(INPUT))) == 2;
    }
    static INPUT_RECORD Key(char ch, bool down) { return new INPUT_RECORD { EventType=1, KeyEvent=new KEY_EVENT_RECORD { KeyDown=down ? 1 : 0, Repeat=1, UnicodeChar=ch } }; }
    static INPUT_RECORD Enter(bool down) { return new INPUT_RECORD { EventType=1, KeyEvent=new KEY_EVENT_RECORD { KeyDown=down ? 1 : 0, Repeat=1, VirtualKey=13, ScanCode=28 } }; }
    public static string ReadText() {
        var output = GetStdHandle(-11); CSBI info;
        if (!GetConsoleScreenBufferInfo(output, out info)) return string.Empty;
        var length = Math.Min((int)info.Size.X * (int)info.Size.Y, 120000);
        var buffer = new StringBuilder(length); uint read;
        ReadConsoleOutputCharacterW(output, buffer, (uint)length, new COORD { X=0, Y=0 }, out read);
        return buffer.ToString();
    }
}
'@
}

function Get-OwnedCodexProcess {
    $processes = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
    $owned = [System.Collections.Generic.HashSet[int]]::new()
    [void]$owned.Add($ConsolePid)
    $changed = $true
    while ($changed) {
        $changed = $false
        foreach ($process in $processes) {
            if ($owned.Contains([int]$process.ParentProcessId) -and $owned.Add([int]$process.ProcessId)) { $changed = $true }
        }
    }
    return $processes | Where-Object { $_.Name -eq 'codex.exe' -and $owned.Contains([int]$_.ProcessId) } | Select-Object -First 1
}

$deadline = [DateTime]::UtcNow.AddSeconds(30)
$attached = $false
$readyText = ''
$modalPattern = '(?i)(select model|choose model|model selection|select an option|mcp.*(select|choose)|mcp startup|servers were not initialized|loading.*codex|initializ|press enter or esc|(?m)^\s*[0-9]+\.\s+gpt-)'
while ([DateTime]::UtcNow -lt $deadline) {
    $codex = Get-OwnedCodexProcess
    $console = Get-Process -Id $ConsolePid -ErrorAction SilentlyContinue
    if ($codex -and $console -and $console.MainWindowHandle -ne 0) {
        if (-not $attached) {
            $attached = [EstateCodexDeskConsoleInputV1]::Attach([uint32]$ConsolePid)
        }
        if ($attached) {
            $readyText = [EstateCodexDeskConsoleInputV1]::ReadText()
            $modal = $readyText -match $modalPattern
            $prompt = $readyText -match '[›❯]'
            if ($prompt -and -not $modal) { break }
        }
    }
    if ($attached) {
        [EstateCodexDeskConsoleInputV1]::Detach()
        $attached = $false
    }
    Start-Sleep -Milliseconds 250
}
if (-not ($readyText -match '[›❯]') -or $readyText -match $modalPattern) {
    throw "Codex $Seat did not expose its normal command prompt before /status."
}

if (-not $attached -and -not [EstateCodexDeskConsoleInputV1]::Attach([uint32]$ConsolePid)) {
    throw "Could not attach to the elevated $Seat Codex console input buffer."
}
if (-not $console -or $console.MainWindowHandle -eq 0) {
    throw "The exact $Seat Codex console HWND disappeared before /status."
}
$consoleHwnd = [IntPtr]$console.MainWindowHandle
$beforeText = [EstateCodexDeskConsoleInputV1]::ReadText()
if (-not [EstateCodexDeskConsoleInputV1]::Focus($consoleHwnd)) {
    throw "Could not focus the exact $Seat Codex console HWND before /status."
}
if (-not [EstateCodexDeskConsoleInputV1]::SendUnicodeText('/status')) {
    throw "Could not type /status into the exact $Seat Codex console HWND."
}
$typed = $false
$typedDeadline = [DateTime]::UtcNow.AddSeconds(2)
while ([DateTime]::UtcNow -lt $typedDeadline) {
    Start-Sleep -Milliseconds 100
    if ([EstateCodexDeskConsoleInputV1]::ReadText() -match '/status') { $typed = $true; break }
}
if (-not $typed) { throw "Codex $Seat did not visibly receive /status before Enter delivery." }
if (-not [EstateCodexDeskConsoleInputV1]::Focus($consoleHwnd)) {
    throw "The exact $Seat Codex console lost focus before Enter."
}
if (-not [EstateCodexDeskConsoleInputV1]::SendReturn()) {
    throw "Could not submit Enter to the exact $Seat Codex console HWND."
}
$verified = $false
$text = ''
$panelDeadline = [DateTime]::UtcNow.AddSeconds(6)
while ([DateTime]::UtcNow -lt $panelDeadline) {
    Start-Sleep -Milliseconds 250
    $text = [EstateCodexDeskConsoleInputV1]::ReadText()
    $panelMarkers = @(
        ($text -match '(?i)(account|session|limits:)'),
        ($text -match '(?i)session'),
        ($text -match '(?i)(weekly|remaining|usage|limit|gpt-5\.6-luna)')
    ) | Where-Object { $_ }
    $changed = $text -ne $beforeText
    if ($changed -and $panelMarkers.Count -ge 2) { $verified = $true; break }
}
$event = [ordered]@{ observed_at=(Get-Date).ToUniversalTime().ToString('o'); seat=$Seat; console_pid=$ConsolePid; console_hwnd=$consoleHwnd.ToInt64(); codex_pid=[int]$codex.ProcessId; command='/status'; text_sent_once=$true; enter_sent_once=$true; panel_verified=$verified }
New-Item -ItemType Directory -Force -Path $runtimeRoot | Out-Null
($event | ConvertTo-Json -Compress) | Add-Content -LiteralPath $eventPath -Encoding utf8
if (-not $verified) { throw "Codex $Seat received /status and Enter but no authoritative status panel was readable." }
