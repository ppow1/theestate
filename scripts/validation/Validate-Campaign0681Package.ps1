[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidatePattern('^WP-\d{4}$')]
    [string]$PackageId,

    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ManifestPath = Join-Path $RepoRoot `
    "collaboration\work_packages\planning\CAMPAIGN_0681_manifest.json"

if (-not (Test-Path -LiteralPath $ManifestPath)) {
    throw "CAMPAIGN-0681 manifest is missing."
}

$Manifest = Get-Content -Raw -LiteralPath $ManifestPath |
    ConvertFrom-Json -Depth 100

$Package = @($Manifest.packages) |
    Where-Object { $_.id -eq $PackageId } |
    Select-Object -First 1

if (-not $Package) {
    throw "Package $PackageId is not listed in CAMPAIGN-0681."
}

$PackagePath = Join-Path $RepoRoot ($Package.path -replace "/", "\")
$ReceiptPath = Join-Path $RepoRoot ($Package.receipt_path -replace "/", "\")

if (-not (Test-Path -LiteralPath $PackagePath)) {
    throw "Package specification is missing: $($Package.path)"
}

$PackageText = Get-Content -Raw -LiteralPath $PackagePath

$RequiredHeadingGroups = @(
    @("## Objective"),
    @("## Required Work", "## Scope", "## Required Behavior", "## Behavior"),
    @("## Required Deliverables", "## Deliverables", "## Required Outputs", "## Outputs"),
    @("## Required Validation", "## Validation", "## Executable Validation Commands", "## Exact Validation Commands"),
    @("## Acceptance Criteria")
)

foreach ($HeadingGroup in $RequiredHeadingGroups) {
    $Matched = @($HeadingGroup | Where-Object {
        $PackageText -match [regex]::Escape($_)
    })
    if ($Matched.Count -eq 0) {
        throw "$PackageId is missing required heading (accepted forms: $($HeadingGroup -join ', '))"
    }
}

if ($PackageText -notmatch "## (?:Executable|Exact|Required) Validation Commands") {
    throw "$PackageId has no executable validation-command section."
}

if (-not (Test-Path -LiteralPath $ReceiptPath)) {
    throw "Completion receipt is missing: $($Package.receipt_path)"
}

$ReceiptText = Get-Content -Raw -LiteralPath $ReceiptPath

if ($ReceiptText -notmatch [regex]::Escape($PackageId)) {
    throw "Completion receipt does not identify $PackageId."
}

$ReceiptRequirements = @(
    "validation",
    "command",
    "result"
)

foreach ($Requirement in $ReceiptRequirements) {
    if ($ReceiptText -notmatch "(?i)$Requirement") {
        throw "Receipt lacks required validation evidence term: $Requirement"
    }
}

$DeliverableSectionMatch = [regex]::Match(
    $PackageText,
    "(?s)## (?:Required Deliverables|Deliverables|Required Outputs|Outputs)\s*(.*?)(?=\r?\n## |\z)"
)

if ($DeliverableSectionMatch.Success) {
    $Candidates = [regex]::Matches(
        $DeliverableSectionMatch.Groups[1].Value,
        '`([^`]+)`'
    ) |
    ForEach-Object {
        $_.Groups[1].Value
    } |
    Where-Object {
        $_ -match '[/\\]' -and
        $_ -notmatch '\*' -and
        $_ -notmatch ' or ' -and
        $_ -notmatch '^https?://'
    } |
    Sort-Object -Unique

    foreach ($Candidate in $Candidates) {
        $CandidatePath = Join-Path $RepoRoot ($Candidate -replace "/", "\")

        if (-not (Test-Path -LiteralPath $CandidatePath)) {
            throw "Required deliverable is missing: $Candidate"
        }
    }
}

Push-Location -LiteralPath $RepoRoot

try {
    $DiffCheckOutput = & git diff --check 2>&1

    if ($LASTEXITCODE -ne 0) {
        throw "git diff --check failed:`n$($DiffCheckOutput -join "`n")"
    }

    $Status = @(& git status --porcelain)

    $UnexpectedGeneratedArtifacts = @(
        $Status | Where-Object {
            $_ -match '\.tmp$|\.bak$|\.orig$|\.rej$'
        }
    )

    if ($UnexpectedGeneratedArtifacts.Count -gt 0) {
        throw "Unexpected temporary artifacts exist:`n$($UnexpectedGeneratedArtifacts -join "`n")"
    }
}
finally {
    Pop-Location
}

Write-Host "Package validation passed: $PackageId"
Write-Host "Specification: $($Package.path)"
Write-Host "Receipt      : $($Package.receipt_path)"
