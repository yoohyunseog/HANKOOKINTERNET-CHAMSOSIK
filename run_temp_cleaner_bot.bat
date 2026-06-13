@echo off
setlocal

cd /d "%~dp0"
if not exist "%~dp0logs\" mkdir "%~dp0logs"

set "TARGET=%LOCALAPPDATA%\Temp"

echo.
echo ===============================
echo   Temp Cleaner BOT - CMD
echo ===============================
echo Target: %TARGET%
echo Logs  : %~dp0logs
echo.

if not exist "%TARGET%\" (
    echo Target folder not found.
    echo %TARGET%
    echo.
    pause
    exit /b 1
)

if /I not "%TARGET%"=="%USERPROFILE%\AppData\Local\Temp" (
    echo Safety stop: target path mismatch.
    echo %TARGET%
    echo.
    pause
    exit /b 1
)

echo Starting cleaner in a separate minimized CMD window...
start "Temp Cleaner BOT" /min cmd /c ""%~dp0temp_cleaner_worker.bat""

echo.
echo Started. It may take several minutes when Temp is very large.
echo Check logs here:
echo %~dp0logs
echo.
pause
