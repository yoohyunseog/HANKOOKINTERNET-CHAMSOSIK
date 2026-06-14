@echo off
setlocal EnableExtensions

REM Use UTF-8 so Korean folder names are handled correctly.
chcp 65001 >nul

set "SERVER=root@211.45.162.155"
set "REMOTE_BLOG_DIR=/var/www/chamsosik/blog"
set "LOCAL_BLOG_DIR=%~dp0"
set "STAGE_DIR=%TEMP%\chamsosik_blog_recent_1hour_upload"
set "REMOTE_STAGE_DIR=/tmp/chamsosik_blog_recent_1hour_upload"

echo ========================================
echo   Blog Recent 1 Hour Upload Script
echo ========================================
echo Local : %LOCAL_BLOG_DIR%
echo Server: %SERVER%
echo Remote: %REMOTE_BLOG_DIR%
echo Stage : %STAGE_DIR%
echo.

if not exist "%LOCAL_BLOG_DIR%" (
  echo [ERROR] Local blog folder not found: %LOCAL_BLOG_DIR%
  exit /b 1
)

echo [1/5] Build local staging folder from files modified in the last 1 hour...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$local=(Resolve-Path -LiteralPath $env:LOCAL_BLOG_DIR).Path;" ^
  "$stage=$env:STAGE_DIR;" ^
  "$cutoff=(Get-Date).AddHours(-1);" ^
  "Write-Host ('Cutoff: ' + $cutoff.ToString('yyyy-MM-dd HH:mm:ss'));" ^
  "if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force };" ^
  "New-Item -ItemType Directory -Path $stage -Force | Out-Null;" ^
  "$files=Get-ChildItem -LiteralPath $local -Recurse -File -Force | Where-Object { $_.FullName -notlike ($stage + '*') -and $_.LastWriteTime -ge $cutoff } | Sort-Object FullName;" ^
  "Write-Host ('Matched files: ' + @($files).Count);" ^
  "foreach ($file in $files) {" ^
  "  $rel=$file.FullName.Substring($local.Length).TrimStart('\','/');" ^
  "  $dest=Join-Path $stage $rel;" ^
  "  $destDir=Split-Path -Parent $dest;" ^
  "  if (!(Test-Path -LiteralPath $destDir)) { New-Item -ItemType Directory -Path $destDir -Force | Out-Null };" ^
  "  Copy-Item -LiteralPath $file.FullName -Destination $dest -Force;" ^
  "  Write-Host ('  + ' + $rel + '  [' + $file.LastWriteTime.ToString('HH:mm:ss') + ', ' + $file.Length + ' bytes]');" ^
  "};" ^
  "if (@($files).Count -eq 0) { Write-Host 'No files changed in the last 1 hour. Nothing to upload.'; exit 2 }"

if errorlevel 3 (
  echo [ERROR] Failed while building local staging folder.
  exit /b 1
)
if errorlevel 2 (
  echo.
  echo ========================================
  echo   No recent files to upload.
  echo ========================================
  exit /b 0
)

echo.
echo [2/5] Prepare remote temporary folder...
ssh %SERVER% "rm -rf %REMOTE_STAGE_DIR% && mkdir -p %REMOTE_STAGE_DIR%"
if errorlevel 1 (
  echo [ERROR] Failed to prepare remote temporary folder.
  exit /b 1
)

echo.
echo [3/5] Upload staged files to remote temporary folder...
scp -r "%STAGE_DIR%\." %SERVER%:%REMOTE_STAGE_DIR%/
if errorlevel 1 (
  echo [ERROR] Failed during scp upload.
  exit /b 1
)

echo.
echo [4/5] Merge staged files into remote blog folder...
ssh %SERVER% "sudo mkdir -p %REMOTE_BLOG_DIR% && sudo rsync -av %REMOTE_STAGE_DIR%/ %REMOTE_BLOG_DIR%/ && sudo rm -rf %REMOTE_STAGE_DIR%"
if errorlevel 1 (
  echo [ERROR] Failed while merging files on remote server.
  exit /b 1
)

echo.
echo [5/5] Set proper permissions...
ssh %SERVER% "sudo chown -R www-data:www-data %REMOTE_BLOG_DIR% && sudo chmod -R 755 %REMOTE_BLOG_DIR%"
if errorlevel 1 (
  echo [ERROR] Failed to set remote permissions.
  exit /b 1
)

echo.
echo Cleaning local staging folder...
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Test-Path -LiteralPath $env:STAGE_DIR) { Remove-Item -LiteralPath $env:STAGE_DIR -Recurse -Force }"

echo.
echo ========================================
echo   Recent 1 hour upload completed!
echo ========================================
echo Blog URL: https://xn--9l4b4xi9r.com/blog/
echo.

endlocal
exit /b 0
