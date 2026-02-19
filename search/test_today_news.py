"""
오늘 주요 뉴스 검색 테스트
Selenium 기반 동적 크롤링 활용
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from search import (
    get_naver_results_smart,
    get_bing_results_smart,
    get_naver_news_rss,
    search_youtube,
    format_multi_search_results,
    multi_search
)


def test_today_news():
    """오늘 주요 뉴스 검색 테스트"""
    
    keyword = "오늘 주요 뉴스"
    
    print("\n" + "="*70)
    print(f"🔍 '{keyword}' 검색 테스트")
    print("="*70)
    
    # 1. Naver 뉴스 검색 (Selenium)
    print("\n📰 Naver 뉴스 검색 (Selenium - Chrome 드라이버)...")
    try:
        naver_results = get_naver_results_smart(keyword, search_type='news', limit=5, use_selenium=True)
        print(f"✅ 결과: {len(naver_results)}개")
        
        if naver_results:
            for i, result in enumerate(naver_results[:3], 1):
                print(f"\n  [{i}] {result.get('title', 'N/A')[:80]}")
                if result.get('date'):
                    print(f"      📅 {result['date']}")
                if result.get('description'):
                    print(f"      📝 {result['description'][:100]}")
        else:
            print("  ⚠️  검색 결과 없음")
    except Exception as e:
        print(f"  ❌ 오류: {e}")
    
    # 2. Bing 검색 (Selenium)
    print("\n\n🌐 Bing 웹 검색 (Selenium - Chrome 드라이버)...")
    try:
        bing_results = get_bing_results_smart("today news", search_type='web', limit=5, use_selenium=True)
        print(f"✅ 결과: {len(bing_results)}개")
        
        if bing_results:
            for i, result in enumerate(bing_results[:3], 1):
                print(f"\n  [{i}] {result.get('title', 'N/A')[:80]}")
                if result.get('description'):
                    print(f"      📝 {result['description'][:100]}")
        else:
            print("  ⚠️  검색 결과 없음")
    except Exception as e:
        print(f"  ❌ 오류: {e}")
    
    # 3. YouTube 검색
    print("\n\n📺 YouTube 검색...")
    try:
        youtube_url = search_youtube(keyword)
        print(f"✅ YouTube 검색 링크:")
        print(f"   {youtube_url[:100]}")
    except Exception as e:
        print(f"  ❌ 오류: {e}")
    
    # 4. 다중 검색
    print("\n\n" + "="*70)
    print("🔄 다중 검색 (Naver + Bing + News)")
    print("="*70)
    
    try:
        results = multi_search(
            keyword=keyword,
            sources=['naver', 'bing', 'news'],
            limit=3
        )
        
        formatted = format_multi_search_results(results)
        print(formatted)
        
        # 통계
        total = sum(len(v) for v in results.values() if v)
        print(f"\n✅ 총 {total}개 검색 결과 수집 완료")
        
    except Exception as e:
        print(f"❌ 다중 검색 오류: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    test_today_news()
