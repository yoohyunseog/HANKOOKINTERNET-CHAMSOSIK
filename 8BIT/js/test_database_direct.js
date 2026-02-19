#!/usr/bin/env node

const db = require('./database');
const path = require('path');
const fs = require('fs');

console.log(`
╔════════════════════════════════════════════════════════════════════╗
║        데이터베이스 직접 테스트                                 ║
╚════════════════════════════════════════════════════════════════════╝
`);

// 테스트 데이터
const testValues = [
    { value: 5.9686932681, type: 'nb_max', label: 'N/B MAX' },
    { value: 999.0000000000, type: 'nb_min', label: 'N/B MIN' },
    { value: 863.0606151036, type: 'nb_max', label: 'TEST' },
    { value: 133.9499910370, type: 'nb_min', label: 'TEST2' }
];

console.log('📊 테스트 데이터 저장 중...\n');

testValues.forEach(item => {
    try {
        const result = db.saveResultToHierarchy(item.value, item.type, {
            text: '테스트',
            bit: 999,
            label: item.label
        });
        console.log(`✓ ${item.label} (${item.value})`);
        console.log(`  저장 경로: ${result.replace('e:\\Ai project\\사이트\\', '')}\n`);
    } catch (error) {
        console.log(`✗ ${item.label} - 오류: ${error.message}\n`);
    }
});

// 저장된 데이터 조회
console.log('\n' + '='.repeat(70));
console.log('📂 저장된 폴더 구조 확인:\n');

const dataDir = path.join(__dirname, '..', '..', 'data');
if (fs.existsSync(dataDir)) {
    console.log(`✓ data 폴더 존재: ${dataDir}`);
    
    // 첫 번째 레벨 (nb_max, nb_min)
    const types = fs.readdirSync(dataDir);
    types.forEach(type => {
        const typePath = path.join(dataDir, type);
        const stat = fs.statSync(typePath);
        if (stat.isDirectory()) {
            console.log(`\n📁 ${type}/`);
            
            // 최대 3개 샘플 폴더 표시
            const firstDigits = fs.readdirSync(typePath).slice(0, 3);
            firstDigits.forEach(digit => {
                const digitPath = path.join(typePath, digit);
                const digitStat = fs.statSync(digitPath);
                console.log(`   └── ${digit}/`);
                
                // result.json 파일 찾기
                const findResultFiles = (dir, depth = 1) => {
                    if (depth > 3) return; // 깊이 제한
                    try {
                        const items = fs.readdirSync(dir);
                        items.forEach(item => {
                            const itemPath = path.join(dir, item);
                            const itemStat = fs.statSync(itemPath);
                            if (item === 'result.json') {
                                const relativePath = path.relative(dataDir, itemPath);
                                console.log(`   ${' '.repeat(depth * 2)}📄 result.json`);
                            } else if (itemStat.isDirectory() && depth < 3) {
                                findResultFiles(itemPath, depth + 1);
                            }
                        });
                    } catch (e) {}
                };
                
                findResultFiles(digitPath);
            });
        }
    });
} else {
    console.log('✗ data 폴더가 없습니다.');
}

console.log('\n' + '='.repeat(70));
console.log('\n✅ 테스트 완료!\n');
