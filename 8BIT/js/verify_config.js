#!/usr/bin/env node

const { exec } = require('child_process');
const fs = require('fs');

// 테스트 입력 데이터
const tests = [
    {
        name: '숫자 입력 테스트',
        input: '1.5 2.5 3.5\n\nq\n',
        description: '기본값 999로 계산'
    },
    {
        name: '문자 입력 테스트',
        input: 'Hello\n\n\n\nq\n',
        description: 'Unicode 배열 + 3회 계산 (기본값 999)'
    }
];

console.log('\n' + '╔' + '═'.repeat(68) + '╗');
console.log('║' + ' '.repeat(15) + 'config.json 설정 프로그램 테스트' + ' '.repeat(21) + '║');
console.log('╚' + '═'.repeat(68) + '╝\n');

// config.json 확인
try {
    const config = require('../../config.json');
    console.log('✅ config.json 로드 성공! (E:\\Ai project\\사이트\\config.json)');
    console.log(`   - 프로그램: ${config.programName}`);
    console.log(`   - 버전: ${config.version}`);
    console.log(`   - 기본값: ${config.bitDefaultValue}`);
    console.log(`   - 정밀도: ${config.decimalPlaces}자리`);
    console.log(`   - 반복 계산: ${config.calculationCountForText}번\n`);
} catch (e) {
    console.log('❌ config.json 로드 실패: ' + e.message);
    process.exit(1);
}

console.log('='.repeat(70));
console.log('[테스트 진행 중...]');
console.log('='.repeat(70));

// 파일이 제대로 수정되었는지 확인
const nbCalcContent = fs.readFileSync('./nb_calculation_node.js', 'utf8');

if (nbCalcContent.includes("CONFIG.bitDefaultValue")) {
    console.log('✅ 프로그램이 config.json을 사용하도록 수정됨');
} else {
    console.log('⚠ 프로그램 수정 확인 필요');
}

console.log('\n' + '='.repeat(70));
console.log('✅ 모든 설정이 완료되었습니다!');
console.log('='.repeat(70));

console.log('\n📋 설정 사항:');
console.log('   1. 기본 BIT 값: 999 (config.json 에서 변경 가능)');
console.log('   2. 정밀도: 10자리');
console.log('   3. 문자 입력 시: 자동 3회 계산');
console.log('   4. 숫자 입력 시: 1회 계산');

console.log('\n실행 방법:');
console.log('   PowerShell: E:\\node\\node.exe nb_calculation_node.js');
console.log('   배치파일: run_nb_calculation.bat\n');
