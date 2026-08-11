[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('C1', 'C2', 'C3')]
    [string]$Seat,
    [string]$Prompt,
    [switch]$NoClipboard
)

$ErrorActionPreference = 'Stop'
$estateRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$configScript = Join-Path $PSScriptRoot 'Get-CodexSeatConfiguration.ps1'
$configuration = (& $configScript -Seat $Seat | Out-String | ConvertFrom-Json)
$seatRecord = @($configuration.seats) | Where-Object { $_.seat_id -eq $Seat } | Select-Object -First 1
if (-not $seatRecord -or -not $seatRecord.codex_home) { throw "No approved CODEX_HOME is configured for $Seat." }

if ([string]::IsNullOrWhiteSpace($Prompt)) {
    $Prompt = Read-Host "[$Seat] Codex prompt"
}
if ([string]::IsNullOrWhiteSpace($Prompt)) { throw 'A prompt is required.' }

$artifactRoot = Join-Path $estateRoot "runtime\codex_bridge\seat_results\$Seat"
New-Item -ItemType Directory -Force -Path $artifactRoot | Out-Null
$runId = "{0}-{1}" -f (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ'), ([guid]::NewGuid().ToString('N').Substring(0, 8))
$messageTemp = Join-Path $artifactRoot ".latest.$runId.md.tmp"
$eventsPath = Join-Path $artifactRoot "$runId.jsonl"
$latestPath = Join-Path $artifactRoot 'latest.md'

$previousCodexHome = $env:CODEX_HOME
$env:CODEX_HOME = [string]$seatRecord.codex_home
$exitCode = 1
try {
    # --output-last-message is the supported final-response handoff. --ephemeral avoids
    # creating/updating a resumable Codex session; authentication is never touched.
    $Prompt | & codex exec --ask-for-approval never --sandbox workspace-write --color never --ephemeral --json --output-last-message $messageTemp - 2>&1 | Tee-Object -FilePath $eventsPath
    $exitCode = $LASTEXITCODE
}
finally {
    if ($null -eq $previousCodexHome) { Remove-Item Env:CODEX_HOME -ErrorAction SilentlyContinue }
    else { $env:CODEX_HOME = $previousCodexHome }
}

if (-not (Test-Path -LiteralPath $messageTemp)) {
    $failureText = "Codex $Seat completed without a final response file. Exit code: $exitCode`r`n`r`nSee JSONL events: $eventsPath"
    [IO.File]::WriteAllText($messageTemp, $failureText, [Text.UTF8Encoding]::new($false))
}

# Publish the seat-local result only after the CLI has finished writing it. A replace
# is isolated per seat, so C1/C2/C3 cannot overwrite one another.
Move-Item -LiteralPath $messageTemp -Destination $latestPath -Force
if (-not $NoClipboard) {
    try { Get-Content -Raw -LiteralPath $latestPath | Set-Clipboard }
    catch { Write-Warning "[$Seat] result saved, but clipboard copy failed: $($_.Exception.Message)" }
}

Write-Host "[$Seat] result saved: $latestPath"
Write-Host '[R] Re-copy this seat''s latest result to clipboard'
Write-Host '[O] Open/view this seat''s latest result'
Write-Host '[Enter] Continue'
$choice = (Read-Host).Trim().ToUpperInvariant()
switch ($choice) {
    'R' {
        try { Get-Content -Raw -LiteralPath $latestPath | Set-Clipboard; Write-Host "[$Seat] latest result copied." }
        catch { Write-Warning "[$Seat] clipboard copy failed: $($_.Exception.Message)" }
    }
    'O' { Start-Process -FilePath $latestPath }
}
exit $exitCode
