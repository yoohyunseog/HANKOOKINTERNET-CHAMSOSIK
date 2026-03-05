@echo off
chcp 65001 >nul
cls

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  🤖 Ollama IDE 실행                                        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

py ide\ollama_chat.py
