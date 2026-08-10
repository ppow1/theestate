[CmdletBinding()]
param(
    [Parameter(Mandatory)] [ValidateSet('GPU1','GPU2')] [string]$Gpu,
    [string]$OfficeUrl = 'http://127.0.0.1:8765/'
)

$ErrorActionPreference = 'Stop'
# Informational only: this action only focuses the existing Office dashboard.
Start-Process ($OfficeUrl.TrimEnd('/') + '/#operational-dashboard?gpu=' + $Gpu.ToLowerInvariant())
