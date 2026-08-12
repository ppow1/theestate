[CmdletBinding(DefaultParameterSetName='Preflight', SupportsShouldProcess)]
param(
    [Parameter(Mandatory=$true)][string]$SourceRoot,
    [Parameter(Mandatory=$true)][string]$TargetRoot,
    [Parameter(Mandatory=$false)][string]$ExpectedSourceSha,
    [Parameter(Mandatory=$false)][string]$ReceiptPath,
    [Parameter(ParameterSetName='Preflight', Mandatory=$true)][switch]$PreflightOnly,
    [Parameter(ParameterSetName='Deploy', Mandatory=$true)][switch]$Deploy
)

$ErrorActionPreference = 'Stop'
# Selective overlay only; never synchronize the repository wholesale.
$relativeFiles = @(
    'src\estate\core\autonomous_chatgpt_mailbox_worker.py', 'src\estate\core\autonomous_reason_execute_loop.py',
    'src\estate\core\chatgpt_execution_runtime.py', 'src\estate\core\chatgpt_reasoning_resident.py',
    'src\estate\core\chatgpt_worker_runtime.py', 'src\estate\core\compute_resources.py',
    'src\estate\core\conference_room_lifecycle.py', 'src\estate\core\consultation_escalation.py',
    'src\estate\core\consultation_execution.py', 'src\estate\core\consultation_projection.py',
    'src\estate\core\consultation_store.py', 'src\estate\core\evidence_acquisition.py',
    'src\estate\core\grace_consultation_loop.py', 'src\estate\core\grace_live_mcp_cli.py',
    'src\estate\core\grace_operational_memory.py', 'src\estate\core\grace_parallel_portfolio.py',
    'src\estate\core\authority_schema_runtime.py', 'src\estate\core\character_bible.py',
    'src\estate\core\comfyui_provider_health.py', 'src\estate\core\engineering_capability_enablement.py',
    'src\estate\core\execution_activity.py', 'src\estate\core\execution_dispatch.py',
    'src\estate\core\execution_provider_adapter.py', 'src\estate\core\execution_provider_adapter_runtime.py',
    'src\estate\core\execution_result_reconciliation_runtime.py', 'src\estate\core\governed_local_provider.py',
    'src\estate\core\gpu_runtime_lanes.py', 'src\estate\core\gpu_runtime_lifecycle.py', 'src\estate\core\grace_comfyui_execution.py',
    'src\estate\core\grace_helen_engineering_composition.py', 'src\estate\core\grace_momentum_service.py',
    'src\estate\core\grace_operations_runtime.py', 'src\estate\core\grace_runtime_bridge.py',
    'src\estate\core\office_personnel_directory.py', 'src\estate\core\openwebui_engineering_workflow.py',
    'src\estate\core\openwebui_grace_assignment.py', 'src\estate\core\operational_events.py',
    'src\estate\core\operations_control_runtime.py', 'src\estate\core\operations_manager.py',
    'src\estate\core\ptm_policy.py', 'src\estate\core\ptm_production_readiness.py',
    'src\estate\core\ptm_readiness_integration.py', 'src\estate\core\ptm_waiver_authority.py',
    'config\runtime\gpu_runtime_lanes.json', 'config\providers\qwen_local_text.json',
    'config\providers\qwen_local_text_p100.json', 'schemas\execution_provider_adapter_request_v1.schema.json',
    'src\estate\core\resident_authority.py', 'src\estate\core\resident_identity_composition.py',
    'src\estate\core\resident_interaction.py', 'src\estate\core\resident_voice_commissioning.py',
    'src\estate\core\steward_help.py',
    'src\estate\ai_services\control.py', 'src\estate\ai_services\discovery.py',
    'src\estate\ai_services\execution.py', 'src\estate\ai_services\manifest.py',
    'src\estate\ai_services\paths.py', 'src\estate\ai_services\policy.py',
    'src\estate\core\assignment_queue.py', 'src\estate\core\background_operations.py',
    'src\estate\core\canonical_webui_gateway_runtime.py', 'src\estate\core\capability_dependency_visualization.py',
    'src\estate\core\character_continuity.py', 'src\estate\core\codex_bridge.py',
    'src\estate\core\codex_bridge_execution_provider_adapter.py', 'src\estate\core\collaboration_events.py',
    'src\estate\core\collaboration_messages.py', 'src\estate\core\dependency_graph.py',
    'src\estate\core\estate_capability_registry.py', 'src\estate\core\estate_skills.py',
    'src\estate\core\execution_adapter_handoff_runtime.py', 'src\estate\core\execution_attempt_runtime.py',
    'src\estate\core\grounded_fact_provider.py', 'src\estate\core\helen_workforce.py',
    'src\estate\core\mailbox_index.py', 'src\estate\core\multi_resident_room.py',
    'src\estate\core\open_webui_multi_resident_gateway.py', 'src\estate\core\openwebui_resident_package.py',
    'src\estate\core\operational_status.py', 'src\estate\core\orchestrator_intake.py',
    'src\estate\core\paths.py', 'src\estate\core\provider_capabilities.py',
    'src\estate\core\provider_capacity.py', 'src\estate\core\provider_catalog.py',
    'src\estate\core\provider_health.py', 'src\estate\core\ptm_ids.py',
    'src\estate\core\qwen_local_text_execution_provider_adapter.py', 'src\estate\core\reflection_worker_request.py',
    'src\estate\core\reflection_workflow.py', 'src\estate\core\relationship_graph.py',
    'src\estate\core\resident_lifecycle.py', 'src\estate\core\resident_mail_bus.py',
    'src\estate\core\resident_memory_runtime.py', 'src\estate\core\resident_registry_snapshot.py',
    'src\estate\core\runtime_envelope.py', 'src\estate\core\traffic_controller.py',
    'src\estate\core\worker_assignments.py', 'src\estate\model_control\assignments.py',
    'src\estate\model_control\policy.py', 'src\estate\model_control\registry.py',
    'src\estate\core\openwebui_resident_surface.py', 'src\estate\core\resident_gateway.py',
    'tools\chatgpt_mailbox_worker_browser.cjs', 'tools\comms8_streamable_http_adapter.py',
    'tools\start_chatgpt_mailbox_worker_canonical.ps1', 'tools\start_grace_consultation_gateway.py',
    'tools\start_openwebui_canonical.ps1'
)

function Hash-File([string]$Path) { if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }; return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function Invoke-Git([string]$Root, [string[]]$GitArgs) { $out = & git -C $Root @GitArgs 2>&1; if ($LASTEXITCODE -ne 0) { throw "git failed: $($out -join ' ')" }; return ($out -join "`n").Trim() }
function Safe-Id([string]$Value) { return (($Value -replace '[^A-Za-z0-9_.-]', '_').Trim('_')) }
function Get-NormalizedGitBlobId([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $bytes = [IO.File]::ReadAllBytes($Path)
    $normalized = New-Object byte[] $bytes.Length
    $count = 0
    for ($i = 0; $i -lt $bytes.Length; $i++) {
        if ($bytes[$i] -eq 13 -and ($i + 1) -lt $bytes.Length -and $bytes[$i + 1] -eq 10) { continue }
        $normalized[$count] = $bytes[$i]; $count++
    }
    $tmp = [IO.Path]::GetTempFileName()
    try { $final = New-Object byte[] $count; [Array]::Copy($normalized, $final, $count); [IO.File]::WriteAllBytes($tmp, $final); return (Invoke-Git $target @('hash-object', $tmp)) }
    finally { Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue }
}
function Find-TrackedBlobProvenance([string]$Root, [string]$RelativePath, [string]$Path) {
    $blob = Get-NormalizedGitBlobId $Path
    if (-not $blob) { return $null }
    $gitPath = $RelativePath.Replace('\','/')
    $commitOutput = Invoke-Git $Root @('log','--all','--format=%H','--',$gitPath)
    $commits = @($commitOutput -split "`r?`n") | Where-Object { $_ }
    foreach ($commit in $commits) {
        $candidate = & git -C $Root rev-parse ("$commit`:$gitPath") 2>$null
        if ($LASTEXITCODE -eq 0 -and (($candidate -join '').Trim() -eq $blob)) {
            return [ordered]@{ blob_id=$blob; commit=$commit; relative_path=$RelativePath; line_ending_normalization='CRLF_TO_LF_FOR_GIT_BLOB_ONLY' }
        }
    }
    return $null
}

$source = [IO.Path]::GetFullPath($SourceRoot)
$target = [IO.Path]::GetFullPath($TargetRoot)
if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw "SourceRoot missing: $source" }
if (-not (Test-Path -LiteralPath $target -PathType Container)) { throw "TargetRoot missing: $target" }
$top = Invoke-Git $source @('rev-parse','--show-toplevel')
if ([IO.Path]::GetFullPath($top) -ne $source) { throw "SourceRoot is not the git worktree root: $source" }
$branch = Invoke-Git $source @('branch','--show-current')
if ($branch -ne 'integration/grace-comms8-parallelism') { throw "Wrong source branch: $branch" }
$sourceSha = Invoke-Git $source @('rev-parse','HEAD')
if ($ExpectedSourceSha -and $sourceSha -ne $ExpectedSourceSha) { throw "Source SHA mismatch: expected $ExpectedSourceSha, got $sourceSha" }
$targetHead = Invoke-Git $target @('rev-parse','HEAD')
$oldReceipt = Join-Path $target 'runtime\deployments\grace_comms8_runtime_overlay.json'
if (-not $ReceiptPath) { $ReceiptPath = $oldReceipt }
$receiptFull = [IO.Path]::GetFullPath($ReceiptPath)
$started = [DateTime]::UtcNow
$deploymentId = 'grace-overlay-' + $started.ToString('yyyyMMddTHHmmssfffZ') + '-' + $sourceSha.Substring(0,12)
$previous = @{}
if (Test-Path -LiteralPath $oldReceipt) { try { $old = Get-Content -LiteralPath $oldReceipt -Raw | ConvertFrom-Json; $priorFiles = if ($old.files) { @($old.files) } else { @($old.manifest) }; foreach($f in $priorFiles){$path = if ($f.path) { $f.path } else { $f.relative_path }; $hash = if ($f.sha256) { $f.sha256 } else { $f.post_target_sha256 }; if ($path -and $hash) { $previous[$path.Replace('/','\')] = [string]$hash } } } catch { } }
$manifestFile = [IO.Path]::GetTempFileName(); $relativeFiles | Set-Content -LiteralPath $manifestFile -Encoding UTF8
$closureScript = Join-Path $source 'tools\runtime_import_closure.py'
$closureOutput = & python $closureScript --source-root (Join-Path $source 'src') --target-root (Join-Path $target 'src') --manifest $manifestFile 2>&1
Remove-Item -LiteralPath $manifestFile -Force -ErrorAction SilentlyContinue
try { $closure = ($closureOutput -join "`n") | ConvertFrom-Json } catch { throw "IMPORT_CLOSURE_BLOCKED: closure output was not valid JSON: $($_.Exception.Message)" }
$manifest = @(); $unknown = @(); $unchanged = @(); $changed = @()
foreach ($relative in $relativeFiles) {
    $sourcePath = Join-Path $source $relative; $targetPath = Join-Path $target $relative
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw "Manifest source is missing: $sourcePath" }
    $sourceHash = Hash-File $sourcePath; $preHash = Hash-File $targetPath
    $provenance = $null
    $class = if ($preHash -and $preHash -eq $sourceHash) { 'INTEGRATION_EQUIVALENT' } elseif ($preHash -and $previous.ContainsKey($relative) -and $preHash -eq $previous[$relative].ToUpperInvariant()) { 'EXPECTED_PREVIOUS_OVERLAY' } elseif (-not $preHash) { 'MISSING_TARGET' } else { $provenance = Find-TrackedBlobProvenance $target $relative $targetPath; if ($provenance) { 'PROVEN_TRACKED_PREDECESSOR' } else { 'UNKNOWN_DRIFT' } }
    if ($class -eq 'UNKNOWN_DRIFT') { $unknown += $relative }
    if ($class -eq 'INTEGRATION_EQUIVALENT') { $unchanged += $relative } else { $changed += $relative }
    $manifest += [ordered]@{relative_path=$relative;source_sha256=$sourceHash;pre_target_sha256=$preHash;post_target_sha256=$null;classification=$class;deployment_action=if($class -eq 'INTEGRATION_EQUIVALENT'){'UNCHANGED'}else{'REPLACE'};provenance=$provenance }
}
$result = if ($unknown.Count -or $closure.status -ne 'IMPORT_CLOSURE_PASS') { 'PREFLIGHT_BLOCKED' } else { 'PREFLIGHT_PASS' }
$receipt = [ordered]@{schema='estate.grace_comms8_runtime_overlay.v2';deployment_id=$deploymentId;timestamp_started=$started.ToString('o');timestamp_completed=$null;actor=$env:USERNAME;source_root=$source;source_branch=$branch;source_sha=$sourceSha;target_root=$target;target_git_head=$targetHead;preflight_result=$result;import_closure=$closure;runtime_drift_classification=$manifest;manifest=$manifest;backup_path=$null;files_changed=$changed;files_unchanged=$unchanged;pre_hashes=@{};source_hashes=@{};post_hashes=@{};rollback_available=$false;rollback_performed=$false;services_requiring_restart=@('resident-gateway','grace-consultation-gateway','chatgpt-mailbox-worker');result=$result;warnings=@();errors=@()}
foreach($m in $manifest){$receipt.pre_hashes[$m.relative_path]=$m.pre_target_sha256;$receipt.source_hashes[$m.relative_path]=$m.source_sha256}
if ($PreflightOnly) { $receipt.timestamp_completed=[DateTime]::UtcNow.ToString('o'); $receipt | ConvertTo-Json -Depth 12; exit 0 }
if ($unknown.Count) { throw "PREFLIGHT_BLOCKED: unknown runtime drift: $($unknown -join ', ')" }
$backup = Join-Path $target ('runtime\deployments\backups\' + $deploymentId); if (Test-Path -LiteralPath $backup) { throw "Backup already exists: $backup" }
New-Item -ItemType Directory -Path $backup -Force | Out-Null
try {
    foreach($m in $manifest){ if($m.pre_target_sha256){$dst=Join-Path $target $m.relative_path;if((Hash-File $dst) -ne $m.pre_target_sha256){throw "Target changed after preflight: $($m.relative_path)"}; $bd=Join-Path $backup $m.relative_path;New-Item -ItemType Directory -Path (Split-Path $bd) -Force | Out-Null;Copy-Item -LiteralPath $dst -Destination $bd; if((Hash-File $bd) -ne $m.pre_target_sha256){throw "Backup verification failed: $($m.relative_path)"} } }
    $meta=[ordered]@{deployment_id=$deploymentId;source_root=$source;source_branch=$branch;source_sha=$sourceSha;target_git_head=$targetHead;manifest=$manifest;rollback_instructions='Copy backup files back to target paths after stopping governed services.'}; $meta | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $backup 'metadata.json') -Encoding UTF8
    $receipt.backup_path=$backup;$receipt.rollback_available=$true
    foreach($m in $manifest){ if($m.classification -ne 'INTEGRATION_EQUIVALENT'){$sp=Join-Path $source $m.relative_path;$dp=Join-Path $target $m.relative_path;New-Item -ItemType Directory -Path (Split-Path $dp) -Force | Out-Null;$tmp=$dp+'.estate-tmp-'+$deploymentId;Copy-Item -LiteralPath $sp -Destination $tmp -Force;if((Hash-File $tmp) -ne $m.source_sha256){throw "Temporary source hash failed: $($m.relative_path)"};Move-Item -LiteralPath $tmp -Destination $dp -Force;if((Hash-File $dp) -ne $m.source_sha256){throw "Post-write hash failed: $($m.relative_path)"}};$m.post_target_sha256=Hash-File (Join-Path $target $m.relative_path);$receipt.post_hashes[$m.relative_path]=$m.post_target_sha256 }
    $receipt.result='DEPLOYMENT_SUCCESS'
} catch {
    $receipt.errors += $_.Exception.Message
    $ok=$true; foreach($m in $manifest){$bd=Join-Path $backup $m.relative_path;$dp=Join-Path $target $m.relative_path;if(Test-Path -LiteralPath $bd){try{Copy-Item -LiteralPath $bd -Destination $dp -Force;if((Hash-File $dp) -ne $m.pre_target_sha256){$ok=$false}}catch{$ok=$false}}};$receipt.rollback_performed=$true;$receipt.result=if($ok){'DEPLOYMENT_ROLLED_BACK'}else{'ROLLBACK_INCOMPLETE'};if(-not $ok){$receipt.errors += 'Rollback verification failed'}
}
$receipt.timestamp_completed=[DateTime]::UtcNow.ToString('o');$receiptDir=Split-Path $receiptFull -Parent;New-Item -ItemType Directory -Path $receiptDir -Force | Out-Null;$receipt | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $receiptFull -Encoding UTF8;$receipt | ConvertTo-Json -Depth 12
if($receipt.result -ne 'DEPLOYMENT_SUCCESS'){exit 2}
