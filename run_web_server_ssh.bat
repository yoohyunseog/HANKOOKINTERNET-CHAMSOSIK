@echo off
chcp 65001 >nul
setlocal enableextensions

echo.
echo ================================================
echo  Remote web server via SSH
echo ================================================
echo.

set "REMOTE_HOST=root@211.45.162.155"
set "REMOTE_DIR=~/web"

echo Connecting to %REMOTE_HOST% ...
ssh -t %REMOTE_HOST% "cd %REMOTE_DIR% ; node server.js"

echo.
echo SSH session ended.
endlocal
