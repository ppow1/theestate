$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'A:\theestate-grace-openwebui-live'
& 'C:\Python314\python.exe' 'A:\theestate-grace-openwebui-live\tools\start_grace_consultation_gateway.py'
exit $LASTEXITCODE
