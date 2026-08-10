@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& 'A:\theestate\launch_operations_center.ps1'; if ($LASTEXITCODE -eq 0) { Start-Process 'http://127.0.0.1:8765/' }"
exit /b %ERRORLEVEL%
