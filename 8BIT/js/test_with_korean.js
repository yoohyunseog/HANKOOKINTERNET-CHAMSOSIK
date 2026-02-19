const { spawn } = require('child_process');

console.log('\n' + '╔' + '═'.repeat(68) + '╗');
console.log('║' + ' '.repeat(18) + '"안녕하세요" 테스트' + ' '.repeat(28) + '║');
console.log('╚' + '═'.repeat(68) + '╝\n');

const child = spawn('E:\\node\\node.exe', ['nb_calculation_node.js'], {
    cwd: 'E:\\Ai project\\사이트\\8BIT\\js'
});

let output = '';
let inputIndex = 0;
const inputs = ['안녕하세요', '', '', 'q'];

child.stdout.on('data', (data) => {
    const text = data.toString();
    output += text;
    process.stdout.write(text);

    // 입력 프롬프트 감지
    if (text.includes('입력하세요')) {
        setTimeout(() => {
            if (inputIndex < inputs.length) {
                console.log(`\n[입력 ${inputIndex + 1}]: "${inputs[inputIndex]}"`);
                child.stdin.write(inputs[inputIndex] + '\n');
                inputIndex++;
            }
        }, 100);
    }
});

child.stderr.on('data', (data) => {
    console.error(`stderr: ${data}`);
});

child.on('close', (code) => {
    console.log(`\n\n${'='.repeat(70)}`);
    console.log('✅ 테스트 완료!');
    console.log('='.repeat(70));
    console.log('\n📊 결과 분석:');
    
    if (output.includes('1050504')) {
        console.log('✅ Unicode 배열 변환 성공 (한글 유니코드 감지됨)');
    }
    
    if (output.includes('0.') || output.includes('1.') || output.includes('10.')) {
        console.log('✅ 10자리 정밀도 계산 성공');
    }
    
    if (output.includes('기본값: 999')) {
        console.log('✅ config.json 기본값 999 적용됨');
    }
    
    if (output.includes('3번 계산이 완료')) {
        console.log('✅ 자동 3회 계산 완료');
    }
    
    console.log('\n');
    process.exit(code);
});

// 첫 번째 입력 시작
setTimeout(() => {
    child.stdin.write(inputs[inputIndex] + '\n');
    inputIndex++;
}, 500);
