"""
복합 검색 모듈 테스트
한글 검색 및 Bing 검색 기능 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from search import (
    multi_search, 
    format_multi_search_results,
    get_naver_results,
    get_bing_results,
    get_naver_news_rss,
    get_youtube_results
)


def test_naver_search():
    """네이버 검색 테스트"""
    print("\n" + "="*60)
    print("1️⃣  네이버 검색 테스트")
    print("="*60)
    
    try:
        results = get_naver_results("주요 뉴스", search_type='web', limit=3)
        print(f"✅ 네이버 검색 성공: {len(results)}개 결과")
        for i, result in enumerate(results, 1):
            print(f"\n  {i}. {result.get('title', 'No title')[:60]}")
            print(f"     URL: {result.get('url', 'N/A')[:60]}")
        return True
    except Exception as e:
        print(f"❌ 네이버 검색 실패: {e}")
        return False


def test_bing_search():
    """Bing 검색 테스트"""
    print("\n" + "="*60)
    print("2️⃣  Bing 검색 테스트")
    print("="*60)
    
    try:
        results = get_bing_results("주요 뉴스", search_type='web', limit=3)
        print(f"✅ Bing 검색 성공: {len(results)}개 결과")
        for i, result in enumerate(results, 1):
            print(f"\n  {i}. {result.get('title', 'No title')[:60]}")
            print(f"     URL: {result.get('url', 'N/A')[:60]}")
        return True
    except Exception as e:
        print(f"❌ Bing 검색 실패: {e}")
        return False


def test_news_search():
    """뉴스 RSS 검색 테스트"""
    print("\n" + "="*60)
    print("3️⃣  뉴스 RSS 검색 테스트")
    print("="*60)
    
    try:
        results = get_naver_news_rss("주요 뉴스", limit=3)
        print(f"✅ 뉴스 검색 성공: {len(results)}개 결과")
        for i, result in enumerate(results, 1):
            print(f"\n  {i}. {result.get('title', 'No title')[:60]}")
            if result.get('date'):
                print(f"     📅 {result['date']}")
        return True
    except Exception as e:
        print(f"❌ 뉴스 검색 실패: {e}")
        return False


def test_youtube_search():
    """YouTube 검색 테스트"""
    print("\n" + "="*60)
    print("4️⃣  YouTube 검색 테스트")
    print("="*60)
    
    try:
        results = get_youtube_results("주요 뉴스", limit=1)
        print(f"✅ YouTube 검색 성공: {len(results)}개 결과")
        for i, result in enumerate(results, 1):
            print(f"\n  {i}. {result.get('title', 'No title')[:60]}")
        return True
    except Exception as e:
        print(f"❌ YouTube 검색 실패: {e}")
        return False


def test_multi_search():
    """다중 검색 테스트"""
    print("\n" + "="*60)
    print("5️⃣  다중 검색 테스트 (Naver + Bing + News)")
    print("="*60)
    
    try:
        keyword = "주요 뉴스"
        print(f"\n🔍 '{keyword}'에 대해 다중 검색 중...")
        
        results = multi_search(
            keyword=keyword,
            sources=['naver', 'bing', 'news'],
            limit=2
        )
        
        formatted = format_multi_search_results(results)
        print(formatted)
        
        total = sum(len(v) for v in results.values())
        print(f"\n✅ 다중 검색 완료: 총 {total}개 결과")
        return True
    except Exception as e:
        print(f"❌ 다중 검색 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_korean_search():
    """한글 검색 테스트"""
    print("\n" + "="*60)
    print("6️⃣  한글 검색 테스트")
    print("="*60)
    
    keywords = ["주요 뉴스", "인공지능", "파이썬 배우기"]
    
    results_summary = {}
    for keyword in keywords:
        print(f"\n📌 검색 키워드: {keyword}")
        
        try:
            # Naver만 테스트
            results = get_naver_results(keyword, search_type='web', limit=1)
            results_summary[keyword] = len(results)
            
            if results:
                print(f"   ✅ 결과: {results[0].get('title', 'N/A')[:50]}")
            else:
                print(f"   ⚠️  결과 없음")
        except Exception as e:
            print(f"   ❌ 오류: {str(e)[:50]}")
    
    return all(v > 0 for v in results_summary.values())


def main():
    """모든 테스트 실행"""
    print("\n")
    print("🧪 " + "="*58)
    print("   검색 모듈 통합 테스트 (한글 + Bing 검색)")
    print("="*60)
    
    tests = [
        ("네이버 검색", test_naver_search),
        ("Bing 검색", test_bing_search),
        ("뉴스 RSS 검색", test_news_search),
        ("YouTube 검색", test_youtube_search),
        ("한글 검색", test_korean_search),
        ("다중 검색", test_multi_search),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} 전체 실패: {e}")
            results[test_name] = False
    
    # 최종 결과
    print("\n\n" + "="*60)
    print("📊 최종 결과")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} | {test_name}")
    
    print("="*60)
    print(f"결과: {passed}/{total} 테스트 성공")
    print("="*60 + "\n")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
