#!/usr/bin/env node

const { execSync } = require('child_process');

// 테스트 1: 문자 입력 (Unicode 배열 변환 + 10자리 정밀도)
const test1Input = '안녕하세요\n5.5\n5.5\n5.5\nq\n';

// 테스트 2: 숫자 입력
const test2Input = '1.5 2.5 3.5\n5.5\nq\n';

console.log('\n╔' + '═'.repeat(68) + '╗');
console.log('║' + ' '.repeat(10) + '수정된 N/B 계산 프로그램 테스트 (10자리 정밀도)' + ' '.repeat(12) + '║');
console.log('╚' + '═'.repeat(68) + '╝');

console.log('\n' + '='.repeat(70));
console.log('[테스트 1] 문자 입력 - Unicode 배열 변환 + 10자리 정밀도');
console.log('='.repeat(70));

try {
    const result1 = execSync(`echo "${test1Input}" | E:\\node\\node.exe nb_calculation_node.js`, {
        cwd: 'E:\\Ai project\\사이트\\8BIT\\js',
        encoding: 'utf8',
        stdio: 'pipe'
    });
    console.log(result1);
} catch (e) {
    console.log(e.stdout);
}

console.log('\n' + '='.repeat(70));
console.log('[테스트 2] 숫자 입력 - 10자리 정밀도');
console.log('='.repeat(70));

try {
    const result2 = execSync(`echo "${test2Input}" | E:\\node\\node.exe nb_calculation_node.js`, {
        cwd: 'E:\\Ai project\\사이트\\8BIT\\js',
        encoding: 'utf8',
        stdio: 'pipe'
    });
    console.log(result2);
} catch (e) {
    console.log(e.stdout);
}

console.log('\n' + '='.repeat(70));
console.log('✅ 모든 테스트 완료!');
console.log('='.repeat(70));
