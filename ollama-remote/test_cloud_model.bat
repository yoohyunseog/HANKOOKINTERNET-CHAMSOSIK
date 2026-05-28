@echo off
chcp 65001 >nul
setlocal enableextensions

echo.
echo ================================================================
echo          Ollama 클라우드 모델 테스트 - 원격 서버
echo ================================================================
echo.

set "REMOTE_HOST=root@211.45.162.155"
set "OLLAMA_PORT=11434"

echo [1/4] Ollama 서버 상태 확인...
ssh %REMOTE_HOST% "systemctl status ollama --no-pager | head -5"
echo.

echo [2/4] 사용 가능한 모델 목록...
ssh %REMOTE_HOST% "ollama list"
echo.

echo [3/4] 클라우드 모델 테스트 (glm-5:cloud)...
echo 질문: "안녕하세요"
echo.
ssh %REMOTE_HOST% "echo '안녕하세요' | timeout 60 ollama run glm-5:cloud"
echo.

echo [4/4] API 직접 테스트...
ssh %REMOTE_HOST% "curl -s http://localhost:%OLLAMA_PORT%/api/generate -d '{\"model\":\"glm-5:cloud\",\"prompt\":\"hi\",\"stream\":false}' | head -c 500"
echo.

echo ================================================================
echo   테스트 완료
echo   클라우드 모델이 작동하지 않으면 로그인이 필요합니다.
echo   로그인: login_ollama_remote.bat
echo ================================================================
echo.

endlocal
pause