@echo off
setlocal
title Ngrok Tunnel for Ollama AI Proxy
cd /d "%~dp0"

set NGROK_EXE=%~dp0ngrok.exe

if not exist "%NGROK_EXE%" (
  if exist "%~dp0ngrok-v3-stable-windows-amd64.zip" (
    echo Extracting ngrok...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%~dp0ngrok-v3-stable-windows-amd64.zip' -DestinationPath '%~dp0' -Force"
  )
)

if not exist "%NGROK_EXE%" (
  echo ngrok.exe was not found in this folder.
  echo Put ngrok.exe or ngrok-v3-stable-windows-amd64.zip in this GAME folder.
  pause
  exit /b 1
)

echo.
echo If this is your first run, register your token once:
echo "%NGROK_EXE%" config add-authtoken YOUR_TOKEN
echo.
echo Starting tunnel for local AI server on port 3110...
echo URL: https://cyclopedically-orthogenetic-sienna.ngrok-free.dev
echo.

"%NGROK_EXE%" http --url=cyclopedically-orthogenetic-sienna.ngrok-free.dev 3110
