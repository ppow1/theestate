$ErrorActionPreference = 'Stop'
$dataRoot = 'A:\AI\OpenWebUI\EstateCanonicalData'
$appRoot = 'A:\AI\OpenWebUI'
$exe = Join-Path $appRoot '.venv\Scripts\open-webui.exe'
$venvRoot = Join-Path $appRoot '.venv'
$frontendRoot = Join-Path $venvRoot 'Lib\site-packages\open_webui\frontend'
$staticRoot = Join-Path $venvRoot 'Lib\site-packages\open_webui\static'
$outPath = Join-Path $appRoot 'openwebui-startup.out.log'
$errPath = Join-Path $appRoot 'openwebui-startup.err.log'
if (-not (Test-Path -LiteralPath (Join-Path $dataRoot 'webui.db'))) { throw 'Canonical Open WebUI database is missing.' }
if (-not (Test-Path -LiteralPath $exe)) { throw "Canonical Open WebUI executable is missing: $exe" }
if (-not (Test-Path -LiteralPath (Join-Path $frontendRoot 'index.html'))) { throw "Canonical Open WebUI frontend is missing: $frontendRoot" }
if (-not (Test-Path -LiteralPath $staticRoot)) { throw "Canonical Open WebUI static root is missing: $staticRoot" }
Remove-Item -LiteralPath $outPath,$errPath -Force -ErrorAction SilentlyContinue
$env:DATA_DIR = $dataRoot
$env:DATABASE_URL = "sqlite:///$($dataRoot.Replace('\','/'))/webui.db"
$env:FRONTEND_BUILD_DIR = $frontendRoot
$env:STATIC_DIR = $staticRoot
Start-Process -WindowStyle Hidden -FilePath $exe -ArgumentList 'serve','--host','127.0.0.1','--port','8080' -WorkingDirectory $appRoot -RedirectStandardOutput $outPath -RedirectStandardError $errPath
