[CmdletBinding()]
param(
    [string]$BuildRoot = "A:\AI\Tools\EstateStreamDeckPlugin"
)

$ErrorActionPreference = "Stop"

$PluginId = "com.estate.statusbridge.sdPlugin"
$PackageName = "com.estate.statusbridge.streamDeckPlugin"
$SourceRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$BuildRootFull = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($BuildRoot)
$DistRoot = Join-Path $BuildRootFull "dist"
$LogsRoot = Join-Path $BuildRootFull "logs"
$SnapshotRoot = Join-Path $BuildRootFull "src"
$PluginRoot = Join-Path $DistRoot $PluginId
$PackagePath = Join-Path $DistRoot $PackageName
$ProfileName = "Estate Operations v0.5 Plugin"
$ProfileSourceRoot = Join-Path $BuildRootFull "profile-src"
$ProfilePath = Join-Path $DistRoot "$ProfileName.streamDeckProfile"
$BuildLog = Join-Path $LogsRoot "build.log"
$BuildReport = Join-Path $BuildRootFull "BUILD_REPORT.md"

function New-RequiredDirectory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Assert-ChildPath {
    param(
        [string]$Path,
        [string]$Root
    )
    $full = [System.IO.Path]::GetFullPath($Path)
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to modify path outside expected root: $full"
    }
}

function Reset-Directory {
    param(
        [string]$Path,
        [string]$Root
    )
    Assert-ChildPath -Path $Path -Root $Root
    if (Test-Path -LiteralPath $Path) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    }
    New-RequiredDirectory -Path $Path
}

function Write-Log {
    param([string]$Message)
    $line = "$(Get-Date -Format o) $Message"
    Add-Content -LiteralPath $BuildLog -Value $line -Encoding UTF8
    Write-Host $Message
}

New-RequiredDirectory -Path $BuildRootFull
New-RequiredDirectory -Path $DistRoot
New-RequiredDirectory -Path $LogsRoot
Set-Content -LiteralPath $BuildLog -Value "Estate Status Bridge build log" -Encoding UTF8

Write-Log "SourceRoot: $SourceRoot"
Write-Log "BuildRoot: $BuildRootFull"

Reset-Directory -Path $PluginRoot -Root $DistRoot
Reset-Directory -Path $SnapshotRoot -Root $BuildRootFull
Reset-Directory -Path $ProfileSourceRoot -Root $BuildRootFull

New-RequiredDirectory -Path (Join-Path $PluginRoot "bin")
New-RequiredDirectory -Path (Join-Path $PluginRoot "images")

Copy-Item -LiteralPath (Join-Path $SourceRoot "manifest.json") -Destination (Join-Path $PluginRoot "manifest.json") -Force
Copy-Item -LiteralPath (Join-Path $SourceRoot "bin\package.json") -Destination (Join-Path $PluginRoot "bin\package.json") -Force
Copy-Item -LiteralPath (Join-Path $SourceRoot "bin\EstateStatusBridge.cmd") -Destination (Join-Path $PluginRoot "bin\EstateStatusBridge.cmd") -Force
Copy-Item -Path (Join-Path $SourceRoot "src\*.js") -Destination (Join-Path $PluginRoot "bin") -Force
Copy-Item -Path (Join-Path $SourceRoot "images\*.svg") -Destination (Join-Path $PluginRoot "images") -Force

Copy-Item -LiteralPath (Join-Path $SourceRoot "manifest.json") -Destination $SnapshotRoot -Force
Copy-Item -LiteralPath (Join-Path $SourceRoot "package.json") -Destination $SnapshotRoot -Force
Copy-Item -LiteralPath (Join-Path $SourceRoot "README.md") -Destination $SnapshotRoot -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath (Join-Path $SourceRoot "src") -Destination $SnapshotRoot -Recurse -Force
Copy-Item -LiteralPath (Join-Path $SourceRoot "images") -Destination $SnapshotRoot -Recurse -Force
Copy-Item -LiteralPath (Join-Path $SourceRoot "tests") -Destination $SnapshotRoot -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item -LiteralPath (Join-Path $SourceRoot "scripts") -Destination $SnapshotRoot -Recurse -Force
Copy-Item -LiteralPath (Join-Path $SourceRoot "operational-mvp") -Destination $SnapshotRoot -Recurse -Force -ErrorAction SilentlyContinue

Copy-Item -LiteralPath (Join-Path $SourceRoot "scripts\install.ps1") -Destination (Join-Path $BuildRootFull "install.ps1") -Force
Copy-Item -LiteralPath (Join-Path $SourceRoot "scripts\uninstall.ps1") -Destination (Join-Path $BuildRootFull "uninstall.ps1") -Force

if (Test-Path -LiteralPath $PackagePath) {
    Remove-Item -LiteralPath $PackagePath -Force
}
$ZipPath = "$PackagePath.zip"
if (Test-Path -LiteralPath $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}
Compress-Archive -LiteralPath $PluginRoot -DestinationPath $ZipPath -Force
Move-Item -LiteralPath $ZipPath -Destination $PackagePath -Force

$NodeVersion = (& node --version) 2>$null
$NpmVersion = (& npm --version) 2>$null
$StreamDeckExe = "C:\Program Files\Elgato\StreamDeck\StreamDeck.exe"
$StreamDeckVersion = if (Test-Path -LiteralPath $StreamDeckExe) { (Get-Item -LiteralPath $StreamDeckExe).VersionInfo.ProductVersion } else { "not found" }
$Manifest = Get-Content -Raw -LiteralPath (Join-Path $PluginRoot "manifest.json") | ConvertFrom-Json
$ProfileGenerator = Join-Path $SourceRoot "scripts\generate-profile.mjs"
$ProfileOutput = & node $ProfileGenerator --output-root $ProfileSourceRoot --profile-name $ProfileName --plugin-version $Manifest.Version 2>&1
$ProfileExitCode = $LASTEXITCODE
$ProfileOutput | ForEach-Object { Write-Log "Profile generator: $_" }
if ($ProfileExitCode -ne 0) {
    throw "Profile generation failed with exit code $ProfileExitCode"
}
if (Test-Path -LiteralPath $ProfilePath) {
    Remove-Item -LiteralPath $ProfilePath -Force
}
$ProfileZipPath = "$ProfilePath.zip"
if (Test-Path -LiteralPath $ProfileZipPath) {
    Remove-Item -LiteralPath $ProfileZipPath -Force
}
Compress-Archive -Path (Join-Path $ProfileSourceRoot "*") -DestinationPath $ProfileZipPath -Force
Move-Item -LiteralPath $ProfileZipPath -Destination $ProfilePath -Force

$PackageHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $PackagePath).Hash
$ManifestHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $PluginRoot "manifest.json")).Hash
$ProfileHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ProfilePath).Hash
$ProfileSummary = Join-Path $ProfileSourceRoot "profile-actions.json"

@(
    "# Estate Status Bridge Build Report"
    ""
    "Generated: $(Get-Date -Format o)"
    "Source path: $SourceRoot"
    "Build root: $BuildRootFull"
    "Plugin folder: $PluginRoot"
    "Package path: $PackagePath"
    "Package SHA-256: $PackageHash"
    "Profile path: $ProfilePath"
    "Profile SHA-256: $ProfileHash"
    "Profile source: $ProfileSourceRoot"
    "Profile action summary: $ProfileSummary"
    "Manifest SHA-256: $ManifestHash"
    "Stream Deck version: $StreamDeckVersion"
    "Node version: $NodeVersion"
    "npm version: $NpmVersion"
    "SDK/tooling: Stream Deck SDK manifest v$($Manifest.SDKVersion); no external SDK package required"
    "Build command: powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -BuildRoot `"$BuildRootFull`""
    "Actions exposed: $($Manifest.Actions.Count)"
    ""
    "## Artifacts"
    ""
    "- $PluginRoot"
    "- $PackagePath"
    "- $ProfilePath"
    "- $ProfileSummary"
    "- $BuildLog"
) | Set-Content -LiteralPath $BuildReport -Encoding UTF8

Write-Log "Package SHA-256: $PackageHash"
Write-Log "Profile SHA-256: $ProfileHash"
Write-Log "Build complete."

Write-Output ([pscustomobject]@{
    SourceRoot = $SourceRoot
    BuildRoot = $BuildRootFull
    PluginFolder = $PluginRoot
    PackagePath = $PackagePath
    PackageSha256 = $PackageHash
    ProfilePath = $ProfilePath
    ProfileSha256 = $ProfileHash
    BuildReport = $BuildReport
})


