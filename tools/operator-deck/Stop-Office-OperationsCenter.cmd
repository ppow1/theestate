@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "A:\theestate\launch_operations_center.ps1" -Stop
exit /b %ERRORLEVEL%
