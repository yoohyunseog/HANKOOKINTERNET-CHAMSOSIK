@echo off
setlocal

cd /d "%~dp0"
if not exist "%~dp0logs\" mkdir "%~dp0logs"

set "HH=%time:~0,2%"
set "HH=%HH: =0%"
set "LOG=%~dp0logs\temp-cleaner-cmd-%date:~0,4%%date:~5,2%%date:~8,2%-%HH%%time:~3,2%%time:~6,2%.log"
set "TARGET=%LOCALAPPDATA%\Temp"
set "EMPTY=%~dp0logs\empty-temp-source"

if not exist "%TARGET%\" exit /b 1
if /I not "%TARGET%"=="%USERPROFILE%\AppData\Local\Temp" exit /b 1

if exist "%EMPTY%\" rd /s /q "%EMPTY%" >nul 2>nul
mkdir "%EMPTY%" >nul 2>nul

(
    echo ===============================
    echo Temp Cleaner BOT Worker
    echo Started: %date% %time%
    echo Target : %TARGET%
    echo Method : robocopy empty folder mirror, retry 0
    echo Exclude: HeadlessChrome*
    echo ===============================
    echo.
) > "%LOG%"

robocopy "%EMPTY%" "%TARGET%" /MIR /R:0 /W:0 /XJ /XD "HeadlessChrome*" /NFL /NDL /NP /NJH /NJS /LOG+:"%LOG%" >nul
set "ROBO=%ERRORLEVEL%"

rd /s /q "%EMPTY%" >nul 2>nul

set /a LEFT_FILES=0
set /a LEFT_FOLDERS=0
for /f %%C in ('dir /a-d /b "%TARGET%" 2^>nul ^| find /c /v ""') do set "LEFT_FILES=%%C"
for /f %%C in ('dir /ad /b "%TARGET%" 2^>nul ^| find /c /v ""') do set "LEFT_FOLDERS=%%C"

(
    echo.
    echo ===============================
    echo Finished: %date% %time%
    echo Robocopy code    : %ROBO%
    echo Remaining files  : %LEFT_FILES%
    echo Remaining folders: %LEFT_FOLDERS%
    echo Note: locked/in-use items can remain.
    echo ===============================
) >> "%LOG%"

exit /b 0
