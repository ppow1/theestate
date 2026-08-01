@echo off
setlocal
set "ESTATE_REPO_ROOT=A:\theestate-wp4233"
set "PYTHONPATH="
set "DATA_DIR="
set "DATABASE_URL="
"C:\Python314\python.exe" "%ESTATE_REPO_ROOT%\scripts\canonical_webui_gateway.py" %*
exit /b %ERRORLEVEL%
