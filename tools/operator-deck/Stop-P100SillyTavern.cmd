@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Stop-P100SillyTavern.ps1" %*
exit /b %ERRORLEVEL%
