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

$PromptFieldDenyList = @(
  "Custom system message",
  "Grammar",
  "Token bans",
  "Seed",
  "Copied terminal transcript",
  "Prompt template",
  "Generation parameters"
)

function Get-TextLines {
  param([AllowEmptyCollection()][string[]]$InputLines)

  if ($null -eq $InputLines) { return @() }
  return @($InputLines)
}

function ConvertTo-YamlLiteralBlock {
  param(
    [Parameter(Mandatory = $true)][string]$Key,
    [AllowEmptyString()][string]$Value
  )

  $block = New-Object System.Collections.Generic.List[string]
  $block.Add(("{0}: |-" -f $Key))
  foreach ($valueLine in (($Value -replace "`r`n", "`n") -split "`n", -1)) {
    $block.Add(("  {0}" -f $valueLine))
  }
  return @($block.ToArray())
}

function Set-YamlScalarLine {
  param(
    [AllowEmptyCollection()][string[]]$InputLines,
    [Parameter(Mandatory = $true)][string]$Key,
    [AllowEmptyString()][string]$Value
  )

  $lines = @(Get-TextLines -InputLines $InputLines)
  $pattern = "^{0}\s*:" -f [regex]::Escape($Key)
  $replacement = "{0}: {1}" -f $Key, $Value
  $found = $false
  $updated = New-Object System.Collections.Generic.List[string]

  foreach ($line in $lines) {
    if (-not $found -and $line -match $pattern) {
      $updated.Add($replacement)
      $found = $true
    } else {
      $updated.Add($line)
    }
  }

  if (-not $found) { $updated.Add($replacement) }
  return @($updated.ToArray())
}

function Get-YamlBlockValue {
  param(
    [AllowEmptyCollection()][string[]]$InputLines,
    [Parameter(Mandatory = $true)][string]$Key
  )

  $lines = @(Get-TextLines -InputLines $InputLines)
  $start = -1
  $pattern = "^{0}\s*:\s*\|-\s*$" -f [regex]::Escape($Key)
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match $pattern) {
      $start = $i + 1
      break
    }
  }
  if ($start -lt 0) { return $null }

  $collected = New-Object System.Collections.Generic.List[string]
  for ($i = $start; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]
    if ($line -match '^[A-Za-z0-9_-]+\s*:') { break }
    if ($line.StartsWith("  ")) {
      $collected.Add($line.Substring(2))
    } elseif ($line.Trim().Length -eq 0) {
      $collected.Add("")
    } else {
      break
    }
  }
  return ($collected -join "`n").TrimEnd()
}

function Set-YamlLiteralBlock {
  param(
    [AllowEmptyCollection()][string[]]$InputLines,
    [Parameter(Mandatory = $true)][string]$Key,
    [AllowEmptyString()][string]$Value
  )

  $lines = @(Get-TextLines -InputLines $InputLines)
  $output = New-Object System.Collections.Generic.List[string]
  $i = 0
  $replaced = $false
  $pattern = "^{0}\s*:" -f [regex]::Escape($Key)

  while ($i -lt $lines.Count) {
    if ($lines[$i] -match $pattern) {
      foreach ($blockLine in (ConvertTo-YamlLiteralBlock -Key $Key -Value $Value)) { $output.Add($blockLine) }
      $i++
      while ($i -lt $lines.Count -and -not ($lines[$i] -match '^[A-Za-z0-9_-]+\s*:')) { $i++ }
      $replaced = $true
      continue
    }
    $output.Add($lines[$i])
    $i++
  }

  if (-not $replaced) {
    foreach ($blockLine in (ConvertTo-YamlLiteralBlock -Key $Key -Value $Value)) { $output.Add($blockLine) }
  }

  return @($output.ToArray())
}

function Assert-CleanPromptField {
  param(
    [Parameter(Mandatory = $true)][string]$FieldName,
    [AllowEmptyString()][string]$Value
  )

  foreach ($label in $PromptFieldDenyList) {
    if ($Value -match [regex]::Escape($label)) {
      throw ("Refusing to write UI transcript label into {0}: {1}" -f $FieldName, $label)
    }
  }
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
$BackupPath = "$SettingsPath.wp0222-$timestamp.bak"
Copy-Item -LiteralPath $SettingsPath -Destination $BackupPath -Force

$settingsLines = @(Get-Content -LiteralPath $SettingsPath -Encoding UTF8)
$settingsLines = Set-YamlScalarLine -InputLines $settingsLines -Key "character" -Value "Alfred"
$settingsLines = Set-YamlScalarLine -InputLines $settingsLines -Key "name1" -Value "Steward"
$settingsLines = Set-YamlScalarLine -InputLines $settingsLines -Key "name2" -Value "Alfred"
$settingsLines = Set-YamlScalarLine -InputLines $settingsLines -Key "mode" -Value "chat"

if ($InjectPromptFields) {
  $exportLines = @(Get-Content -LiteralPath $ExportPath -Encoding UTF8)
  $context = Get-YamlBlockValue -InputLines $exportLines -Key "context"
  $greeting = Get-YamlBlockValue -InputLines $exportLines -Key "greeting"
  $customSystemMessage = Get-YamlBlockValue -InputLines $exportLines -Key "custom_system_message"

  if ([string]::IsNullOrWhiteSpace($customSystemMessage)) {
    throw "Missing Alfred custom_system_message in TextGen export. Refusing ambiguous prompt injection."
  }

  Assert-CleanPromptField -FieldName "context" -Value $context
  Assert-CleanPromptField -FieldName "greeting" -Value $greeting
  Assert-CleanPromptField -FieldName "custom_system_message" -Value $customSystemMessage

  if ($null -ne $context) { $settingsLines = Set-YamlLiteralBlock -InputLines $settingsLines -Key "context" -Value $context }
  if ($null -ne $greeting) { $settingsLines = Set-YamlLiteralBlock -InputLines $settingsLines -Key "greeting" -Value $greeting }
  $settingsLines = Set-YamlLiteralBlock -InputLines $settingsLines -Key "custom_system_message" -Value $customSystemMessage
}

Set-Content -LiteralPath $SettingsPath -Value $settingsLines -Encoding UTF8

Write-Host "Installed Alfred TextGen 4.9 export: $TargetCharacterPath"
Write-Host "Backed up TextGen settings: $BackupPath"
Write-Host "Updated active routing fields: character=Alfred, name1=Steward, name2=Alfred, mode=chat"
if ($InjectPromptFields) { Write-Host "Injected Alfred context, greeting, and custom_system_message into settings.yaml from the Alfred export." }

Write-Host ""
Write-Host "Next UI steps:"
Write-Host "1. Restart TextGen 4.9."
Write-Host "2. Open the Chat tab and confirm Character is Alfred."
Write-Host "3. Start a new chat so stale conversation state is not reused."
Write-Host "4. Before UI testing, inspect settings.yaml and confirm context, greeting, and custom_system_message are separate YAML fields, not collapsed transcripts."
Write-Host "5. If prompt preview is available, verify Alfred's Chief of Staff context or greeting is present."
Write-Host "6. Ask: Who are you? State your full role and title."
Write-Host "Pass: Alfred identifies as Alfred, Chief of Staff of the Estate."
Write-Host "Fail: the model identifies as Qwen, Llama, a base model, a generic assistant, or a private local character."
Write-Host ""
Write-Host "Privacy boundary: this helper copied only Alfred.yaml and edited settings.yaml routing and Alfred prompt fields. It did not inspect private character files."
