@echo off
chcp 65001 >nul
setlocal enableextensions

echo.
echo ================================================
echo  Web server watchdog (auto-restart)
echo ================================================
echo.

REM Optional: stop loop if this flag file exists
set "STOP_FLAG=stop_web_server.flag"

:loop
if exist "%STOP_FLAG%" (
    echo Stop flag found: %STOP_FLAG%
    echo Exiting watchdog.
    goto :end
)

pushd "web"
echo [%date% %time%] Starting server...
node server.js
set "exitCode=%ERRORLEVEL%"
popd

echo.
echo [%date% %time%] Server exited with code %exitCode%.
echo Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto :loop

:end
echo Done.
endlocal
