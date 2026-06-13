@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%generate_rss.ps1"

if errorlevel 1 (
  echo.
  echo RSS generation failed.
  exit /b 1
)

echo.
echo RSS generation completed.
exit /b 0
