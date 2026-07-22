[CmdletBinding()]
param(
    [string]$SourcePath = 'A:\AI\Tools\EstateStreamDeckPlugin',
    [string]$InstalledPath = (Join-Path $env:APPDATA 'Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin'),
    [string]$ExportRoot = 'A:\EstateExports'
)

CLS
$ErrorActionPreference = 'Stop'

$allowedExtensions = @('.js', '.json', '.cmd', '.ps1', '.csv', '.md', '.txt')
$excludedSegments = @('node_modules', 'backups', 'logs', '.git')
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$destination = Join-Path $ExportRoot "OperatorDeck-StreamDeck-Context-$timestamp"
$zipPath = "$destination.zip"

function Test-IncludedFile {
    param([System.IO.FileInfo]$File, [string]$Root)
    if ($allowedExtensions -notcontains $File.Extension.ToLowerInvariant()) { return $false }
    $relative = [System.IO.Path]::GetRelativePath($Root, $File.FullName)
    $segments = $relative -split '[\\/]'
    foreach ($segment in $segments) {
        if ($excludedSegments -contains $segment) { return $false }
    }
    return $true
}

function Copy-ContextTree {
    param([string]$Root, [string]$ArchivePrefix)
    if (-not (Test-Path -LiteralPath $Root)) {
        Write-Warning "Source not found and was skipped: $Root"
        return @()
    }

    $records = @()
    foreach ($file in Get-ChildItem -LiteralPath $Root -File -Recurse) {
        if (-not (Test-IncludedFile -File $file -Root $Root)) { continue }
        $relative = [System.IO.Path]::GetRelativePath($Root, $file.FullName)
        $archiveRelative = Join-Path $ArchivePrefix $relative
        $target = Join-Path $destination $archiveRelative
        $targetDirectory = Split-Path -Parent $target
        New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $target -Force
        $records += [ordered]@{
            source_root = $Root
            source_path = $file.FullName
            archive_path = $archiveRelative
            bytes = $file.Length
            sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
    return $records
}

try {
    Write-Host 'Collecting bounded Stream Deck integration context...'
    New-Item -ItemType Directory -Path $destination -Force | Out-Null

    $files = @()
    $files += Copy-ContextTree -Root $SourcePath -ArchivePrefix 'source'
    $files += Copy-ContextTree -Root $InstalledPath -ArchivePrefix 'installed'

    if ($files.Count -eq 0) {
        throw 'No eligible Stream Deck integration files were found.'
    }

    $manifest = [ordered]@{
        schema_version = 'operator_deck_stream_deck_context_v1'
        created_at = (Get-Date).ToUniversalTime().ToString('o')
        source_path = $SourcePath
        installed_path = $InstalledPath
        exclusions = [ordered]@{
            extensions = 'Only .js, .json, .cmd, .ps1, .csv, .md, and .txt were included.'
            directories = $excludedSegments
            stream_deck_profiles = 'Not collected.'
        }
        file_count = $files.Count
        files = $files | Sort-Object archive_path
    }
    $manifestPath = Join-Path $destination 'export-manifest.json'
    $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding utf8

    Compress-Archive -Path (Join-Path $destination '*') -DestinationPath $zipPath -CompressionLevel Optimal
    $zipHash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()

    $report = @(
        'STREAM DECK CONTEXT EXPORT COMPLETE'
        "Files collected: $($files.Count)"
        "Folder: $destination"
        "ZIP: $zipPath"
        "ZIP SHA256: $zipHash"
        'Profiles, backups, logs, node_modules, and Git metadata were not collected.'
        'Attach the ZIP to the Work-mode conversation.'
    ) -join "`n"

    $report | Write-Output
    $report | Set-Clipboard
    exit 0
} catch {
    Write-Error "Stream Deck context export failed: $($_.Exception.Message)"
    exit 1
}
