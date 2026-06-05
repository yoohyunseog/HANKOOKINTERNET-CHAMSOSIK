@echo off
setlocal

REM Use UTF-8 so Korean folder names are handled correctly.
chcp 65001 >nul

set "SERVER=root@211.45.162.155"
set "REMOTE_ROOT=/var/www/한국인터넷.한국"
set "LOCAL_DIR=E:\Ai project\사이트\web\public\한국인터넷.한국"

echo ========================================
echo ICNN History Upload Script
echo ========================================
echo.

echo [1/3] Uploading icnn-history.html...
scp "%LOCAL_DIR%\icnn-history.html" %SERVER%:%REMOTE_ROOT%/icnn-history.html

echo.
echo [2/3] Uploading config.json...
scp "%LOCAL_DIR%\config.json" %SERVER%:%REMOTE_ROOT%/config.json

echo.
echo [3/3] Uploading domain-check.js...
scp "%LOCAL_DIR%\domain-check.js" %SERVER%:%REMOTE_ROOT%/domain-check.js

echo.
echo [4/4] Uploading assets/images/korean-internet-domain-2015.png...
ssh %SERVER% "mkdir -p %REMOTE_ROOT%/assets/images"
scp "%LOCAL_DIR%\assets\images\korean-internet-domain-2015.png" %SERVER%:%REMOTE_ROOT%/assets/images/korean-internet-domain-2015.png

echo.
echo ========================================
echo Upload completed successfully!
echo Remote location: %REMOTE_ROOT%
echo ========================================
endlocal