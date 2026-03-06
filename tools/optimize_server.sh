#!/bin/bash
# 서버 성능 최적화 스크립트

echo "========================================="
echo "서버 최적화 시작"
echo "========================================="
echo ""

# 1. 기존 Node.js 프로세스 종료
echo "1. 현재 Node.js 프로세스 종료 중..."
ps aux | grep "node server.js" | grep -v grep | awk '{print $2}' | xargs -r kill -9
sleep 2
echo "   ✓ 프로세스 종료 완료"
echo ""

# 2. .env 파일 생성
echo "2. .env 파일 생성 중..."
cd /root/web
cat > .env << 'EOF'
NODE_ENV=production
DEBUG=false
LOG_LEVEL=error
RECENT_CACHE_TTL_MS=30000
RECENT_CACHE_TTL_LIMIT_100_MS=120000
RECENT_CACHE_TTL_LIMIT_1_MS=20000
KEYWORDS_CACHE_TTL_MS=120000
EOF
echo "   ✓ .env 파일 생성 완료"
cat .env
echo ""

# 3. 서버 재시작
echo "3. 서버 재시작 중..."
cd /root/web
nohup node server.js > /dev/null 2>&1 &
NEW_PID=$!
sleep 3
echo "   ✓ 서버 시작됨 (PID: $NEW_PID)"
echo ""

# 4. 서버 상태 확인
echo "4. 서버 상태 확인..."
ps aux | grep "node server.js" | grep -v grep
echo ""

# 5. 시스템 상태 확인
echo "5. 시스템 리소스 확인..."
echo "   CPU & 메모리:"
top -bn1 | head -5
echo ""
echo "   메모리:"
free -h
echo ""

echo "========================================="
echo "최적화 완료!"
echo "========================================="
echo ""
echo "변경 사항:"
echo "  - NODE_ENV=production 설정"
echo "  - 디버그 로그 비활성화"
echo "  - 캐시 TTL 최적화 (30초-120초)"
echo ""
echo "모니터링 명령:"
echo "  tail -f /root/web/server.log    # 로그 모니터링"
echo "  ps aux | grep node              # 프로세스 확인"
echo "  top -p \$(pgrep -f 'node server')  # CPU/메모리 모니터링"
