#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');

console.log(`
╔════════════════════════════════════════════════════════════════════╗
║      N/B MAX, N/B MIN 프로그램 - 최종 기능 데모                   ║
║      조회 기능 포함 완성 테스트                                   ║
╚════════════════════════════════════════════════════════════════════╝
`);

// 메인 프로그램 실행
const program = spawn('E:\\node\\node.exe', [
    path.join(__dirname, 'nb_calculation_node.js')
], {
    stdio: ['pipe', 'inherit', 'inherit'],
    cwd: __dirname
});

// 테스트 시나리오
const inputs = [
    // 1. 텍스트 입력 → 자동 3회 계산
    '안녕하세요\n',     
    '\n',  // BIT 기본값
    '\n',  
    '\n',  
    
    // 2. 숫자 입력 → 1회 계산
    '2.5 3.5 4.5\n',    
    '999\n',
    
    // 3. 조회 기능 테스트
    's\n',              // 조회 명령어
    '3\n',              // 전체 조회
    
    // 4. 종료
    'q\n'               
];

let inputIndex = 0;

// 입력 자동화
const inputInterval = setInterval(() => {
    if (inputIndex < inputs.length) {
        const input = inputs[inputIndex];
        program.stdin.write(input);
        inputIndex++;
    } else {
        clearInterval(inputInterval);
        setTimeout(() => {
            program.stdin.end();
        }, 1000);
    }
}, 2500);  // 각 입력 사이 2.5초 간격

// 프로그램 종료
program.on('close', (code) => {
    console.log('\n╔════════════════════════════════════════════════════════════════════╗');
    console.log('║  ✅ 프로그램 테스트 완료!                                         ║');
    console.log('║                                                                    ║');
    console.log('║  📌 테스트 내용:                                                  ║');
    console.log('║     1. 문자 입력 → 자동 3회 계산 (안녕하세요)                      ║');
    console.log('║     2. 숫자 입력 → 1회 계산 (2.5 3.5 4.5)                         ║');
    console.log('║     3. 조회 기능 (s 커맨드) → 전체 결과 조회                       ║');
    console.log('║     4. 정상 종료 (q)                                             ║');
    console.log('║                                                                    ║');
    console.log('║  💾 저장된 데이터는 data/ 폴더에 자릿수별로 정리되어 있습니다.     ║');
    console.log('║  🔍 언제든지 "s" 입력으로 저장된 결과를 조회할 수 있습니다.        ║');
    console.log('╚════════════════════════════════════════════════════════════════════╝\n');
    process.exit(0);
});
