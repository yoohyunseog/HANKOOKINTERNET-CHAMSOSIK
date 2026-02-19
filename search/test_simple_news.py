"""
간단한 뉴스 검색 테스트 (BeautifulSoup만 사용)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from search import get_naver_results, search_youtube

keyword = "주요 뉴스"

print(f"\n🔍 '{keyword}' 검색 (BeautifulSoup 방식)")
print("=" * 70)

# Naver 뉴스
print("\n📰 네이버 뉴스 검색...")
try:
    results = get_naver_results(keyword, search_type='news', limit=5)
    print(f"✅ 결과: {len(results)}개")
    
    for i, result in enumerate(results, 1):
        print(f"\n[{i}] {result.get('title', 'N/A')[:80]}")
        if result.get('description'):
            print(f"    📝 {result['description'][:100]}")
        if result.get('url'):
            print(f"    🔗 {result['url'][:80]}")
except Exception as e:
    print(f"❌ 오류: {e}")
    import traceback
    traceback.print_exc()

# YouTube
print("\n📺 유튜브 검색...")
try:
    youtube_url = search_youtube(keyword)
    print(f"✅ {youtube_url}")
except Exception as e:
    print(f"❌ 오류: {e}")

print("\n" + "=" * 70 + "\n")
