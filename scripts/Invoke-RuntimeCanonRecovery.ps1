[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RecoveryArguments
)

$ErrorActionPreference = 'Stop'
$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$PreviousPythonPath = $env:PYTHONPATH

try {
    $SourceRoot = Join-Path $RepositoryRoot 'src'
    $env:PYTHONPATH = if ($PreviousPythonPath) {
        "$SourceRoot$([IO.Path]::PathSeparator)$PreviousPythonPath"
    } else {
        $SourceRoot
    }

    & python -m estate.core.runtime_canon_recovery `
        --repository-root $RepositoryRoot @RecoveryArguments
    exit $LASTEXITCODE
}
finally {
    $env:PYTHONPATH = $PreviousPythonPath
}
