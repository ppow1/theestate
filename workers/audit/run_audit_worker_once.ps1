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

Write-Host "=== Estate Audit Worker v1 ==="
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

$Request = Get-Content -Path $ActivePath -Raw | ConvertFrom-Json

$RequestId = if ($Request.request_id) { $Request.request_id } else { [System.IO.Path]::GetFileNameWithoutExtension($RequestFile.Name) }
$WorkPackageId = if ($Request.work_package_id) { $Request.work_package_id } else { "unknown" }
$Classification = if ($Request.classification) { $Request.classification } else { "Estate Internal" }

$Repository = "ppow1/theestate"
$Branch = (& git rev-parse --abbrev-ref HEAD).Trim()
$Commit = (& git rev-parse HEAD).Trim()

$AuditStarted = Get-Date
$StdoutPath = Join-Path $ResultsDir ("$RequestId.stdout.txt")
$StderrPath = Join-Path $ResultsDir ("$RequestId.stderr.txt")
$CommandRun = ".\estate.bat audit"

$ExitCode = 0
$WorkerError = $null

try {
    $Output = & .\estate.bat audit 2>&1
    $ExitCode = $LASTEXITCODE
    $OutputText = ($Output | Out-String).Trim()
    Set-Content -Path $StdoutPath -Value $OutputText -Encoding UTF8
    Set-Content -Path $StderrPath -Value "" -Encoding UTF8
}
catch {
    $ExitCode = 999
    $WorkerError = $_.Exception.Message
    $OutputText = ""
    Set-Content -Path $StdoutPath -Value "" -Encoding UTF8
    Set-Content -Path $StderrPath -Value $WorkerError -Encoding UTF8
}

$AuditFinished = Get-Date
$Stdout = Get-Content -Path $StdoutPath -Raw
$Stderr = Get-Content -Path $StderrPath -Raw

$FailedCount = $null
if ($Stdout -match "Failed:\s*(\d+)") {
    $FailedCount = [int]$Matches[1]
}

if ($WorkerError) {
    $Status = "error"
}
elseif ($ExitCode -eq 0 -and ($FailedCount -eq $null -or $FailedCount -eq 0)) {
    $Status = "pass"
}
else {
    $Status = "fail"
}

$HistoryDriftDetected = $false
if ($Stdout -match "history drift|latest git.*ledger|ledger.*git|devlog|EC-" -or $Stderr -match "history drift|latest git.*ledger|ledger.*git|devlog|EC-") {
    $HistoryDriftDetected = $true
}

$FollowUpRequired = ($Status -ne "pass") -or $HistoryDriftDetected
$Summary = "Audit status=$Status exit_code=$ExitCode branch=$Branch commit=$Commit work_package=$WorkPackageId"

$Result = [ordered]@{
    request_id = $RequestId
    status = $Status
    repository = $Repository
    branch = $Branch
    local_commit = $Commit
    work_package_id = $WorkPackageId
    audit_started_at = $AuditStarted.ToString("s")
    audit_finished_at = $AuditFinished.ToString("s")
    command_run = $CommandRun
    exit_code = $ExitCode
    summary = $Summary
    full_audit_output = $Stdout
    stderr = $Stderr
    follow_up_required = $FollowUpRequired
    history_drift_detected = $HistoryDriftDetected
    classification = $Classification
}

$ResultPath = Join-Path $ResultsDir ("$RequestId.result.json")
$Result | ConvertTo-Json -Depth 8 | Set-Content -Path $ResultPath -Encoding UTF8

if ($WorkerError) {
    Move-Item -Path $ActivePath -Destination (Join-Path $FailedDir $RequestFile.Name) -Force
}
else {
    Move-Item -Path $ActivePath -Destination (Join-Path $ArchiveDir $RequestFile.Name) -Force
}

Write-Host "Result written: $ResultPath"
Write-Host $Summary

if ($Status -eq "error") {
    exit 1
}

exit 0
