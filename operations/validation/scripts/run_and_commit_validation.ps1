param(
    [Parameter(Mandatory=$true)][string]$WorkPackageId,
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")
Push-Location $RepoRoot
try {
    $SafeId = ($WorkPackageId.ToUpper() -replace '[^A-Z0-9_-]', '_')
    $before = git status --porcelain=v1
    if ($before) {
        throw "Refusing to validate with unrelated local changes present. Commit, stash, or revert them first."
    }

    $upstream = git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null
    if ($LASTEXITCODE -eq 0 -and $upstream) {
        git pull --ff-only
    }

    $env:PYTHONPATH = "src" + [IO.Path]::PathSeparator + $env:PYTHONPATH
    python -m estate.cli.main validate-work-package --id $SafeId --json
    if ($LASTEXITCODE -ne 0) { throw "Validation command failed." }

    $allowed = @(
        "operations/validation/reports/${SafeId}_validation.md",
        "runtime/validation/work_packages/${SafeId}_validation.json",
        "runtime/validation/work_packages/latest.json"
    )
    $capturePrefix = "runtime/validation/work_packages/captures/${SafeId}_"
    $changed = git status --porcelain=v1 | ForEach-Object { $_.Substring(3) -replace '\\','/' }
    $disallowed = @($changed | Where-Object { ($allowed -notcontains $_) -and (-not $_.StartsWith($capturePrefix)) })
    if ($disallowed.Count -gt 0) {
        throw "Refusing to stage non-validation artifacts: $($disallowed -join ', ')"
    }

    foreach ($path in $allowed) { if (Test-Path $path) { git add -- $path } }
    if (Test-Path "runtime/validation/work_packages/captures") {
        git status --porcelain=v1 -- "runtime/validation/work_packages/captures" | ForEach-Object {
            $p = $_.Substring(3) -replace '\\','/'
            if ($p.StartsWith($capturePrefix)) { git add -- $p }
        }
    }

    $staged = git diff --cached --name-only
    if (-not $staged) {
        Write-Host "No validation artifacts to commit."
        exit 0
    }
    git commit -m "Validate $SafeId"
    if (-not $NoPush) { git push }
} finally {
    Pop-Location
}
