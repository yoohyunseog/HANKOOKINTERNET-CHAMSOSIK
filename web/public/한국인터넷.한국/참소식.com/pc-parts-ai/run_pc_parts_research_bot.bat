@echo off
setlocal
cd /d "%~dp0"
set PC_PARTS_OLLAMA_MODEL=gemma4:31b-cloud
node pc_parts_ai_loop.js --loop --collect-interval 1800 --assembly-interval 60
pause
