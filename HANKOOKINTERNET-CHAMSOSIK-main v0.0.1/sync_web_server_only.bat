@echo off
setlocal

REM Use UTF-8 so Korean folder names are handled correctly.
chcp 65001 >nul

set "SERVER=root@211.45.162.155"
set "REMOTE_BASE=/root"
set "LOCAL_DIR=E:\Ai project\사이트\web"

if not exist "%LOCAL_DIR%" (
  echo Local folder not found: %LOCAL_DIR%
  exit /b 1
)

echo [1/2] Ensure remote folder exists...
ssh %SERVER% "mkdir -p %REMOTE_BASE%/web"

echo [2/2] Upload server files only to %REMOTE_BASE%/web...
scp "%LOCAL_DIR%\server.js" %SERVER%:%REMOTE_BASE%/web/
scp "%LOCAL_DIR%\storage.js" %SERVER%:%REMOTE_BASE%/web/
scp "%LOCAL_DIR%\calculate.js" %SERVER%:%REMOTE_BASE%/web/
scp "%LOCAL_DIR%\package.json" %SERVER%:%REMOTE_BASE%/web/
scp "%LOCAL_DIR%\package-lock.json" %SERVER%:%REMOTE_BASE%/web/

echo Done.
endlocal
