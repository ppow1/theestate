[CmdletBinding()]
param(
    [string]$BuildRoot = "A:\AI\Tools\EstateStreamDeckPlugin"
)

$ErrorActionPreference = "Stop"

$SourceRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$BuildRootFull = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($BuildRoot)
$LogsRoot = Join-Path $BuildRootFull "logs"
$TestLog = Join-Path $LogsRoot "test.log"
$TestReport = Join-Path $BuildRootFull "TEST_REPORT.md"

if (-not (Test-Path -LiteralPath $BuildRootFull)) {
    New-Item -ItemType Directory -Path $BuildRootFull -Force | Out-Null
}
if (-not (Test-Path -LiteralPath $LogsRoot)) {
    New-Item -ItemType Directory -Path $LogsRoot -Force | Out-Null
}

Push-Location $SourceRoot
try {
    $Output = & npm test 2>&1
    $ExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

$Output | Set-Content -LiteralPath $TestLog -Encoding UTF8
$NodeVersion = (& node --version) 2>$null
$NpmVersion = (& npm --version) 2>$null
$Status = if ($ExitCode -eq 0) { "passed" } else { "failed" }

@(
    "# Estate Status Bridge Test Report"
    ""
    "Generated: $(Get-Date -Format o)"
    "Source path: $SourceRoot"
    "Build root: $BuildRootFull"
    "Command: npm test"
    "Status: $Status"
    "Exit code: $ExitCode"
    "Node version: $NodeVersion"
    "npm version: $NpmVersion"
    "Log: $TestLog"
    ""
    "## Output"
    ""
    '```text'
    ($Output -join [Environment]::NewLine)
    '```'
) | Set-Content -LiteralPath $TestReport -Encoding UTF8

if ($ExitCode -ne 0) {
    throw "Tests failed with exit code $ExitCode"
}

Write-Output ([pscustomobject]@{
    Status = $Status
    TestReport = $TestReport
    TestLog = $TestLog
})


