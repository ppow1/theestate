$ErrorActionPreference = 'Stop'
$ToolRoot = [IO.Path]::GetFullPath((Join-Path -Path $PSScriptRoot -ChildPath '..'))
$PackageJson = Join-Path -Path $ToolRoot -ChildPath 'package.json'
$TsConfig = Join-Path -Path $ToolRoot -ChildPath 'tsconfig.json'
$CliPath = Join-Path -Path $ToolRoot -ChildPath 'dist\cli.js'
$ConfigPath = Join-Path -Path $ToolRoot -ChildPath 'config.example.json'

if (-not (Test-Path -LiteralPath $PackageJson -PathType Leaf)) { throw "Installed tool is missing package.json: $PackageJson" }
if (-not (Test-Path -LiteralPath $TsConfig -PathType Leaf)) { throw "Installed tool is missing tsconfig.json: $TsConfig" }
if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) { throw "Installed tool is missing configuration: $ConfigPath" }

Set-Location -LiteralPath $ToolRoot
try {
    if (-not (Test-Path -LiteralPath (Join-Path $ToolRoot 'node_modules') -PathType Container)) { & npm install; if ($LASTEXITCODE -ne 0) { throw "npm install failed with exit code $LASTEXITCODE" } }
    & npm run build; if ($LASTEXITCODE -ne 0) { throw "npm run build failed with exit code $LASTEXITCODE" }
    & node $CliPath init-profile --config $ConfigPath
    if ($LASTEXITCODE -ne 0) { throw "Initialization failed with exit code $LASTEXITCODE" }
} catch { Write-Error $_; exit 1 }
