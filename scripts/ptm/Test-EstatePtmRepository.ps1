#requires -Version 5.1
<#
.SYNOPSIS
Verifies the repository-maintained Estate PTM planning and completion evidence.

.DESCRIPTION
Performs read-only consistency checks across the PTM package, campaign, and
dependency manifests, their referenced repository files, and package completion
receipts. The command never infers acceptance or changes lifecycle state.

.PARAMETER RepositoryRoot
Repository root to inspect. Defaults to the root containing this script.

.PARAMETER Json
Writes the complete result envelope as JSON instead of the human-readable report.

.PARAMETER SkipCompletionReceipts
Skips completion-receipt checks when validating a campaign that is still running.

.EXAMPLE
CLS
& .\scripts\ptm\Test-EstatePtmRepository.ps1

.EXAMPLE
CLS
& .\scripts\ptm\Test-EstatePtmRepository.ps1 -Json |
    Set-Content -Encoding UTF8 .\ptm-verification.json
#>
[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [switch]$Json,
    [switch]$SkipCompletionReceipts
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:Findings = [System.Collections.Generic.List[object]]::new()

function Add-Finding {
    param(
        [ValidateSet('Error', 'Warning')][string]$Severity,
        [string]$Code,
        [string]$Message,
        [string]$Artifact = ''
    )
    $script:Findings.Add([pscustomobject]@{
        severity = $Severity.ToLowerInvariant()
        code = $Code
        message = $Message
        artifact = $Artifact
    })
}

function Resolve-RepositoryPath {
    param([string]$RelativePath)
    if ([string]::IsNullOrWhiteSpace($RelativePath)) { return $null }
    if ([IO.Path]::IsPathRooted($RelativePath)) {
        Add-Finding Error 'PTM-PATH-ABSOLUTE' "Manifest path must be repository-relative: $RelativePath" $RelativePath
        return $null
    }
    $root = [IO.Path]::GetFullPath($RepositoryRoot).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
    $candidate = [IO.Path]::GetFullPath((Join-Path $root $RelativePath))
    if (($candidate -ne $root) -and (-not $candidate.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase))) {
        Add-Finding Error 'PTM-PATH-ESCAPE' "Manifest path escapes the repository: $RelativePath" $RelativePath
        return $null
    }
    return $candidate
}

function Test-ReferencedFile {
    param([string]$RelativePath, [string]$Code = 'PTM-FILE-MISSING')
    $resolved = Resolve-RepositoryPath $RelativePath
    if ($null -ne $resolved -and -not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        Add-Finding Error $Code "Referenced file does not exist: $RelativePath" $RelativePath
        return $false
    }
    return $null -ne $resolved
}

function Read-Manifest {
    param([string]$RelativePath)
    $resolved = Resolve-RepositoryPath $RelativePath
    if ($null -eq $resolved -or -not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        Add-Finding Error 'PTM-MANIFEST-MISSING' "Required manifest does not exist: $RelativePath" $RelativePath
        return $null
    }
    try { return Get-Content -LiteralPath $resolved -Raw -Encoding UTF8 | ConvertFrom-Json }
    catch {
        Add-Finding Error 'PTM-MANIFEST-JSON' "Manifest is not valid JSON: $RelativePath ($($_.Exception.Message))" $RelativePath
        return $null
    }
}

function Test-UniqueIds {
    param([object[]]$Items, [string]$Property, [string]$Kind)
    @($Items | Group-Object -Property $Property | Where-Object Count -gt 1) | ForEach-Object {
        Add-Finding Error 'PTM-ID-DUPLICATE' "Duplicate $Kind ID: $($_.Name)" $_.Name
    }
}

function Test-AcyclicDependencies {
    param([hashtable]$Graph)
    $visiting = @{}
    $visited = @{}
    function Visit-Node([string]$Node, [string[]]$Trail) {
        if ($visiting.ContainsKey($Node)) {
            Add-Finding Error 'PTM-DEPENDENCY-CYCLE' "Dependency cycle: $((@($Trail) + $Node) -join ' -> ')" $Node
            return
        }
        if ($visited.ContainsKey($Node)) { return }
        $visiting[$Node] = $true
        foreach ($dependency in @($Graph[$Node])) { Visit-Node $dependency (@($Trail) + $Node) }
        $visiting.Remove($Node)
        $visited[$Node] = $true
    }
    foreach ($node in @($Graph.Keys)) { Visit-Node $node @() }
}

$manifestDirectory = 'collaboration/work_packages/planning'
$packageManifestPath = "$manifestDirectory/estate_ptm_package_manifest.json"
$campaignManifestPath = "$manifestDirectory/estate_ptm_campaign_manifest.json"
$dependencyManifestPath = "$manifestDirectory/estate_ptm_dependency_manifest.json"
$packageManifest = Read-Manifest $packageManifestPath
$campaignManifest = Read-Manifest $campaignManifestPath
$dependencyManifest = Read-Manifest $dependencyManifestPath

if ($null -ne $packageManifest -and $null -ne $campaignManifest -and $null -ne $dependencyManifest) {
    $packages = @($packageManifest.packages)
    $campaigns = @($campaignManifest.campaigns)
    Test-UniqueIds $packages 'package_id' 'package'
    Test-UniqueIds $campaigns 'campaign_id' 'campaign'

    $packageById = @{}
    foreach ($package in $packages) {
        $id = [string]$package.package_id
        if ([string]::IsNullOrWhiteSpace($id)) {
            Add-Finding Error 'PTM-PACKAGE-ID-MISSING' 'A package manifest entry has no package_id.' $packageManifestPath
            continue
        }
        $packageById[$id] = $package
        foreach ($pathProperty in @('pending_path', 'source_draft_path', 'campaign_instruction_path')) {
            $path = [string]$package.$pathProperty
            if ([string]::IsNullOrWhiteSpace($path)) {
                Add-Finding Error 'PTM-PACKAGE-PATH-MISSING' "$id has no $pathProperty." $packageManifestPath
            } else { [void](Test-ReferencedFile $path) }
        }
        if ([string]$package.file_path -ne [string]$package.pending_path) {
            Add-Finding Error 'PTM-PACKAGE-PATH-MISMATCH' "$id file_path and pending_path differ." $packageManifestPath
        }
        if ([string]$package.execution_lane -ne 'Codex' -or [string]$package.preferred_lane -ne 'Codex') {
            Add-Finding Error 'PTM-LANE-POLICY' "$id is not assigned to the required Codex lane." $packageManifestPath
        }
        if (-not $SkipCompletionReceipts) {
            $receipt = "collaboration/work_packages/completions/${id}_completion_receipt.md"
            if (Test-ReferencedFile $receipt 'PTM-RECEIPT-MISSING') {
                $receiptText = Get-Content -LiteralPath (Resolve-RepositoryPath $receipt) -Raw -Encoding UTF8
                if ($receiptText -notmatch [regex]::Escape($id) -or
                    $receiptText -notmatch '(?i)\b(complete|completed|completion)\b') {
                    Add-Finding Error 'PTM-RECEIPT-CONTENT' "Completion receipt does not identify $id and completion evidence." $receipt
                }
            }
        }
    }

    $campaignById = @{}
    $campaignMembership = @{}
    foreach ($campaign in $campaigns) {
        $campaignId = [string]$campaign.campaign_id
        $campaignById[$campaignId] = $campaign
        [void](Test-ReferencedFile ([string]$campaign.campaign_instruction_path))
        foreach ($packageId in @($campaign.included_package_ids)) {
            if (-not $packageById.ContainsKey([string]$packageId)) {
                Add-Finding Error 'PTM-CAMPAIGN-UNKNOWN-PACKAGE' "$campaignId includes unknown package $packageId." $campaignManifestPath
                continue
            }
            if ($campaignMembership.ContainsKey([string]$packageId)) {
                Add-Finding Error 'PTM-CAMPAIGN-DUPLICATE-MEMBERSHIP' "$packageId belongs to more than one campaign." $campaignManifestPath
            }
            $campaignMembership[[string]$packageId] = $campaignId
            if ([string]$packageById[[string]$packageId].campaign -ne $campaignId) {
                Add-Finding Error 'PTM-CAMPAIGN-MISMATCH' "$packageId names a different campaign in the package manifest." $packageId
            }
        }
        foreach ($prerequisite in @($campaign.prerequisite_campaigns)) {
            if (-not (@($campaigns.campaign_id) -contains $prerequisite)) {
                Add-Finding Error 'PTM-CAMPAIGN-UNKNOWN-PREREQUISITE' "$campaignId requires unknown campaign $prerequisite." $campaignManifestPath
            }
        }
        foreach ($path in @($campaign.pending_package_paths + $campaign.draft_paths)) { [void](Test-ReferencedFile ([string]$path)) }
    }
    foreach ($id in $packageById.Keys) {
        if (-not $campaignMembership.ContainsKey($id)) {
            Add-Finding Error 'PTM-CAMPAIGN-MEMBERSHIP-MISSING' "$id is absent from all campaigns." $campaignManifestPath
        }
    }

    $graph = @{}
    foreach ($property in @($dependencyManifest.hard_dependencies.PSObject.Properties)) {
        $id = [string]$property.Name
        $dependencies = @($property.Value)
        $graph[$id] = $dependencies
        if (-not $packageById.ContainsKey($id)) {
            Add-Finding Error 'PTM-DEPENDENCY-UNKNOWN-PACKAGE' "Dependency manifest defines unknown package $id." $dependencyManifestPath
            continue
        }
        if ((@($packageById[$id].dependencies) -join "`n") -ne ($dependencies -join "`n")) {
            Add-Finding Error 'PTM-DEPENDENCY-MISMATCH' "$id dependencies differ between package and dependency manifests." $id
        }
        foreach ($dependency in $dependencies) {
            if (-not $packageById.ContainsKey([string]$dependency)) {
                Add-Finding Error 'PTM-DEPENDENCY-UNKNOWN-TARGET' "$id depends on unknown package $dependency." $dependencyManifestPath
            }
        }
    }
    foreach ($id in $packageById.Keys) {
        if (-not $graph.ContainsKey($id)) { Add-Finding Error 'PTM-DEPENDENCY-ENTRY-MISSING' "$id has no hard-dependency entry." $dependencyManifestPath }
    }
    Test-AcyclicDependencies $graph

    foreach ($pathMap in @($dependencyManifest.promoted_pending_paths, $dependencyManifest.campaign_instruction_paths)) {
        foreach ($pathProperty in @($pathMap.PSObject.Properties)) {
            [void](Test-ReferencedFile ([string]$pathProperty.Value))
        }
    }
}

$errors = @($script:Findings | Where-Object severity -eq 'error')
$warnings = @($script:Findings | Where-Object severity -eq 'warning')
$result = [pscustomobject]@{
    schema_version = '1.0'
    verifier = 'Estate.PTM.Repository'
    repository_root = [IO.Path]::GetFullPath($RepositoryRoot)
    generated_at_utc = [DateTime]::UtcNow.ToString('o')
    passed = ($errors.Count -eq 0)
    summary = [pscustomobject]@{ errors = $errors.Count; warnings = $warnings.Count; findings = $script:Findings.Count }
    findings = @($script:Findings)
}

if ($Json) { $result | ConvertTo-Json -Depth 8 }
else {
    $status = if ($result.passed) { 'PASS' } else { 'FAIL' }
    Write-Host "Estate PTM repository verification: $status"
    Write-Host "Errors: $($errors.Count)  Warnings: $($warnings.Count)"
    foreach ($finding in $script:Findings) {
        Write-Host ("[{0}] {1}: {2}" -f $finding.severity.ToUpperInvariant(), $finding.code, $finding.message)
    }
}

if (-not $result.passed) { exit 1 }
exit 0
