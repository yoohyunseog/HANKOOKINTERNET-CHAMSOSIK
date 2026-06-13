@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

set "PYTHONIOENCODING=utf-8"
set "YOUTUBE_SEARCH_ENABLED=true"
set "YOUTUBE_SEARCH_RESULTS=50"
set "YOUTUBE_MAX_KEYWORDS=1"
set "YOUTUBE_SEARCH_TIMEOUT_SECONDS=180"

echo ========================================
echo YouTube N/B Analysis
echo ========================================
echo.
echo Settings:
echo   YOUTUBE_SEARCH_ENABLED=%YOUTUBE_SEARCH_ENABLED%
echo   YOUTUBE_SEARCH_RESULTS=%YOUTUBE_SEARCH_RESULTS%
echo   YOUTUBE_MAX_KEYWORDS=%YOUTUBE_MAX_KEYWORDS%
echo   YOUTUBE_SEARCH_TIMEOUT_SECONDS=%YOUTUBE_SEARCH_TIMEOUT_SECONDS%
echo.
echo Log tags:
echo   START CONFIG FILE KEYWORD YOUTUBE VIDEO NB SUMMARY SAVE
echo.

py -u analyze_keywords_bot.py

echo.
pause
