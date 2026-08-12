param(
    [Parameter(Mandatory)]
    [ValidateSet("resident_gateway","office","open_webui","sillytavern","textgen","comfyui","ollama")]
    [string]$ServiceId
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "Estate-Service-Lib.ps1")
Get-EstateServiceRuntimeStatus -Service (Get-EstateService -ServiceId $ServiceId) |
    ConvertTo-Json -Depth 10
