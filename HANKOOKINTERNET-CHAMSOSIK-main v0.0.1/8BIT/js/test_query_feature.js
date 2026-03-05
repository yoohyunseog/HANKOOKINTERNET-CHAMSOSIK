#!/usr/bin/env node

const readline = require('readline');
const { saveResultToHierarchy, getAllResults } = require('./database');

console.log(`
╔════════════════════════════════════════════════════════════════════╗
║        조회 기능 자동 테스트                                    ║
╚════════════════════════════════════════════════════════════════════╝
`);

// 1. 테스트 데이터 저장
console.log('📝 [1단계] 테스트 데이터 저장 중...\n');

const testData = [
    { value: 5.9686932681, type: 'nb_max', text: '안녕하세요', bit: 999 },
    { value: 999.0000000000, type: 'nb_min', text: '안녕하세요', bit: 999 },
    { value: 863.0606151036, type: 'nb_max', text: '테스트', bit: 999 },
    { value: 133.9499910370, type: 'nb_min', text: '테스트', bit: 999 },
    { value: 456.1234567890, type: 'nb_max', text: '한글테스트', bit: 500 },
];

testData.forEach(item => {
    try {
        saveResultToHierarchy(item.value, item.type, {
            text: item.text,
            bit: item.bit
        });
        console.log(`✓ 저장: ${item.text} → ${item.type} = ${item.value.toFixed(10)}`);
    } catch (e) {
        console.log(`✗ 오류: ${e.message}`);
    }
});

console.log('\n' + '='.repeat(70));

// 2. 저장된 데이터 조회
console.log('\n📂 [2단계] 저장된 데이터 조회\n');

const allResults = getAllResults();

console.log(`✓ N/B MAX: ${allResults.nb_max.length}개`);
console.log(`✓ N/B MIN: ${allResults.nb_min.length}개\n`);

console.log('▸ N/B MAX 목록:');
if (allResults.nb_max.length > 0) {
    allResults.nb_max.forEach((item, idx) => {
        console.log(`  ${idx + 1}. ${item.value.toFixed(10)} (문자: "${item.input.text}", BIT: ${item.input.bit})`);
    });
} else {
    console.log('  (없음)');
}

console.log('\n▸ N/B MIN 목록:');
if (allResults.nb_min.length > 0) {
    allResults.nb_min.forEach((item, idx) => {
        console.log(`  ${idx + 1}. ${item.value.toFixed(10)} (문자: "${item.input.text}", BIT: ${item.input.bit})`);
    });
} else {
    console.log('  (없음)');
}

console.log('\n' + '='.repeat(70));
console.log('\n✅ 조회 기능 테스트 완료!\n');
console.log('💡 팁: 메인 프로그램에서 "s" 입력하면 조회 메뉴가 표시됩니다.\n');

process.exit(0);
