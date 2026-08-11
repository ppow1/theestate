[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [ValidateSet('C1', 'C2', 'C3')]
    [string]$Seat
)

$ErrorActionPreference = 'Stop'
$estateRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$configScript = Join-Path $PSScriptRoot 'Get-CodexSeatConfiguration.ps1'
$configuration = (& $configScript -Seat $Seat | Out-String | ConvertFrom-Json)
$seatRecord = @($configuration.seats) | Where-Object { $_.seat_id -eq $Seat } | Select-Object -First 1
if (-not $seatRecord -or -not $seatRecord.codex_home) { throw "No approved CODEX_HOME is configured for $Seat." }

# Interactive Luna seat: normal persistent Codex session, full permissions.
# Deliberately no --ephemeral and no --output-last-message handoff.
$previousCodexHome = $env:CODEX_HOME
$env:CODEX_HOME = [string]$seatRecord.codex_home
try {
    & codex --cd $estateRoot --sandbox danger-full-access
    $exitCode = $LASTEXITCODE
}
finally {
    if ($null -eq $previousCodexHome) { Remove-Item Env:CODEX_HOME -ErrorAction SilentlyContinue }
    else { $env:CODEX_HOME = $previousCodexHome }
}
exit $exitCode
