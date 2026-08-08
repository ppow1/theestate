$ErrorActionPreference = 'Stop'
$appRoot = 'A:\AI\OpenWebUI'
$dataRoot = Join-Path $appRoot 'EstateCanonicalData'
$estateRoot = 'A:\theestate-grace-openwebui-live'
$python = Join-Path $appRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'canonical Open WebUI Python interpreter is missing' }
if (-not (Test-Path -LiteralPath (Join-Path $dataRoot 'webui.db'))) { throw 'canonical Open WebUI database is missing' }
$env:DATA_DIR = $dataRoot
$env:PYTHONPATH = Join-Path $estateRoot 'src'
Push-Location $appRoot
try {
    & $python -m estate.core.autonomous_chatgpt_mailbox_worker @args
    exit $LASTEXITCODE
}
finally { Pop-Location }
