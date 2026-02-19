/**
 * N/B 계산기 프론트엔드 스크립트
 */

// DOM 요소
const numberInput = document.getElementById('numbers');
const textInput = document.getElementById('text');
const bitInput = document.getElementById('bit');
const calculateBtn = document.getElementById('calculate-btn');
const resultSection = document.getElementById('result-section');
const numberResult = document.getElementById('number-result');
const textResult = document.getElementById('text-result');
const resultError = document.getElementById('result-error');

// 입력 타입 선택 버튼
const typeButtons = document.querySelectorAll('.type-btn');
let currentType = 'number';

// 이벤트 리스너
typeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const type = btn.dataset.type;
        switchInputType(type);
    });
});

calculateBtn.addEventListener('click', handleCalculate);

// 엔터 키로도 계산 가능
numberInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleCalculate();
});
textInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleCalculate();
});

/**
 * 입력 타입 전환
 */
function switchInputType(type) {
    currentType = type;

    // 버튼 활성화 상태 변경 (Bootstrap)
    typeButtons.forEach(btn => {
        if (btn.dataset.type === type) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // 입력 폼 표시/숨김 (Bootstrap d-none 사용)
    document.getElementById('number-form').classList.toggle('d-none', type !== 'number');
    document.getElementById('text-form').classList.toggle('d-none', type !== 'text');

    // 입력 필드 포커스
    if (type === 'number') {
        numberInput.focus();
    } else {
        textInput.focus();
    }
}

/**
 * 계산 처리
 */
async function handleCalculate() {
    try {
        resultError.style.display = 'none';

        let input;
        if (currentType === 'number') {
            input = numberInput.value.trim();
        } else {
            input = textInput.value.trim();
        }

        if (!input) {
            showError('입력이 없습니다. 값을 입력해주세요.');
            return;
        }

        const bit = parseFloat(bitInput.value) || 999;

        if (bit < 1 || bit > 10000) {
            showError('BIT 값은 1에서 10000 사이여야 합니다.');
            return;
        }

        // 로딩 상태
        calculateBtn.disabled = true;
        calculateBtn.textContent = '⏳ 계산 중...';

        // API 호출
        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ input, bit })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || '계산 중 오류가 발생했습니다.');
        }

        // 결과 표시
        displayResults(data);
        resultSection.style.display = 'block';
        resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    } catch (error) {
        showError(error.message);
    } finally {
        calculateBtn.disabled = false;
        calculateBtn.textContent = '🚀 계산하기';
    }
}

/**
 * 결과 표시
 */
function displayResults(data) {
    numberResult.style.display = 'none';
    textResult.style.display = 'none';

    if (data.type === 'number') {
        displayNumberResults(data);
    } else {
        displayTextResults(data);
    }
}

/**
 * 숫자 결과 표시
 */
function displayNumberResults(data) {
    document.getElementById('result-input').textContent = 
        `[${data.input.join(', ')}]`;
    document.getElementById('result-max').textContent = 
        data.nb_max.toFixed(10);
    document.getElementById('result-min').textContent = 
        data.nb_min.toFixed(10);
    document.getElementById('result-diff').textContent = 
        data.difference.toFixed(10);

    numberResult.style.display = 'block';
}

/**
 * 문자 결과 표시
 */
function displayTextResults(data) {
    document.getElementById('result-text').textContent = data.input;
    document.getElementById('result-unicode').textContent = 
        `[${data.unicode.join(', ')}]`;

    // 계산 결과 표시
    const calculationResults = document.getElementById('calculation-results');
    calculationResults.innerHTML = '';

    data.results.forEach((result, index) => {
        const item = document.createElement('div');
        item.className = 'calculation-item';
        item.innerHTML = `
            <div class="calc-header">🔄 계산 ${result.calculation}/3</div>
            <div class="calc-results">
                <div class="calc-result">
                    <div class="calc-result-label">N/B MAX</div>
                    <div class="calc-result-value">${result.nb_max.toFixed(10)}</div>
                </div>
                <div class="calc-result">
                    <div class="calc-result-label">N/B MIN</div>
                    <div class="calc-result-value">${result.nb_min.toFixed(10)}</div>
                </div>
                <div class="calc-result">
                    <div class="calc-result-label">차이</div>
                    <div class="calc-result-value">${result.difference.toFixed(10)}</div>
                </div>
            </div>
        `;
        calculationResults.appendChild(item);
    });

    textResult.style.display = 'block';
}

/**
 * 에러 표시
 */
function showError(message) {
    resultError.textContent = `❌ ${message}`;
    resultError.style.display = 'block';
    resultSection.style.display = 'block';
}

// 페이지 로드 시
document.addEventListener('DOMContentLoaded', () => {
    // 기본 입력 필드에 포커스
    numberInput.focus();

    // 서버 상태 확인
    checkServerStatus();
});

/**
 * 서버 상태 확인
 */
async function checkServerStatus() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        console.log('✅ 서버 상태:', data);
    } catch (error) {
        console.error('❌ 서버 연결 실패:', error);
    }
}
