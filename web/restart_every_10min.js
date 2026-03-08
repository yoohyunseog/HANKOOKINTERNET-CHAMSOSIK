const { spawn, exec } = require('child_process');
const path = require('path');

const RESTART_INTERVAL_MS = 10 * 60 * 1000;
const GRACEFUL_SHUTDOWN_MS = 10 * 1000;

const SERVER_FILE = path.join(__dirname, 'server.js');

let child = null;
let isShuttingDown = false;
let isRestarting = false;

function now() {
  return new Date().toISOString();
}

function log(message) {
  console.log(`[${now()}] ${message}`);
}

function killAllNodeProcesses(callback) {
  log('포트 3000 강제 정리 중...');
  const currentPid = process.pid;
  const currentChild = child ? child.pid : null;
  
  // 1단계: lsof로 포트 3000 사용 프로세스 모두 강제 종료
  exec('(lsof -ti:3000 2>/dev/null || true) | xargs kill -9 2>/dev/null || true', (err1) => {
    // 2단계: fuser로 추가 포트 정리
    exec('fuser -k 3000/tcp 3000/udp 2>/dev/null || true', (err2) => {
      // 3단계: 나머지 node 프로세스 강제 종료 (현재 supervisor와 child 제외)
      const excludePids = [currentPid, currentChild].filter(Boolean).join('|');
      exec(`ps aux | grep "node " | grep -v grep | grep -Ev "(${excludePids})" | awk '{print $2}' | xargs kill -9 2>/dev/null || true`, (err3) => {
        log('포트 정리 완료, 5초 대기 중...');
        setTimeout(() => {
          log('서버 시작 준비 완료');
          if (callback) callback();
        }, 5000);
      });
    });
  });
}

function startServer() {
  child = spawn(process.execPath, [SERVER_FILE], {
    cwd: __dirname,
    stdio: 'inherit',
    env: process.env
  });

  log(`서버 시작됨 (pid: ${child.pid})`);

  child.on('exit', (code, signal) => {
    log(`서버 종료됨 (code: ${code}, signal: ${signal})`);

    // 수동 종료 중이거나 이미 재시작 중이면 무시
    if (!isShuttingDown && !isRestarting) {
      isRestarting = true;
      log('예상치 못한 종료 감지 -> 포트 정리 후 재시작');
      setTimeout(() => {
        killAllNodeProcesses(() => {
          isRestarting = false;
          startServer();
        });
      }, 1000);
    }
  });

  child.on('error', (err) => {
    log(`서버 프로세스 오류: ${err.message}`);
  });
}

function stopServerGracefully(callback) {
  if (!child || child.killed) {
    callback();
    return;
  }

  const targetPid = child.pid;
  log(`서버 종료 시도 (pid: ${targetPid})`);

  let finished = false;
  const done = () => {
    if (finished) return;
    finished = true;
    callback();
  };

  const forceKillTimer = setTimeout(() => {
    if (child && !child.killed) {
      log(`강제 종료 실행 (pid: ${targetPid})`);
      child.kill('SIGKILL');
    }
  }, GRACEFUL_SHUTDOWN_MS);

  child.once('exit', () => {
    clearTimeout(forceKillTimer);
    done();
  });

  child.kill('SIGTERM');
}

function restartServer() {
  log('10분 주기 재시작 시작');
  stopServerGracefully(() => {
    log('포트 정리 후 재시작 진행');
    killAllNodeProcesses(() => {
      startServer();
    });
  });
}

function shutdownSupervisor(signal) {
  if (isShuttingDown) return;
  isShuttingDown = true;
  log(`슈퍼바이저 종료 요청 수신 (${signal})`);

  stopServerGracefully(() => {
    log('슈퍼바이저 종료 완료');
    process.exit(0);
  });
}

// 시작
log('슈퍼바이저 시작...');
killAllNodeProcesses(() => {
  setTimeout(startServer, 2000); // 2초 후 서버 시작
  setInterval(restartServer, RESTART_INTERVAL_MS);
});

process.on('SIGINT', () => shutdownSupervisor('SIGINT'));
process.on('SIGTERM', () => shutdownSupervisor('SIGTERM'));
