const fs = require('fs');
const path = require('path');

// ============================================================================
// 경로별 데이터 저장 함수
// ============================================================================

/**
 * N/B 결과를 각 자릿수별 폴더로 저장
 * 예: 863.0606151036 → data/nb_max/8/6/3/0/6/0/6/1/5/1/0/3/6/result.json
 */
function saveResultToHierarchy(resultValue, type = 'nb_max', inputData = {}) {
    try {
        // 소수점 제거 및 각 자리수 추출
        const digits = resultValue
            .toFixed(10)  // 10자리로 고정
            .replace('.', '')  // 소수점 제거
            .split('');  // 각 자리수로 분할

        // 폴더 경로 구성
        const dataDir = path.join(__dirname, '..', '..', 'data');
        let currentPath = path.join(dataDir, type);

        // nb_max 또는 nb_min 폴더 생성
        if (!fs.existsSync(currentPath)) {
            fs.mkdirSync(currentPath, { recursive: true });
        }

        // 각 자릿수별로 폴더 생성
        for (let digit of digits) {
            currentPath = path.join(currentPath, digit);
            if (!fs.existsSync(currentPath)) {
                fs.mkdirSync(currentPath, { recursive: true });
            }
        }

        // 결과 저장
        const resultData = {
            timestamp: new Date().toISOString(),
            value: resultValue,
            type: type,
            input: inputData,
            path: currentPath
        };

        const resultFile = path.join(currentPath, 'result.json');
        fs.writeFileSync(resultFile, JSON.stringify(resultData, null, 2), 'utf8');

        return resultFile;

    } catch (error) {
        console.error(`❌ 데이터 저장 실패: ${error.message}`);
        return null;
    }
}

/**
 * 저장된 결과 조회
 */
function readResultFromHierarchy(type = 'nb_max') {
    try {
        const dataDir = path.join(__dirname, '..', '..', 'data', type);
        if (!fs.existsSync(dataDir)) {
            return null;
        }

        // 디렉토리 구조 탐색
        const results = [];
        const walkDir = (dir, depth = 0) => {
            const files = fs.readdirSync(dir);
            for (let file of files) {
                const fullPath = path.join(dir, file);
                const stat = fs.statSync(fullPath);

                if (stat.isDirectory()) {
                    walkDir(fullPath, depth + 1);
                } else if (file === 'result.json') {
                    const data = JSON.parse(fs.readFileSync(fullPath, 'utf8'));
                    results.push(data);
                }
            }
        };

        walkDir(dataDir);
        return results;

    } catch (error) {
        console.error(`❌ 데이터 조회 실패: ${error.message}`);
        return null;
    }
}

/**
 * 모든 N/B MAX, N/B MIN 결과 조회
 */
function getAllResults() {
    return {
        nb_max: readResultFromHierarchy('nb_max'),
        nb_min: readResultFromHierarchy('nb_min')
    };
}

// ============================================================================
// 테스트
// ============================================================================

if (require.main === module) {
    console.log('\n' + '='.repeat(70));
    console.log('데이터베이스 저장 시스템 테스트');
    console.log('='.repeat(70));

    // 테스트 데이터
    const testResults = [
        { value: 863.0606151036, type: 'nb_max', input: { text: '안녕하세요', bit: 999 } },
        { value: 133.9499910370, type: 'nb_min', input: { text: '안녕하세요', bit: 999 } },
        { value: 5.9686932681, type: 'nb_max', input: { values: [1.5, 2.5, 3.5], bit: 5.5 } }
    ];

    testResults.forEach(result => {
        console.log(`\n📁 저장: ${result.type.toUpperCase()} = ${result.value}`);
        const savedPath = saveResultToHierarchy(result.value, result.type, result.input);
        if (savedPath) {
            console.log(`✅ 저장 완료: ${savedPath}`);
        }
    });

    console.log('\n' + '='.repeat(70));
    console.log('저장된 모든 결과:');
    console.log('='.repeat(70));
    const allResults = getAllResults();
    console.log('\n📊 N/B MAX 결과:');
    if (allResults.nb_max && allResults.nb_max.length > 0) {
        allResults.nb_max.forEach(r => {
            console.log(`  - ${r.value} (${r.timestamp})`);
        });
    } else {
        console.log('  (없음)');
    }

    console.log('\n📊 N/B MIN 결과:');
    if (allResults.nb_min && allResults.nb_min.length > 0) {
        allResults.nb_min.forEach(r => {
            console.log(`  - ${r.value} (${r.timestamp})`);
        });
    } else {
        console.log('  (없음)');
    }

    console.log('\n' + '='.repeat(70));
}

module.exports = {
    saveResultToHierarchy,
    readResultFromHierarchy,
    getAllResults
};
