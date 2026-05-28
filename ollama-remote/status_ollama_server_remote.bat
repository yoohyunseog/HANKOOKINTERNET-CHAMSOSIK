@echo off
chcp 65001 >nul
setlocal enableextensions

echo.
echo ================================================================
echo          Ollama 서버 상태 확인 - 원격 서버
echo ================================================================
echo.

set "REMOTE_HOST=root@211.45.162.155"
set "OLLAMA_PORT=11434"

echo [1/4] 디스크 용량 확인...
ssh %REMOTE_HOST% "df -h / | tail -1"

echo.
echo [2/4] Ollama 설치 여부 확인...
ssh %REMOTE_HOST% "which ollama && ollama --version || echo 'Ollama 미설치'"

echo.
echo [3/4] Ollama 서비스 상태...
ssh %REMOTE_HOST% "systemctl status ollama 2>/dev/null || echo '서비스 미실행'"

echo.
echo [4/4] API 응답 확인...
ssh %REMOTE_HOST% "curl -s http://localhost:%OLLAMA_PORT%/api/tags 2>/dev/null | head -c 300 || echo 'API 응답 없음'"

echo.
echo ================================================================
echo   상태 확인 완료
echo ================================================================
echo.

endlocal
pause