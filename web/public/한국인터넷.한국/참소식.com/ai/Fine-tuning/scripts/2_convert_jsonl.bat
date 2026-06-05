@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "2_convert_jsonl.ps1"