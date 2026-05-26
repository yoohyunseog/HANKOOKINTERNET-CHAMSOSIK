@echo off
setlocal
cd /d "%~dp0"
set PC_PARTS_OLLAMA_MODEL=gemma4:31b-cloud
set PC_PARTS_AI_DISCOVERY=1
set PC_PARTS_COLLECT_BATCH_SIZE=3
set PC_PARTS_CHROME_TIMEOUT_MS=15000
node pc_parts_ai_loop.js --loop --collect-interval 10 --assembly-interval 0
pause
