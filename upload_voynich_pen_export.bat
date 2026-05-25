@echo off
setlocal

REM Upload only the Voynich pen export folder.
chcp 65001 >nul

set "SERVER=root@211.45.162.155"
set "LOCAL_DIR=E:\Ai project\사이트\web\public\한국인터넷.한국\보이니치\pen-export-emzyZae"
set "REMOTE_DIR=/var/www/한국인터넷.한국/보이니치/pen-export-emzyZae"
set "REMOTE_TMP=/tmp/voynich_pen_export_upload"

if not exist "%LOCAL_DIR%" (
  echo Local folder not found: %LOCAL_DIR%
  exit /b 1
)

echo [1/5] Remove remote temporary folder...
ssh %SERVER% "rm -rf %REMOTE_TMP%"
if errorlevel 1 exit /b 1

echo [2/5] Create remote temporary folder...
ssh %SERVER% "mkdir -p %REMOTE_TMP%"
if errorlevel 1 exit /b 1

echo [3/5] Upload folder contents...
scp -r "%LOCAL_DIR%\*" %SERVER%:%REMOTE_TMP%/
if errorlevel 1 exit /b 1

echo [4/5] Mirror to final remote folder...
ssh %SERVER% "sudo mkdir -p '%REMOTE_DIR%'"
if errorlevel 1 exit /b 1
ssh %SERVER% "sudo rsync -a --delete %REMOTE_TMP%/ '%REMOTE_DIR%/'"
if errorlevel 1 exit /b 1

echo [5/5] Clean temporary folder...
ssh %SERVER% "rm -rf %REMOTE_TMP%"
if errorlevel 1 exit /b 1

echo.
echo Upload completed.
echo Local : %LOCAL_DIR%
echo Remote: %REMOTE_DIR%
endlocal
