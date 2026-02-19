"""
검색 모듈
네이버, Bing, YouTube 등 다양한 검색 기능 제공
"""

from .naver_search import search_naver, get_naver_results, fetch_page_content, get_latest_naver_news
from .bing_search import search_bing, get_bing_results, format_bing_results
from .youtube_search import search_youtube, get_youtube_results
from .news_rss import get_naver_news_rss, get_news_by_category, format_news_summary
from .selenium_search import search_naver_selenium, search_bing_selenium
from .naver_news_selenium import get_naver_news_by_category, get_naver_news_search_selenium  # NEW: Selenium 기반 넲이버 뉴스


def multi_search(keyword: str, sources: list = None, limit: int = 5) -> dict:
    """
    여러 검색 엔진에서 동시에 검색
    
    Args:
        keyword: 검색 키워드
        sources: 검색 대상 ('naver', 'bing', 'news', 'youtube')
                 기본값: ['naver', 'bing', 'news']
        limit: 각 검색당 결과 개수 제한
    
    Returns:
        각 검색 엔진별 결과 딕셔너리
    """
    if sources is None:
        sources = ['naver', 'bing', 'news']
    
    results = {}
    
    try:
        if 'naver' in sources or 'web' in sources:
            print("🔍 네이버 검색 중 (Selenium 우선)...")
            try:
                results['naver'] = get_naver_results_smart(keyword, search_type='web', limit=limit, use_selenium=True)
            except Exception as e:
                print(f"❌ 네이버 검색 실패: {e}")
                results['naver'] = []
        
        if 'bing' in sources or 'web' in sources:
            print("🔍 Bing 검색 중 (Selenium 우선)...")
            try:
                results['bing'] = get_bing_results_smart(keyword, search_type='web', limit=limit, use_selenium=True)
            except Exception as e:
                print(f"❌ Bing 검색 실패: {e}")
                results['bing'] = []
        
        if 'news' in sources:
            print("📰 뉴스 검색 중 (Selenium)...")
            try:
                results['news'] = get_naver_news_smart(keyword, limit=limit, use_selenium=True)
            except Exception as e:
                print(f"❌ 뉴스 검색 실패: {e}")
                results['news'] = []
        
        if 'youtube' in sources:
            print("📺 YouTube 검색 중...")
            try:
                results['youtube'] = get_youtube_results(keyword, limit=limit)
            except Exception as e:
                print(f"❌ YouTube 검색 실패: {e}")
                results['youtube'] = []
    
    except Exception as e:
        print(f"전체 검색 오류: {e}")
    
    return results


def format_multi_search_results(results: dict) -> str:
    """
    다중 검색 결과를 보기 좋게 포맷팅
    
    Args:
        results: multi_search의 반환값
    
    Returns:
        포맷팅된 텍스트
    """
    output = []
    
    for source, items in results.items():
        if not items:
            continue
        
        source_icon = {
            'naver': '🔍',
            'bing': '🔎',
            'news': '📰',
            'youtube': '📺'
        }.get(source, '📄')
        
        output.append(f"\n\n{'='*60}")
        output.append(f"{source_icon} {source.upper()} 검색 결과 ({len(items)}개)")
        output.append('='*60)
        
        for i, item in enumerate(items, 1):
            output.append(f"\n{i}. {item.get('title', 'No title')}")
            
            if item.get('description'):
                desc = item['description'][:100]
                output.append(f"   📝 {desc}{'...' if len(item.get('description', '')) > 100 else ''}")
            
            if item.get('date'):
                output.append(f"   📅 {item['date']}")
            
            if item.get('url'):
                output.append(f"   🔗 {item['url']}")
    
    return '\n'.join(output) if output else "검색 결과가 없습니다."


def get_naver_results_smart(keyword: str, search_type: str = 'web', limit: int = 5, use_selenium: bool = True):
    """
    스마트 네이버 검색 - Selenium 우선, 실패 시 일반 BeautifulSoup 사용
    
    Args:
        keyword: 검색 키워드
        search_type: 'web', 'news', 'blog'
        limit: 결과 개수
        use_selenium: Selenium 사용 여부 (기본: True)
    
    Returns:
        검색 결과 리스트
    """
    if use_selenium:
        try:
            results = search_naver_selenium(keyword, search_type, limit)
            if results:
                return results
        except Exception as e:
            print(f"⚠️  Selenium 검색 실패, 일반 방식으로 전환: {e}")
    
    # Fallback: 일반 BeautifulSoup 사용
    return get_naver_results(keyword, search_type, limit)


def get_bing_results_smart(keyword: str, search_type: str = 'web', limit: int = 5, use_selenium: bool = True):
    """
    스마트 Bing 검색 - Selenium 우선, 실패 시 일반 BeautifulSoup 사용
    
    Args:
        keyword: 검색 키워드
        search_type: 'web', 'news'
        limit: 결과 개수
        use_selenium: Selenium 사용 여부 (기본: True)
    
    Returns:
        검색 결과 리스트
    """
    if use_selenium:
        try:
            results = search_bing_selenium(keyword, search_type, limit)
            if results:
                return results
        except Exception as e:
            print(f"⚠️  Selenium 검색 실패, 일반 방식으로 전환: {e}")
    
    # Fallback: 일반 BeautifulSoup 사용
    return get_bing_results(keyword, search_type, limit)


def get_naver_news_smart(keyword: str = None, category_id: int = None, limit: int = 10, use_selenium: bool = True) -> list:
    """
    스마트 네이버 뉴스 수집
    Selenium 기반 동적 크롤링
    
    Args:
        keyword: 검색 키워드 (None 시는 category_id 사용)
        category_id: 카테고리 ID (None=메인, 100=정치, 101=경제, etc)
        limit: 수집 개수
        use_selenium: Selenium 사용 (기본: True)
    
    Returns:
        뉴스 리스트
    """
    keyword_clean = (keyword or '').strip()
    generic_queries = ['오늘 주요 뉴스', '주요 뉴스', '최신 뉴스', '오늘 뉴스', '뉴스']

    if use_selenium:
        try:
            if keyword_clean and keyword_clean not in generic_queries:
                results = get_naver_news_search_selenium(keyword_clean, limit)
            else:
                results = get_naver_news_by_category(category_id, limit)
            
            if results:
                return results
        except Exception as e:
            print(f"⚠️  Selenium 뉴스 수집 실패: {e}")
    
    # Fallback 1: HTML 뉴스 검색 (RSS 검색 404 대응)
    html_keyword = keyword_clean or '뉴스'
    results = get_naver_results(html_keyword, search_type='news', limit=limit)
    if results:
        return results

    # Fallback 2: RSS 섹션 사용
    return get_news_by_category('society', limit)


__all__ = [
    # Naver
    'search_naver',
    'get_naver_results',
    'get_naver_results_smart',
    'fetch_page_content',
    'get_latest_naver_news',
    # Bing
    'search_bing',
    'get_bing_results',
    'get_bing_results_smart',
    'format_bing_results',
    # Selenium (동적 크롤링)
    'search_naver_selenium',
    'search_bing_selenium',
    'get_naver_news_by_category',  # NEW
    'get_naver_news_search_selenium',  # NEW
    'get_naver_news_smart',  # NEW
    # YouTube
    'search_youtube',
    'get_youtube_results',
    # News RSS (legacy)
    'get_naver_news_rss',
    'get_news_by_category',
    'format_news_summary',
    # Multi Search
    'multi_search',
    'format_multi_search_results'
]
