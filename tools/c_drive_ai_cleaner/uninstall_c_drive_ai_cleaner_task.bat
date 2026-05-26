@echo off
setlocal

set TASK_NAME=CDriveAICleanerScan

echo Removing scheduled task: %TASK_NAME%
echo.

schtasks /Delete /TN "%TASK_NAME%" /F

echo.
pause
