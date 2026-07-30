$ErrorActionPreference = 'Stop'
$LifecyclePath = Join-Path $PSScriptRoot 'Archive-ChatGPTConversationArchiveLifecycle.ps1'
if (-not (Test-Path -LiteralPath $LifecyclePath -PathType Leaf)) { throw "Installed tool is missing lifecycle helper: $LifecyclePath" }
. $LifecyclePath
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
    $ProfilePath = (Resolve-Path -LiteralPath (Join-Path $ToolRoot 'profile')).Path
    if (@(Get-ArchiveProfileProcesses -ProfilePath $ProfilePath).Count -gt 0) { throw "PROFILE_IN_USE: close the dedicated Chrome session before initialization: $ProfilePath" }
    $ChromeArguments = @("--user-data-dir=$ProfilePath", '--window-size=1400,900', '--window-position=50,50', '--disable-extensions', 'https://chatgpt.com/')
    $Chrome = Start-Process -FilePath $ChromePath -ArgumentList $ChromeArguments -PassThru
    $StartupDeadline = (Get-Date).AddSeconds(15)
    do {
        Start-Sleep -Milliseconds 500
        $Effective = @(Get-ArchiveProfileProcesses -ProfilePath $ProfilePath)
        $Windows = @(Get-ArchiveBrowserWindows -ProfilePath $ProfilePath -Processes $Effective)
    } while ($Windows.Count -eq 0 -and (Get-Date) -lt $StartupDeadline)
    if ($Windows.Count -eq 0) { throw "AUTHENTICATION_REQUIRED: the dedicated Chrome window did not become available for profile $ProfilePath" }
    if (($Effective -join "`n") -match '--remote-debugging-(?:pipe|port)|--no-sandbox|--disable-setuid-sandbox') { throw "Manual Chrome launch contains a forbidden automation or sandbox argument: $($Effective -join ' | ')" }
    $InitialPidExited = -not (Get-Process -Id $Chrome.Id -ErrorAction SilentlyContinue)
    $MainIds = ($Windows | Select-Object -ExpandProperty ProcessId) -join ', '
    Write-Host "Independent Chrome login window started (initial launcher PID $($Chrome.Id); initial PID exited=$InitialPidExited; dedicated main PID(s)=$MainIds)."
    Write-Host 'Complete ChatGPT login and any legitimate security challenge in that dedicated Chrome window.'
    Read-Host 'When the ChatGPT conversation interface is visible, press Enter here'
    $Windows = @(Get-ArchiveBrowserWindows -ProfilePath $ProfilePath)
    if ($Windows.Count -eq 0) { throw 'AUTHENTICATION_REQUIRED: the dedicated Chrome window closed before login confirmation' }
    Read-Host 'Close the dedicated Chrome window now, then press Enter here for verification'
    $CloseDeadline = (Get-Date).AddSeconds(120)
    do {
        $Windows = @(Get-ArchiveBrowserWindows -ProfilePath $ProfilePath)
        $LocksReleased = Test-ArchiveProfileLocksReleased -ProfilePath $ProfilePath
        if ($Windows.Count -eq 0 -and $LocksReleased) { break }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $CloseDeadline)
    if ($Windows.Count -gt 0) { throw "AUTHENTICATION_REQUIRED: dedicated Chrome main window remains open after 120 seconds (PID(s): $(($Windows | Select-Object -ExpandProperty ProcessId) -join ', '))" }
    if (-not $LocksReleased) { throw "PROFILE_LOCK_TIMEOUT: dedicated Chrome closed but the profile lock was not released within 120 seconds: $ProfilePath" }
    Write-Host "Dedicated Chrome main window exited and profile lock released: $ProfilePath"
    & node $CliPath verify-auth --config $ConfigPath
    if ($LASTEXITCODE -ne 0) { throw "Authenticated profile verification failed with exit code $LASTEXITCODE" }
} catch { Write-Error $_; exit 1 }
