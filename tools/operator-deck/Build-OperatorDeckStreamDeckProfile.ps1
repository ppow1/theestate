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
$pluginVersion = '0.5.0'
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

function New-PageAction([ValidateSet('previous','next')][string]$Direction) {
    $name = if ($Direction -eq 'previous') { 'Previous Page' } else { 'Next Page' }
    return [ordered]@{
        ActionID = [guid]::NewGuid().ToString()
        LinkedTitle = $true
        Name = $name
        Plugin = [ordered]@{ Name = 'Pages'; UUID = 'com.elgato.streamdeck.page'; Version = '1.0' }
        Resources = $null
        Settings = [pscustomobject]@{}
        State = 0
        States = @([ordered]@{})
        UUID = 'com.elgato.streamdeck.page.' + $Direction
    }
}

function Assert-ProfilePackage([string]$Root, [string]$PageManifestPath, [string]$PlacementPageManifestPath) {
    $page = Get-Content -LiteralPath $PageManifestPath -Raw | ConvertFrom-Json
    $actions = $page.Controllers[0].Actions
    $properties = @($actions.PSObject.Properties)
    if ($properties.Count -ne 22) { throw "Expected 22 placed actions; found $($properties.Count)." }
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
    $expectedControls = [ordered]@{
        '4,0' = 'com.estate.statusbridge.operator_deck.undo'
        '5,0' = 'com.estate.statusbridge.operator_deck.clear_selection'
        '6,0' = 'com.estate.statusbridge.operator_deck.select_active'
    }
    foreach ($position in $expectedControls.Keys) {
        $control = $actions.PSObject.Properties[$position]
        if (-not $control -or $control.Value.UUID -ne $expectedControls[$position]) { throw "Control action is missing from $position." }
    }
    foreach ($position in @('6,3','7,3')) {
        $direction = if ($position -eq '6,3') { 'previous' } else { 'next' }
        $navigation = $actions.PSObject.Properties[$position]
        if (-not $navigation -or $navigation.Value.UUID -ne ('com.elgato.streamdeck.page.' + $direction)) { throw "Page navigation is missing from $position." }
    }
    $placementPage = Get-Content -LiteralPath $PlacementPageManifestPath -Raw | ConvertFrom-Json
    $placementActions = $placementPage.Controllers[0].Actions
    $placementExpected = [ordered]@{
        '0,0' = 'com.estate.statusbridge.operator_deck.monitor.m1'
        '1,0' = 'com.estate.statusbridge.operator_deck.monitor.m2'
        '2,0' = 'com.estate.statusbridge.operator_deck.monitor.m3'
        '3,0' = 'com.estate.statusbridge.operator_deck.monitor.m4'
        '0,1' = 'com.estate.statusbridge.operator_deck.shape.full'
        '1,1' = 'com.estate.statusbridge.operator_deck.shape.left'
        '2,1' = 'com.estate.statusbridge.operator_deck.shape.right'
        '3,1' = 'com.estate.statusbridge.operator_deck.shape.top'
        '4,1' = 'com.estate.statusbridge.operator_deck.shape.bottom'
        '4,0' = 'com.estate.statusbridge.operator_deck.undo'
        '5,0' = 'com.estate.statusbridge.operator_deck.clear_selection'
        '6,0' = 'com.estate.statusbridge.operator_deck.select_active'
        '6,1' = 'com.estate.statusbridge.operator_deck.dictation'
        '7,0' = 'com.estate.statusbridge.operator_deck.return'
    }
    if (@($placementActions.PSObject.Properties).Count -ne 16) { throw "Expected 16 mixed-placement actions." }
    foreach ($position in $placementExpected.Keys) {
        $action = $placementActions.PSObject.Properties[$position]
        if (-not $action -or $action.Value.UUID -ne $placementExpected[$position]) { throw "Mixed-placement action is missing from $position." }
    }
    foreach ($position in @('6,3','7,3')) {
        $direction = if ($position -eq '6,3') { 'previous' } else { 'next' }
        $navigation = $placementActions.PSObject.Properties[$position]
        if (-not $navigation -or $navigation.Value.UUID -ne ('com.elgato.streamdeck.page.' + $direction)) { throw "Mixed-placement page navigation is missing from $position." }
    }
    foreach ($required in @('package.json', 'Profiles')) {
        if (-not (Test-Path -LiteralPath (Join-Path $Root $required))) { throw "Package component missing: $required" }
    }
}

$temporaryRoot = Join-Path $env:TEMP ('operator-deck-profile-' + [guid]::NewGuid().ToString('N'))

try {
    $profileUuid = [guid]::NewGuid().ToString().ToUpperInvariant()
    $pageUuid = [guid]::NewGuid().ToString().ToUpperInvariant()
    $placementPageUuid = [guid]::NewGuid().ToString().ToUpperInvariant()
    $profileRoot = Join-Path $temporaryRoot ('Profiles\' + $profileUuid + '.sdProfile')
    $pageRoot = Join-Path $profileRoot ('Profiles\' + $pageUuid)
    $placementPageRoot = Join-Path $profileRoot ('Profiles\' + $placementPageUuid)
    New-Item -ItemType Directory -Path $pageRoot -Force | Out-Null
    New-Item -ItemType Directory -Path $placementPageRoot -Force | Out-Null

    $actions = [ordered]@{}
    foreach ($entry in $layout) {
        $uuid = 'com.estate.statusbridge.operator_deck.slot.' + $entry.Slot.ToLowerInvariant()
        $actions[$entry.Position] = New-PluginAction -Name ("Operator Deck " + $entry.Display) -Uuid $uuid
    }
    $actions['7,0'] = New-PluginAction -Name 'Operator Deck Voice Typing' -Uuid 'com.estate.statusbridge.operator_deck.dictation'
    $actions['4,0'] = New-PluginAction -Name 'Operator Deck Undo' -Uuid 'com.estate.statusbridge.operator_deck.undo'
    $actions['5,0'] = New-PluginAction -Name 'Operator Deck Clear Selection' -Uuid 'com.estate.statusbridge.operator_deck.clear_selection'
    $actions['6,0'] = New-PluginAction -Name 'Operator Deck Select Active' -Uuid 'com.estate.statusbridge.operator_deck.select_active'
    $actions['6,3'] = New-PageAction -Direction previous
    $actions['7,3'] = New-PageAction -Direction next

    $pageManifest = [ordered]@{
        Controllers = @([ordered]@{ Actions = $actions; Type = 'Keypad' })
        Icon = ''
        Name = 'Four Monitor Wall'
    }
    $pageManifestPath = Join-Path $pageRoot 'manifest.json'
    $pageManifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $pageManifestPath -Encoding utf8

    $placementActions = [ordered]@{}
    $placementActions['0,0'] = New-PluginAction -Name 'Operator Deck Destination M1' -Uuid 'com.estate.statusbridge.operator_deck.monitor.m1'
    $placementActions['1,0'] = New-PluginAction -Name 'Operator Deck Destination M2' -Uuid 'com.estate.statusbridge.operator_deck.monitor.m2'
    $placementActions['2,0'] = New-PluginAction -Name 'Operator Deck Destination M3' -Uuid 'com.estate.statusbridge.operator_deck.monitor.m3'
    $placementActions['3,0'] = New-PluginAction -Name 'Operator Deck Destination M4' -Uuid 'com.estate.statusbridge.operator_deck.monitor.m4'
    $placementActions['0,1'] = New-PluginAction -Name 'Operator Deck Shape Full' -Uuid 'com.estate.statusbridge.operator_deck.shape.full'
    $placementActions['1,1'] = New-PluginAction -Name 'Operator Deck Shape Left' -Uuid 'com.estate.statusbridge.operator_deck.shape.left'
    $placementActions['2,1'] = New-PluginAction -Name 'Operator Deck Shape Right' -Uuid 'com.estate.statusbridge.operator_deck.shape.right'
    $placementActions['3,1'] = New-PluginAction -Name 'Operator Deck Shape Top' -Uuid 'com.estate.statusbridge.operator_deck.shape.top'
    $placementActions['4,1'] = New-PluginAction -Name 'Operator Deck Shape Bottom' -Uuid 'com.estate.statusbridge.operator_deck.shape.bottom'
    $placementActions['4,0'] = New-PluginAction -Name 'Operator Deck Undo' -Uuid 'com.estate.statusbridge.operator_deck.undo'
    $placementActions['5,0'] = New-PluginAction -Name 'Operator Deck Clear Selection' -Uuid 'com.estate.statusbridge.operator_deck.clear_selection'
    $placementActions['6,0'] = New-PluginAction -Name 'Operator Deck Select Active' -Uuid 'com.estate.statusbridge.operator_deck.select_active'
    $placementActions['6,1'] = New-PluginAction -Name 'Operator Deck Voice Typing' -Uuid 'com.estate.statusbridge.operator_deck.dictation'
    $placementActions['7,0'] = New-PluginAction -Name 'Operator Deck Return Promoted Window' -Uuid 'com.estate.statusbridge.operator_deck.return'
    $placementActions['6,3'] = New-PageAction -Direction previous
    $placementActions['7,3'] = New-PageAction -Direction next
    $placementPageManifest = [ordered]@{
        Controllers = @([ordered]@{ Actions = $placementActions; Type = 'Keypad' })
        Icon = ''
        Name = 'Mixed Placement'
    }
    $placementPageManifestPath = Join-Path $placementPageRoot 'manifest.json'
    $placementPageManifest | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $placementPageManifestPath -Encoding utf8

    $profileManifest = [ordered]@{
        AppIdentifier = '*'
        Device = [ordered]@{ Model = $deviceModel; UUID = $DeviceUuid }
        Name = $profileName
        Pages = [ordered]@{
            Current = '00000000-0000-0000-0000-000000000000'
            Default = $pageUuid.ToLowerInvariant()
            Pages = @($pageUuid.ToLowerInvariant(), $placementPageUuid.ToLowerInvariant())
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
        RequiredPlugins = @(
            [ordered]@{ Name = $pluginName; UUID = $pluginUuid; Version = $pluginVersion },
            [ordered]@{ Name = 'Pages'; UUID = 'com.elgato.streamdeck.page'; Version = '1.0' }
        )
    }
    $package | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $temporaryRoot 'package.json') -Encoding utf8

    Assert-ProfilePackage -Root $temporaryRoot -PageManifestPath $pageManifestPath -PlacementPageManifestPath $placementPageManifestPath

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
        'Page 1: 22 actions (16 quadrants + UNDO + CLEAR + SELECT + Voice Typing + Previous/Next Page)'
        'Page 2: 16 actions (M1-M4 + FULL/LEFT/RIGHT/TOP/BOTTOM + UNDO/CLEAR/SELECT + Voice Typing + RETURN + Previous/Next Page)'
        'The validated Page 1 quadrant matrix remains unchanged.'
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
