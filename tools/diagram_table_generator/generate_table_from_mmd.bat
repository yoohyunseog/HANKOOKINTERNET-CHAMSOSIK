@echo off
chcp 65001
REM Mermaid .mmd 파일을 OLLAMA AI로 .table 변환
REM OLLAMA_MODEL=gemma3:1b 사용

setlocal
set OLLAMA_MODEL=gpt-oss:120b-cloud
set OLLAMA_URL=http://localhost:11434

set INPUT_MMD=E:\Ai project\사이트\web\public\한국인터넷.한국\참소식.com\website_diagram.mmd
set OUTPUT_JSON=..\..\web\public\한국인터넷.한국\참소식.com\website_from_diagram.json
call E:\python_env\Scripts\activate.bat

REM Ollama API 호출 (Python 스크립트로 처리)
python "%~dp0generate_table_from_mmd.py" "%INPUT_MMD%" "%OUTPUT_JSON%" "%OLLAMA_MODEL%"
endlocal
