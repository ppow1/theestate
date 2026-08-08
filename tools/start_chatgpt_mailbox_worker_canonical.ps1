$ErrorActionPreference = 'Stop'

# This wrapper is intentionally a child of the canonical Open WebUI owner.
# It derives the same working directory/key-file source and never copies or
# places WEBUI_SECRET_KEY on the command line.
$appRoot = 'A:\AI\OpenWebUI'
$dataRoot = Join-Path $appRoot 'EstateCanonicalData'
$estateRoot = 'A:\theestate'
$python = Join-Path $appRoot '.venv\Scripts\python.exe'
$keyFile = Join-Path $appRoot '.webui_secret_key'

if (-not (Test-Path -LiteralPath $python)) { throw 'canonical Open WebUI Python interpreter is missing' }
if (-not (Test-Path -LiteralPath (Join-Path $dataRoot 'webui.db'))) { throw 'canonical Open WebUI database is missing' }
if (-not (Test-Path -LiteralPath $keyFile)) { throw 'canonical Open WebUI secret-key source is missing' }

$env:DATA_DIR = $dataRoot
$env:PYTHONPATH = Join-Path $estateRoot 'src'
Push-Location $appRoot
try {
    & $python -m estate.core.autonomous_chatgpt_mailbox_worker @args
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
