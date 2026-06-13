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
echo   Blog HTML/JS/CSS Upload Script
echo ========================================
echo.

echo [1/4] Create temporary upload directory...
ssh %SERVER% "rm -rf /tmp/blog_upload && mkdir -p /tmp/blog_upload"
if errorlevel 1 exit /b 1

echo [2/4] Upload HTML, JS, CSS, JSON files (including subfolders)...
REM Upload root level files
for %%f in ("%LOCAL_BLOG_DIR%*.html" "%LOCAL_BLOG_DIR%*.js" "%LOCAL_BLOG_DIR%*.css" "%LOCAL_BLOG_DIR%*.json") do (
  if exist "%%f" (
    echo Uploading: %%~nxf
    scp "%%f" %SERVER%:/tmp/blog_upload/
    if errorlevel 1 exit /b 1
  )
)

REM Upload files from subfolders (js, css, assets, posts, etc.)
for /d %%d in ("%LOCAL_BLOG_DIR%*") do (
  if exist "%%d\" (
    echo Processing folder: %%~nxd
    ssh %SERVER% "mkdir -p /tmp/blog_upload/%%~nxd"
    
    REM Upload all HTML, JS, CSS, JSON files in subfolder
    for %%f in ("%%d\*.html" "%%d\*.js" "%%d\*.css" "%%d\*.json") do (
      if exist "%%f" (
        echo   Uploading: %%~nxd/%%~nxf
        scp "%%f" %SERVER%:/tmp/blog_upload/%%~nxd/
        if errorlevel 1 exit /b 1
      )
    )
    
    REM Recursively handle nested folders (e.g., assets/images)
    for /r "%%d" %%f in (*.html *.js *.css) do (
      for %%p in ("%%~dpf.") do (
        set "relpath=%%~pnxf"
        setlocal enabledelayedexpansion
        set "relpath=!relpath:%LOCAL_BLOG_DIR%=!"
        if "!relpath!" neq "" (
          echo   Uploading: !relpath!
          ssh %SERVER% "mkdir -p /tmp/blog_upload/!relpath:\=/!"
          scp "%%f" %SERVER%:/tmp/blog_upload/!relpath:\=/!
        )
        endlocal
      )
    )
  )
)

echo [3/4] Move files to final location with sudo...
ssh %SERVER% "sudo rsync -a --delete /tmp/blog_upload/ %REMOTE_BLOG_DIR%/ 2>/dev/null; sudo rm -rf /tmp/blog_upload"
if errorlevel 1 exit /b 1

echo [4/4] Set proper permissions...
ssh %SERVER% "sudo chown -R www-data:www-data %REMOTE_BLOG_DIR% && sudo chmod -R 755 %REMOTE_BLOG_DIR%"
if errorlevel 1 exit /b 1

echo.
echo ========================================
echo   Upload completed successfully!
echo ========================================
echo.
echo Blog URL: https://xn--9l4b4xi9r.com/blog/
echo.

endlocal