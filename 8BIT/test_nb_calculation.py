"""
N/B 계산 프로그램 자동 테스트 스크립트
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
    """테스트 케이스 실행"""
    
    print("=" * 70)
    print("N/B 계산 프로그램 자동 테스트")
    print("=" * 70)
    
    # 테스트 1: N/B MAX & MIN 동시 계산 (정상 입력)
    print("\n[테스트 1] 정상 입력: N/B MAX & MIN 동시 계산")
    print("-" * 70)
    inputs_1 = [
        "3",              # 옵션: N/B MAX & MIN
        "1.5 2.5 3.5",    # 숫자 입력
        "5.5",            # BIT 값
        "4"               # 종료
    ]
    stdout, stderr = test_with_inputs(inputs_1)
    print(stdout)
    if stderr:
        print(f"에러: {stderr}")
    
    print("\n" + "=" * 70)
    
    # 테스트 2: 문자 입력 (자동 3번 계산)
    print("\n[테스트 2] 문자 입력: 자동으로 3번 계산 실행")
    print("-" * 70)
    inputs_2 = [
        "3",              # 옵션: N/B MAX & MIN
        "test",           # 문자 입력 -> 자동 3번 계산
        "5.5",            # 1번째 계산 BIT
        "6.0",            # 2번째 계산 BIT
        "5.0",            # 3번째 계산 BIT
        "4"               # 종료
    ]
    stdout, stderr = test_with_inputs(inputs_2)
    print(stdout)
    if stderr:
        print(f"에러: {stderr}")
    
    print("\n" + "=" * 70)
    
    # 테스트 3: N/B MAX만 계산
    print("\n[테스트 3] N/B MAX 계산만 수행")
    print("-" * 70)
    inputs_3 = [
        "1",              # 옵션: N/B MAX
        "-1.2 0.5 2.3",   # 음수, 양수 포함
        "",               # BIT 기본값 (5.5)
        "4"               # 종료
    ]
    stdout, stderr = test_with_inputs(inputs_3)
    print(stdout)
    if stderr:
        print(f"에러: {stderr}")
    
    print("\n" + "=" * 70)
    
    # 테스트 4: N/B MIN 계산
    print("\n[테스트 4] N/B MIN 계산 수행")
    print("-" * 70)
    inputs_4 = [
        "2",              # 옵션: N/B MIN
        "-5.0 10.0",      # 큰 범위의 숫자
        "7.0",            # 커스텀 BIT 값
        "4"               # 종료
    ]
    stdout, stderr = test_with_inputs(inputs_4)
    print(stdout)
    if stderr:
        print(f"에러: {stderr}")
    
    print("\n" + "=" * 70)
    print("모든 테스트가 완료되었습니다!")
    print("=" * 70)


if __name__ == "__main__":
    main()
