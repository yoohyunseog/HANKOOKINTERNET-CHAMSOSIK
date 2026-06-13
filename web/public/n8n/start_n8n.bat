@echo off
cd /d "%~dp0"
echo Starting n8n...
echo n8n will be available at: http://localhost:5678
echo.
npx n8n start
pause