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
$pythonCandidates = @(
    (Join-Path $estateRoot '.venv\Scripts\python.exe'),
    (Join-Path $env:ProgramFiles 'Python314\python.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314\python.exe'),
    (Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source)
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique
$python = $pythonCandidates | Select-Object -First 1
if (-not $python) { throw 'Estate seat configuration lookup requires Python, but no absolute Python executable was found.' }
$previousPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = Join-Path $estateRoot 'src'
try {
    $json = & $python -m estate.cli.main @cliArgs
    if ($LASTEXITCODE -ne 0) { throw "Estate seat configuration lookup failed (python=$python, exit=$LASTEXITCODE)." }
} finally {
    if ($null -eq $previousPythonPath) { Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue }
    else { $env:PYTHONPATH = $previousPythonPath }
}
$json -join [Environment]::NewLine
