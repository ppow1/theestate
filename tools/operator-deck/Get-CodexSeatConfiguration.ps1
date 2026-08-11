[CmdletBinding()]
param(
    [ValidateSet('C1', 'C2', 'C3')]
    [string]$Seat
)

# Read-only adapter over the Estate source of truth; no CODEX_HOME values live here.
$estateRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$estateBat = Join-Path $estateRoot 'estate.bat'
$cliArgs = @('codex-seat-config')
if ($Seat) { $cliArgs += @('--seat', $Seat) }
$json = & $estateBat @cliArgs
if ($LASTEXITCODE -ne 0) { throw "Estate seat configuration lookup failed." }
$json -join [Environment]::NewLine
