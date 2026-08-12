@echo off
setlocal

set "PLUGIN_DIR=%~dp0"
set "LOG=%PLUGIN_DIR%estate-statusbridge.log"
set "NODE="

if exist "C:\Program Files\nodejs\node.exe" (
    set "NODE=C:\Program Files\nodejs\node.exe"
)

if not defined NODE (
    for /f "delims=" %%I in ('where.exe node 2^>nul') do (
        set "NODE=%%~fI"
        goto node_resolved
    )
)

:node_resolved

if not defined NODE (
    echo %date% %time% ERROR node.exe not found via default path or PATH lookup >> "%LOG%"
    exit /b 2
)

if not exist "%PLUGIN_DIR%plugin.js" (
    echo %date% %time% ERROR plugin.js not found at "%PLUGIN_DIR%plugin.js" >> "%LOG%"
    exit /b 3
)

echo %date% %time% START %* >> "%LOG%"
echo %date% %time% NODE "%NODE%" >> "%LOG%"

"%NODE%" "%PLUGIN_DIR%plugin.js" %* >> "%LOG%" 2>&1

set "RC=%ERRORLEVEL%"
echo %date% %time% EXIT %RC% >> "%LOG%"

exit /b %RC%


