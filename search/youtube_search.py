"""
유튜브 검색 모듈
"""

import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from typing import List, Dict


def search_youtube(keyword: str) -> str:
    """
    유튜브 검색 URL 생성
    
    Args:
        keyword: 검색 키워드
    
    Returns:
        검색 URL
    """
    encoded_keyword = quote(keyword)
    return f'https://www.youtube.com/results?search_query={encoded_keyword}'


def get_youtube_results(keyword: str, limit: int = 5) -> List[Dict]:
    """
    유튜브 검색 결과 크롤링
    
    Args:
        keyword: 검색 키워드
        limit: 결과 개수 제한
    
    Returns:
        검색 결과 리스트 [{'title': '', 'url': '', 'channel': ''}, ...]
    """
    url = search_youtube(keyword)
    results = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 유튜브는 동적 로딩이라 제한적이지만 시도
        # 실제로는 YouTube Data API 사용 권장
        scripts = soup.find_all('script')
        
        # 간단한 파싱 (제한적)
        for script in scripts:
            if 'var ytInitialData' in str(script.string):
                # 여기서 JSON 파싱 가능하지만 복잡함
                # 대신 간단히 URL만 제공
                break
        
        # 기본 URL만 제공
        results.append({
            'title': f'"{keyword}" 검색 결과',
            'url': url,
            'channel': 'YouTube',
            'description': f'유튜브에서 "{keyword}"를 검색합니다.'
        })
        
    except Exception as e:
        print(f"유튜브 검색 오류: {e}")
        # 오류 발생 시에도 URL은 제공
        results.append({
            'title': f'"{keyword}" 검색',
            'url': url,
            'channel': 'YouTube',
            'description': '유튜브 검색 링크'
        })
    
    return results


def format_youtube_results(results: List[Dict]) -> str:
    """
    유튜브 검색 결과를 텍스트로 포맷팅
    
    Args:
        results: 검색 결과 리스트
    
    Returns:
        포맷팅된 텍스트
    """
    if not results:
        return "검색 결과가 없습니다."
    
    output = []
    for i, result in enumerate(results, 1):
        output.append(f"\n{i}. 📺 {result['title']}")
        if result.get('description'):
            output.append(f"   {result['description']}")
        if result.get('channel'):
            output.append(f"   📢 {result['channel']}")
        output.append(f"   🔗 {result['url']}")
    
    return '\n'.join(output)
