@echo off
setlocal
set "ESTATE_REPO_ROOT=A:\theestate-wp4233"
rem Set the canonical paths in this operator boundary as well as in the
rem detached children. Stream Deck invokes this file through cmd.exe, so an
empty inherited variable must never shadow the canonical configuration.
set "PYTHONPATH=%ESTATE_REPO_ROOT%\src"
set "DATA_DIR=A:\AI\OpenWebUI\EstateCanonicalData"
set "DATABASE_URL=sqlite:///A:/AI/OpenWebUI/EstateCanonicalData/webui.db"
"C:\Python314\python.exe" "%ESTATE_REPO_ROOT%\scripts\canonical_webui_gateway.py" %*
exit /b %ERRORLEVEL%
