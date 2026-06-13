@echo off
setlocal

REM Use UTF-8 so Korean folder names are handled correctly.
chcp 65001 >nul

set "SERVER=root@211.45.162.155"
set "REMOTE_BLOG_DIR=/var/www/chamsosik/blog"
set "LOCAL_BLOG_DIR=%~dp0"

if not exist "%LOCAL_BLOG_DIR%" (
  echo Local blog folder not found: %LOCAL_BLOG_DIR%
  exit /b 1
)

echo ========================================
echo   Blog Folder Upload Script
echo ========================================
echo.

echo [1/4] Ensure remote blog folder exists...
ssh %SERVER% "sudo mkdir -p %REMOTE_BLOG_DIR%/posts/2026/06"
if errorlevel 1 exit /b 1

echo [2/4] Upload blog files to temporary location...
ssh %SERVER% "rm -rf /tmp/blog_upload && mkdir -p /tmp/blog_upload"
if errorlevel 1 exit /b 1
scp -r "%LOCAL_BLOG_DIR%*" %SERVER%:/tmp/blog_upload/
if errorlevel 1 exit /b 1

echo [3/4] Move files to final location with sudo...
ssh %SERVER% "sudo rsync -a /tmp/blog_upload/ %REMOTE_BLOG_DIR%/ && sudo rm -rf /tmp/blog_upload"
if errorlevel 1 exit /b 1

echo [4/4] Set proper permissions...
ssh %SERVER% "sudo chown -R www-data:www-data %REMOTE_BLOG_DIR% && sudo chmod -R 755 %REMOTE_BLOG_DIR%"
if errorlevel 1 exit /b 1

echo.
echo ========================================
echo   Blog upload completed successfully!
echo ========================================
echo.
echo Blog URL: https://xn--9l4b4xi9r.com/blog/
echo.

endlocal
