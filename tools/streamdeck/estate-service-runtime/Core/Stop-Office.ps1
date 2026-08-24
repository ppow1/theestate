# Estate Office service stop wrapper
# Purpose: stop only owned Office of the Steward processes.
# Date: 2026-08-24

try { Clear-Host -ErrorAction SilentlyContinue } catch { }
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Estate-Service-Lib.ps1")

$service = Get-EstateService -ServiceId "office"
$result = Stop-EstateServiceProcess -Service $service -AllOwnedInstances
$result | ConvertTo-Json -Depth 12
