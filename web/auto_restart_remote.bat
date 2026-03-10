@echo off
REM 원격 서버에 SSH로 접속하여 web 디렉토리로 이동 후 node web/restart_every_10min.js 자동 실행

set SERVER=211.45.162.155
set USER=root
set REMOTE_DIR=web
set REMOTE_CMD=node restart_every_10min.js

REM sshpass가 설치되어 있으면 비밀번호 자동 입력도 가능 (아래는 기본 SSH)
ssh %USER%@%SERVER% "cd %REMOTE_DIR% && %REMOTE_CMD%"

pause
