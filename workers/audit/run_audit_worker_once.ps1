Clear-Host
$ErrorActionPreference = "Stop"

$EstateRoot = "A:\theestate"
Set-Location $EstateRoot

$PendingDir = Join-Path $EstateRoot "collaboration\audit\pending"
$ActiveDir = Join-Path $EstateRoot "collaboration\audit\active"
$ResultsDir = Join-Path $EstateRoot "collaboration\audit\results"
$ArchiveDir = Join-Path $EstateRoot "collaboration\audit\archive"
$FailedDir = Join-Path $EstateRoot "collaboration\audit\failed"

foreach ($Dir in @($PendingDir, $ActiveDir, $ResultsDir, $ArchiveDir, $FailedDir)) {
    New-Item -ItemType Directory -Force -Path $Dir | Out-Null
}

Write-Host "=== Estate Audit Worker v1.1 ==="
Write-Host "Estate Root: $EstateRoot"
Write-Host ""

$Pending = Get-ChildItem -Path $PendingDir -Filter "*.json" -File -ErrorAction SilentlyContinue | Sort-Object Name

if ($Pending.Count -eq 0) {
    Write-Host "No pending audit requests."
    exit 0
}

$RequestFile = $Pending[0]
$ActivePath = Join-Path $ActiveDir $RequestFile.Name

Write-Host "Processing request: $($RequestFile.Name)"
Move-Item -Path $RequestFile.FullName -Destination $ActivePath -Force

$AuditStarted = Get-Date
$RequestId = [System.IO.Path]::GetFileNameWithoutExtension($RequestFile.Name)
$Repository = "ppow1/theestate"
$Branch = (& git rev-parse --abbrev-ref HEAD).Trim()
$Commit = (& git rev-parse HEAD).Trim()
$Classification = "Estate Internal"
$WorkPackageId = "unknown"

try {
    $RequestRaw = Get-Content -Path $ActivePath -Raw
    $Request = $RequestRaw | ConvertFrom-Json

    if ($Request.request_id) { $RequestId = $Request.request_id }
    if ($Request.work_package_id) { $WorkPackageId = $Request.work_package_id }
    if ($Request.classification) { $Classification = $Request.classification }

    $Target = if ($Request.target) { Join-Path $EstateRoot $Request.target } else { $null }

    if (-not $Request.request_id) {
        throw "Missing required field: request_id"
    }

    if (-not $Request.target) {
        throw "Missing required field: target"
    }

    if (-not (Test-Path $Target)) {
        throw "Audit target does not exist: $($Request.target)"
    }

    $AuditFinished = Get-Date

    $Result = [ordered]@{
        request_id = $RequestId
        status = "pass"
        repository = $Repository
        branch = $Branch
        local_commit = $Commit
        work_package_id = $WorkPackageId
        audit_started_at = $AuditStarted.ToString("s")
        audit_finished_at = $AuditFinished.ToString("s")
        command_run = "structure validation"
        exit_code = 0
        summary = "Audit request parsed successfully and target exists."
        full_audit_output = "Validated target: $($Request.target)"
        stderr = ""
        follow_up_required = $false
        history_drift_detected = $false
        classification = $Classification
    }

    $ResultPath = Join-Path $ResultsDir ("$RequestId.result.json")
    $Result | ConvertTo-Json -Depth 8 | Set-Content -Path $ResultPath -Encoding UTF8

    Move-Item -Path $ActivePath -Destination (Join-Path $ArchiveDir $RequestFile.Name) -Force

    Write-Host "Audit request passed."
    Write-Host "Result written: $ResultPath"
    exit 0
}
catch {
    $AuditFinished = Get-Date

    $Result = [ordered]@{
        request_id = $RequestId
        status = "error"
        repository = $Repository
        branch = $Branch
        local_commit = $Commit
        work_package_id = $WorkPackageId
        audit_started_at = $AuditStarted.ToString("s")
        audit_finished_at = $AuditFinished.ToString("s")
        command_run = "structure validation"
        exit_code = 1
        summary = "Audit request failed validation."
        full_audit_output = ""
        stderr = $_.Exception.Message
        follow_up_required = $true
        history_drift_detected = $false
        classification = $Classification
    }

    $ResultPath = Join-Path $ResultsDir ("$RequestId.result.json")
    $Result | ConvertTo-Json -Depth 8 | Set-Content -Path $ResultPath -Encoding UTF8

    Move-Item -Path $ActivePath -Destination (Join-Path $FailedDir $RequestFile.Name) -Force

    Write-Host "Audit request failed validation."
    Write-Host "Result written: $ResultPath"
    Write-Host $_.Exception.Message
    exit 0
}
