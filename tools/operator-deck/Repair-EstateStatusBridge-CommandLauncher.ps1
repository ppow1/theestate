[CmdletBinding()]
param(
    [switch]$Apply,
    [string]$PluginSourceRoot = 'A:\AI\Tools\EstateStreamDeckPlugin',
    [string]$InstalledPluginRoot = (Join-Path $env:APPDATA 'Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin')
)

$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    Write-Error 'Repair-EstateStatusBridge-CommandLauncher.ps1 requires Windows.'
    exit 2
}

$sourcePlugin = Join-Path $PluginSourceRoot 'src\plugin.js'
$installedPlugin = Join-Path $InstalledPluginRoot 'bin\plugin.js'
$oldLauncher = 'const child = spawn("cmd.exe", ["/d", "/s", "/c", "start", "", commandPath], { detached: true, stdio: "ignore", windowsHide: true });'
$newLauncher = 'const child = spawn("cmd.exe", ["/d", "/s", "/c", "call", commandPath], { detached: true, stdio: "ignore", windowsHide: true });'

function Assert-File([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Required file not found: $Path" }
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Assert-Baseline {
    Assert-File $sourcePlugin
    Assert-File $installedPlugin
    if ((Get-Sha256 $sourcePlugin) -ne (Get-Sha256 $installedPlugin)) {
        throw 'Source and installed plugin.js differ.'
    }
    $text = Get-Content -LiteralPath $sourcePlugin -Raw
    $oldCount = ([regex]::Matches($text, [regex]::Escape($oldLauncher))).Count
    $newCount = ([regex]::Matches($text, [regex]::Escape($newLauncher))).Count
    if (($oldCount -eq 1 -and $newCount -eq 0) -or ($oldCount -eq 0 -and $newCount -eq 1)) { return }
    throw "Unexpected shared launcher posture: old=$oldCount, repaired=$newCount."
}

function Convert-Launcher([string]$Text) {
    if ($Text.Contains($newLauncher) -and -not $Text.Contains($oldLauncher)) { return $Text }
    if (-not $Text.Contains($oldLauncher)) { throw 'The expected START-based launcher was not found.' }
    return $Text.Replace($oldLauncher, $newLauncher)
}

function Test-Candidate([string]$Path) {
    $text = Get-Content -LiteralPath $Path -Raw
    if ($text.Contains($oldLauncher)) { throw 'The START-based launcher remains in the candidate.' }
    if (([regex]::Matches($text, [regex]::Escape($newLauncher))).Count -ne 1) { throw 'The repaired CALL-based launcher is missing or duplicated.' }
    $node = Get-Command node.exe -ErrorAction Stop
    & $node.Source --check $Path
    if ($LASTEXITCODE -ne 0) { throw "Node syntax validation failed: $Path" }
}

$temporaryRoot = Join-Path $env:TEMP ('estate-statusbridge-launcher-' + [guid]::NewGuid().ToString('N'))
$backupRoot = $null

try {
    Assert-Baseline
    New-Item -ItemType Directory -Path $temporaryRoot -Force | Out-Null
    $candidate = Join-Path $temporaryRoot 'plugin.js'
    Convert-Launcher (Get-Content -LiteralPath $sourcePlugin -Raw) | Set-Content -LiteralPath $candidate -Encoding utf8
    Test-Candidate $candidate

    $alreadyRepaired = (Get-Content -LiteralPath $sourcePlugin -Raw).Contains($newLauncher)
    if (-not $Apply) {
        $report = @(
            'ESTATE STATUS BRIDGE SHARED COMMAND LAUNCHER PREFLIGHT: PASS'
            "Already repaired: $alreadyRepaired"
            'Candidate replaces CMD START with hidden CMD CALL for every plugin action.'
            'Source and installed baselines match; candidate Node validation passed.'
            'No files were changed. Re-run with -Apply only after reviewing this result.'
        ) -join "`n"
        $report | Write-Output
        $report | Set-Clipboard
        exit 0
    }

    $backupRoot = Join-Path $PluginSourceRoot ('backups\shared-command-launcher-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    New-Item -ItemType Directory -Path $backupRoot -Force | Out-Null
    Copy-Item -LiteralPath $sourcePlugin -Destination (Join-Path $backupRoot 'source-plugin.js')
    Copy-Item -LiteralPath $installedPlugin -Destination (Join-Path $backupRoot 'installed-plugin.js')

    Copy-Item -LiteralPath $candidate -Destination $sourcePlugin -Force
    Copy-Item -LiteralPath $candidate -Destination $installedPlugin -Force

    Assert-Baseline
    Test-Candidate $sourcePlugin

    $report = @(
        'ESTATE STATUS BRIDGE SHARED COMMAND LAUNCHER: VALIDATED'
        "Backup: $backupRoot"
        'All plugin command actions now use the hidden CALL-based launcher.'
        'Source and installed plugin.js match; Node validation passed.'
        'Stream Deck was not restarted automatically.'
    ) -join "`n"
    $report | Write-Output
    $report | Set-Clipboard
} catch {
    if ($backupRoot -and (Test-Path -LiteralPath $backupRoot)) {
        Copy-Item -LiteralPath (Join-Path $backupRoot 'source-plugin.js') -Destination $sourcePlugin -Force
        Copy-Item -LiteralPath (Join-Path $backupRoot 'installed-plugin.js') -Destination $installedPlugin -Force
    }
    Write-Error "Estate Status Bridge shared launcher repair failed: $($_.Exception.Message)"
    exit 1
} finally {
    if (Test-Path -LiteralPath $temporaryRoot) { Remove-Item -LiteralPath $temporaryRoot -Recurse -Force }
}
