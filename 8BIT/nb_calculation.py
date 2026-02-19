"""
N/B MAX, N/B MIN 계산 프로그램
JavaScript의 BIT 계산 시스템을 Python으로 변환
"""

import math
import sys

class NBCalculator:
    """N/B 가중치 계산 클래스"""
    
    def __init__(self):
        self.SUPER_BIT = 0
    
    def initialize_arrays(self, count):
        """배열 초기화"""
        arrays = {
            'BIT_START_A50': [0] * count,
            'BIT_START_A100': [0] * count,
            'BIT_START_B50': [0] * count,
            'BIT_START_B100': [0] * count,
            'BIT_START_NBA100': [0] * count,
        }
        return arrays
    
    def calculate_bit(self, nb, bit=5.5, reverse=False):
        """N/B 값을 계산하는 함수"""
        
        if len(nb) < 2:
            return bit / 100
        
        BIT_NB = bit
        max_val = max(nb)
        min_val = min(nb)
        COUNT = 50
        CONT = 20
        range_val = max_val - min_val
        
        # 음수와 양수 범위를 구분하여 증분 계산
        negative_range = abs(min_val) if min_val < 0 else 0
        positive_range = max_val if max_val > 0 else 0
        
        negative_increment = negative_range / (COUNT * len(nb) - 1) if (COUNT * len(nb) - 1) > 0 else 0
        positive_increment = positive_range / (COUNT * len(nb) - 1) if (COUNT * len(nb) - 1) > 0 else 0
        
        arrays = self.initialize_arrays(COUNT * len(nb))
        count = 0
        total_sum = 0
        
        for value in nb:
            for i in range(COUNT):
                BIT_END = 1
                
                # 부호에 따른 A50, B50 계산
                if value < 0:
                    A50 = min_val + negative_increment * (count + 1)
                else:
                    A50 = min_val + positive_increment * (count + 1)
                
                A100 = (count + 1) * BIT_NB / (COUNT * len(nb))
                
                if value < 0:
                    B50 = A50 - negative_increment * 2
                    B100 = A50 + negative_increment
                else:
                    B50 = A50 - positive_increment * 2
                    B100 = A50 + positive_increment
                
                NBA100 = A100 / (len(nb) - BIT_END) if (len(nb) - BIT_END) > 0 else 0
                
                arrays['BIT_START_A50'][count] = A50
                arrays['BIT_START_A100'][count] = A100
                arrays['BIT_START_B50'][count] = B50
                arrays['BIT_START_B100'][count] = B100
                arrays['BIT_START_NBA100'][count] = NBA100
                count += 1
            
            total_sum += value
        
        # Reverse 옵션 처리
        if reverse:
            arrays['BIT_START_NBA100'].reverse()
        
        # NB50 계산
        NB50 = 0
        for value in nb:
            for a in range(len(arrays['BIT_START_NBA100'])):
                if arrays['BIT_START_B50'][a] <= value <= arrays['BIT_START_B100'][a]:
                    NB50 += arrays['BIT_START_NBA100'][min(a, len(arrays['BIT_START_NBA100']) - 1)]
                    break
        
        # 평균 비율 기반 NB50 정규화
        BIT = max((10 - len(nb)) * 10, 1)
        abs_max = abs(max_val) if max_val != 0 else 1
        average_ratio = (total_sum / (len(nb) * abs_max)) * 100
        NB50 = min((NB50 / 100) * average_ratio, BIT_NB)
        
        if len(nb) == 2:
            return bit - NB50
        
        return NB50
    
    def update_super_bit(self, new_value):
        """SUPER_BIT 업데이트"""
        self.SUPER_BIT = new_value
    
    def bit_max_nb(self, nb, bit=5.5):
        """N/B MAX 계산 (역방향 비활성화)"""
        result = self.calculate_bit(nb, bit, False)
        
        if not math.isfinite(result) or math.isnan(result) or result > 100 or result < -100:
            return self.SUPER_BIT
        else:
            self.update_super_bit(result)
            return result
    
    def bit_min_nb(self, nb, bit=5.5):
        """N/B MIN 계산 (역방향 활성화)"""
        result = self.calculate_bit(nb, bit, True)
        
        if not math.isfinite(result) or math.isnan(result) or result > 100 or result < -100:
            return self.SUPER_BIT
        else:
            self.update_super_bit(result)
            return result


def parse_input(input_str):
    """문자열 입력을 숫자 리스트로 변환"""
    try:
        # 쉼표, 공백으로 구분된 입력을 파싱
        values = [float(x.strip()) for x in input_str.replace(',', ' ').split() if x.strip()]
        if len(values) < 2:
            print("오류: 최소 2개 이상의 숫자를 입력해주세요.")
            return None, False
        return values, False
    except ValueError:
        # 문자 입력 시 자동으로 3번 계산하도록 플래그 반환
        print(f"\n⚠ 문자 입력 감지: '{input_str}'")
        print("✓ 자동으로 3번 계산을 실행합니다.\n")
        return None, True


def main():
    """메인 함수"""
    print("=" * 60)
    print("N/B MAX, N/B MIN 계산 프로그램")
    print("=" * 60)
    print()
    
    calculator = NBCalculator()
    
    while True:
        # 직접 입력 받기
        input_str = input("\n문자를 입력하세요 (또는 q를 입력하여 종료): ").strip()
        
        if input_str.lower() == 'q':
            print("\n프로그램을 종료합니다.")
            break
        
        # 숫자 입력 시 처리
        try:
            values = [float(x.strip()) for x in input_str.replace(',', ' ').split() if x.strip()]
            if len(values) >= 2:
                # 숫자 입력이 정상적이면 1번 계산
                print("\n✓ 정상 입력: 1번 계산 실행")
                bit_input = input("BIT 값을 입력하세요 (기본값: 5.5): ").strip()
                try:
                    bit_value = float(bit_input) if bit_input else 5.5
                except ValueError:
                    print("BIT 값이 잘못되었습니다. 기본값(5.5)를 사용합니다.")
                    bit_value = 5.5
                
                print("\n" + "=" * 60)
                print(f"입력값: {values}")
                print(f"BIT 값: {bit_value}")
                print("=" * 60)
                
                try:
                    max_result = calculator.bit_max_nb(values, bit_value)
                    min_result = calculator.bit_min_nb(values, bit_value)
                    print(f"\n✓ N/B MAX 결과: {max_result:.6f}")
                    print(f"✓ N/B MIN 결과: {min_result:.6f}")
                    print(f"✓ 차이 (MAX - MIN): {max_result - min_result:.6f}")
                except Exception as e:
                    print(f"오류가 발생했습니다: {str(e)}")
                continue
            else:
                # 숫자가 1개 이하면 문자 입력으로 간주
                raise ValueError
        except ValueError:
            # 문자 입력 시 3번 계산 실행
            print(f"\n⚠ 문자 입력 감지: '{input_str}'")
            print("✓ 자동으로 3번 계산을 실행합니다.\n")
            print("=" * 60)
            
            for i in range(3):
                print(f"\n[계산 {i+1}/3]")
                print("-" * 60)
                
                # BIT 값 입력 (선택사항)
                bit_input = input("BIT 값을 입력하세요 (기본값: 5.5): ").strip()
                try:
                    bit_value = float(bit_input) if bit_input else 5.5
                except ValueError:
                    print("BIT 값이 잘못되었습니다. 기본값(5.5)를 사용합니다.")
                    bit_value = 5.5
                
                # 계산 실행
                try:
                    max_result = calculator.bit_max_nb([], bit_value)
                    min_result = calculator.bit_min_nb([], bit_value)
                    print(f"✓ N/B MAX 결과: {max_result:.6f}")
                    print(f"✓ N/B MIN 결과: {min_result:.6f}")
                    print(f"✓ 차이 (MAX - MIN): {max_result - min_result:.6f}")
                except Exception as e:
                    print(f"오류가 발생했습니다: {str(e)}")
            
            print("\n" + "=" * 60)
            print("3번 계산이 완료되었습니다.")
            print("=" * 60)


if __name__ == "__main__":
    main()
