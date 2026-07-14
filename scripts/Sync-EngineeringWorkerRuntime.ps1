CLS
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$source = Join-Path $repo 'external/engineering_worker_runtime'
$target = 'A:\AI\Tools\EngineeringWorkerRuntime'
if ((Test-Path $target) -and (Test-Path (Join-Path $target 'Invoke-EngineeringWorker.ps1')) -and -not (Test-Path (Join-Path $target 'runtime_manifest.json'))) {
  $legacy = Join-Path $target ('legacy_campaign_0550_' + (Get-Date -Format 'yyyyMMddHHmmss'))
  New-Item -ItemType Directory -Force -Path $legacy | Out-Null
  Copy-Item -Path (Join-Path $target '*') -Destination $legacy -Recurse -Force
  Write-Host "Migrated existing Campaign 0550 runtime to $legacy before synchronization."
}
New-Item -ItemType Directory -Force -Path $target | Out-Null
Copy-Item -Path (Join-Path $source '*') -Destination $target -Recurse -Force
$summary = "Engineering Worker Runtime synchronized to $target from $source"
Write-Host $summary
try { $summary | Set-Clipboard } catch { Write-Warning 'Clipboard unavailable; summary printed above.' }
