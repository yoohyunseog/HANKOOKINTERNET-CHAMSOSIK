@echo off
setlocal

REM Use UTF-8 so Korean folder names are handled correctly.
chcp 65001 >nul

set "SERVER=root@211.45.162.155"
set "REMOTE_BASE=/root/web/public/한국인터넷.한국/data"
set "LOCAL_BASE=E:\Ai project\사이트\data"

if not exist "%LOCAL_BASE%" (
  echo Local folder not found: %LOCAL_BASE%
  exit /b 1
)

echo [1/3] Ensure remote data folder exists...
ssh %SERVER% "mkdir -p %REMOTE_BASE%/nb_max %REMOTE_BASE%/nb_min"

echo [2/3] Upload nb_max...
scp -r "%LOCAL_BASE%\nb_max" %SERVER%:%REMOTE_BASE%/

echo [3/3] Upload nb_min...
scp -r "%LOCAL_BASE%\nb_min" %SERVER%:%REMOTE_BASE%/

echo Done.
endlocal