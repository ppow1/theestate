[CmdletBinding()]
param(
    [string]$OutputPath = (Join-Path $PSScriptRoot 'runtime\voice-typing-status.json'),
    [switch]$Watch,
    [ValidateRange(100, 60000)]
    [int]$IntervalMilliseconds = 500,
    [switch]$NoClipboard,
    [switch]$Quiet
)

CLS
$ErrorActionPreference = 'Stop'
$voiceTypingRecord = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone\MicrosoftWindows.Client.CBS_cw5n1h2txyewy'

function Get-VoiceTypingObservation {
    if (-not (Test-Path -LiteralPath $voiceTypingRecord)) {
        return [ordered]@{
            contract_version = '1.0'
            observed_at = (Get-Date).ToUniversalTime().ToString('o')
            capability = 'dictation.status'
            state = 'unknown'
            confidence = 'none'
            evidence = @()
            diagnostic = 'The calibrated Windows Client CBS microphone capability record was not found.'
        }
    }

    $record = Get-ItemProperty -LiteralPath $voiceTypingRecord
    $start = [int64]$record.LastUsedTimeStart
    $stop = [int64]$record.LastUsedTimeStop
    $active = $start -gt 0 -and ($stop -eq 0 -or $start -gt $stop)

    if ($start -le 0) {
        $state = 'unknown'
        $confidence = 'none'
        $diagnostic = 'The calibrated record exists but has no usable start timestamp.'
    } elseif ($active) {
        $state = 'listening'
        $confidence = 'high'
        $diagnostic = 'The calibrated Windows Client CBS microphone capability record is active.'
    } else {
        $state = 'off'
        $confidence = 'high'
        $diagnostic = 'The calibrated Windows Client CBS microphone capability record is inactive.'
    }

    return [ordered]@{
        contract_version = '1.0'
        observed_at = (Get-Date).ToUniversalTime().ToString('o')
        capability = 'dictation.status'
        state = $state
        confidence = $confidence
        evidence = @(
            [ordered]@{
                evidence_type = 'microphone_capability_usage'
                package = 'MicrosoftWindows.Client.CBS_cw5n1h2txyewy'
                last_used_time_start = $start
                last_used_time_stop = $stop
                active = $active
            }
        )
        diagnostic = $diagnostic
    }
}

function Publish-Observation {
    param([System.Collections.IDictionary]$Observation)

    $directory = Split-Path -Parent $OutputPath
    if ($directory) { New-Item -ItemType Directory -Path $directory -Force | Out-Null }
    $json = $Observation | ConvertTo-Json -Depth 5
    $temporaryPath = "$OutputPath.tmp"
    $json | Set-Content -LiteralPath $temporaryPath -Encoding utf8
    Move-Item -LiteralPath $temporaryPath -Destination $OutputPath -Force
    return $json
}

try {
    $lastState = $null
    do {
        $observation = Get-VoiceTypingObservation
        $json = Publish-Observation -Observation $observation

        if (-not $Quiet -and (-not $Watch -or $observation.state -ne $lastState)) {
            if ($Watch) {
                Write-Host ("{0}  Voice Typing: {1} ({2})" -f $observation.observed_at, $observation.state.ToUpperInvariant(), $observation.confidence)
            } else {
                $json | Write-Output
                Write-Host "Status written to: $OutputPath"
            }
        }

        if (-not $Watch -and -not $NoClipboard) {
            $json | Set-Clipboard
            if (-not $Quiet) { Write-Host 'The JSON status is on the clipboard.' }
        }

        $lastState = $observation.state
        if ($Watch) { Start-Sleep -Milliseconds $IntervalMilliseconds }
    } while ($Watch)

    if ($observation.state -eq 'unknown') { exit 3 }
    exit 0
} catch {
    Write-Error "Voice Typing status publication failed: $($_.Exception.Message)"
    exit 1
}
