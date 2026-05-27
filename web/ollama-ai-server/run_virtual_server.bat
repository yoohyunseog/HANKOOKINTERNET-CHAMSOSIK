@echo off
setlocal
title Ollama AI Proxy Server
cd /d "%~dp0"

if not exist logs mkdir logs

set PORT=3110
set HOST=0.0.0.0
set OLLAMA_URL=http://127.0.0.1:11434
set OLLAMA_MODEL=kimi-k2.6:cloud
set OLLAMA_API_KEY=d8cf2811037b4791b2e36ffb4afee830.LrLvzfuvzutO7MLHciyiUtpq

echo ========================================
echo Ollama AI Proxy Server
echo ========================================
echo HOST=%HOST%
echo PORT=%PORT%
echo OLLAMA_URL=%OLLAMA_URL%
echo OLLAMA_MODEL=%OLLAMA_MODEL%
if "%OLLAMA_API_KEY%"=="" (
  echo OLLAMA_API_KEY=d8cf2811037b4791b2e36ffb4afee830.LrLvzfuvzutO7MLHciyiUtpq
) else (
  echo OLLAMA_API_KEY=set
)
echo.
echo Health: http://127.0.0.1:%PORT%/health
echo Chat:   http://127.0.0.1:%PORT%/api/chat
echo Search: http://127.0.0.1:%PORT%/api/web-search
echo Search Chat: http://127.0.0.1:%PORT%/api/search-chat
echo Game:   http://127.0.0.1:%PORT%/api/game-ai-advice
echo.

node server.js

echo.
echo Server stopped.
pause
