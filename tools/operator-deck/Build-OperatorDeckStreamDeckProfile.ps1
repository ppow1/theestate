[CmdletBinding()]
param(
    [string]$OutputPath = 'A:\AI\Tools\EstateStreamDeckMVP\Profiles\Operator-Deck-Four-Monitor-Wall.streamDeckProfile',
    [string]$DeviceUuid = '608c6387-9038-4e77-a606-876ffdb47dde',
    [switch]$OpenImport
)

$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    Write-Error 'Build-OperatorDeckStreamDeckProfile.ps1 requires Windows.'
    exit 2
}

$pluginUuid = 'com.estate.statusbridge'
$pluginName = 'Estate Status Bridge'
$pluginVersion = '0.3.0'
$deviceModel = '20GAT9902'
$profileName = 'Operator Deck - Four Monitor Wall'

$layout = @(
    # Physical 4x4 wall: each 2x2 key block represents one monitor.
    [ordered]@{ Position = '0,0'; Slot = 'M1_TOP_LEFT'; Display = 'M1 Top Left' },
    [ordered]@{ Position = '1,0'; Slot = 'M1_TOP_RIGHT'; Display = 'M1 Top Right' },
    [ordered]@{ Position = '0,1'; Slot = 'M1_BOTTOM_LEFT'; Display = 'M1 Bottom Left' },
    [ordered]@{ Position = '1,1'; Slot = 'M1_BOTTOM_RIGHT'; Display = 'M1 Bottom Right' },

    [ordered]@{ Position = '2,0'; Slot = 'M2_TOP_LEFT'; Display = 'M2 Top Left' },
    [ordered]@{ Position = '3,0'; Slot = 'M2_TOP_RIGHT'; Display = 'M2 Top Right' },
    [ordered]@{ Position = '2,1'; Slot = 'M2_BOTTOM_LEFT'; Display = 'M2 Bottom Left' },
    [ordered]@{ Position = '3,1'; Slot = 'M2_BOTTOM_RIGHT'; Display = 'M2 Bottom Right' },

    [ordered]@{ Position = '0,2'; Slot = 'M3_TOP_LEFT'; Display = 'M3 Top Left' },
    [ordered]@{ Position = '1,2'; Slot = 'M3_TOP_RIGHT'; Display = 'M3 Top Right' },
    [ordered]@{ Position = '0,3'; Slot = 'M3_BOTTOM_LEFT'; Display = 'M3 Bottom Left' },
    [ordered]@{ Position = '1,3'; Slot = 'M3_BOTTOM_RIGHT'; Display = 'M3 Bottom Right' },

    [ordered]@{ Position = '2,2'; Slot = 'M4_TOP_LEFT'; Display = 'M4 Top Left' },
    [ordered]@{ Position = '3,2'; Slot = 'M4_TOP_RIGHT'; Display = 'M4 Top Right' },
    [ordered]@{ Position = '2,3'; Slot = 'M4_BOTTOM_LEFT'; Display = 'M4 Bottom Left' },
    [ordered]@{ Position = '3,3'; Slot = 'M4_BOTTOM_RIGHT'; Display = 'M4 Bottom Right' }
)

function New-PluginAction([string]$Name, [string]$Uuid) {
    return [ordered]@{
        ActionID = [guid]::NewGuid().ToString()
        LinkedTitle = $false
        Name = $Name
        Plugin = [ordered]@{
            Name = $pluginName
            UUID = $pluginUuid
            Version = $pluginVersion
        }
        Settings = [pscustomobject]@{}
        State = 0
        States = @([ordered]@{ ShowTitle = $false; Title = '' })
        UUID = $Uuid
    }
}

function Assert-ProfilePackage([string]$Root, [string]$PageManifestPath) {
    $page = Get-Content -LiteralPath $PageManifestPath -Raw | ConvertFrom-Json
    $actions = $page.Controllers[0].Actions
    $properties = @($actions.PSObject.Properties)
    if ($properties.Count -ne 17) { throw "Expected 17 placed actions; found $($properties.Count)." }
    foreach ($entry in $layout) {
        $uuid = 'com.estate.statusbridge.operator_deck.slot.' + $entry.Slot.ToLowerInvariant()
        $property = $actions.PSObject.Properties[$entry.Position]
        if (-not $property -or $property.Value.UUID -ne $uuid) {
            throw "Missing or incorrect quadrant action at $($entry.Position): $uuid"
        }
    }
    $voice = $actions.PSObject.Properties['7,0']
    if (-not $voice -or $voice.Value.UUID -ne 'com.estate.statusbridge.operator_deck.dictation') {
        throw 'Voice Typing action is missing from position 7,0.'
    }
    foreach ($required in @('package.json', 'Profiles')) {
        if (-not (Test-Path -LiteralPath (Join-Path $Root $required))) { throw "Package component missing: $required" }
    }
}

$temporaryRoot = Join-Path $env:TEMP ('operator-deck-profile-' + [guid]::NewGuid().ToString('N'))

try {
    $profileUuid = [guid]::NewGuid().ToString().ToUpperInvariant()
    $pageUuid = [guid]::NewGuid().ToString().ToUpperInvariant()
    $profileRoot = Join-Path $temporaryRoot ('Profiles\' + $profileUuid + '.sdProfile')
    $pageRoot = Join-Path $profileRoot ('Profiles\' + $pageUuid)
    New-Item -ItemType Directory -Path $pageRoot -Force | Out-Null

    $actions = [ordered]@{}
    foreach ($entry in $layout) {
        $uuid = 'com.estate.statusbridge.operator_deck.slot.' + $entry.Slot.ToLowerInvariant()
        $actions[$entry.Position] = New-PluginAction -Name ("Operator Deck " + $entry.Display) -Uuid $uuid
    }
    $actions['7,0'] = New-PluginAction -Name 'Operator Deck Voice Typing' -Uuid 'com.estate.statusbridge.operator_deck.dictation'

    $pageManifest = [ordered]@{
        Controllers = @([ordered]@{ Actions = $actions; Type = 'Keypad' })
        Icon = ''
        Name = 'Four Monitor Wall'
    }
    $pageManifestPath = Join-Path $pageRoot 'manifest.json'
    $pageManifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $pageManifestPath -Encoding utf8

    $profileManifest = [ordered]@{
        AppIdentifier = '*'
        Device = [ordered]@{ Model = $deviceModel; UUID = $DeviceUuid }
        Name = $profileName
        Pages = [ordered]@{
            Current = '00000000-0000-0000-0000-000000000000'
            Default = $pageUuid.ToLowerInvariant()
            Pages = @($pageUuid.ToLowerInvariant())
        }
        Version = '3.0'
    }
    $profileManifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $profileRoot 'manifest.json') -Encoding utf8

    $package = [ordered]@{
        AppVersion = '7.5.0.22885'
        DeviceModel = $deviceModel
        DeviceSettings = $null
        FormatVersion = 1
        OSType = 'Windows'
        OSVersion = [System.Environment]::OSVersion.Version.ToString()
        RequiredPlugins = @([ordered]@{ Name = $pluginName; UUID = $pluginUuid; Version = $pluginVersion })
    }
    $package | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $temporaryRoot 'package.json') -Encoding utf8

    Assert-ProfilePackage -Root $temporaryRoot -PageManifestPath $pageManifestPath

    $outputDirectory = Split-Path -Parent $OutputPath
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
    $zipPath = Join-Path $env:TEMP ('operator-deck-profile-' + [guid]::NewGuid().ToString('N') + '.zip')
    $previousPackageBackup = ''
    if (Test-Path -LiteralPath $OutputPath) {
        $previousPackageBackup = $OutputPath + '.backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
        Move-Item -LiteralPath $OutputPath -Destination $previousPackageBackup
    }
    Compress-Archive -Path (Join-Path $temporaryRoot '*') -DestinationPath $zipPath -CompressionLevel Optimal
    Move-Item -LiteralPath $zipPath -Destination $OutputPath

    $report = @(
        'OPERATOR DECK STREAM DECK PROFILE: VALIDATED'
        "Profile: $profileName"
        "Package: $OutputPath"
        'Placed actions: 17 (16 quadrants + Voice Typing)'
        'Quadrant matrix: columns 0-3, rows 0-3'
        'Reserved expansion area: columns 4-7'
        $(if ($previousPackageBackup) { "Previous package backup: $previousPackageBackup" })
        'The existing Stream Deck profiles were not modified.'
        $(if ($OpenImport) { 'Opening the Stream Deck profile import dialog.' } else { 'Re-run with -OpenImport to open the import dialog.' })
    ) -join "`n"
    $report | Write-Output
    $report | Set-Clipboard

    if ($OpenImport) { Start-Process -FilePath $OutputPath }
} catch {
    Write-Error "Operator Deck profile build failed: $($_.Exception.Message)"
    exit 1
} finally {
    if (Test-Path -LiteralPath $temporaryRoot) { Remove-Item -LiteralPath $temporaryRoot -Recurse -Force }
}
