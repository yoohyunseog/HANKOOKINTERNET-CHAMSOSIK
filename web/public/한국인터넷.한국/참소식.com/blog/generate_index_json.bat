@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ========================================
echo Generate blog posts/index.json
echo ========================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0generate_index_json.ps1"
if errorlevel 1 (
  echo.
  echo [ERROR] Failed to generate posts/index.json
  pause
  exit /b 1
)

echo.
echo Done.
pause
exit /b 0
