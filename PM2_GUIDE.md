# PM2 자동 재시작 설정 가이드

## 개요
서버가 갑자기 다운될 때 자동으로 재시작하도록 PM2(Process Manager 2)를 설정합니다.

## PM2 자동 재시작 기능
- ✅ 프로세스 크래시 시 자동 재시작
- ✅ 메모리 제한 초과 시 자동 재시작 (500MB 설정)
- ✅ 최소 가동 시간 체크 (10초)
- ✅ 재시작 시도 제한 (1분당 10회)
- ✅ Exponential backoff (재시작 실패 시 대기 시간 증가)
- ✅ 매일 새벽 4시 자동 재시작 (cron)

## 설치 방법

### 방법 1: 자동 설치 (추천)
```batch
setup_pm2.bat
```

### 방법 2: 수동 설치
```bash
# 1. SSH 접속
ssh root@211.45.162.155

# 2. PM2 설치
npm install -g pm2

# 3. 로그 디렉토리 생성
mkdir -p ~/logs

# 4. ecosystem.config.js 파일 업로드 (로컬에서)
scp web\ecosystem.config.js root@211.45.162.155:~/web/

# 5. PM2로 서버 시작
cd ~/web
pm2 start ecosystem.config.js

# 6. 시스템 부팅 시 자동 시작
pm2 save
pm2 startup
```

## PM2 주요 명령어

### 서버 상태 확인
```bash
pm2 status           # 서버 상태 확인
pm2 list             # 프로세스 목록
pm2 info web-server  # 상세 정보
```

### 로그 확인
```bash
pm2 logs             # 실시간 로그
pm2 logs --lines 100 # 최근 100줄
pm2 logs web-server  # 특정 앱 로그
```

### 서버 제어
```bash
pm2 restart web-server  # 서버 재시작
pm2 reload web-server   # 무중단 재시작
pm2 stop web-server     # 서버 중지
pm2 start web-server    # 서버 시작
```

### 모니터링
```bash
pm2 monit            # 실시간 모니터링 (CPU, 메모리)
pm2 show web-server  # 상세 정보
```

## 로컬 개발 환경

로컬에서는 기존 watchdog 방식 사용:
```batch
run_web_server_watch.bat
```

이 배치 파일은 서버가 종료되면 5초 후 자동 재시작합니다.

중지하려면: `stop_web_server.flag` 파일을 생성하세요.

## 로그 파일 위치
- 에러 로그: `/root/logs/web-server-error.log`
- 출력 로그: `/root/logs/web-server-out.log`
- PM2 로그: `~/.pm2/logs/`

## 문제 해결

### 서버가 계속 재시작되는 경우
```bash
# 에러 로그 확인
pm2 logs web-server --err --lines 50

# 서버 정보 확인
pm2 info web-server

# 수동으로 서버 실행해서 에러 확인
cd ~/web
node server.js
```

### PM2 초기화
```bash
pm2 delete all       # 모든 프로세스 삭제
pm2 kill             # PM2 데몬 종료
pm2 start ecosystem.config.js  # 재시작
```

## 설정 파일 (ecosystem.config.js)

주요 설정:
- `autorestart: true` - 자동 재시작 활성화
- `max_memory_restart: '500M'` - 메모리 500MB 초과 시 재시작
- `min_uptime: '10s'` - 10초 이상 실행되어야 정상
- `max_restarts: 10` - 1분 내 최대 10번 재시작
- `restart_delay: 3000` - 재시작 사이 3초 대기
- `cron_restart: '0 4 * * *'` - 매일 새벽 4시 재시작

## 모니터링

SSH로 접속해서 확인:
```bash
ssh root@211.45.162.155
pm2 monit
```

또는 원격에서 확인:
```bash
ssh root@211.45.162.155 "pm2 status; pm2 logs --lines 20"
```
