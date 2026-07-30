CLS
$ErrorActionPreference='Stop'; $ToolRoot=Split-Path -Parent $PSScriptRoot; Push-Location $ToolRoot
try { node dist/cli.js validate --config config.example.json } catch { Write-Error $_; exit 2 } finally { Pop-Location }
