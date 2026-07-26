# Version: 1.0.0

CLS

[CmdletBinding()]
param(
    [string]$BundlePath = (
        Join-Path $PSScriptRoot "backups\command-chair-backups-2026-07-26.json"
    ),

    [string]$DestinationPath = (
        Join-Path $PSScriptRoot "restored-backups"
    )
)

$ErrorActionPreference = "Stop"

try {
    if (-not (Test-Path -LiteralPath $BundlePath -PathType Leaf)) {
        throw "Backup bundle not found: $BundlePath"
    }

    New-Item `
        -ItemType Directory `
        -Path $DestinationPath `
        -Force |
        Out-Null

    $bundle = Get-Content `
        -LiteralPath $BundlePath `
        -Raw |
        ConvertFrom-Json

    if ($bundle.schema_version -ne "operator_deck_command_chair_backup_bundle_v1") {
        throw "Unsupported bundle schema: $($bundle.schema_version)"
    }

    $results = foreach ($file in @($bundle.files)) {
        $outputPath = Join-Path $DestinationPath $file.name
        $bytes = [Convert]::FromBase64String($file.base64)

        [IO.File]::WriteAllBytes($outputPath, $bytes)

        $observedHash = (
            Get-FileHash `
                -LiteralPath $outputPath `
                -Algorithm SHA256
        ).Hash.ToLowerInvariant()

        $expectedHash = ([string]$file.sha256).ToLowerInvariant()

        [pscustomobject]@{
            file     = $file.name
            bytes    = $bytes.Length
            expected = $expectedHash
            observed = $observedHash
            result   = if ($observedHash -eq $expectedHash) {
                "PASS"
            }
            else {
                "FAIL"
            }
        }
    }

    CLS

    Write-Host "COMMAND CHAIR BACKUP RESTORE" -ForegroundColor Cyan
    Write-Host ""

    $results |
        Format-Table file, bytes, result -AutoSize

    $failed = @($results | Where-Object result -ne "PASS")

    if ($failed.Count -gt 0) {
        Write-Host ""
        Write-Host "STOP: One or more restored files failed SHA-256 verification." -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "PASS: All Command Chair backup files restored and verified." -ForegroundColor Green
    Write-Host (Resolve-Path -LiteralPath $DestinationPath) -ForegroundColor Cyan
}
catch {
    Write-Host ""
    Write-Host "STOP: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
