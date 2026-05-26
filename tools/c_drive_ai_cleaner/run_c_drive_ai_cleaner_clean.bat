@echo off
setlocal
cd /d "%~dp0\..\.."

echo C Drive AI Cleaner automatic safe cleanup
echo.
echo Mode: clean old allowlisted temp/cache files
echo Reports: data\cleanup-reports
echo Logs: data\cleanup-logs
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "tools\c_drive_ai_cleaner\c_drive_ai_cleaner.ps1" -Clean

echo.
echo Finished. Check data\cleanup-reports and data\cleanup-logs.
pause
