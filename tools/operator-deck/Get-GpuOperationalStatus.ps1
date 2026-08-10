[CmdletBinding()]
param(
    [Parameter(Mandatory)] [ValidateSet('GPU1','GPU2')] [string]$Gpu,
    [string]$EstateRoot = 'A:\theestate'
)

$ErrorActionPreference = 'Stop'
$projectionPath = Join-Path $EstateRoot 'runtime\compute_resources\gpus.json'
try {
    $projection = Get-Content -LiteralPath $projectionPath -Raw | ConvertFrom-Json
    $row = @($projection.resources) | Where-Object { $_.logical_gpu_id -eq $Gpu } | Select-Object -First 1
    if ($null -eq $row) { throw "GPU projection does not contain $Gpu." }
    $health = [string]($row.health_state ?? 'UNKNOWN')
    $freshness = [string]($row.freshness ?? 'unknown')
    $severity = if ($freshness -in @('stale','unknown') -or $health -in @('UNKNOWN','LOST')) { 'warning' } elseif ($health -ne 'HEALTHY') { 'warning' } else { 'nominal' }
    [ordered]@{
        schema_version = 'operator_deck_gpu_status_v1'
        gpu = $Gpu
        compute_percent = $row.utilization_percent
        vram_used_mib = $row.memory_used_mib
        vram_total_mib = $row.memory_total_mib
        vram_percent = $row.vram_utilization_percent
        health = $health
        freshness = $freshness
        severity = $severity
        observed_at = $row.observed_at
        source = 'runtime/compute_resources/gpus.json'
        read_only = $true
        drilldown = "http://127.0.0.1:8765/#operational-dashboard&gpu=$($Gpu.ToLowerInvariant())"
    } | ConvertTo-Json -Depth 5
} catch {
    [ordered]@{ schema_version = 'operator_deck_gpu_status_v1'; gpu = $Gpu; severity = 'warning'; health = 'UNKNOWN'; freshness = 'unknown'; error = $_.Exception.Message; read_only = $true } | ConvertTo-Json -Depth 5
    exit 1
}
