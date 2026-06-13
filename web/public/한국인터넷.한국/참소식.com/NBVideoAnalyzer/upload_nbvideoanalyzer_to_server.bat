@echo off
setlocal

REM Use UTF-8 so Korean folder names are handled correctly.
chcp 65001 >nul

set "SERVER=root@211.45.162.155"
set "LOCAL_DIR=%~dp0"
set "REMOTE_DIR=/var/www/chamsosik/NBVideoAnalyzer"

echo ========================================
echo NBVideoAnalyzer web server upload
echo ========================================
echo.

if not exist "%LOCAL_DIR%" (
  echo Local folder not found:
  echo %LOCAL_DIR%
  echo.
  pause
  exit /b 1
)

where ssh >nul 2>nul
if errorlevel 1 (
  echo ssh command not found. Install OpenSSH Client first.
  echo.
  pause
  exit /b 1
)

where scp >nul 2>nul
if errorlevel 1 (
  echo scp command not found. Install OpenSSH Client first.
  echo.
  pause
  exit /b 1
)

echo Local:
echo %LOCAL_DIR%
echo.
echo Remote:
echo %SERVER%:%REMOTE_DIR%
echo.

echo [1/3] Ensure remote folder exists...
ssh %SERVER% "sudo mkdir -p %REMOTE_DIR%"
if errorlevel 1 goto :fail

echo [2/3] Upload files to temporary location...
ssh %SERVER% "rm -rf /tmp/nbvideo_upload && mkdir -p /tmp/nbvideo_upload"
if errorlevel 1 goto :fail
scp -r "%LOCAL_DIR%*" %SERVER%:/tmp/nbvideo_upload/
if errorlevel 1 goto :fail

echo [3/3] Move files to final location with sudo...
ssh %SERVER% "sudo rsync -a /tmp/nbvideo_upload/ %REMOTE_DIR%/ && sudo rm -rf /tmp/nbvideo_upload"
if errorlevel 1 goto :fail

echo.
echo Upload complete.
echo URL path: /NBVideoAnalyzer/
echo.
pause
exit /b 0

:fail
echo.
echo Upload failed. Check SSH access, server address, or network connection.
echo.
pause
exit /b 1

endlocal