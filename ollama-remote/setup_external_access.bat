@echo off
chcp 65001 >nul
setlocal enableextensions

echo.
echo ================================================================
echo          Ollama 외부 접속 설정 - 원격 서버
echo ================================================================
echo.

set "REMOTE_HOST=root@211.45.162.155"
set "OLLAMA_API_KEY=d8cf2811037b4791b2e36ffb4afee830.LrLvzfuvzutO7MLHciyiUtpq"

echo [1/4] systemd 설정 디렉토리 생성...
ssh %REMOTE_HOST% "mkdir -p /etc/systemd/system/ollama.service.d"
echo 완료
echo.

echo [2/4] 외부 접속 허용 설정 작성...
ssh %REMOTE_HOST% "cat > /etc/systemd/system/ollama.service.d/override.conf << 'EOF'
[Service]
Environment=OLLAMA_HOST=0.0.0.0:11434
Environment=OLLAMA_API_KEY=%OLLAMA_API_KEY%
EOF"
echo 완료
echo.

echo [3/4] systemd 재로드 및 Ollama 재시작...
ssh %REMOTE_HOST% "systemctl daemon-reload; systemctl restart ollama"
timeout /t 3 /nobreak >nul
echo 완료
echo.

echo [4/4] 서비스 상태 및 포트 확인...
ssh %REMOTE_HOST% "systemctl status ollama --no-pager | head -10; echo '---'; ss -tlnp | grep 11434"

echo.
echo ================================================================
echo   외부 접속 설정 완료!
echo   이제 http://211.45.162.155:11434 로 접속 가능
echo ================================================================
echo.

endlocal
pause