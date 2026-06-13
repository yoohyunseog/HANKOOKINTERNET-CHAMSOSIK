@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul

set "PYTHONIOENCODING=utf-8"

echo ========================================
echo NB Video Analyzer RSS Feed Generator
echo ========================================
echo.
echo This script generates RSS feed for dlvr.it integration
echo Output: rss.xml
echo.

py -u generate_rss.py

echo.
echo RSS feed generation complete!
echo.
echo RSS Feed URL: https://www.xn--9l4b4xi9r.com/NBVideoAnalyzer/rss.xml
echo.
echo Next steps:
echo 1. Upload rss.xml to your web server
echo 2. Add the RSS feed URL to dlvr.it
echo 3. Configure dlvr.it to post to your social media accounts
echo.

pause