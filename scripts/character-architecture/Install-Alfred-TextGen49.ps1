[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [string]$EstateRoot = "A:\theestate",

  [Parameter(Mandatory = $false)]
  [string]$TextGenRoot = "A:\AI\TextGen\textgen-4.9",

  [Parameter(Mandatory = $false)]
  [switch]$InjectPromptFields
)

$ErrorActionPreference = "Stop"

function Set-YamlScalarLine {
  param(
    [Parameter(Mandatory = $true)][string[]]$Lines,
    [Parameter(Mandatory = $true)][string]$Key,
    [Parameter(Mandatory = $true)][string]$Value
  )

  $pattern = "^$([regex]::Escape($Key))\s*:"
  $replacement = "$Key`: $Value"
  $found = $false
  $updated = foreach ($line in $Lines) {
    if (-not $found -and $line -match $pattern) {
      $found = $true
      $replacement
    } else {
      $line
    }
  }

  if (-not $found) {
    $updated += $replacement
  }

  return ,$updated
}

function Get-YamlBlockValue {
  param(
    [Parameter(Mandatory = $true)][string[]]$Lines,
    [Parameter(Mandatory = $true)][string]$Key
  )

  $start = -1
  for ($i = 0; $i -lt $Lines.Count; $i++) {
    if ($Lines[$i] -match "^$([regex]::Escape($Key))\s*:\s*\|-\s*$") {
      $start = $i + 1
      break
    }
  }
  if ($start -lt 0) { return $null }

  $collected = New-Object System.Collections.Generic.List[string]
  for ($i = $start; $i -lt $Lines.Count; $i++) {
    $line = $Lines[$i]
    if ($line -match '^[A-Za-z0-9_-]+\s*:') { break }
    if ($line.StartsWith("  ")) {
      $collected.Add($line.Substring(2))
    } elseif ($line.Trim().Length -eq 0) {
      $collected.Add("")
    } else {
      break
    }
  }
  return ($collected -join "`n")
}

function Set-YamlLiteralBlock {
  param(
    [Parameter(Mandatory = $true)][string[]]$Lines,
    [Parameter(Mandatory = $true)][string]$Key,
    [Parameter(Mandatory = $true)][string]$Value
  )

  $output = New-Object System.Collections.Generic.List[string]
  $i = 0
  $replaced = $false
  while ($i -lt $Lines.Count) {
    if ($Lines[$i] -match "^$([regex]::Escape($Key))\s*:") {
      $output.Add("$Key`: |-")
      foreach ($valueLine in ($Value -split "`n", -1)) { $output.Add("  $valueLine") }
      $i++
      while ($i -lt $Lines.Count -and -not ($Lines[$i] -match '^[A-Za-z0-9_-]+\s*:')) { $i++ }
      $replaced = $true
      continue
    }
    $output.Add($Lines[$i])
    $i++
  }

  if (-not $replaced) {
    $output.Add("$Key`: |-")
    foreach ($valueLine in ($Value -split "`n", -1)) { $output.Add("  $valueLine") }
  }

  return ,($output.ToArray())
}

$ExportPath = Join-Path $EstateRoot "docs\residents\alfred\platform-exports\textgen-4_9-alfred-v0_1.yaml"
$CharactersDir = Join-Path $TextGenRoot "user_data\characters"
$TargetCharacterPath = Join-Path $CharactersDir "Alfred.yaml"
$SettingsPath = Join-Path $TextGenRoot "user_data\settings.yaml"

if (-not (Test-Path $ExportPath)) { throw "Missing Alfred TextGen 4.9 export: $ExportPath" }
if (-not (Test-Path $TextGenRoot)) { throw "Missing TextGen root: $TextGenRoot" }
if (-not (Test-Path $CharactersDir)) { New-Item -ItemType Directory -Path $CharactersDir | Out-Null }
if (-not (Test-Path $SettingsPath)) { throw "Missing TextGen settings file: $SettingsPath" }

Copy-Item -LiteralPath $ExportPath -Destination $TargetCharacterPath -Force

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupPath = "$SettingsPath.wp0221-$timestamp.bak"
Copy-Item -LiteralPath $SettingsPath -Destination $BackupPath -Force

$settingsLines = Get-Content -LiteralPath $SettingsPath -Encoding UTF8
$settingsLines = Set-YamlScalarLine -Lines $settingsLines -Key "character" -Value "Alfred"
$settingsLines = Set-YamlScalarLine -Lines $settingsLines -Key "name1" -Value "Steward"
$settingsLines = Set-YamlScalarLine -Lines $settingsLines -Key "name2" -Value "Alfred"
$settingsLines = Set-YamlScalarLine -Lines $settingsLines -Key "mode" -Value "chat"

if ($InjectPromptFields) {
  $exportLines = Get-Content -LiteralPath $ExportPath -Encoding UTF8
  $context = Get-YamlBlockValue -Lines $exportLines -Key "context"
  $greeting = Get-YamlBlockValue -Lines $exportLines -Key "greeting"
  if ($null -ne $context) { $settingsLines = Set-YamlLiteralBlock -Lines $settingsLines -Key "context" -Value $context }
  if ($null -ne $greeting) { $settingsLines = Set-YamlLiteralBlock -Lines $settingsLines -Key "greeting" -Value $greeting }
}

Set-Content -LiteralPath $SettingsPath -Value $settingsLines -Encoding UTF8

Write-Host "Installed Alfred TextGen 4.9 export: $TargetCharacterPath"
Write-Host "Backed up TextGen settings: $BackupPath"
Write-Host "Updated active routing fields: character=Alfred, name1=Steward, name2=Alfred, mode=chat"
if ($InjectPromptFields) { Write-Host "Injected Alfred context and greeting into settings.yaml from the Alfred export." }

Write-Host ""
Write-Host "Next UI steps:"
Write-Host "1. Restart TextGen 4.9."
Write-Host "2. Open the Chat tab and confirm Character is Alfred."
Write-Host "3. Start a new chat so stale conversation state is not reused."
Write-Host "4. If prompt preview is available, verify Alfred's Chief of Staff context or greeting is present."
Write-Host "5. Ask: Who are you? State your full role and title."
Write-Host "Pass: Alfred identifies as Alfred, Chief of Staff of the Estate."
Write-Host "Fail: the model identifies as Qwen, Llama, a base model, a generic assistant, or a private local character."
Write-Host ""
Write-Host "Privacy boundary: this helper copied only Alfred.yaml and edited settings.yaml routing fields. It did not inspect private character files."
