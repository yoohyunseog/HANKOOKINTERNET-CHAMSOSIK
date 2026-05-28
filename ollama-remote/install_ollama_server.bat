@echo off
chcp 65001 >nul
setlocal enableextensions

echo.
echo ================================================================
echo          Ollama 설치 - 원격 서버 (Linux)
echo ================================================================
echo.

set "REMOTE_HOST=root@211.45.162.155"

echo [1/3] Ollama 설치 스크립트 다운로드 및 실행...
echo 서버: %REMOTE_HOST%
echo.

ssh -t %REMOTE_HOST% "curl -fsSL https://ollama.com/install.sh | sh"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [오류] Ollama 설치 실패
    pause
    exit /b 1
)

echo.
echo [2/3] Ollama 버전 확인...
ssh %REMOTE_HOST% "ollama --version"

echo.
echo [3/3] Ollama 서비스 상태 확인...
ssh %REMOTE_HOST% "systemctl status ollama 2>/dev/null || echo '서비스가 아직 시작되지 않음'"

echo.
echo ================================================
echo  설치 완료!
echo  - 실행: run_ollama_server_remote.bat
echo  - 중지: stop_ollama_server_remote.bat
echo ================================================
echo.

endlocal
pause