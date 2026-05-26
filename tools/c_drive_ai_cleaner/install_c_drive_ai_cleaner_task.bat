@echo off
setlocal
cd /d "%~dp0\..\.."

set TASK_NAME=CDriveAICleanerScan
set SCRIPT=%CD%\tools\c_drive_ai_cleaner\c_drive_ai_cleaner.ps1

echo Installing scheduled task: %TASK_NAME%
echo This registers a daily scan-only run at 09:00.
echo It does not enable automatic deletion.
echo.

schtasks /Create /TN "%TASK_NAME%" /SC DAILY /ST 09:00 /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"%SCRIPT%\"" /F

echo.
echo Done. Logs will be written to data\cleanup-logs.
pause
