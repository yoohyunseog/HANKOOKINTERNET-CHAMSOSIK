@echo off
chcp 65001 >nul
setlocal enableextensions

echo.
echo ================================================================
echo          Ollama 서버 시작 - 원격 서버 (클라우드 모델)
echo ================================================================
echo.

set "REMOTE_HOST=root@211.45.162.155"
set "OLLAMA_PORT=11434"
set "OLLAMA_API_KEY=d8cf2811037b4791b2e36ffb4afee830.LrLvzfuvzutO7MLHciyiUtpq"

echo [1/6] 기존 Ollama 서비스 중지...
ssh %REMOTE_HOST% "systemctl stop ollama 2>/dev/null; pkill -9 ollama 2>/dev/null || true"
timeout /t 2 /nobreak >nul
echo 완료
echo.

echo [2/6] 외부 접속 허용 설정...
ssh %REMOTE_HOST% "mkdir -p /etc/systemd/system/ollama.service.d"
ssh %REMOTE_HOST% "echo '[Service]' > /etc/systemd/system/ollama.service.d/override.conf"
ssh %REMOTE_HOST% "echo 'Environment=OLLAMA_HOST=0.0.0.0:11434' >> /etc/systemd/system/ollama.service.d/override.conf"
ssh %REMOTE_HOST% "echo 'Environment=OLLAMA_API_KEY=%OLLAMA_API_KEY%' >> /etc/systemd/system/ollama.service.d/override.conf"
ssh %REMOTE_HOST% "systemctl daemon-reload"
echo 완료
echo.

echo [3/6] Ollama 서비스 시작...
ssh %REMOTE_HOST% "systemctl start ollama"
timeout /t 3 /nobreak >nul
echo 완료
echo.

echo [4/6] Ollama 로그인 상태 확인...
ssh %REMOTE_HOST% "test -f ~/.ollama/id_ed25519 && echo '로그인 키 존재' || echo '로그인 필요'"
echo.

echo [5/6] Ollama 로그인 (클라우드 모델용)...
echo 클라우드 모델 사용을 위해 로그인이 필요합니다.
echo.
echo 로그인 URL이 표시되면 브라우저에서 열어주세요.
echo Google/GitHub로 로그인 후 "Device Connected Successfully"가 표시되면
echo 이 창에서 Enter를 눌러주세요.
echo.
echo ================================================================
echo.

ssh -t %REMOTE_HOST% "ollama login"

echo.
echo 로그인 완료! 계속하려면 Enter를 누르세요...
pause >nul
echo.

echo [6/6] 서버 상태 확인...
ssh %REMOTE_HOST% "systemctl status ollama --no-pager | head -10"
echo.
ssh %REMOTE_HOST% "ss -tlnp | grep %OLLAMA_PORT% || echo '포트 대기...'"
echo.

echo API 응답 확인...
ssh %REMOTE_HOST% "curl -s http://localhost:%OLLAMA_PORT%/api/version || echo '서버 시작 중...'"

echo.
echo ================================================================
echo   Ollama 서버 실행 중!
echo   API: http://211.45.162.155:%OLLAMA_PORT%
echo   클라우드 모델: glm-5:cloud, gemma4:31b-cloud
echo ================================================================
echo.

echo ==================== 실시간 로그 ====================
echo.

ssh -t %REMOTE_HOST% "journalctl -u ollama -f --no-pager 2>/dev/null || tail -f /tmp/ollama.log 2>/dev/null || echo '로그 없음'"

endlocal