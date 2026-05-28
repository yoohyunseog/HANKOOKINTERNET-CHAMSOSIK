@echo off
chcp 65001 >nul
setlocal enableextensions

echo.
echo ================================================================
echo          Ollama 서버 중지 - 원격 서버
echo ================================================================
echo.

set "REMOTE_HOST=root@211.45.162.155"

echo [1/2] Ollama 서비스 중지...
ssh %REMOTE_HOST% "systemctl stop ollama 2>/dev/null || pkill -f 'ollama serve'"

echo.
echo [2/2] 서버 상태 확인...
ssh %REMOTE_HOST% "pgrep -a ollama || echo 'Ollama 프로세스 없음'"

echo.
echo ================================================
echo  Ollama 서버가 중지되었습니다.
echo ================================================
echo.

endlocal
pause