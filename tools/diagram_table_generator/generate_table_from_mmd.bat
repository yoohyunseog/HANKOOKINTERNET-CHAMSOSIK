@echo off
chcp 65001 >nul
setlocal

rem Convert website_diagram.mmd to website_from_diagram.json using Ollama

set "OLLAMA_MODEL=gpt-oss:120b-cloud"
set "OLLAMA_URL=http://localhost:11434"

set "INPUT_MMD=E:\Ai project\사이트\web\public\한국인터넷.한국\참소식.com\website_diagram.mmd"
set "OUTPUT_JSON=E:\Ai project\사이트\web\public\한국인터넷.한국\참소식.com\website_from_diagram.json"
set "PYTHON_EXE=python"

if exist "E:\python_env\Scripts\activate.bat" (
    call "E:\python_env\Scripts\activate.bat"
)

echo [1/2] Input: %INPUT_MMD%
echo [2/2] Output: %OUTPUT_JSON%
echo Model: %OLLAMA_MODEL%

%PYTHON_EXE% "%~dp0generate_table_from_mmd.py" "%INPUT_MMD%" "%OUTPUT_JSON%" "%OLLAMA_MODEL%"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo Failed with exit code %EXIT_CODE%.
    endlocal & exit /b %EXIT_CODE%
)

echo Done.
endlocal & exit /b 0
