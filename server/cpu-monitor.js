/**
 * CPU 사용량 모니터링 봇
 * 초당 CPU 사용량을 확인하고 로그로 출력
 */

const os = require('os');
const fs = require('fs');
const path = require('path');

// 설정
const CONFIG = {
    interval: 1000, // 1초마다 체크
    logFile: '/tmp/cpu-monitor.log',
    alertThreshold: 80, // 80% 이상이면 경고
    historySize: 60 // 60초간 히스토리 유지
};

// CPU 사용량 계산
let lastCpuInfo = null;

function getCpuUsage() {
    const cpus = os.cpus();
    const currentCpuInfo = cpus.map(cpu => ({
        user: cpu.times.user,
        nice: cpu.times.nice,
        sys: cpu.times.sys,
        idle: cpu.times.idle,
        irq: cpu.times.irq
    }));

    if (!lastCpuInfo) {
        lastCpuInfo = currentCpuInfo;
        return { usage: 0, perCore: [] };
    }

    const usagePerCore = [];
    let totalUsage = 0;

    for (let i = 0; i < cpus.length; i++) {
        const current = currentCpuInfo[i];
        const last = lastCpuInfo[i];

        const total = (current.user - last.user) +
                     (current.nice - last.nice) +
                     (current.sys - last.sys) +
                     (current.idle - last.idle) +
                     (current.irq - last.irq);

        const idle = current.idle - last.idle;
        const usage = total > 0 ? ((total - idle) / total) * 100 : 0;

        usagePerCore.push({
            core: i,
            usage: usage.toFixed(1)
        });
        totalUsage += usage;
    }

    lastCpuInfo = currentCpuInfo;

    return {
        usage: (totalUsage / cpus.length).toFixed(1),
        perCore: usagePerCore,
        cores: cpus.length
    };
}

// 메모리 사용량 계산
function getMemoryUsage() {
    const total = os.totalmem();
    const free = os.freemem();
    const used = total - free;
    const usage = (used / total) * 100;

    return {
        total: (total / 1024 / 1024 / 1024).toFixed(2),
        used: (used / 1024 / 1024 / 1024).toFixed(2),
        free: (free / 1024 / 1024 / 1024).toFixed(2),
        usage: usage.toFixed(1)
    };
}

// 로그 기록
function log(message) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${message}\n`;
    
    console.log(logMessage.trim());
    
    // 파일에도 기록
    try {
        fs.appendFileSync(CONFIG.logFile, logMessage);
    } catch (e) {
        // 파일 기록 실패 시 무시
    }
}

// 히스토리 관리
const history = [];

function addToHistory(cpuUsage, memoryUsage) {
    history.push({
        timestamp: new Date(),
        cpu: parseFloat(cpuUsage),
        memory: parseFloat(memoryUsage.usage)
    });

    // 히스토리 크기 유지
    while (history.length > CONFIG.historySize) {
        history.shift();
    }
}

// 통계 계산
function getStats() {
    if (history.length === 0) return null;

    const cpuValues = history.map(h => h.cpu);
    const memValues = history.map(h => h.memory);

    return {
        cpu: {
            avg: (cpuValues.reduce((a, b) => a + b, 0) / cpuValues.length).toFixed(1),
            max: Math.max(...cpuValues).toFixed(1),
            min: Math.min(...cpuValues).toFixed(1)
        },
        memory: {
            avg: (memValues.reduce((a, b) => a + b, 0) / memValues.length).toFixed(1),
            max: Math.max(...memValues).toFixed(1),
            min: Math.min(...memValues).toFixed(1)
        }
    };
}

// 메인 모니터링 함수
function monitor() {
    const cpu = getCpuUsage();
    const memory = getMemoryUsage();

    // 히스토리에 추가
    addToHistory(cpu.usage, memory);

    // 기본 로그
    const message = `CPU: ${cpu.usage}% | 메모리: ${memory.usage}% (${memory.used}GB / ${memory.total}GB) | 코어: ${cpu.cores}개`;

    // 경고 체크
    if (parseFloat(cpu.usage) >= CONFIG.alertThreshold) {
        log(`⚠️ [경고] ${message}`);
    } else {
        log(`📊 ${message}`);
    }

    // 10초마다 통계 출력
    if (history.length % 10 === 0 && history.length > 0) {
        const stats = getStats();
        if (stats) {
            log(`📈 [통계 - 최근 ${history.length}초] CPU 평균: ${stats.cpu.avg}% (최대: ${stats.cpu.max}%, 최소: ${stats.cpu.min}%) | 메모리 평균: ${stats.memory.avg}%`);
        }
    }
}

// 시작
console.log('╔════════════════════════════════════════════════════════════╗');
console.log('║           CPU 사용량 모니터링 봇 시작                      ║');
console.log('╚════════════════════════════════════════════════════════════╝');
console.log(`📊 간격: ${CONFIG.interval}ms`);
console.log(`⚠️ 경고 임계값: ${CONFIG.alertThreshold}%`);
console.log(`📝 로그 파일: ${CONFIG.logFile}`);
console.log(`💻 CPU 코어: ${os.cpus().length}개`);
console.log(`💾 전체 메모리: ${(os.totalmem() / 1024 / 1024 / 1024).toFixed(2)}GB`);
console.log('─'.repeat(60));

// 즉시 첫 번째 체크 실행
monitor();

// 주기적 실행
setInterval(monitor, CONFIG.interval);

// 종료 처리
process.on('SIGINT', () => {
    console.log('\n\n📊 모니터링 종료...');
    const stats = getStats();
    if (stats) {
        console.log(`📈 최종 통계:`);
        console.log(`   CPU 평균: ${stats.cpu.avg}% (최대: ${stats.cpu.max}%, 최소: ${stats.cpu.min}%)`);
        console.log(`   메모리 평균: ${stats.memory.avg}% (최대: ${stats.memory.max}%, 최소: ${stats.memory.min}%)`);
    }
    process.exit(0);
});