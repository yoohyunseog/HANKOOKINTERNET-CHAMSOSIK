@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "1_fetch_data.ps1"