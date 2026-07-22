[CmdletBinding()]
param(
    [string]$OutputPath = (Join-Path $PSScriptRoot 'runtime\operator-deck-state.json'),
    [switch]$Watch,
    [ValidateRange(100, 60000)]
    [int]$IntervalMilliseconds = 500,
    [switch]$NoClipboard,
    [switch]$Quiet
)

CLS
$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    Write-Error 'Get-OperatorDeckState.ps1 requires Windows.'
    exit 2
}

$nativeSource = @'
using System;
using System.Runtime.InteropServices;
public static class EstateWindowIdentityV1 {
    [DllImport("user32.dll")] public static extern bool IsWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
}
'@

function Read-IniSection {
    param([string]$Path, [string]$Section)
    $values = [ordered]@{}
    if (-not (Test-Path -LiteralPath $Path)) { return $values }
    $inside = $false
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if ($trimmed -match '^\[(.+)\]$') {
            $inside = $Matches[1] -eq $Section
            continue
        }
        if ($inside -and $trimmed -match '^([^=]+)=(.*)$') {
            $values[$Matches[1].Trim()] = $Matches[2].Trim()
        }
    }
    return $values
}

function Test-WindowIdentity {
    param([int64]$Hwnd, [int64]$ExpectedPid)
    if ($Hwnd -le 0 -or $ExpectedPid -le 0) { return $false }
    $pointer = [IntPtr]::new($Hwnd)
    if (-not [EstateWindowIdentityV1]::IsWindow($pointer)) { return $false }
    [uint32]$actualPid = 0
    [void][EstateWindowIdentityV1]::GetWindowThreadProcessId($pointer, [ref]$actualPid)
    return $actualPid -eq $ExpectedPid
}

function Get-VoiceTypingState {
    $path = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone\MicrosoftWindows.Client.CBS_cw5n1h2txyewy'
    if (-not (Test-Path -LiteralPath $path)) {
        return [ordered]@{ state = 'unknown'; confidence = 'none'; active = $false }
    }
    $record = Get-ItemProperty -LiteralPath $path
    $start = [int64]$record.LastUsedTimeStart
    $stop = [int64]$record.LastUsedTimeStop
    $active = $start -gt 0 -and ($stop -eq 0 -or $start -gt $stop)
    return [ordered]@{
        state = if ($start -le 0) { 'unknown' } elseif ($active) { 'listening' } else { 'off' }
        confidence = if ($start -le 0) { 'none' } else { 'high' }
        active = $active
    }
}

function Get-SelectionState {
    $path = Join-Path $PSScriptRoot 'runtime\window-selection.ini'
    $selection = Read-IniSection -Path $path -Section 'Selection'
    if ($selection.Count -eq 0) { return [ordered]@{ armed = $false } }
    $hwnd = [int64]$selection.hwnd
    $processId = [int64]$selection.pid
    $valid = Test-WindowIdentity -Hwnd $hwnd -ExpectedPid $processId
    return [ordered]@{
        armed = $valid
        valid = $valid
        hwnd = ('0x{0:X}' -f $hwnd)
        process_id = $processId
        process = $selection.process
        title = $selection.title
        source_slot = if ($selection.Contains('source_slot')) { $selection.source_slot } else { '' }
    }
}

function Get-PlacementChoiceState {
    $path = Join-Path $PSScriptRoot 'runtime\placement-choice.ini'
    if (-not (Test-Path -LiteralPath $path)) {
        return [ordered]@{ armed = $false; monitor = ''; shape = '' }
    }
    $monitor = ''
    $shape = ''
    foreach ($line in Get-Content -LiteralPath $path) {
        if ($line -match '^monitor=(.*)

function Get-PromotionState {
    $path = Join-Path $PSScriptRoot 'runtime\window-promotion.ini'
    $promotion = Read-IniSection -Path $path -Section 'Promotion'
    if ($promotion.Count -eq 0) { return [ordered]@{ available = $false } }
    $hwnd = [int64]$promotion.hwnd
    $processId = [int64]$promotion.pid
    $valid = Test-WindowIdentity -Hwnd $hwnd -ExpectedPid $processId
    return [ordered]@{
        available = $valid
        valid = $valid
        hwnd = ('0x{0:X}' -f $hwnd)
        process_id = $processId
        origin = [ordered]@{
            x = [int]$promotion.x
            y = [int]$promotion.y
            width = [int]$promotion.w
            height = [int]$promotion.h
        }
    }
}

function Get-BindingState {
    $path = Join-Path $PSScriptRoot 'runtime\window-bindings.ini'
    $bindings = Read-IniSection -Path $path -Section 'Bindings'
    $result = @()
    foreach ($target in $bindings.Keys | Sort-Object) {
        $metadata = Read-IniSection -Path $path -Section "BindingMeta:$target"
        $hwnd = [int64]$bindings[$target]
        $processId = [int64]$metadata.pid
        $result += [ordered]@{
            target = $target
            valid = Test-WindowIdentity -Hwnd $hwnd -ExpectedPid $processId
            hwnd = ('0x{0:X}' -f $hwnd)
            process_id = $processId
            process = $metadata.process
            title = $metadata.title
        }
    }
    return $result
}

function Get-OperatorDeckObservation {
    return [ordered]@{
        schema_version = 'operator_deck_state_v1'
        observed_at = (Get-Date).ToUniversalTime().ToString('o')
        dictation = Get-VoiceTypingState
        selection = Get-SelectionState
        placement = Get-PlacementChoiceState
        promotion = Get-PromotionState
        bindings = @(Get-BindingState)
    }
}

function Publish-State {
    param([System.Collections.IDictionary]$State)
    $directory = Split-Path -Parent $OutputPath
    if ($directory) { New-Item -ItemType Directory -Path $directory -Force | Out-Null }
    $json = $State | ConvertTo-Json -Depth 7
    $temporaryPath = "$OutputPath.tmp"
    $json | Set-Content -LiteralPath $temporaryPath -Encoding utf8
    Move-Item -LiteralPath $temporaryPath -Destination $OutputPath -Force
    return $json
}

try {
    if (-not ('EstateWindowIdentityV1' -as [type])) {
        Add-Type -TypeDefinition $nativeSource -ErrorAction Stop
    }

    $lastFingerprint = $null
    do {
        $state = Get-OperatorDeckObservation
        $json = Publish-State -State $state
        $fingerprint = "$($state.dictation.state)|$($state.selection.armed)|$(($state.bindings | ForEach-Object { "$($_.target):$($_.valid)" }) -join ',')"

        if (-not $Quiet -and (-not $Watch -or $fingerprint -ne $lastFingerprint)) {
            if ($Watch) {
                Write-Host ("{0}  Dictation: {1}; Selection armed: {2}; Valid bindings: {3}" -f
                    $state.observed_at,
                    $state.dictation.state.ToUpperInvariant(),
                    $state.selection.armed,
                    @($state.bindings | Where-Object valid).Count)
            } else {
                $json | Write-Output
                Write-Host "State written to: $OutputPath"
            }
        }

        if (-not $Watch -and -not $NoClipboard) {
            $json | Set-Clipboard
            if (-not $Quiet) { Write-Host 'The Operator Deck state is on the clipboard.' }
        }
        $lastFingerprint = $fingerprint
        if ($Watch) { Start-Sleep -Milliseconds $IntervalMilliseconds }
    } while ($Watch)
    exit 0
} catch {
    Write-Error "Operator Deck state publication failed: $($_.Exception.Message)"
    exit 1
}
) { $monitor = $Matches[1].Trim() }
        if ($line -match '^shape=(.*)

function Get-PromotionState {
    $path = Join-Path $PSScriptRoot 'runtime\window-promotion.ini'
    $promotion = Read-IniSection -Path $path -Section 'Promotion'
    if ($promotion.Count -eq 0) { return [ordered]@{ available = $false } }
    $hwnd = [int64]$promotion.hwnd
    $processId = [int64]$promotion.pid
    $valid = Test-WindowIdentity -Hwnd $hwnd -ExpectedPid $processId
    return [ordered]@{
        available = $valid
        valid = $valid
        hwnd = ('0x{0:X}' -f $hwnd)
        process_id = $processId
        origin = [ordered]@{
            x = [int]$promotion.x
            y = [int]$promotion.y
            width = [int]$promotion.w
            height = [int]$promotion.h
        }
    }
}

function Get-BindingState {
    $path = Join-Path $PSScriptRoot 'runtime\window-bindings.ini'
    $bindings = Read-IniSection -Path $path -Section 'Bindings'
    $result = @()
    foreach ($target in $bindings.Keys | Sort-Object) {
        $metadata = Read-IniSection -Path $path -Section "BindingMeta:$target"
        $hwnd = [int64]$bindings[$target]
        $processId = [int64]$metadata.pid
        $result += [ordered]@{
            target = $target
            valid = Test-WindowIdentity -Hwnd $hwnd -ExpectedPid $processId
            hwnd = ('0x{0:X}' -f $hwnd)
            process_id = $processId
            process = $metadata.process
            title = $metadata.title
        }
    }
    return $result
}

function Get-OperatorDeckObservation {
    return [ordered]@{
        schema_version = 'operator_deck_state_v1'
        observed_at = (Get-Date).ToUniversalTime().ToString('o')
        dictation = Get-VoiceTypingState
        selection = Get-SelectionState
        placement = Get-PlacementChoiceState
        promotion = Get-PromotionState
        bindings = @(Get-BindingState)
    }
}

function Publish-State {
    param([System.Collections.IDictionary]$State)
    $directory = Split-Path -Parent $OutputPath
    if ($directory) { New-Item -ItemType Directory -Path $directory -Force | Out-Null }
    $json = $State | ConvertTo-Json -Depth 7
    $temporaryPath = "$OutputPath.tmp"
    $json | Set-Content -LiteralPath $temporaryPath -Encoding utf8
    Move-Item -LiteralPath $temporaryPath -Destination $OutputPath -Force
    return $json
}

try {
    if (-not ('EstateWindowIdentityV1' -as [type])) {
        Add-Type -TypeDefinition $nativeSource -ErrorAction Stop
    }

    $lastFingerprint = $null
    do {
        $state = Get-OperatorDeckObservation
        $json = Publish-State -State $state
        $fingerprint = "$($state.dictation.state)|$($state.selection.armed)|$(($state.bindings | ForEach-Object { "$($_.target):$($_.valid)" }) -join ',')"

        if (-not $Quiet -and (-not $Watch -or $fingerprint -ne $lastFingerprint)) {
            if ($Watch) {
                Write-Host ("{0}  Dictation: {1}; Selection armed: {2}; Valid bindings: {3}" -f
                    $state.observed_at,
                    $state.dictation.state.ToUpperInvariant(),
                    $state.selection.armed,
                    @($state.bindings | Where-Object valid).Count)
            } else {
                $json | Write-Output
                Write-Host "State written to: $OutputPath"
            }
        }

        if (-not $Watch -and -not $NoClipboard) {
            $json | Set-Clipboard
            if (-not $Quiet) { Write-Host 'The Operator Deck state is on the clipboard.' }
        }
        $lastFingerprint = $fingerprint
        if ($Watch) { Start-Sleep -Milliseconds $IntervalMilliseconds }
    } while ($Watch)
    exit 0
} catch {
    Write-Error "Operator Deck state publication failed: $($_.Exception.Message)"
    exit 1
}
) { $shape = $Matches[1].Trim() }
    }
    return [ordered]@{
        armed = ($monitor -ne '' -or $shape -ne '')
        monitor = $monitor
        shape = $shape
    }
}

function Get-PromotionState {
    $path = Join-Path $PSScriptRoot 'runtime\window-promotion.ini'
    $promotion = Read-IniSection -Path $path -Section 'Promotion'
    if ($promotion.Count -eq 0) { return [ordered]@{ available = $false } }
    $hwnd = [int64]$promotion.hwnd
    $processId = [int64]$promotion.pid
    $valid = Test-WindowIdentity -Hwnd $hwnd -ExpectedPid $processId
    return [ordered]@{
        available = $valid
        valid = $valid
        hwnd = ('0x{0:X}' -f $hwnd)
        process_id = $processId
        origin = [ordered]@{
            x = [int]$promotion.x
            y = [int]$promotion.y
            width = [int]$promotion.w
            height = [int]$promotion.h
        }
    }
}

function Get-BindingState {
    $path = Join-Path $PSScriptRoot 'runtime\window-bindings.ini'
    $bindings = Read-IniSection -Path $path -Section 'Bindings'
    $result = @()
    foreach ($target in $bindings.Keys | Sort-Object) {
        $metadata = Read-IniSection -Path $path -Section "BindingMeta:$target"
        $hwnd = [int64]$bindings[$target]
        $processId = [int64]$metadata.pid
        $result += [ordered]@{
            target = $target
            valid = Test-WindowIdentity -Hwnd $hwnd -ExpectedPid $processId
            hwnd = ('0x{0:X}' -f $hwnd)
            process_id = $processId
            process = $metadata.process
            title = $metadata.title
        }
    }
    return $result
}

function Get-OperatorDeckObservation {
    return [ordered]@{
        schema_version = 'operator_deck_state_v1'
        observed_at = (Get-Date).ToUniversalTime().ToString('o')
        dictation = Get-VoiceTypingState
        selection = Get-SelectionState
        placement = Get-PlacementChoiceState
        promotion = Get-PromotionState
        bindings = @(Get-BindingState)
    }
}

function Publish-State {
    param([System.Collections.IDictionary]$State)
    $directory = Split-Path -Parent $OutputPath
    if ($directory) { New-Item -ItemType Directory -Path $directory -Force | Out-Null }
    $json = $State | ConvertTo-Json -Depth 7
    $temporaryPath = "$OutputPath.tmp"
    $json | Set-Content -LiteralPath $temporaryPath -Encoding utf8
    Move-Item -LiteralPath $temporaryPath -Destination $OutputPath -Force
    return $json
}

try {
    if (-not ('EstateWindowIdentityV1' -as [type])) {
        Add-Type -TypeDefinition $nativeSource -ErrorAction Stop
    }

    $lastFingerprint = $null
    do {
        $state = Get-OperatorDeckObservation
        $json = Publish-State -State $state
        $fingerprint = "$($state.dictation.state)|$($state.selection.armed)|$(($state.bindings | ForEach-Object { "$($_.target):$($_.valid)" }) -join ',')"

        if (-not $Quiet -and (-not $Watch -or $fingerprint -ne $lastFingerprint)) {
            if ($Watch) {
                Write-Host ("{0}  Dictation: {1}; Selection armed: {2}; Valid bindings: {3}" -f
                    $state.observed_at,
                    $state.dictation.state.ToUpperInvariant(),
                    $state.selection.armed,
                    @($state.bindings | Where-Object valid).Count)
            } else {
                $json | Write-Output
                Write-Host "State written to: $OutputPath"
            }
        }

        if (-not $Watch -and -not $NoClipboard) {
            $json | Set-Clipboard
            if (-not $Quiet) { Write-Host 'The Operator Deck state is on the clipboard.' }
        }
        $lastFingerprint = $fingerprint
        if ($Watch) { Start-Sleep -Milliseconds $IntervalMilliseconds }
    } while ($Watch)
    exit 0
} catch {
    Write-Error "Operator Deck state publication failed: $($_.Exception.Message)"
    exit 1
}
