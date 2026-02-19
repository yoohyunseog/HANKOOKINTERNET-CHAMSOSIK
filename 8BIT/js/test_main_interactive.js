#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');

console.log(`
╔════════════════════════════════════════════════════════════════════╗
║        메인 프로그램 대화형 테스트                              ║
║        (조회 기능 포함)                                         ║
╚════════════════════════════════════════════════════════════════════╝
`);

// 메인 프로그램 실행
const program = spawn('E:\\node\\node.exe', [
    path.join(__dirname, 'nb_calculation_node.js')
], {
    stdio: ['pipe', 'inherit', 'inherit'],
    cwd: __dirname
});

// 테스트 순서
const inputs = [
    '안녕하세요\n',     // 문자 입력 → 3회 자동 계산
    '\n',               // BIT 기본값
    '\n',               // BIT 기본값
    '\n',               // BIT 기본값
    's\n',              // 조회 명령어
    '3\n',              // 전체 조회
    '1 2 3\n',          // 숫자 입력 → 1회 계산
    '999\n',            // BIT 값
    's\n',              // 다시 조회
    '1\n',              // N/B MAX만 조회
    'q\n'               // 종료
];

let inputIndex = 0;

// 입력 자동화
const inputInterval = setInterval(() => {
    if (inputIndex < inputs.length) {
        const input = inputs[inputIndex];
        console.log(`\n>> 입력 [${inputIndex + 1}/${inputs.length}]: ${input.trim()}`);
        program.stdin.write(input);
        inputIndex++;
    } else {
        clearInterval(inputInterval);
        setTimeout(() => {
            program.stdin.end();
        }, 1000);
    }
}, 2000);  // 2초 간격으로 입력

// 프로그램 종료
program.on('close', (code) => {
    console.log('\n' + '='.repeat(70));
    console.log(`\n✅ 테스트 완료! (종료 코드: ${code})\n`);
    process.exit(0);
});
