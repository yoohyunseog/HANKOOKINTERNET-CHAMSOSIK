@echo off
setlocal
title Ollama AI Proxy Server
cd /d "%~dp0"

if not exist logs mkdir logs

set PORT=3110
set HOST=0.0.0.0
set OLLAMA_URL=http://127.0.0.1:11434
set OLLAMA_MODEL=kimi-k2.6:cloud

echo ========================================
echo Ollama AI Proxy Server
echo ========================================
echo HOST=%HOST%
echo PORT=%PORT%
echo OLLAMA_URL=%OLLAMA_URL%
echo OLLAMA_MODEL=%OLLAMA_MODEL%
echo.
echo Health: http://127.0.0.1:%PORT%/health
echo Chat:   http://127.0.0.1:%PORT%/api/chat
echo Game:   http://127.0.0.1:%PORT%/api/game-ai-advice
echo.

node server.js

echo.
echo Server stopped.
pause
