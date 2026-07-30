[CmdletBinding()]
param(
    [string]$EstateRoot = 'A:\theestate-wp4233',
    [string]$RuntimeRoot = 'A:\AI\Tools\EngineeringWorkerRuntime',
    [string]$WorktreeRoot = 'A:\AI\EngineeringWorktrees',
    [string]$RunRoot = 'A:\AI\EngineeringRuns',
    [string]$OutputRoot = 'A:\AI\Reports\EngineeringOperationalEvidence',
    [int]$RecentRunLimit = 20,
    [int]$MaxTextFileMB = 5
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
CLS

$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$reportRoot = Join-Path $OutputRoot $timestamp
$evidenceRoot = Join-Path $reportRoot 'evidence'
$summaryPath = Join-Path $reportRoot 'SUMMARY.txt'
$jsonPath = Join-Path $reportRoot 'engineering-operational-evidence.json'
$transcriptPath = Join-Path $reportRoot 'collector-transcript.txt'
$zipPath = "$reportRoot.zip"

New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null
Start-Transcript -Path $transcriptPath -Force | Out-Null

function Write-Section {
    param([string]$Title)
    Write-Host ''
    Write-Host ('=' * 78)
    Write-Host $Title
    Write-Host ('=' * 78)
}

function Get-SafeHash {
    param([Parameter(Mandatory)][string]$Path)
    try {
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
        }
    }
    catch {
        return "HASH_ERROR: $($_.Exception.Message)"
    }
    return $null
}

function ConvertTo-RedactedText {
    param([Parameter(Mandatory)][string]$Text)

    $patterns = @(
        '(?im)(api[_-]?key\s*[=:]\s*)[^\s\"\'']+',
        '(?im)(token\s*[=:]\s*)[^\s\"\'']+',
        '(?im)(secret\s*[=:]\s*)[^\s\"\'']+',
        '(?im)(password\s*[=:]\s*)[^\s\"\'']+',
        '(?im)(authorization\s*:\s*bearer\s+)[^\s\"\'']+',
        '(?im)(sk-[A-Za-z0-9_-]{12,})',
        '(?im)(gh[pousr]_[A-Za-z0-9_]{20,})'
    )

    $result = $Text
    foreach ($pattern in $patterns) {
        $result = [regex]::Replace($result, $pattern, {
            param($m)
            if ($m.Groups.Count -gt 1 -and $m.Groups[1].Success) {
                return $m.Groups[1].Value + '<REDACTED>'
            }
            return '<REDACTED>'
        })
    }
    return $result
}

function Copy-RedactedTextFile {
    param(
        [Parameter(Mandatory)][string]$Source,
        [Parameter(Mandatory)][string]$Destination
    )

    try {
        $file = Get-Item -LiteralPath $Source -ErrorAction Stop
        if ($file.Length -gt ($MaxTextFileMB * 1MB)) {
            return [pscustomobject]@{
                source = $Source
                copied = $false
                reason = "File exceeds ${MaxTextFileMB}MB limit"
                sha256 = Get-SafeHash -Path $Source
            }
        }

        $text = Get-Content -LiteralPath $Source -Raw -ErrorAction Stop
        $redacted = ConvertTo-RedactedText -Text $text
        $parent = Split-Path -Parent $Destination
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
        [System.IO.File]::WriteAllText($Destination, $redacted, [System.Text.UTF8Encoding]::new($false))
        return [pscustomobject]@{
            source = $Source
            copied = $true
            destination = $Destination
            sha256 = Get-SafeHash -Path $Source
        }
    }
    catch {
        return [pscustomobject]@{
            source = $Source
            copied = $false
            reason = $_.Exception.Message
            sha256 = Get-SafeHash -Path $Source
        }
    }
}

function Get-DirectoryInventory {
    param([Parameter(Mandatory)][string]$Root)

    if (-not (Test-Path -LiteralPath $Root)) {
        return @()
    }

    return @(
        Get-ChildItem -LiteralPath $Root -Recurse -Force -File -ErrorAction SilentlyContinue |
            ForEach-Object {
                [pscustomobject]@{
                    full_name = $_.FullName
                    relative_path = $_.FullName.Substring($Root.TrimEnd('\').Length).TrimStart('\')
                    length = $_.Length
                    last_write_time = $_.LastWriteTime.ToString('o')
                    extension = $_.Extension
                    sha256 = Get-SafeHash -Path $_.FullName
                }
            }
    )
}

function Get-RecentDirectories {
    param(
        [Parameter(Mandatory)][string]$Root,
        [int]$Limit = 20
    )

    if (-not (Test-Path -LiteralPath $Root)) {
        return @()
    }

    return @(
        Get-ChildItem -LiteralPath $Root -Directory -Force -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First $Limit |
            ForEach-Object {
                [pscustomobject]@{
                    name = $_.Name
                    full_name = $_.FullName
                    creation_time = $_.CreationTime.ToString('o')
                    last_write_time = $_.LastWriteTime.ToString('o')
                    file_count = @(Get-ChildItem -LiteralPath $_.FullName -Recurse -File -ErrorAction SilentlyContinue).Count
                }
            }
    )
}

function Get-CommandProbe {
    param([Parameter(Mandatory)][string]$Name)
    try {
        $cmd = Get-Command $Name -ErrorAction Stop
        return [pscustomobject]@{
            name = $Name
            found = $true
            command_type = $cmd.CommandType.ToString()
            source = $cmd.Source
            path = $cmd.Path
            version = if ($cmd.Version) { $cmd.Version.ToString() } else { $null }
        }
    }
    catch {
        return [pscustomobject]@{
            name = $Name
            found = $false
            error = $_.Exception.Message
        }
    }
}

Write-Section 'Engineering Operational Evidence Collector'
Write-Host "Estate root:    $EstateRoot"
Write-Host "Runtime root:   $RuntimeRoot"
Write-Host "Worktree root:  $WorktreeRoot"
Write-Host "Run root:       $RunRoot"
Write-Host "Report root:    $reportRoot"
Write-Host ''
Write-Host 'This collector is read-only for the Estate and Engineering runtime.'
Write-Host 'It creates files only beneath the report root shown above.'

$evidence = [ordered]@{
    collector = [ordered]@{
        version = '1.0.0'
        started_at = (Get-Date).ToString('o')
        computer_name = $env:COMPUTERNAME
        user_name = $env:USERNAME
        powershell_version = $PSVersionTable.PSVersion.ToString()
        estate_root = $EstateRoot
        runtime_root = $RuntimeRoot
        worktree_root = $WorktreeRoot
        run_root = $RunRoot
        report_root = $reportRoot
    }
    path_status = [ordered]@{}
    manifest = $null
    manifest_validation = [ordered]@{}
    runtime_inventory = @()
    runtime_source_copies = @()
    runtime_reasoning_signals = @()
    estate_integration_files = @()
    recent_runs = @()
    recent_worktrees = @()
    run_evidence_copies = @()
    command_probes = @()
    relevant_processes = @()
    conclusions = @()
    errors = @()
}

Write-Section '1. Path existence'
foreach ($entry in @{
    EstateRoot = $EstateRoot
    RuntimeRoot = $RuntimeRoot
    WorktreeRoot = $WorktreeRoot
    RunRoot = $RunRoot
}.GetEnumerator()) {
    $exists = Test-Path -LiteralPath $entry.Value
    $evidence.path_status[$entry.Key] = [ordered]@{
        path = $entry.Value
        exists = $exists
        item_type = if ($exists) { (Get-Item -LiteralPath $entry.Value).PSIsContainer ? 'Directory' : 'File' } else { $null }
    }
    Write-Host ("{0,-15} {1,-5} {2}" -f $entry.Key, $exists, $entry.Value)
}

Write-Section '2. Runtime manifest and entrypoint'
$manifestPath = Join-Path $RuntimeRoot 'runtime_manifest.json'
if (Test-Path -LiteralPath $manifestPath -PathType Leaf) {
    try {
        $manifestText = Get-Content -LiteralPath $manifestPath -Raw
        $manifest = $manifestText | ConvertFrom-Json
        $evidence.manifest = $manifest
        $evidence.manifest_validation.manifest_exists = $true
        $evidence.manifest_validation.manifest_sha256 = Get-SafeHash -Path $manifestPath
        $evidence.manifest_validation.runtime_id_matches = ($manifest.runtime_id -eq 'engineering-worker-runtime')
        $evidence.manifest_validation.version_matches = ($manifest.version -eq '1.0.0')
        $evidence.manifest_validation.canonical_root_matches = ($manifest.canonical_runtime_root -eq $RuntimeRoot)
        $entrypointPath = if ($manifest.entrypoint) { Join-Path $RuntimeRoot $manifest.entrypoint } else { $null }
        $evidence.manifest_validation.entrypoint = $entrypointPath
        $evidence.manifest_validation.entrypoint_exists = [bool]($entrypointPath -and (Test-Path -LiteralPath $entrypointPath -PathType Leaf))
        $evidence.manifest_validation.entrypoint_sha256 = if ($entrypointPath) { Get-SafeHash -Path $entrypointPath } else { $null }
        Write-Host "Manifest found: $manifestPath"
        Write-Host "Runtime ID:     $($manifest.runtime_id)"
        Write-Host "Version:        $($manifest.version)"
        Write-Host "Entrypoint:     $entrypointPath"
    }
    catch {
        $evidence.errors += "Manifest parse failed: $($_.Exception.Message)"
        Write-Warning "Manifest parse failed: $($_.Exception.Message)"
    }
}
else {
    $evidence.manifest_validation.manifest_exists = $false
    $evidence.errors += "Runtime manifest missing: $manifestPath"
    Write-Warning "Runtime manifest missing: $manifestPath"
}

Write-Section '3. Runtime inventory and safe source capture'
$runtimeInventory = Get-DirectoryInventory -Root $RuntimeRoot
$evidence.runtime_inventory = $runtimeInventory
Write-Host "Runtime files inventoried: $($runtimeInventory.Count)"

$allowedExtensions = @('.py', '.ps1', '.psm1', '.json', '.toml', '.yaml', '.yml', '.md', '.txt', '.ini', '.cfg', '.bat', '.cmd')
if (Test-Path -LiteralPath $RuntimeRoot) {
    $runtimeCopyRoot = Join-Path $evidenceRoot 'runtime-source-redacted'
    foreach ($file in Get-ChildItem -LiteralPath $RuntimeRoot -Recurse -File -Force -ErrorAction SilentlyContinue) {
        if ($allowedExtensions -notcontains $file.Extension.ToLowerInvariant()) { continue }
        $relative = $file.FullName.Substring($RuntimeRoot.TrimEnd('\').Length).TrimStart('\')
        $destination = Join-Path $runtimeCopyRoot $relative
        $evidence.runtime_source_copies += Copy-RedactedTextFile -Source $file.FullName -Destination $destination
    }
}
Write-Host "Runtime text files safely copied: $(@($evidence.runtime_source_copies | Where-Object copied).Count)"

Write-Section '4. Reasoning, model, and provider signal scan'
$signalPattern = '(?i)\b(llm|model|provider|openai|anthropic|ollama|qwen|codex|chat\s*completion|responses?\s*api|prompt|system\s*prompt|inference|agent|planner|planning|reasoning|validate|retry|approve|reject|comfyui|workflow)\b'
$signalFiles = @()
if (Test-Path -LiteralPath $RuntimeRoot) {
    $signalFiles = Get-ChildItem -LiteralPath $RuntimeRoot -Recurse -File -Force -ErrorAction SilentlyContinue |
        Where-Object { $allowedExtensions -contains $_.Extension.ToLowerInvariant() }
}
foreach ($file in $signalFiles) {
    try {
        if ($file.Length -gt ($MaxTextFileMB * 1MB)) { continue }
        $matches = Select-String -LiteralPath $file.FullName -Pattern $signalPattern -AllMatches -ErrorAction Stop
        foreach ($match in $matches) {
            $line = ConvertTo-RedactedText -Text $match.Line.Trim()
            $evidence.runtime_reasoning_signals += [pscustomobject]@{
                file = $file.FullName
                line_number = $match.LineNumber
                line = $line
            }
        }
    }
    catch {
        $evidence.errors += "Signal scan failed for $($file.FullName): $($_.Exception.Message)"
    }
}
Write-Host "Reasoning/model/provider signal lines: $($evidence.runtime_reasoning_signals.Count)"

Write-Section '5. Estate integration file capture'
$estatePaths = @(
    'src\estate\core\local_engineering_department.py',
    'src\estate\cli\local_engineering_department.py',
    'src\estate\core\grace_operations_runtime.py',
    'src\estate\core\grace_helen_engineering_composition.py',
    'src\estate\core\helen_workforce.py',
    'src\estate\core\execution_dispatch.py',
    'src\estate\core\execution_adapter_handoff_runtime.py',
    'scripts\Sync-EngineeringWorkerRuntime.ps1'
)
foreach ($relative in $estatePaths) {
    $source = Join-Path $EstateRoot $relative
    if (Test-Path -LiteralPath $source -PathType Leaf) {
        $destination = Join-Path (Join-Path $evidenceRoot 'estate-integration-redacted') $relative
        $evidence.estate_integration_files += Copy-RedactedTextFile -Source $source -Destination $destination
    }
    else {
        $evidence.estate_integration_files += [pscustomobject]@{
            source = $source
            copied = $false
            reason = 'Not found'
            sha256 = $null
        }
    }
}
Write-Host "Estate integration files found: $(@($evidence.estate_integration_files | Where-Object copied).Count) / $($estatePaths.Count)"

Write-Section '6. Recent Engineering runs and worktrees'
$evidence.recent_runs = Get-RecentDirectories -Root $RunRoot -Limit $RecentRunLimit
$evidence.recent_worktrees = Get-RecentDirectories -Root $WorktreeRoot -Limit $RecentRunLimit
Write-Host "Recent runs found:      $($evidence.recent_runs.Count)"
Write-Host "Recent worktrees found: $($evidence.recent_worktrees.Count)"

$runCopyRoot = Join-Path $evidenceRoot 'recent-run-evidence-redacted'
foreach ($run in $evidence.recent_runs) {
    $runFiles = Get-ChildItem -LiteralPath $run.full_name -Recurse -File -Force -ErrorAction SilentlyContinue |
        Where-Object {
            $allowedExtensions -contains $_.Extension.ToLowerInvariant() -and
            $_.Length -le ($MaxTextFileMB * 1MB)
        }
    foreach ($file in $runFiles) {
        $relativeWithinRun = $file.FullName.Substring($run.full_name.TrimEnd('\').Length).TrimStart('\')
        $destination = Join-Path (Join-Path $runCopyRoot $run.name) $relativeWithinRun
        $evidence.run_evidence_copies += Copy-RedactedTextFile -Source $file.FullName -Destination $destination
    }
}
Write-Host "Recent run text files safely copied: $(@($evidence.run_evidence_copies | Where-Object copied).Count)"

Write-Section '7. Local command availability'
foreach ($commandName in @('python', 'py', 'git', 'codex', 'ollama', 'open-webui')) {
    $probe = Get-CommandProbe -Name $commandName
    $evidence.command_probes += $probe
    Write-Host ("{0,-12} {1}" -f $commandName, $probe.found)
}

Write-Section '8. Relevant running processes (no command lines collected)'
$processNames = @('python', 'pythonw', 'codex', 'ollama', 'open-webui', 'node', 'comfyui')
$evidence.relevant_processes = @(
    Get-Process -ErrorAction SilentlyContinue |
        Where-Object { $processNames -contains $_.ProcessName.ToLowerInvariant() } |
        ForEach-Object {
            [pscustomobject]@{
                process_name = $_.ProcessName
                id = $_.Id
                start_time = try { $_.StartTime.ToString('o') } catch { $null }
                path = try { $_.Path } catch { $null }
            }
        }
)
Write-Host "Relevant processes observed: $($evidence.relevant_processes.Count)"

Write-Section '9. Preliminary local conclusions'
if (-not $evidence.manifest_validation.manifest_exists) {
    $evidence.conclusions += 'LIVE_RUNTIME_NOT_MATERIALIZED: The expected runtime manifest was not found.'
}
elseif (-not $evidence.manifest_validation.entrypoint_exists) {
    $evidence.conclusions += 'LIVE_RUNTIME_INCOMPLETE: The manifest exists, but the declared entrypoint is missing.'
}
else {
    $evidence.conclusions += 'LIVE_RUNTIME_PRESENT: The manifest and declared entrypoint exist.'
}

$reasoningKeywords = @($evidence.runtime_reasoning_signals | Where-Object {
    $_.line -match '(?i)\b(llm|openai|anthropic|ollama|qwen|chat\s*completion|responses?\s*api|inference|planner|reasoning|agent)\b'
})
if ($reasoningKeywords.Count -eq 0) {
    $evidence.conclusions += 'NO_OBVIOUS_MODEL_REASONING_SIGNAL: No obvious LLM/model/planner invocation signal was found in the runtime text files. Manual review is still required.'
}
else {
    $evidence.conclusions += "MODEL_REASONING_SIGNALS_FOUND: $($reasoningKeywords.Count) potentially relevant source lines require review."
}

if ($evidence.recent_runs.Count -eq 0) {
    $evidence.conclusions += 'NO_RECENT_ENGINEERING_RUN_DIRECTORIES: No run directories were found beneath the configured run root.'
}
else {
    $evidence.conclusions += "ENGINEERING_RUN_DIRECTORIES_FOUND: $($evidence.recent_runs.Count) recent run directories were inventoried."
}

$evidence.collector.completed_at = (Get-Date).ToString('o')
$evidence | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

$summaryLines = @(
    'ENGINEERING OPERATIONAL EVIDENCE COLLECTION',
    "Collected: $($evidence.collector.completed_at)",
    "Computer: $($evidence.collector.computer_name)",
    "Estate root: $EstateRoot",
    "Runtime root: $RuntimeRoot",
    "Run root: $RunRoot",
    '',
    'PATH STATUS'
)
foreach ($key in $evidence.path_status.Keys) {
    $item = $evidence.path_status[$key]
    $summaryLines += "- $key : exists=$($item.exists) path=$($item.path)"
}
$summaryLines += @(
    '',
    'MANIFEST VALIDATION',
    "- manifest_exists: $($evidence.manifest_validation.manifest_exists)",
    "- runtime_id_matches: $($evidence.manifest_validation.runtime_id_matches)",
    "- version_matches: $($evidence.manifest_validation.version_matches)",
    "- canonical_root_matches: $($evidence.manifest_validation.canonical_root_matches)",
    "- entrypoint_exists: $($evidence.manifest_validation.entrypoint_exists)",
    '',
    'COUNTS',
    "- runtime_files: $($evidence.runtime_inventory.Count)",
    "- runtime_source_files_copied: $(@($evidence.runtime_source_copies | Where-Object copied).Count)",
    "- reasoning_model_provider_signal_lines: $($evidence.runtime_reasoning_signals.Count)",
    "- recent_runs: $($evidence.recent_runs.Count)",
    "- recent_worktrees: $($evidence.recent_worktrees.Count)",
    "- recent_run_files_copied: $(@($evidence.run_evidence_copies | Where-Object copied).Count)",
    '',
    'PRELIMINARY CONCLUSIONS'
)
foreach ($conclusion in $evidence.conclusions) {
    $summaryLines += "- $conclusion"
}
if ($evidence.errors.Count -gt 0) {
    $summaryLines += @('', 'ERRORS')
    foreach ($errorItem in $evidence.errors) {
        $summaryLines += "- $errorItem"
    }
}
$summaryLines | Set-Content -LiteralPath $summaryPath -Encoding UTF8

Stop-Transcript | Out-Null

if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}
Compress-Archive -LiteralPath $reportRoot -DestinationPath $zipPath -CompressionLevel Optimal

Write-Section 'COLLECTION COMPLETE'
Write-Host "Summary: $summaryPath"
Write-Host "JSON:    $jsonPath"
Write-Host "ZIP:     $zipPath"
Write-Host ''
Write-Host 'Please upload the ZIP file back into the chat.'
Write-Host 'Do not paste the entire transcript unless the ZIP upload fails.'
