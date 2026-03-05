"""
수정된 N/B 계산 프로그램 테스트
"""

import subprocess
import sys

def test_with_inputs(inputs):
    """입력값들을 자동으로 전달하여 테스트"""
    process = subprocess.Popen(
        [sys.executable, "nb_calculation.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        cwd="."
    )
    
    input_str = '\n'.join(inputs) + '\n'
    stdout, stderr = process.communicate(input=input_str)
    
    return stdout, stderr


def main():
    """테스트 실행"""
    
    print("=" * 70)
    print("수정된 N/B 계산 프로그램 테스트")
    print("=" * 70)
    
    # 테스트 1: 문자 입력 (자동 3번 계산)
    print("\n[테스트 1] 문자 입력 - 자동 3번 계산")
    print("-" * 70)
    inputs_1 = [
        "hello",    # 문자 입력 -> 3번 계산
        "5.5",      # 1번째 BIT
        "6.0",      # 2번째 BIT
        "5.0",      # 3번째 BIT
        "q"         # 종료
    ]
    stdout, _ = test_with_inputs(inputs_1)
    print(stdout)
    
    print("\n" + "=" * 70)
    
    # 테스트 2: 숫자 입력 (정상 계산)
    print("\n[테스트 2] 숫자 입력 - 정상 계산")
    print("-" * 70)
    inputs_2 = [
        "1.5 2.5 3.5",  # 숫자 입력 -> 1번 계산
        "5.5",          # BIT 값
        "q"             # 종료
    ]
    stdout, _ = test_with_inputs(inputs_2)
    print(stdout)
    
    print("\n" + "=" * 70)
    
    # 테스트 3: 다양한 문자로 3번 계산
    print("\n[테스트 3] 특수문자 입력 - 자동 3번 계산")
    print("-" * 70)
    inputs_3 = [
        "test@123",     # 특수문자 포함 -> 3번 계산
        "7.0",          # 1번째 BIT
        "6.5",          # 2번째 BIT
        "5.5",          # 3번째 BIT
        "q"             # 종료
    ]
    stdout, _ = test_with_inputs(inputs_3)
    print(stdout)
    
    print("\n" + "=" * 70)
    print("모든 테스트 완료!")
    print("=" * 70)


if __name__ == "__main__":
    main()
