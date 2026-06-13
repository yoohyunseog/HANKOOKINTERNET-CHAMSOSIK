@echo off
setlocal

cd /d "%~dp0"

echo.
echo Installing daily Temp Cleaner BOT task...
echo Task name: Temp Cleaner BOT
echo Time     : 03:30 every day
echo.

schtasks /Create /TN "Temp Cleaner BOT" /SC DAILY /ST 03:30 /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"%~dp0temp_cleaner_bot.ps1\" -OlderThanDays 7 -Quiet" /F

echo.
echo Done. To remove it later:
echo schtasks /Delete /TN "Temp Cleaner BOT" /F
echo.
pause
