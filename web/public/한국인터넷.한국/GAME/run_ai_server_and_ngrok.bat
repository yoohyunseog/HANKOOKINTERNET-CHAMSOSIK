@echo off
setlocal
title Game AI Server + Ngrok
cd /d "%~dp0"

set "AI_SERVER_DIR=%~dp0..\..\..\ollama-ai-server"
set "NGROK_EXE=%~dp0ngrok.exe"
set "PORT=3110"
set "HOST=0.0.0.0"
set "NODE_ENV=production"
set "NARRATIVE_MEMORY_PERSIST=0"
set "OLLAMA_URL=http://127.0.0.1:11434"
set "OLLAMA_MODEL=kimi-k2.6:cloud"
set "NGROK_DOMAIN=cyclopedically-orthogenetic-sienna.ngrok-free.dev"
set "NGROK_URL=https://%NGROK_DOMAIN%"

if not exist "%NGROK_EXE%" (
  if exist "%~dp0ngrok-v3-stable-windows-amd64.zip" (
    echo Extracting ngrok...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%~dp0ngrok-v3-stable-windows-amd64.zip' -DestinationPath '%~dp0' -Force"
  )
)

if not exist "%NGROK_EXE%" (
  echo ngrok.exe was not found.
  echo Put ngrok.exe or ngrok-v3-stable-windows-amd64.zip in this GAME folder.
  pause
  exit /b 1
)

echo Closing old server on port %PORT% if it exists...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$c=Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue; if($c){$c | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}"

echo Closing old ngrok process from this GAME folder if it exists...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ng='%NGROK_EXE%'; Get-Process ngrok -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $ng } | ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }"

echo Starting Ollama AI proxy server...
start "Ollama AI Proxy Server" cmd /k "cd /d "%AI_SERVER_DIR%" && set "PORT=%PORT%" && set "HOST=%HOST%" && set "NODE_ENV=%NODE_ENV%" && set "NARRATIVE_MEMORY_PERSIST=%NARRATIVE_MEMORY_PERSIST%" && set "OLLAMA_URL=%OLLAMA_URL%" && set "OLLAMA_MODEL=%OLLAMA_MODEL%" && node server.js"

echo Waiting for server...
timeout /t 2 /nobreak >nul

echo Starting ngrok tunnel...
start "Ngrok AI Domain" cmd /k ""%NGROK_EXE%" http --url=%NGROK_URL% %PORT%"

echo.
echo Done.
echo AI API URL:
echo https://%NGROK_DOMAIN%
echo.
echo Open this to test:
echo https://%NGROK_DOMAIN%/health
echo.
pause
