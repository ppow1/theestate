CLS
$ErrorActionPreference='Stop'
$ToolRoot=Split-Path -Parent $PSScriptRoot
Push-Location $ToolRoot
try { if(-not (Test-Path node_modules)){ npm install }; npm run build; node dist/cli.js init-profile --config config.example.json } catch { Write-Error $_; exit 1 } finally { Pop-Location }
