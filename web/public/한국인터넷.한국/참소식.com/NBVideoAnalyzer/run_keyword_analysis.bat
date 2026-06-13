@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
echo ========================================
echo Keyword Analysis Bot
echo ========================================
echo.
echo Analyzing all keywords in: keywords\
echo.
set YOUTUBE_SEARCH_ENABLED=false
py analyze_keywords_bot.py
echo.
pause
