@echo off
chcp 65001 >nul
setlocal enableextensions

echo.
echo ================================================
echo  PM2 설치 및 서버 자동 재시작 설정
echo ================================================
echo.

set "REMOTE_HOST=root@211.45.162.155"

echo [1/4] PM2 설치 중...
ssh %REMOTE_HOST% "npm install -g pm2"

echo.
echo [2/4] 로그 디렉토리 생성...
ssh %REMOTE_HOST% "mkdir -p ~/logs"

echo.
echo [3/4] PM2 설정 파일 업로드...
scp web\ecosystem.config.js %REMOTE_HOST%:~/web/

echo.
echo [4/4] PM2로 서버 시작...
ssh %REMOTE_HOST% "cd ~/web ; pm2 start ecosystem.config.js"

echo.
echo ================================================
echo  설치 완료!
echo ================================================
echo.
echo PM2 명령어:
echo   pm2 status          - 서버 상태 확인
echo   pm2 logs            - 로그 확인
echo   pm2 restart all     - 서버 재시작
echo   pm2 stop all        - 서버 중지
echo   pm2 delete all      - PM2에서 제거
echo   pm2 monit           - 실시간 모니터링
echo   pm2 save            - 설정 저장
echo   pm2 startup         - 시스템 부팅시 자동 시작
echo.

endlocal
