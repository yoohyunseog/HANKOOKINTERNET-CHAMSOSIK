"""
네이버 크리에이터 트렌드 분석기 테스트
- 설정 파일 확인
- 필요한 패키지 확인
- 기본 기능 테스트
"""

import os
import json
import sys

def check_config_file():
    """설정 파일 확인"""
    config_file = "config/naver_creator_config.json"
    
    print("=" * 50)
    print("1. 설정 파일 확인")
    print("=" * 50)
    
    if not os.path.exists(config_file):
        print(f"❌ 설정 파일이 없습니다: {config_file}")
        print("   config/naver_creator_config.json 파일을 생성해주세요.")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"✅ 설정 파일 존재: {config_file}")
        
        # 필수 항목 확인
        required_fields = ['naver_id', 'naver_password', 'blog_id']
        for field in required_fields:
            if field in config and config[field] and config[field] != f'your_{field}':
                print(f"   ✅ {field}: 설정됨")
            else:
                print(f"   ❌ {field}: 설정 필요")
        
        return True
        
    except Exception as e:
        print(f"❌ 설정 파일 읽기 오류: {e}")
        return False

def check_packages():
    """필요한 패키지 확인"""
    print("\n" + "=" * 50)
    print("2. 필요한 패키지 확인")
    print("=" * 50)
    
    packages = {
        'selenium': '웹 자동화',
        'pandas': '데이터 처리',
        'schedule': '예약 실행'
    }
    
    all_installed = True
    
    for package, description in packages.items():
        try:
            __import__(package)
            print(f"✅ {package:15s} - {description}")
        except ImportError:
            print(f"❌ {package:15s} - {description} (설치 필요)")
            all_installed = False
    
    if not all_installed:
        print("\n⚠️ 누락된 패키지를 설치하세요:")
        print("   pip install -r 8BIT/requirements_naver_creator.txt")
    
    return all_installed

def check_chrome_driver():
    """Chrome 드라이버 확인"""
    print("\n" + "=" * 50)
    print("3. Chrome 드라이버 확인")
    print("=" * 50)
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        driver.quit()
        
        print("✅ Chrome 드라이버 정상 작동")
        return True
        
    except Exception as e:
        print(f"❌ Chrome 드라이버 오류: {e}")
        print("\n해결 방법:")
        print("1. Chrome 브라우저 최신 버전 설치")
        print("2. ChromeDriver 자동 설치:")
        print("   pip install webdriver-manager")
        return False

def check_data_directory():
    """데이터 디렉토리 확인"""
    print("\n" + "=" * 50)
    print("4. 데이터 디렉토리 확인")
    print("=" * 50)
    
    data_dir = "data/naver_creator_trends"
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        print(f"✅ 데이터 디렉토리 생성: {data_dir}")
    else:
        print(f"✅ 데이터 디렉토리 존재: {data_dir}")
        
        # 기존 파일 확인
        files = list(os.listdir(data_dir))
        if files:
            print(f"   📁 기존 파일 {len(files)}개:")
            for file in files[:5]:  # 처음 5개만
                print(f"      - {file}")
            if len(files) > 5:
                print(f"      ... 외 {len(files) - 5}개")
        else:
            print("   📁 파일 없음 (새로 시작)")
    
    return True

def test_basic_functionality():
    """기본 기능 테스트"""
    print("\n" + "=" * 50)
    print("5. 기본 기능 테스트")
    print("=" * 50)
    
    try:
        # 데이터 구조 테스트
        test_data = {
            'collection_time': '2026-02-18T14:30:22',
            'blog_id': 'test_blog',
            'total_items': 5,
            'trend_data': [
                {
                    'index': 1,
                    'title': '테스트 트렌드',
                    'keywords': ['키워드1', '키워드2'],
                    'metrics': {'조회수': '1234'},
                    'timestamp': '2026-02-18T14:30:22'
                }
            ]
        }
        
        # JSON 저장 테스트
        test_file = "data/naver_creator_trends/test_data.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        print("✅ JSON 저장 테스트 통과")
        
        # JSON 로드 테스트
        with open(test_file, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        print("✅ JSON 로드 테스트 통과")
        
        # 데이터 검증
        assert loaded_data['total_items'] == 5
        assert len(loaded_data['trend_data']) == 1
        
        print("✅ 데이터 검증 테스트 통과")
        
        # 테스트 파일 삭제
        os.remove(test_file)
        
        return True
        
    except Exception as e:
        print(f"❌ 기본 기능 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("""
    ╔══════════════════════════════════════════════════╗
    ║  네이버 크리에이터 트렌드 분석기 테스트          ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    results = []
    
    # 테스트 실행
    results.append(("설정 파일", check_config_file()))
    results.append(("필요한 패키지", check_packages()))
    results.append(("Chrome 드라이버", check_chrome_driver()))
    results.append(("데이터 디렉토리", check_data_directory()))
    results.append(("기본 기능", test_basic_functionality()))
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("테스트 결과 요약")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{name:20s} ... {status}")
    
    print(f"\n총 {total}개 테스트 중 {passed}개 통과")
    
    if passed == total:
        print("\n🎉 모든 테스트 통과! 프로그램을 실행할 수 있습니다.")
        print("   실행: python 8BIT/naver_creator_trend_analyzer.py")
    else:
        print("\n⚠️ 일부 테스트 실패. 위의 오류를 해결한 후 다시 시도하세요.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
