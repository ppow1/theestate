[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$RepositoryRoot = 'A:\theestate',
    [string]$RuntimeRoot = 'A:\EstateRuntime\host\estate-main\current'
)

$ErrorActionPreference = 'Stop'

# This is a selective runtime overlay. It intentionally does not synchronize
# the repository wholesale and therefore cannot import unrelated feature work.
$relativeFiles = @(
    'src\estate\core\autonomous_chatgpt_mailbox_worker.py',
    'src\estate\core\autonomous_reason_execute_loop.py',
    'src\estate\core\chatgpt_execution_runtime.py',
    'src\estate\core\chatgpt_reasoning_resident.py',
    'src\estate\core\chatgpt_worker_runtime.py',
    'src\estate\core\compute_resources.py',
    'src\estate\core\conference_room_lifecycle.py',
    'src\estate\core\consultation_escalation.py',
    'src\estate\core\consultation_execution.py',
    'src\estate\core\consultation_projection.py',
    'src\estate\core\consultation_store.py',
    'src\estate\core\evidence_acquisition.py',
    'src\estate\core\grace_consultation_loop.py',
    'src\estate\core\grace_live_mcp_cli.py',
    'src\estate\core\grace_operational_memory.py',
    'src\estate\core\grace_parallel_portfolio.py',
    'src\estate\core\openwebui_resident_surface.py',
    'src\estate\core\resident_gateway.py',
    'tools\chatgpt_mailbox_worker_browser.cjs',
    'tools\comms8_streamable_http_adapter.py',
    'tools\start_chatgpt_mailbox_worker_canonical.ps1',
    'tools\start_grace_consultation_gateway.py',
    'tools\start_openwebui_canonical.ps1'
)

$repo = [IO.Path]::GetFullPath($RepositoryRoot)
$runtime = [IO.Path]::GetFullPath($RuntimeRoot)
if (-not (Test-Path -LiteralPath (Join-Path $repo '.git') -PathType Container)) {
    throw "Repository root is not a checkout: $repo"
}
if (-not (Test-Path -LiteralPath $runtime -PathType Container)) {
    throw "Runtime root is missing: $runtime"
}

$receipt = [ordered]@{
    schema = 'estate.grace_comms8_runtime_overlay.v1'
    generated_at = [DateTime]::UtcNow.ToString('o')
    repository_root = $repo
    runtime_root = $runtime
    source_revision = (& git -C $repo rev-parse HEAD).Trim()
    files = @()
}

foreach ($relative in $relativeFiles) {
    $source = Join-Path $repo $relative
    $target = Join-Path $runtime $relative
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Manifest source is missing: $source" }
    $targetDir = Split-Path -Parent $target
    if (-not (Test-Path -LiteralPath $targetDir -PathType Container)) {
        New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    }
    if ($PSCmdlet.ShouldProcess($target, 'Deploy selective Grace/Comms8 runtime file')) {
        Copy-Item -LiteralPath $source -Destination $target -Force
    }
    $hash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    $receipt.files += [ordered]@{ path = $relative; sha256 = $hash }
}

$receiptPath = Join-Path $runtime 'runtime\deployments\grace_comms8_runtime_overlay.json'
$receiptDir = Split-Path -Parent $receiptPath
if (-not (Test-Path -LiteralPath $receiptDir -PathType Container)) {
    New-Item -ItemType Directory -Path $receiptDir -Force | Out-Null
}
if ($PSCmdlet.ShouldProcess($receiptPath, 'Write deployment receipt')) {
    $receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
}
Write-Output ($receipt | ConvertTo-Json -Depth 8)
