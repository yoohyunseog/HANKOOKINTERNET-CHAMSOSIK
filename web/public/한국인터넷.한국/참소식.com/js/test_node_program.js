#!/usr/bin/env node

const { spawn } = require('child_process');
const fs = require('fs');

function testWithInputs(inputs, description) {
    return new Promise((resolve) => {
        console.log('\n' + '='.repeat(70));
        console.log(description);
        console.log('='.repeat(70));

        const child = spawn('E:\\node\\node.exe', ['nb_calculation_node.js'], {
            cwd: 'E:\\Ai project\\사이트\\8BIT\\js'
        });

        let output = '';
        let inputIndex = 0;

        child.stdout.on('data', (data) => {
            output += data.toString();
            process.stdout.write(data);

            // 입력 프롬프트가 나타나면 다음 입력을 보냄
            if (data.toString().includes('입력하세요') && inputIndex < inputs.length) {
                setTimeout(() => {
                    child.stdin.write(inputs[inputIndex++] + '\n');
                }, 100);
            }
        });

        child.stderr.on('data', (data) => {
            console.error(`stderr: ${data}`);
        });

        child.on('close', (code) => {
            console.log(`\n프로세스 종료 코드: ${code}\n`);
            resolve(output);
        });

        // 첫 번째 입력 시작
        if (inputs.length > 0) {
            setTimeout(() => {
                child.stdin.write(inputs[inputIndex++] + '\n');
            }, 500);
        }
    });
}

async function main() {
    console.log('\n\n');
    console.log('╔' + '═'.repeat(68) + '╗');
    console.log('║' + ' '.repeat(15) + 'Node.js N/B 계산 프로그램 자동 테스트' + ' '.repeat(16) + '║');
    console.log('╚' + '═'.repeat(68) + '╝');

    // 테스트 1: 문자 입력 (자동 3번 계산)
    await testWithInputs(
        ['안녕하세요', '5.5', '6.0', '5.0', 'q'],
        '[테스트 1] 문자 입력 - 자동 3번 계산'
    );

    // 테스트 2: 숫자 입력 (정상 계산)
    await testWithInputs(
        ['1.5 2.5 3.5', '5.5', 'q'],
        '[테스트 2] 숫자 입력 - 정상 계산'
    );

    // 테스트 3: 음수/양수 포함
    await testWithInputs(
        ['-1.2 0.5 2.3', '5.5', 'test', '7.0', '6.5', '5.5', 'q'],
        '[테스트 3] 음수/양수 입력 + 문자 입력'
    );

    console.log('\n\n');
    console.log('╔' + '═'.repeat(68) + '╗');
    console.log('║' + ' '.repeat(20) + '모든 테스트 완료!' + ' '.repeat(30) + '║');
    console.log('╚' + '═'.repeat(68) + '╝');
    console.log('\n');
}

main().catch(console.error);
