module.exports = {
  apps: [{
    name: 'web-server',
    script: './server.js',
    cwd: '/root/web',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '500M',
    env: {
      NODE_ENV: 'production',
      PORT: 3000,
      OLLAMA_BASE_URL: 'http://localhost:11434',
      RECENT_CACHE_TTL_MS: '10000',
      RECENT_CACHE_TTL_LIMIT_100_MS: '60000',
      RECENT_CACHE_TTL_LIMIT_1_MS: '10000'
    },
    error_file: '/root/logs/web-server-error.log',
    out_file: '/root/logs/web-server-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    // 자동 재시작 설정
    min_uptime: '10s',           // 최소 10초 이상 실행되어야 정상으로 간주
    max_restarts: 10,            // 1분 내 최대 10번까지 재시작 시도
    restart_delay: 3000,         // 재시작 사이 3초 대기
    // 크래시 시 exponential backoff
    exp_backoff_restart_delay: 100,
    // 크론 재시작 (매일 새벽 4시)
    cron_restart: '0 4 * * *'
  }]
};
