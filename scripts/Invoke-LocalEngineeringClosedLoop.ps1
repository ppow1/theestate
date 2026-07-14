CLS
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Push-Location $repo
try {
  $env:PYTHONPATH = (Join-Path $repo 'src')
  python -m estate.cli.local_engineering_department run-closed-loop
  "Local engineering closed-loop run finished. Review runtime/local_engineering_department/latest.json" | Set-Clipboard
} finally {
  Pop-Location
}
