$ErrorActionPreference = 'Stop'
$dataRoot = 'A:\AI\OpenWebUI\EstateCanonicalData'
$appRoot = 'A:\AI\OpenWebUI'
$exe = Join-Path $appRoot '.venv\Scripts\open-webui.exe'
$outPath = Join-Path $appRoot 'openwebui-startup.out.log'
$errPath = Join-Path $appRoot 'openwebui-startup.err.log'
if (-not (Test-Path -LiteralPath (Join-Path $dataRoot 'webui.db'))) { throw 'Canonical Open WebUI database is missing.' }
Remove-Item -LiteralPath $outPath,$errPath -Force -ErrorAction SilentlyContinue
$env:DATA_DIR = $dataRoot
Start-Process -WindowStyle Hidden -FilePath $exe -ArgumentList 'serve','--host','127.0.0.1','--port','8080' -WorkingDirectory $appRoot -RedirectStandardOutput $outPath -RedirectStandardError $errPath
