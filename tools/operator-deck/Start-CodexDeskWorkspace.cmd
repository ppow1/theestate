@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem This wrapper is invoked by Stream Deck outside an interactive shell. Keep a
rem durable record of that exact boundary before starting PowerShell.
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_PATH=%SCRIPT_DIR%Start-CodexDeskWorkspace.ps1"
set "LOG_PATH=%SCRIPT_DIR%runtime\codex-desk-cold-start.log"
if not exist "%SCRIPT_DIR%runtime" mkdir "%SCRIPT_DIR%runtime" >nul 2>&1

>>"%LOG_PATH%" echo.
>>"%LOG_PATH%" echo [CMD-BEGIN] utc=%DATE% %TIME% local=%DATE% %TIME% pid=%PROCESS_ID% parent_pid=%PPID% cwd=%CD%
>>"%LOG_PATH%" echo [CMD] command_line=%COMSPEC% /d /c "%~f0" %*
>>"%LOG_PATH%" echo [CMD] script_path=%SCRIPT_PATH%
>>"%LOG_PATH%" echo [CMD] PATH=%PATH%
>>"%LOG_PATH%" echo [CMD] PATHEXT=%PATHEXT%
>>"%LOG_PATH%" echo [CMD] USERPROFILE=%USERPROFILE%
>>"%LOG_PATH%" echo [CMD] LOCALAPPDATA=%LOCALAPPDATA%
>>"%LOG_PATH%" echo [CMD] APPDATA=%APPDATA%
>>"%LOG_PATH%" echo [CMD] ProgramFiles=%ProgramFiles%
>>"%LOG_PATH%" echo [CMD] ProgramFiles(x86)=%ProgramFiles(x86)%
>>"%LOG_PATH%" echo [CMD] CODEX_HOME=%CODEX_HOME%

set "POWERSHELL_EXE="
for %%P in ("%ProgramFiles%\PowerShell\7\pwsh.exe" "%ProgramFiles(x86)%\PowerShell\7\pwsh.exe" "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe") do if not defined POWERSHELL_EXE if exist "%%~P" set "POWERSHELL_EXE=%%~P"
>>"%LOG_PATH%" echo [CMD] resolved_powershell=%POWERSHELL_EXE%
if not defined POWERSHELL_EXE (
  >>"%LOG_PATH%" echo [CMD-FAIL] No supported PowerShell executable was found.
  exit /b 9009
)
if not exist "%SCRIPT_PATH%" (
  >>"%LOG_PATH%" echo [CMD-FAIL] Bootstrap script does not exist: %SCRIPT_PATH%
  exit /b 2
)

set "POWERSHELL_OUTPUT=%LOG_PATH%.stdout"
"%POWERSHELL_EXE%" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_PATH%" %* >>"%POWERSHELL_OUTPUT%" 2>&1
set "EXIT_CODE=%ERRORLEVEL%"
>>"%LOG_PATH%" echo [CMD-POWERSHELL-OUTPUT] begin=%POWERSHELL_OUTPUT%
type "%POWERSHELL_OUTPUT%" >>"%LOG_PATH%"
>>"%LOG_PATH%" echo [CMD-POWERSHELL-OUTPUT] end
>>"%LOG_PATH%" echo [CMD-END] exit_code=%EXIT_CODE% utc=%DATE% %TIME%
exit /b %EXIT_CODE%
