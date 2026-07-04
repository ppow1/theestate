<#
.SYNOPSIS
  Steward-facing local launcher for the Estate Operations Center.

.DESCRIPTION
  Verifies the Estate workspace root, checks local dependencies, loads local
  Operations Center settings, starts the existing local server bootstrap, prints
  the local URL, reports degraded optional components, and shows safe shutdown
  guidance. This launcher is local-first only: it does not store secrets, run
  work packages, or change command authority.
#>
[CmdletBinding()]
param(
  [string]$HostName = "127.0.0.1",
  [int]$Port = 8765,
  [switch]$StatusOnly,
  [switch]$Stop
)

$ErrorActionPreference = "Stop"

function Write-OperatorLine {
  param([string]$Message)
  Write-Host "[Estate Operations Center] $Message"
}

function Fail-Operator {
  param([string]$Message)
  Write-Error "Estate Operations Center launch failed: $Message"
  exit 1
}

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptRoot

$requiredPaths = @(
  "README.md",
  "src/estate/cli/main.py",
  "src/estate/core/operations_center_bootstrap.py",
  "src/estate/core/operations_center_settings.py"
)
$missingRootPaths = @($requiredPaths | Where-Object { -not (Test-Path (Join-Path $ScriptRoot $_)) })
if ($missingRootPaths.Count -gt 0) {
  Fail-Operator "Run this script from the Estate repository root. Missing: $($missingRootPaths -join ', ')"
}
Write-OperatorLine "Verified Estate root: $ScriptRoot"

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
  $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $pythonCommand) {
  Fail-Operator "Python was not found on PATH. Install Python or activate the Estate local environment, then retry."
}
$pythonExe = $pythonCommand.Source
Write-OperatorLine "Using Python: $pythonExe"

$env:PYTHONPATH = if ($env:PYTHONPATH) { "$ScriptRoot/src$([IO.Path]::PathSeparator)$env:PYTHONPATH" } else { "$ScriptRoot/src" }
$env:ESTATE_ROOT = $ScriptRoot

function Invoke-EstateJson {
  param([string[]]$Arguments)
  $output = & $pythonExe @Arguments 2>&1
  $exitCode = $LASTEXITCODE
  if ($exitCode -ne 0) {
    Fail-Operator "Command failed ($($Arguments -join ' ')) with exit code $exitCode. Output: $output"
  }
  try {
    return ($output | Out-String | ConvertFrom-Json)
  } catch {
    Fail-Operator "Command did not return valid JSON ($($Arguments -join ' ')). Output: $output"
  }
}

Write-OperatorLine "Loading local configuration/settings..."
$settings = Invoke-EstateJson @("-m", "estate.cli.main", "operations-center-settings", "--json")
Write-OperatorLine "Settings source: $($settings.effective_source); settings path: $($settings.path)"
if ($settings.warnings.Count -gt 0) {
  Write-OperatorLine "Settings warnings / degraded configuration:"
  foreach ($warning in $settings.warnings) {
    Write-Host "  - [$($warning.type)] $($warning.message) ($($warning.path))"
  }
}

if ($Stop) {
  Write-OperatorLine "Stopping local Operations Center server..."
  $stopPayload = Invoke-EstateJson @("-m", "estate.cli.main", "operations-center", "stop", "--json")
  Write-OperatorLine $stopPayload.message
  exit 0
}

if ($StatusOnly) {
  $statusPayload = Invoke-EstateJson @("-m", "estate.cli.main", "operations-center", "status", "--json")
  Write-OperatorLine "Running: $($statusPayload.running)"
  Write-OperatorLine "URL: $($statusPayload.url)"
  Write-OperatorLine "Log: $($statusPayload.log_file)"
  exit 0
}

Write-OperatorLine "Starting the existing local Operations Center server bootstrap..."
$startPayload = Invoke-EstateJson @("-m", "estate.cli.main", "operations-center", "start", "--host", $HostName, "--port", "$Port", "--json")

if (-not $startPayload.started -and -not $startPayload.running) {
  Fail-Operator "$($startPayload.message) Inspect $($startPayload.log_file) for details."
}

Write-OperatorLine $startPayload.message
Write-OperatorLine "Local URL: $($startPayload.url)"
Write-OperatorLine "Static entry point: $($startPayload.entry_point)"
Write-OperatorLine "Log: $($startPayload.log_file)"

if ($startPayload.preflight) {
  Write-OperatorLine "Preflight / optional component status:"
  foreach ($item in $startPayload.preflight) {
    $status = $item.status
    if ($status -ne "available" -and $status -ne "healthy") {
      Write-Host "  - DEGRADED: $($item.name) status=$status path=$($item.path)"
    } else {
      Write-Host "  - OK: $($item.name) status=$status path=$($item.path)"
    }
  }
}

Write-OperatorLine "Safe shutdown: run .\launch_operations_center.ps1 -Stop or python -m estate.cli.main operations-center stop"
Write-OperatorLine "Authority boundary: local launcher only; no cloud dependency, no secret storage, no automatic work package execution, and no Steward authorization bypass."
