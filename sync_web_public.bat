@echo off
setlocal

REM Use UTF-8 so Korean folder names are handled correctly.
chcp 65001 >nul

set "SERVER=root@211.45.162.155"
set "REMOTE_BASE=/root/web/public"
set "LOCAL_DIR=E:\Ai project\사이트\web\public\한국인터넷.한국"

if not exist "%LOCAL_DIR%" (
  echo Local folder not found: %LOCAL_DIR%
  exit /b 1
)

echo [1/3] Ensure remote folder exists...
ssh %SERVER% "mkdir -p %REMOTE_BASE%/한국인터넷.한국"

echo [2/3] Remove all other folders under %REMOTE_BASE% except 한국인터넷.한국...
ssh %SERVER% "find %REMOTE_BASE% -mindepth 1 -maxdepth 1 ! -name '한국인터넷.한국' -exec rm -rf {} +"

echo [3/3] Upload current 한국인터넷.한국 folder...
scp -r "%LOCAL_DIR%" %SERVER%:%REMOTE_BASE%/

echo Done.
endlocal
