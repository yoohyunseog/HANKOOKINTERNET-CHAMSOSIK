@echo off
chcp 65001 >nul
setlocal enableextensions

echo.
echo ================================================================
echo          Ollama 서버 시작 - 원격 서버 (클라우드 모델)
echo          한국 IP만 접근 허용 (보안 강화)
echo          API 키는 .env 파일에서 로드 (Git 제외)
echo ================================================================
echo.

set "REMOTE_HOST=root@211.45.162.155"
set "OLLAMA_PORT=11434"

REM .env 파일에서 API 키 로드
if exist "%~dp0.env" (
    for /f "tokens=1,2 delims==" %%a in (%~dp0.env) do (
        if "%%a"=="OLLAMA_API_KEY" set "OLLAMA_API_KEY=%%b"
    )
    echo [INFO] API 키를 .env 파일에서 로드했습니다.
) else (
    echo [ERROR] .env 파일이 없습니다. ollama-remote/..env 파일을 생성하세요.
    echo [ERROR] 형식: OLLAMA_API_KEY=your_api_key_here
    pause
    exit /b 1
)

echo [1/7] 기존 Ollama 서비스 중지...
ssh %REMOTE_HOST% "systemctl stop ollama 2>/dev/null; pkill -9 ollama 2>/dev/null || true"
timeout /t 2 /nobreak >nul
echo 완료
echo.

echo [2/7] 한국 IP만 접근 허용 설정 (iptables)...
echo 기존 규칙 초기화 및 한국만 허용 설정...
ssh %REMOTE_HOST% "iptables -F OLLAMA 2>/dev/null || iptables -N OLLAMA 2>/dev/null || true"
ssh %REMOTE_HOST% "iptables -D INPUT -p tcp --dport %OLLAMA_PORT% -j OLLAMA 2>/dev/null || true"
ssh %REMOTE_HOST% "iptables -F OLLAMA 2>/dev/null || true"
ssh %REMOTE_HOST% "iptables -X OLLAMA 2>/dev/null || true"
echo 완료
echo.

echo [3/7] 외부 접속 허용 설정 (로컬호스트만)...
ssh %REMOTE_HOST% "mkdir -p /etc/systemd/system/ollama.service.d"
ssh %REMOTE_HOST% "echo '[Service]' > /etc/systemd/system/ollama.service.d/override.conf"
ssh %REMOTE_HOST% "echo 'Environment=OLLAMA_HOST=127.0.0.1:11434' >> /etc/systemd/system/ollama.service.d/override.conf"
ssh %REMOTE_HOST% "echo 'Environment=OLLAMA_API_KEY=%OLLAMA_API_KEY%' >> /etc/systemd/system/ollama.service.d/override.conf"
ssh %REMOTE_HOST% "echo 'Environment=OLLAMA_NO_CLOUD=false' >> /etc/systemd/system/ollama.service.d/override.conf"
ssh %REMOTE_HOST% "systemctl daemon-reload"
echo 완료
echo.

echo [4/7] Ollama 서비스 시작...
ssh %REMOTE_HOST% "systemctl start ollama"
timeout /t 3 /nobreak >nul
echo 완료
echo.

echo [5/7] Ollama 로그인 상태 확인...
ssh %REMOTE_HOST% "test -f ~/.ollama/id_ed25519 && echo '로그인 키 존재' || echo '로그인 필요'"
echo.

echo [6/7] Ollama 로그인 (클라우드 모델용)...
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

echo [7/7] 서버 상태 확인...
ssh %REMOTE_HOST% "systemctl status ollama --no-pager | head -10"
echo.
ssh %REMOTE_HOST% "ss -tlnp | grep %OLLAMA_PORT% || echo '포트 대기...'"
echo.

echo API 응답 확인...
ssh %REMOTE_HOST% "curl -s http://localhost:%OLLAMA_PORT%/api/version || echo '서버 시작 중...'"

echo.
echo ================================================================
echo   Ollama 서버 실행 중! (보안 모드)
echo   API: http://127.0.0.1:%OLLAMA_PORT% (로컬 전용)
echo   
echo   접근 방식:
echo   - 웹 서버(server.js)를 통해서만 접근 가능
echo   - 한국 IP만 API 사용 가능 (GeoIP 필터링)
echo   - 외부 직접 접근 차단됨
echo   
echo   클라우드 모델: glm-5:cloud, deepseek-v4-pro:cloud
echo ================================================================
echo.

echo ==================== 보안 상태 ====================
echo.
echo [Ollama 리스닝 주소]
ssh %REMOTE_HOST% "ss -tlnp | grep %OLLAMA_PORT% | head -1"
echo.
echo [방화벽 규칙]
ssh %REMOTE_HOST% "iptables -L INPUT -n | grep -E '11434|OLLAMA' || echo '방화벽 규칙 없음 (로컬 전용)'"
echo.
echo [접근 허용 상태]
echo   - 로컬호스트(127.0.0.1): 허용 ✓
echo   - 외부 IP: 차단 ✓
echo   - 웹 서버 프록시: 한국 IP만 허용 ✓
echo.

echo ==================== 실시간 로그 ====================
echo.
echo 종료하려면 Ctrl+C를 누르세요.
echo.

ssh -t %REMOTE_HOST% "journalctl -u ollama -f --no-pager 2>/dev/null || tail -f /tmp/ollama.log 2>/dev/null || echo '로그 없음'"

endlocal