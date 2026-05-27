@echo off
setlocal

title Cloudflare Quick Tunnel - Chamsosik AI

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_cloudflare_quick_tunnel_ai.ps1"

echo.
echo Tunnel stopped.
pause
