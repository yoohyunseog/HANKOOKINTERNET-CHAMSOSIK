@echo off
setlocal
cd /d "%~dp0"
cd ..\..\..
cd ollama-ai-server
call run_virtual_server.bat
