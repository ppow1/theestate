param([switch]$ValidateOnly)

$ErrorActionPreference = 'Stop'
$dataRoot = 'A:\AI\OpenWebUI\EstateCanonicalData'
$appRoot = 'A:\AI\OpenWebUI'
$exe = Join-Path $appRoot '.venv\Scripts\open-webui.exe'
$outPath = Join-Path $appRoot 'openwebui-startup.out.log'
$errPath = Join-Path $appRoot 'openwebui-startup.err.log'
$databasePath = Join-Path $dataRoot 'webui.db'
if ([System.IO.Path]::GetFullPath($dataRoot) -ne 'A:\AI\OpenWebUI\EstateCanonicalData') {
    throw "Canonical Open WebUI DATA_DIR resolved unexpectedly: $dataRoot"
}
if (-not (Test-Path -LiteralPath $dataRoot -PathType Container)) {
    throw "Canonical Open WebUI data directory is missing: $dataRoot"
}
if (-not (Test-Path -LiteralPath $databasePath -PathType Leaf)) {
    throw "Canonical Open WebUI database is missing: $databasePath"
}
try {
    $stream = [System.IO.File]::Open($databasePath, 'Open', 'Read', 'ReadWrite')
    $stream.Dispose()
}
catch {
    throw "Canonical Open WebUI database is not readable: $databasePath ($($_.Exception.Message))"
}
$env:DATA_DIR = $dataRoot
if ($ValidateOnly) {
    [pscustomobject]@{
        data_dir = $env:DATA_DIR
        database = $databasePath
        state = 'VALID'
    } | ConvertTo-Json -Compress
    exit 0
}
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
    throw "Canonical Open WebUI executable is missing: $exe"
}
Remove-Item -LiteralPath $outPath,$errPath -Force -ErrorAction SilentlyContinue
Set-Location -LiteralPath $appRoot
Start-Process -WindowStyle Hidden -FilePath $exe -ArgumentList 'serve','--host','127.0.0.1','--port','8080' -WorkingDirectory $appRoot -RedirectStandardOutput $outPath -RedirectStandardError $errPath
