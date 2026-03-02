@echo off
setlocal

REM Use UTF-8 so Korean folder names are handled correctly.
chcp 65001 >nul

set "SERVER=root@211.45.162.155"
set "REMOTE_ROOT=/var/www/한국인터넷.한국"
set "LOCAL_DIR=E:\Ai project\사이트\web\public\한국인터넷.한국"

if not exist "%LOCAL_DIR%" (
  echo Local folder not found: %LOCAL_DIR%
  exit /b 1
)

echo [1/4] Create temporary upload directory...
ssh %SERVER% "rm -rf /tmp/hankookinternet_upload && mkdir -p /tmp/hankookinternet_upload"

echo [2/4] Ensure remote folder exists...
ssh %SERVER% "sudo mkdir -p %REMOTE_ROOT%"

echo [3/4] Upload all files to temp directory...
scp -r "%LOCAL_DIR%"/* %SERVER%:/tmp/hankookinternet_upload/

echo [4/4] Move files to final location with sudo...
ssh %SERVER% "sudo rsync -av --delete /tmp/hankookinternet_upload/ %REMOTE_ROOT%/ && sudo rm -rf /tmp/hankookinternet_upload"

echo.
echo ========================================
echo Upload completed successfully!
echo Remote location: %REMOTE_ROOT%
echo ========================================
endlocal
