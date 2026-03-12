@echo off
setlocal

REM Use UTF-8 so Korean folder names are handled correctly.
chcp 65001 >nul

set "SERVER=root@211.45.162.155"
set "REMOTE_ROOT=/var/www/chamsosik"
set "LOCAL_DIR=E:\Ai project\사이트\web\public\한국인터넷.한국\참소식.com"

if not exist "%LOCAL_DIR%" (
  echo Local folder not found: %LOCAL_DIR%
  exit /b 1
)

echo [1/3] Ensure remote folder exists...
ssh %SERVER% "sudo mkdir -p %REMOTE_ROOT%"

echo [2/3] Upload all files to %REMOTE_ROOT% ...
scp -r "%LOCAL_DIR%\*" %SERVER%:/tmp/chamsosik_upload/

echo [3/3] Move files to final location with sudo...
ssh %SERVER% "sudo rsync -a /tmp/chamsosik_upload/ %REMOTE_ROOT%/ && sudo rm -rf /tmp/chamsosik_upload"

echo Done.
endlocal
