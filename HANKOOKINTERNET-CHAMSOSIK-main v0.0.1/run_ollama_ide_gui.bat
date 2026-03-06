@echo off
chcp 65001 >nul
title Ollama IDE GUI
cd /d "%~dp0"
py ide/ollama_ide_gui.py
pause
