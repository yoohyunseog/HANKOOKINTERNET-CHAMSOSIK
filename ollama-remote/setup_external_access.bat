@echo off
chcp 65001 >nul
setlocal enableextensions

echo.
echo ================================================================
echo          Ollama 외부 접속 설정 - 원격 서버 (보안 모드)
echo          한국 IP만 접근 허용
echo ================================================================
echo.

set "REMOTE_HOST=root@211.45.162.155"
set "OLLAMA_API_KEY=d8cf2811037b4791b2e36ffb4afee830.LrLvzfuvzutO7MLHciyiUtpq"

echo [1/5] systemd 설정 디렉토리 생성...
ssh %REMOTE_HOST% "mkdir -p /etc/systemd/system/ollama.service.d"
echo 완료
echo.

echo [2/5] 보안 설정 (로컬호스트만 리스닝)...
ssh %REMOTE_HOST% "cat > /etc/systemd/system/ollama.service.d/override.conf << 'EOF'
[Service]
Environment=OLLAMA_HOST=127.0.0.1:11434
Environment=OLLAMA_API_KEY=%OLLAMA_API_KEY%
Environment=OLLAMA_NO_CLOUD=false
EOF"
echo 완료
echo.

echo [3/5] systemd 재로드 및 Ollama 재시작...
ssh %REMOTE_HOST% "systemctl daemon-reload; systemctl restart ollama"
timeout /t 3 /nobreak >nul
echo 완료
echo.

echo [4/5] 서비스 상태 및 포트 확인...
ssh %REMOTE_HOST% "systemctl status ollama --no-pager | head -10; echo '---'; ss -tlnp | grep 11434"

echo.
echo [5/5] 보안 상태 확인...
echo.
echo [리스닝 주소]
ssh %REMOTE_HOST% "ss -tlnp | grep 11434 | head -1"
echo.
echo [접근 정책]
echo   - Ollama: 127.0.0.1:11434 (로컬 전용)
echo   - 웹 서버 프록시: 한국 IP만 허용
echo   - 외부 직접 접근: 차단
echo.

echo ================================================================
echo   보안 설정 완료!
echo   
echo   접근 방식:
echo   - 웹 서버(server.js)를 통해서만 접근 가능
echo   - 한국 IP만 API 사용 가능 (GeoIP 필터링)
echo   - 외부 직접 접근 차단됨
echo   
echo   웹 서버 API: https://한국인터넷.한국/api/ollama-*
echo ================================================================
echo.

endlocal
pause