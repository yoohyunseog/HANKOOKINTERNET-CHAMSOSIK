"""
리팩토링된 Ollama IDE GUI 테스트 스크립트
"""

import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """모든 모듈 import 테스트"""
    print("=" * 60)
    print("모듈 Import 테스트 시작")
    print("=" * 60)
    
    try:
        print("\n[1/8] config 모듈 import...")
        from gui.config import OLLAMA_URL, COLORS, CATEGORIES
        print("✅ config 모듈 import 성공")
        print(f"   - OLLAMA_URL: {OLLAMA_URL}")
        print(f"   - 색상 테마: {len(COLORS)}개")
        print(f"   - 카테고리: {len(CATEGORIES)}개")
        
        print("\n[2/8] utils 모듈 import...")
        from gui.utils import log_debug, clean_text_simple, format_news_answer
        print("✅ utils 모듈 import 성공")
        
        print("\n[3/8] news_manager 모듈 import...")
        from gui.news_manager import NewsManager, DateHelper
        print("✅ news_manager 모듈 import 성공")
        
        print("\n[4/8] search_handler 모듈 import...")
        from gui.search_handler import SearchHandler
        print("✅ search_handler 모듈 import 성공")
        
        print("\n[5/8] ai_handler 모듈 import...")
        from gui.ai_handler import AIHandler
        print("✅ ai_handler 모듈 import 성공")
        
        print("\n[6/8] repeat_manager 모듈 import...")
        from gui.repeat_manager import RepeatManager, BatchManager
        print("✅ repeat_manager 모듈 import 성공")
        
        print("\n[7/8] ui_builder 모듈 import...")
        from gui.ui_builder import UIBuilder
        print("✅ ui_builder 모듈 import 성공")
        
        print("\n[8/8] 메인 모듈 import...")
        import ollama_ide_gui_refactored
        print("✅ 메인 모듈 import 성공")
        
        print("\n" + "=" * 60)
        print("✅ 모든 모듈 import 성공!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ Import 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_managers():
    """매니저 클래스 초기화 테스트"""
    print("\n" + "=" * 60)
    print("매니저 클래스 초기화 테스트")
    print("=" * 60)
    
    try:
        from gui.news_manager import NewsManager, DateHelper
        from gui.ai_handler import AIHandler
        from gui.search_handler import SearchHandler
        from gui.repeat_manager import RepeatManager, BatchManager
        
        print("\n[1/5] NewsManager 초기화...")
        news_mgr = NewsManager()
        print("✅ NewsManager 초기화 성공")
        
        print("\n[2/5] AIHandler 초기화...")
        ai_handler = AIHandler(model="test-model")
        print("✅ AIHandler 초기화 성공")
        print(f"   - 현재 모델: {ai_handler.current_model}")
        
        print("\n[3/5] SearchHandler 초기화...")
        search_handler = SearchHandler(ai_handler=ai_handler)
        print("✅ SearchHandler 초기화 성공")
        
        print("\n[4/5] RepeatManager 초기화...")
        repeat_mgr = RepeatManager()
        print("✅ RepeatManager 초기화 성공")
        print(f"   - 활성화 상태: {repeat_mgr.is_active()}")
        
        print("\n[5/5] BatchManager 초기화...")
        batch_mgr = BatchManager()
        print("✅ BatchManager 초기화 성공")
        print(f"   - 활성화 상태: {batch_mgr.is_active()}")
        
        print("\n" + "=" * 60)
        print("✅ 모든 매니저 초기화 성공!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ 매니저 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_utilities():
    """유틸리티 함수 테스트"""
    print("\n" + "=" * 60)
    print("유틸리티 함수 테스트")
    print("=" * 60)
    
    try:
        from gui.utils import clean_text_simple, format_news_answer, extract_news_items
        from gui.news_manager import DateHelper
        
        print("\n[1/4] clean_text_simple 테스트...")
        test_text = "<p>Hello &nbsp; World</p>"
        result = clean_text_simple(test_text)
        assert "Hello World" in result
        print(f"✅ clean_text_simple: '{test_text}' → '{result}'")
        
        print("\n[2/4] format_news_answer 테스트...")
        test_news = "1️⃣ 뉴스1 // 2️⃣ 뉴스2"
        result = format_news_answer(test_news)
        assert "\n" in result
        print(f"✅ format_news_answer: 줄바꿈 적용됨")
        
        print("\n[3/4] extract_news_items 테스트...")
        test_answer = "1. 첫번째 뉴스\n2. 두번째 뉴스\n- 세번째 뉴스"
        items = extract_news_items(test_answer)
        print(f"✅ extract_news_items: {len(items)}개 항목 추출")
        
        print("\n[4/4] DateHelper 테스트...")
        assert DateHelper.is_today_news_date("오늘") == True
        assert DateHelper.is_today_news_date("어제") == False
        print("✅ DateHelper: 날짜 판단 정상 작동")
        
        print("\n" + "=" * 60)
        print("✅ 모든 유틸리티 함수 테스트 통과!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ 유틸리티 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 실행"""
    print("\n" + "🚀 " * 15)
    print("Ollama IDE GUI 리팩토링 테스트")
    print("🚀 " * 15 + "\n")
    
    results = []
    
    # Import 테스트
    results.append(("Import 테스트", test_imports()))
    
    # 매니저 테스트
    results.append(("매니저 초기화 테스트", test_managers()))
    
    # 유틸리티 테스트
    results.append(("유틸리티 함수 테스트", test_utilities()))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ 성공" if passed else "❌ 실패"
        print(f"{status} - {name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 모든 테스트 통과! 리팩토링 성공!")
        print("\n실행 명령어:")
        print("  python ollama_ide_gui_refactored.py")
    else:
        print("⚠️ 일부 테스트 실패")
    print("=" * 60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
