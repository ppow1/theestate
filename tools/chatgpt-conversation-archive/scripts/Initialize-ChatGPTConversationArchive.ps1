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
    & node $CliPath prepare-profile --config $ConfigPath
    if ($LASTEXITCODE -ne 0) { throw "Profile preparation failed with exit code $LASTEXITCODE" }

    $ChromePath = 'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'
    if (-not (Test-Path -LiteralPath $ChromePath -PathType Leaf)) { throw "Stable Chrome executable was not found: $ChromePath" }
    $ChromeArguments = @("--user-data-dir=$((Resolve-Path -LiteralPath (Join-Path $ToolRoot 'profile')).Path)", '--window-size=1400,900', '--window-position=50,50', '--disable-extensions', 'https://chatgpt.com/')
    $Chrome = Start-Process -FilePath $ChromePath -ArgumentList $ChromeArguments -PassThru
    Start-Sleep -Milliseconds 500
    $Effective = @(Get-CimInstance Win32_Process -Filter "Name='chrome.exe'" | Where-Object { $_.CommandLine -like '*ChatGPTConversationArchive*' } | Select-Object -ExpandProperty CommandLine)
    if (($Effective -join "`n") -match '--remote-debugging-(?:pipe|port)|--no-sandbox|--disable-setuid-sandbox') { throw "Manual Chrome launch contains a forbidden automation or sandbox argument: $($Effective -join ' | ')" }
    Write-Host "Independent Chrome login window started (PID $($Chrome.Id))."
    Write-Host 'Complete ChatGPT login and any legitimate security challenge in that dedicated Chrome window.'
    Read-Host 'When the ChatGPT conversation interface is visible, press Enter here'
    if ($Chrome.HasExited) { throw 'AUTHENTICATION_REQUIRED: the dedicated Chrome window closed before login confirmation' }
    Read-Host 'Close the dedicated Chrome window now, then press Enter here for verification'
    if (-not $Chrome.HasExited) { Wait-Process -Id $Chrome.Id }
    if (-not $Chrome.HasExited) { throw 'AUTHENTICATION_REQUIRED: the dedicated Chrome process did not exit' }
    & node $CliPath verify-auth --config $ConfigPath
    if ($LASTEXITCODE -ne 0) { throw "Authenticated profile verification failed with exit code $LASTEXITCODE" }
} catch { Write-Error $_; exit 1 }
