// 📌 1. 주어진 배열들을 초기화하는 함수
function initializeArrays(count) {
    const arrays = ['BIT_START_A50', 'BIT_START_A100', 'BIT_START_B50', 'BIT_START_B100', 'BIT_START_NBA100'];
    const initializedArrays = {};
    arrays.forEach(array => {
        initializedArrays[array] = new Array(count).fill(0);
    });
    return initializedArrays;
}

// 📌 2. N/B 값을 계산하는 함수 (가중치 상한치 및 하한치 기반)
function calculateBit(nb, bit = 999, reverse = false) {
    if (nb.length < 2) {
        return bit / 100;
    }

    const BIT_NB = bit;
    const max = Math.max(...nb);
    const min = Math.min(...nb);
    const COUNT = 50;
    const CONT = 20;
    const range = max - min;

    // 음수와 양수 범위를 구분하여 증분 계산
    const negativeRange = min < 0 ? Math.abs(min) : 0;
    const positiveRange = max > 0 ? max : 0;

    const negativeIncrement = negativeRange / (COUNT * nb.length - 1);
    const positiveIncrement = positiveRange / (COUNT * nb.length - 1);

    const arrays = initializeArrays(COUNT * nb.length);
    let count = 0;
    let totalSum = 0;

    for (let value of nb) {
        for (let i = 0; i < COUNT; i++) {
            const BIT_END = 1;

            // 부호에 따른 A50, B50 계산
            const A50 = value < 0
                ? min + negativeIncrement * (count + 1) // 음수일 때
                : min + positiveIncrement * (count + 1); // 양수일 때

            const A100 = (count + 1) * BIT_NB / (COUNT * nb.length);

            const B50 = value < 0
                ? A50 - negativeIncrement * 2
                : A50 - positiveIncrement * 2;

            const B100 = value < 0
                ? A50 + negativeIncrement
                : A50 + positiveIncrement;

            const NBA100 = A100 / (nb.length - BIT_END);

            arrays.BIT_START_A50[count] = A50;
            arrays.BIT_START_A100[count] = A100;
            arrays.BIT_START_B50[count] = B50;
            arrays.BIT_START_B100[count] = B100;
            arrays.BIT_START_NBA100[count] = NBA100;
            count++;
        }
        totalSum += value;
    }

    // Reverse 옵션 처리 (시간 역방향 흐름 분석)
    if (reverse) {
        arrays.BIT_START_NBA100.reverse();
    }

    // NB50 계산 (시간 흐름 기반 가중치 분석)
    let NB50 = 0;
    for (let value of nb) {
        for (let a = 0; a < arrays.BIT_START_NBA100.length; a++) {
            if (arrays.BIT_START_B50[a] <= value && arrays.BIT_START_B100[a] >= value) {
                NB50 += arrays.BIT_START_NBA100[Math.min(a, arrays.BIT_START_NBA100.length - 1)];
                break;
            }
        }
    }

    // 평균 비율 기반 NB50 정규화
    const BIT = Math.max((10 - nb.length) * 10, 1);
    const averageRatio = (totalSum / (nb.length * Math.abs(max || 1))) * 100; // 절대값으로 계산
    NB50 = Math.min((NB50 / 100) * averageRatio, BIT_NB);

    // 시간 흐름의 상한치(MAX)와 하한치(MIN) 보정
    if (nb.length === 2) {
        return bit - NB50; // NB 분석 점수가 작을수록 시간 흐름 안정성이 높음
    }

    return NB50;
}

// 📌 3. SUPER_BIT 글로벌 변수 및 업데이트 함수
let SUPER_BIT = 0;

function updateSuperBit(newValue) {
    // SUPER_BIT는 현재 N/B 분석 상태를 반영한 전역 가중치
    SUPER_BIT = newValue;
}

// 📌 4. BIT_MAX_NB 함수 (시간 흐름 상한치 분석)
function BIT_MAX_NB(nb, bit = 999) {
    let result = calculateBit(nb, bit, false); // 시간 순방향 분석 (Forward Time Flow)

    // 결과 값이 유효 범위를 벗어나면 SUPER_BIT 반환
    if (!isFinite(result) || isNaN(result)) {
        return SUPER_BIT;
    } else {
        updateSuperBit(result);
        return result;
    }
}

// 📌 5. BIT_MIN_NB 함수 (시간 흐름 하한치 분석)
function BIT_MIN_NB(nb, bit = 999) {
    let result = calculateBit(nb, bit, true); // 시간 역방향 분석 (Reverse Time Flow)

    // 결과 값이 유효 범위를 벗어나면 SUPER_BIT 반환
    if (!isFinite(result) || isNaN(result)) {
        return SUPER_BIT;
    } else {
        updateSuperBit(result);
        return result;
    }
}

// ============================================================================
// 설정 파일 읽기
// ============================================================================

let CONFIG = {};
try {
    CONFIG = require('../../config.json');
} catch (e) {
    // config.json이 없으면 기본값 사용
    CONFIG = {
        bitDefaultValue: 999,
        bitMinValue: 1,
        bitMaxValue: 10000,
        calculationCountForText: 3,
        decimalPlaces: 10,
        programName: 'N/B MAX, N/B MIN 계산 프로그램',
        version: '1.0.0'
    };
    console.warn('⚠ ../../config.json을 찾을 수 없습니다. 기본값을 사용합니다.\n');
}

// ============================================================================
// 문자열을 Unicode 배열로 변환하는 함수
// ============================================================================

function wordNbUnicodeFormat(text) {
    if (!text || typeof text !== 'string') {
        return [];
    }

    const langRanges = [
        { range: [0xAC00, 0xD7AF], prefix: 1000000 }, // Korean
        { range: [0x3040, 0x309F], prefix: 2000000 }, // Japanese Hiragana
        { range: [0x30A0, 0x30FF], prefix: 3000000 }, // Japanese Katakana
        { range: [0x4E00, 0x9FFF], prefix: 4000000 }, // Chinese
        { range: [0x0410, 0x044F], prefix: 5000000 }, // Russian
        { range: [0x0041, 0x007A], prefix: 6000000 }, // English
        { range: [0x0590, 0x05FF], prefix: 7000000 }, // Hebrew
        { range: [0x00C0, 0x00FD], prefix: 8000000 }, // Vietnamese
        { range: [0x0E00, 0x0E7F], prefix: 9000000 }, // Thai
    ];

    return Array.from(text).map(char => {
        const unicodeValue = char.codePointAt(0);
        const lang = langRanges.find(l => 
            unicodeValue >= l.range[0] && unicodeValue <= l.range[1]
        );
        const prefix = lang ? lang.prefix : 0;
        return prefix + unicodeValue;
    });
}

// ============================================================================
// 모듈 불러오기
// ============================================================================

const readline = require('readline');
const { saveResultToHierarchy, getAllResults, readResultFromHierarchy } = require('./database');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function prompt(question) {
    return new Promise(resolve => {
        rl.question(question, resolve);
    });
}

/**
 * 조회 함수
 */
async function showQueryMenu() {
    console.log('\n' + '='.repeat(60));
    console.log('📂 저장된 결과 조회');
    console.log('='.repeat(60));
    
    const allResults = getAllResults();
    
    if (!allResults || (allResults.nb_max.length === 0 && allResults.nb_min.length === 0)) {
        console.log('✗ 저장된 데이터가 없습니다.\n');
        return;
    }
    
    console.log(`\n✓ N/B MAX: ${allResults.nb_max.length}개`);
    console.log(`✓ N/B MIN: ${allResults.nb_min.length}개`);
    
    const choice = await prompt('\n조회 항목 선택 (1=MAX, 2=MIN, 3=전체): ');
    
    console.log('\n' + '-'.repeat(60));
    
    if (choice === '1' || choice === '1') {
        // N/B MAX 조회
        if (allResults.nb_max.length === 0) {
            console.log('N/B MAX 데이터가 없습니다.');
        } else {
            console.log('📊 N/B MAX 결과:\n');
            allResults.nb_max.forEach((item, idx) => {
                const inputInfo = item.input.text 
                    ? `문자: "${item.input.text}"` 
                    : `배열: [${item.input.values.slice(0, 3).join(', ')}${item.input.values.length > 3 ? ', ...' : ''}]`;
                console.log(`  ${idx + 1}. ${item.value.toFixed(10)} (BIT: ${item.input.bit}, ${inputInfo})`);
                console.log(`     저장: ${item.timestamp}`);
            });
        }
    } else if (choice === '2') {
        // N/B MIN 조회
        if (allResults.nb_min.length === 0) {
            console.log('N/B MIN 데이터가 없습니다.');
        } else {
            console.log('📊 N/B MIN 결과:\n');
            allResults.nb_min.forEach((item, idx) => {
                const inputInfo = item.input.text 
                    ? `문자: "${item.input.text}"` 
                    : `배열: [${item.input.values.slice(0, 3).join(', ')}${item.input.values.length > 3 ? ', ...' : ''}]`;
                console.log(`  ${idx + 1}. ${item.value.toFixed(10)} (BIT: ${item.input.bit}, ${inputInfo})`);
                console.log(`     저장: ${item.timestamp}`);
            });
        }
    } else if (choice === '3') {
        // 전체 조회
        console.log('📊 모든 결과:\n');
        
        if (allResults.nb_max.length > 0) {
            console.log('▸ N/B MAX:');
            allResults.nb_max.forEach((item, idx) => {
                const inputInfo = item.input.text 
                    ? `문자: "${item.input.text}"` 
                    : `배열: [${item.input.values.slice(0, 3).join(', ')}${item.input.values.length > 3 ? ', ...' : ''}]`;
                console.log(`    ${idx + 1}. ${item.value.toFixed(10)} (BIT: ${item.input.bit}, ${inputInfo})`);
            });
        }
        
        if (allResults.nb_min.length > 0) {
            console.log('\n▸ N/B MIN:');
            allResults.nb_min.forEach((item, idx) => {
                const inputInfo = item.input.text 
                    ? `문자: "${item.input.text}"` 
                    : `배열: [${item.input.values.slice(0, 3).join(', ')}${item.input.values.length > 3 ? ', ...' : ''}]`;
                console.log(`    ${idx + 1}. ${item.value.toFixed(10)} (BIT: ${item.input.bit}, ${inputInfo})`);
            });
        }
    }
    
    console.log('\n' + '='.repeat(60));
}

async function main() {
    console.log('='.repeat(60));
    console.log(CONFIG.programName + ' (Node.js)');
    console.log('버전: ' + CONFIG.version);
    console.log('='.repeat(60));
    console.log();

    while (true) {
        const input = await prompt('\n문자/숫자를 입력하세요 (또는 q를 입력하여 종료, s=조회): ');

        if (input.toLowerCase() === 'q') {
            console.log('\n프로그램을 종료합니다.');
            break;
        }

        // 조회 명령어 처리
        if (['s', 'search', '검색', '조회', '/s'].includes(input.toLowerCase())) {
            await showQueryMenu();
            continue;
        }

        // 숫자 입력 시 처리
        try {
            const values = input.replace(/,/g, ' ').split(/\s+/).filter(x => x.trim()).map(parseFloat);
            
            if (values.length >= 2 && values.every(v => !isNaN(v))) {
                // 숫자 입력이 정상적이면 1번 계산
                console.log('\n✓ 정상 입력: 1번 계산 실행');
                
                const bitInput = await prompt(`BIT 값을 입력하세요 (기본값: ${CONFIG.bitDefaultValue}): `);
                const bitValue = bitInput.trim() ? parseFloat(bitInput) : CONFIG.bitDefaultValue;

                console.log('\n' + '='.repeat(60));
                console.log(`입력값: [${values.join(', ')}]`);
                console.log(`BIT 값: ${bitValue}`);
                console.log('='.repeat(60));

                const maxResult = BIT_MAX_NB(values, bitValue);
                const minResult = BIT_MIN_NB(values, bitValue);
                
                console.log(`\n✓ N/B MAX 결과: ${maxResult.toFixed(CONFIG.decimalPlaces)}`);
                console.log(`✓ N/B MIN 결과: ${minResult.toFixed(CONFIG.decimalPlaces)}`);
                console.log(`✓ 차이 (MAX - MIN): ${(maxResult - minResult).toFixed(CONFIG.decimalPlaces)}`);
                
                // 데이터베이스에 저장
                saveResultToHierarchy(maxResult, 'nb_max', { values: values, bit: bitValue });
                saveResultToHierarchy(minResult, 'nb_min', { values: values, bit: bitValue });
            } else {
                throw new Error('Invalid input');
            }
        } catch (e) {
            // 문자 입력 시 3번 계산 실행
            console.log(`\n⚠ 문자 입력 감지: '${input}'`);
            
            // 문자열을 Unicode 배열로 변환
            const unicodeArray = wordNbUnicodeFormat(input);
            
            if (unicodeArray.length === 0) {
                console.log('⚠ 유효한 입력이 없습니다.');
                continue;
            }

            console.log(`✓ 문자 배열 변환: [${unicodeArray.slice(0, 5).join(', ')}${unicodeArray.length > 5 ? '...' : ''}]`);
            console.log('✓ 자동으로 ' + CONFIG.calculationCountForText + '번 계산을 실행합니다.\n');
            console.log('='.repeat(60));

            for (let i = 1; i <= CONFIG.calculationCountForText; i++) {
                console.log(`\n[계산 ${i}/${CONFIG.calculationCountForText}]`);
                console.log('-'.repeat(60));

                const bitInput = await prompt(`BIT 값을 입력하세요 (기본값: ${CONFIG.bitDefaultValue}): `);
                const bitValue = bitInput.trim() ? parseFloat(bitInput) : CONFIG.bitDefaultValue;

                // 문자 배열로 계산
                const maxResult = BIT_MAX_NB(unicodeArray, bitValue);
                const minResult = BIT_MIN_NB(unicodeArray, bitValue);
                
                console.log(`✓ N/B MAX 결과: ${maxResult.toFixed(CONFIG.decimalPlaces)}`);
                console.log(`✓ N/B MIN 결과: ${minResult.toFixed(CONFIG.decimalPlaces)}`);
                console.log(`✓ 차이 (MAX - MIN): ${(maxResult - minResult).toFixed(CONFIG.decimalPlaces)}`);
                
                // 데이터베이스에 저장
                saveResultToHierarchy(maxResult, 'nb_max', { text: input, bit: bitValue });
                saveResultToHierarchy(minResult, 'nb_min', { text: input, bit: bitValue });
            }

            console.log('\n' + '='.repeat(60));
            console.log(CONFIG.calculationCountForText + '번 계산이 완료되었습니다.');
            console.log('='.repeat(60));
        }
    }

    rl.close();
}

// 프로그램 시작
main().catch(console.error);
