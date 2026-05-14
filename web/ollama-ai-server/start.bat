@echo off
setlocal

if "%PORT%"=="" set PORT=3110
if "%HOST%"=="" set HOST=0.0.0.0
if "%OLLAMA_URL%"=="" set OLLAMA_URL=http://127.0.0.1:11434
if "%OLLAMA_MODEL%"=="" set OLLAMA_MODEL=kimi-k2.6:cloud

node "%~dp0server.js"
