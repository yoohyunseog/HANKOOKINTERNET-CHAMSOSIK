@echo off
chcp 65001 >nul
echo ============================================
echo    Ollama 로컬 번역 실행
echo ============================================
echo.

cd /d "%~dp0.."

echo 이 스크립트는 Ollama 로컬 모델을 사용하여
echo 한국어 번역을 생성합니다.
echo.
echo [사전 요구사항]
echo   1. Ollama 설치 (https://ollama.ai)
echo   2. 한국어 번역 모델 다운로드:
echo      ollama pull qwen2:7b
echo      또는
echo      ollama pull llama3
echo.

echo Ollama가 실행 중인지 확인 중...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Ollama가 실행 중이지 않습니다.
    echo Ollama를 먼저 실행하세요: ollama serve
    pause
    exit /b 1
)

echo Ollama가 실행 중입니다.
echo.

echo 사용 가능한 모델:
curl -s http://localhost:11434/api/tags
echo.

set /p model="사용할 모델명 (기본: qwen2:7b): "
if "%model%"=="" set model=qwen2:7b

echo.
echo 모델: %model%
echo.

.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'scripts'); from translate_korean import main; main()" -- --method ollama --model %model%

echo.
echo ============================================
echo    번역 완료!
echo ============================================
pause