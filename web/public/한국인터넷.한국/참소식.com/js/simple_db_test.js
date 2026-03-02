#!/usr/bin/env node

console.log('\n=== 데이터베이스 저장 테스트 ===\n');

const db = require('./database');

// 직접 저장 테스트
console.log('1. 데이터 저장 테스트 (5.9686932681):');
try {
    const result = db.saveResultToHierarchy(5.9686932681, 'nb_max', {
        text: '테스트',
        bit: 999
    });
    console.log(`✓ 저장 완료: ${result}\n`);
} catch (error) {
    console.log(`✗ 오류: ${error.message}\n`);
}

console.log('2. 데이터 저장 테스트 (999.0000000000):');
try {
    const result = db.saveResultToHierarchy(999.0000000000, 'nb_min', {
        text: '테스트',
        bit: 999
    });
    console.log(`✓ 저장 완료: ${result}\n`);
} catch (error) {
    console.log(`✗ 오류: ${error.message}\n`);
}

console.log('3. 저장된 모든 데이터 조회:');
try {
    const all = db.getAllResults();
    console.log('\n✓ 저장된 데이터:');
    if (all.nb_max.length > 0) {
        console.log('  NB_MAX: ' + all.nb_max.length + '개');
    }
    if (all.nb_min.length > 0) {
        console.log('  NB_MIN: ' + all.nb_min.length + '개');
    }
} catch (error) {
    console.log(`✗ 오류: ${error.message}`);
}

console.log('\n=== 테스트 완료 ===\n');
process.exit(0);
