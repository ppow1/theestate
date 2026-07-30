CLS
$ErrorActionPreference='Stop'; $ToolRoot=Split-Path -Parent $PSScriptRoot; Push-Location $ToolRoot
try { node dist/cli.js sync --config config.example.json --quiet } catch { Write-Error $_; exit 2 } finally { Pop-Location }
