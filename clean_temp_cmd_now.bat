@echo off
setlocal

cd /d "%~dp0"
echo Starting Temp Cleaner worker...
call "%~dp0temp_cleaner_worker.bat"
echo Done. Check logs:
echo %~dp0logs
echo.
pause
