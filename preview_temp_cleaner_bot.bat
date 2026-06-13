@echo off
setlocal

cd /d "%~dp0"

echo.
echo ===============================
echo   Temp Cleaner BOT Preview
echo ===============================
echo Target: C:\Users\dbghw\AppData\Local\Temp
echo Rule  : show items older than 7 days without deleting
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0temp_cleaner_bot.ps1" -OlderThanDays 7 -DryRun

echo.
pause
