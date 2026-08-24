# Estate Office service start wrapper
# Purpose: ensure only the Office of the Steward service is healthy.
# Date: 2026-08-24

try { Clear-Host -ErrorAction SilentlyContinue } catch { }
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot "Estate-Service-Lib.ps1")

$service = Get-EstateService -ServiceId "office"
$result = Start-EstateServiceProcess -Service $service
$result | ConvertTo-Json -Depth 12
