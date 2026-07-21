[CmdletBinding()]
param(
    [string]$OutputPath = (Join-Path $PSScriptRoot 'runtime\voice-typing-surface.json'),
    [switch]$NoClipboard
)

CLS
$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    Write-Error 'Inspect-VoiceTypingSurface.ps1 requires Windows.'
    exit 2
}

Write-Host 'Inspecting Windows Voice Typing surfaces (read-only)...'

$nativeSource = @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public static class EstateWindowInventory {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc callback, IntPtr extraData);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern int GetWindowTextLength(IntPtr hWnd);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
}
'@

try {
    Add-Type -TypeDefinition $nativeSource -ErrorAction SilentlyContinue
    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes

    $processNames = @('TextInputHost', 'ShellExperienceHost', 'ApplicationFrameHost', 'explorer')
    $surfacePattern = '(?i)voice typing|dictation|listening|microphone'
    $windows = [System.Collections.Generic.List[object]]::new()

    $callback = [EstateWindowInventory+EnumWindowsProc]{
        param([IntPtr]$hWnd, [IntPtr]$lParam)
        if (-not [EstateWindowInventory]::IsWindowVisible($hWnd)) { return $true }

        [uint32]$processId = 0
        [void][EstateWindowInventory]::GetWindowThreadProcessId($hWnd, [ref]$processId)
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if (-not $process) { return $true }

        $length = [EstateWindowInventory]::GetWindowTextLength($hWnd)
        $builder = [System.Text.StringBuilder]::new($length + 1)
        [void][EstateWindowInventory]::GetWindowText($hWnd, $builder, $builder.Capacity)
        $title = $builder.ToString()

        if (($processNames -notcontains $process.ProcessName) -and ($title -notmatch $surfacePattern)) { return $true }

        $automationName = $null
        $automationType = $null
        try {
            $element = [System.Windows.Automation.AutomationElement]::FromHandle($hWnd)
            $automationName = $element.Current.Name
            $automationType = $element.Current.ControlType.ProgrammaticName
        } catch { }

        $windows.Add([pscustomobject]@{
            hwnd = ('0x{0:X}' -f $hWnd.ToInt64())
            process_id = $processId
            process_name = $process.ProcessName
            title = $title
            automation_name = $automationName
            automation_control_type = $automationType
        })
        return $true
    }

    [void][EstateWindowInventory]::EnumWindows($callback, [IntPtr]::Zero)

    $text = (($windows | ForEach-Object { "$($_.title) $($_.automation_name)" }) -join ' ')
    $state = 'unknown'
    $confidence = 'none'
    $diagnostic = 'No reliable state selector has been calibrated on this workstation.'
    if ($text -match '(?i)listening') {
        $state = 'listening'; $confidence = 'medium'; $diagnostic = 'A visible candidate surface contains the word listening.'
    } elseif ($text -match '(?i)voice typing|dictation') {
        $state = 'ready'; $confidence = 'low'; $diagnostic = 'A visible candidate surface identifies Voice Typing or dictation, but listening state was not proven.'
    } elseif ($windows.Count -eq 0) {
        $state = 'off'; $confidence = 'low'; $diagnostic = 'No candidate surface was visible; Windows may still hide or rename the surface.'
    }

    $report = [ordered]@{
        contract_version = '1.0'
        observed_at = (Get-Date).ToUniversalTime().ToString('o')
        capability = 'dictation.status'
        state = $state
        confidence = $confidence
        evidence = @($windows)
        diagnostic = $diagnostic
    }

    $directory = Split-Path -Parent $OutputPath
    if ($directory) { New-Item -ItemType Directory -Path $directory -Force | Out-Null }
    $json = $report | ConvertTo-Json -Depth 6
    $json | Set-Content -LiteralPath $OutputPath -Encoding utf8
    $json | Write-Output
    if (-not $NoClipboard) { $json | Set-Clipboard }
    Write-Host "Report written to: $OutputPath"
    if (-not $NoClipboard) { Write-Host 'The JSON report is on the clipboard.' }
    exit 0
} catch {
    Write-Error "Voice Typing inspection failed: $($_.Exception.Message)"
    exit 1
}
