@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-P100SillyTavern.ps1" %*
exit /b %ERRORLEVEL%
