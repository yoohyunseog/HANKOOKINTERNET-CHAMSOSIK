@echo off
setlocal

chcp 65001 >nul

set "PAUSE_ON_EXIT=1"
if /I "%~1"=="-NoPause" set "PAUSE_ON_EXIT=0"

echo.
echo ============================================================
echo  Chamsosik Blog Post Common Assets Checker
echo ============================================================
echo.
echo Folder:
echo   %~dp0
echo.
echo What this checks:
echo   - favicon link
echo   - apple-touch-icon link
echo   - Google AdSense loader
echo   - view-tracker.js
echo   - BlogViewTracker.trackPostVisit() call
echo.
echo Tip:
echo   add_blog_post_common_assets.bat -DryRun
echo   add_blog_post_common_assets.bat
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0add_blog_post_common_assets.ps1" %*
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo ============================================================
if "%EXIT_CODE%"=="0" (
  echo  Finished successfully.
) else (
  echo  Finished with error code %EXIT_CODE%.
)
echo ============================================================
echo.

if "%PAUSE_ON_EXIT%"=="1" pause
exit /b %EXIT_CODE%
