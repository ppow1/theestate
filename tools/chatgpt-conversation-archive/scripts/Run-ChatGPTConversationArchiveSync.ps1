$ErrorActionPreference = 'Stop'
$ToolRoot = [IO.Path]::GetFullPath((Join-Path -Path $PSScriptRoot -ChildPath '..'))
$CliPath = Join-Path -Path $ToolRoot -ChildPath 'dist\cli.js'
$ConfigPath = Join-Path -Path $ToolRoot -ChildPath 'config.example.json'
if (-not (Test-Path -LiteralPath $CliPath -PathType Leaf)) { throw "Installed tool is missing the compiled CLI: $CliPath" }
if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) { throw "Installed tool is missing configuration: $ConfigPath" }
Set-Location -LiteralPath $ToolRoot
try { $env:CHATGPT_ARCHIVE_HEADLESS = 'true'; & node $CliPath sync --config $ConfigPath --quiet; if ($LASTEXITCODE -ne 0) { throw "Sync failed with exit code $LASTEXITCODE" } } catch { Write-Error $_; exit 2 }
