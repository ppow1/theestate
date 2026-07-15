CLS
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'

$Plugin='A:\AI\Tools\EstateStreamDeckPlugin'
$Installed="$env:APPDATA\Elgato\StreamDeck\Plugins\com.estate.statusbridge.sdPlugin"
$Core='A:\AI\Tools\EstateStreamDeckMVP\Core'
$Stamp=Get-Date -Format 'yyyyMMdd-HHmmss'
$Backup=Join-Path $Plugin "backups\longpress-comfy-$Stamp"
New-Item -ItemType Directory -Force -Path $Backup|Out-Null

function Save([string]$p){if(!(Test-Path -LiteralPath $p)){throw "Missing: $p