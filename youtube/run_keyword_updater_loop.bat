@echo off
setlocal
cd /d "%~dp0"

set "INTERVAL_SECONDS=600"

:loop
echo ===============================================
echo Keyword updater loop started at %date% %time%
echo ===============================================
call "%~dp0run_keyword_updater.bat"

echo.
echo Waiting 10 minutes before next run...
timeout /t %INTERVAL_SECONDS% /nobreak >nul
goto loop
