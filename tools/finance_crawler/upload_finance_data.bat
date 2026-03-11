@echo off
setlocal

REM Use UTF-8 so Korean folder names are handled correctly.
chcp 65001 >nul

set "SERVER=root@211.45.162.155"
set "REMOTE_ROOT=/var/www/chamsosik"

set "LOCAL_FILE=E:\Ai project\사이트\tools\finance_crawler\realtime_finance_data.json"
set "COPY_TARGET=E:\Ai project\사이트\web\public\한국인터넷.한국\참소식.com\realtime_finance_data.json"


if not exist "%LOCAL_FILE%" (
  echo Local file not found: %LOCAL_FILE%
  exit /b 1
)

REM Copy to local web/public/한국인터넷.한국/참소식.com
copy /Y "%LOCAL_FILE%" "%COPY_TARGET%"
if errorlevel 1 (
  echo Failed to copy to %COPY_TARGET%
  exit /b 1
)

echo [1/2] Ensure remote folder exists...
ssh %SERVER% "sudo mkdir -p %REMOTE_ROOT%"

echo [2/2] Upload finance data file...
scp "%LOCAL_FILE%" %SERVER%:%REMOTE_ROOT%/

echo Done.
endlocal
