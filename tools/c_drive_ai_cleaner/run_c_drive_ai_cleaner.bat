@echo off
setlocal
cd /d "%~dp0\..\.."

echo C Drive AI Cleaner automatic scan
echo.
echo Mode: scan only
echo Model: deepseek-v4-flash:cloud unless OLLAMA_MODEL is set
echo Reports: data\cleanup-reports
echo Logs: data\cleanup-logs
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "tools\c_drive_ai_cleaner\c_drive_ai_cleaner.ps1"

echo.
echo Finished. Check data\cleanup-reports and data\cleanup-logs.
pause
