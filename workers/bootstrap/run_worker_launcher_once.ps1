Clear-Host

$ErrorActionPreference = "Stop"

$EstateRoot = "A:\theestate"
Set-Location $EstateRoot

$PendingDir = Join-Path $EstateRoot "collaboration\workers\launch\pending"
$ActiveDir = Join-Path $EstateRoot "collaboration\workers\launch\active"
$ResultsDir = Join-Path $EstateRoot "collaboration\workers\launch\results"
$ArchiveDir = Join-Path $EstateRoot "collaboration\workers\launch\archive"
$FailedDir = Join-Path $EstateRoot "collaboration\workers\launch\failed"
$SessionRoot = Join-Path $EstateRoot "runtime\worker_sessions"

foreach ($Dir in @($PendingDir, $ActiveDir, $ResultsDir, $ArchiveDir, $FailedDir, $SessionRoot)) {
    New-Item -ItemType Directory -Force -Path $Dir | Out-Null
}

function Remove-AnsiNoise {
    param([string]$Text)

    $esc = [char]27
    $Clean = $Text
    $Clean = $Clean -replace "$esc\[[0-9;?]*[A-Za-z]", ""
    $Clean = $Clean -replace "[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]\s*", ""
    $Clean = $Clean -replace "(?m)^\s*$", ""
    return $Clean.Trim()
}

Write-Host "=== Estate Local Worker Launcher v1.1 ==="
Write-Host "Estate Root: $EstateRoot"
Write-Host ""

$Pending = Get-ChildItem -Path $PendingDir -Filter "*.json" -File -ErrorAction SilentlyContinue | Sort-Object Name

if ($Pending.Count -eq 0) {
    Write-Host "No pending worker launch requests."
    exit 0
}

$RequestFile = $Pending[0]
$ActivePath = Join-Path $ActiveDir $RequestFile.Name

Write-Host "Processing launch request: $($RequestFile.Name)"
Move-Item -Path $RequestFile.FullName -Destination $ActivePath -Force

$Request = Get-Content -Path $ActivePath -Raw | ConvertFrom-Json

$RequestId = if ($Request.request_id) { $Request.request_id } else { [System.IO.Path]::GetFileNameWithoutExtension($RequestFile.Name) }
$WorkerId = if ($Request.worker_id) { $Request.worker_id } else { "local_worker" }
$Model = if ($Request.model) { $Request.model } else { throw "Launch request missing model." }
$Role = if ($Request.role) { $Request.role } else { "worker" }
$WorkPackageId = if ($Request.work_package_id) { $Request.work_package_id } else { "unknown" }
$WorkPackagePath = if ($Request.work_package_path) { Join-Path $EstateRoot $Request.work_package_path } else { throw "Launch request missing work_package_path." }
$Classification = if ($Request.classification) { $Request.classification } else { "Estate Internal" }

$Models = @(ollama list | Select-Object -Skip 1 | ForEach-Object { ($_ -split "\s+")[0] } | Where-Object { $_ })
if ($Models -notcontains $Model) {
    throw "Requested Ollama model not found: $Model"
}

if (!(Test-Path $WorkPackagePath)) {
    throw "Work package not found: $WorkPackagePath"
}

$SessionDir = Join-Path $SessionRoot $RequestId
New-Item -ItemType Directory -Force -Path $SessionDir | Out-Null

$PromptPath = Join-Path $SessionDir "worker_prompt.txt"
$TranscriptPath = Join-Path $SessionDir "worker_output.txt"
$RawTranscriptPath = Join-Path $SessionDir "worker_output.raw.txt"

$Docs = @(
    "docs\onboarding\visual_manifest.md",
    "docs\collaboration\Worker_Runtime_Contract_v1.md",
    "docs\collaboration\Instruction_Precedence_v1.md",
    "docs\governance\Estate_Orientation_Handbook.md",
    "docs\governance\Estate_Manual.md"
)

foreach ($Doc in $Docs) {
    $Full = Join-Path $EstateRoot $Doc
    if (!(Test-Path $Full)) {
        throw "Missing onboarding document: $Doc"
    }
}

$Prompt = @"
You are $WorkerId, an Estate local $Role worker.

Runtime authority:
- Local repository: A:\theestate
- Classification: $Classification
- Work Package: $WorkPackageId

Follow the Worker Runtime Contract and Instruction Precedence.
Do not assume GitHub is part of your runtime unless explicitly authorized.
Review the onboarding visual manifest before beginning.
Then review the assigned work package and produce the requested output.

Repository context follows.
"@

foreach ($Doc in $Docs) {
    $Full = Join-Path $EstateRoot $Doc
    $Prompt += "`n`n============================================================`n"
    $Prompt += "FILE: $Doc`n"
    $Prompt += "============================================================`n"
    $Prompt += Get-Content $Full -Raw
}

$Prompt += "`n`n============================================================`n"
$Prompt += "FILE: $($Request.work_package_path)`n"
$Prompt += "============================================================`n"
$Prompt += Get-Content $WorkPackagePath -Raw

Set-Content -Path $PromptPath -Value $Prompt -Encoding UTF8

$StartedAt = Get-Date
Write-Host "Launching model: $Model"
Write-Host "Prompt: $PromptPath"
Write-Host "Transcript: $TranscriptPath"
Write-Host "Raw transcript: $RawTranscriptPath"
Write-Host ""

try {
    $RawOutput = Get-Content $PromptPath -Raw | ollama run $Model 2>&1 | Out-String
    Set-Content -Path $RawTranscriptPath -Value $RawOutput -Encoding UTF8

    $CleanOutput = Remove-AnsiNoise -Text $RawOutput
    Set-Content -Path $TranscriptPath -Value $CleanOutput -Encoding UTF8

    if ($CleanOutput) {
        Write-Host $CleanOutput
    } else {
        Write-Host "Worker completed but produced no clean transcript output."
    }

    $Status = "completed"
    $ErrorText = ""
    Move-Item -Path $ActivePath -Destination (Join-Path $ArchiveDir $RequestFile.Name) -Force
}
catch {
    $Status = "error"
    $ErrorText = $_.Exception.Message
    Set-Content -Path $RawTranscriptPath -Value $ErrorText -Encoding UTF8
    Set-Content -Path $TranscriptPath -Value $ErrorText -Encoding UTF8
    Move-Item -Path $ActivePath -Destination (Join-Path $FailedDir $RequestFile.Name) -Force
}

$FinishedAt = Get-Date
$DurationSeconds = [math]::Round(($FinishedAt - $StartedAt).TotalSeconds, 3)
$Branch = (& git rev-parse --abbrev-ref HEAD).Trim()
$Commit = (& git rev-parse HEAD).Trim()
$TranscriptLength = if (Test-Path $TranscriptPath) { (Get-Item $TranscriptPath).Length } else { 0 }

$Result = [ordered]@{
    request_id = $RequestId
    worker_id = $WorkerId
    status = $Status
    model = $Model
    role = $Role
    work_package_id = $WorkPackageId
    prompt_path = $PromptPath
    transcript_path = $TranscriptPath
    raw_transcript_path = $RawTranscriptPath
    transcript_length_bytes = $TranscriptLength
    branch = $Branch
    local_commit = $Commit
    started_at = $StartedAt.ToString("s")
    finished_at = $FinishedAt.ToString("s")
    duration_seconds = $DurationSeconds
    classification = $Classification
    error = $ErrorText
}

$ResultPath = Join-Path $ResultsDir ("$RequestId.result.json")
$Result | ConvertTo-Json -Depth 8 | Set-Content -Path $ResultPath -Encoding UTF8

Write-Host ""
Write-Host "Worker result: $Status"
Write-Host "Result file: $ResultPath"
Write-Host "Clean transcript: $TranscriptPath"

if ($Status -eq "error") {
    exit 1
}

exit 0
