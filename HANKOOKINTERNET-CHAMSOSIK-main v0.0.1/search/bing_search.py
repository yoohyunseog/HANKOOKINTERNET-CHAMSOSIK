"""
Bing 검색 모듈
"""

import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from typing import List, Dict
import re


def search_bing(keyword: str, search_type: str = 'web') -> str:
    """
    Bing 검색 URL 생성
    
    Args:
        keyword: 검색 키워드
        search_type: 검색 유형 ('web', 'news', 'image', 'video')
    
    Returns:
        검색 URL
    """
    encoded_keyword = quote(keyword)
    
    url_map = {
        'web': f'https://www.bing.com/search?q={encoded_keyword}',
        'news': f'https://www.bing.com/news/search?q={encoded_keyword}',
        'image': f'https://www.bing.com/images/search?q={encoded_keyword}',
        'video': f'https://www.bing.com/videos/search?q={encoded_keyword}'
    }
    
    return url_map.get(search_type, url_map['web'])


def get_bing_results(keyword: str, search_type: str = 'web', limit: int = 5) -> List[Dict]:
    """
    Bing 검색 결과 크롤링
    
    Args:
        keyword: 검색 키워드
        search_type: 검색 유형 ('web', 'news', 'image', 'video')
        limit: 결과 개수 제한
    
    Returns:
        검색 결과 리스트 [{'title': '', 'description': '', 'url': '', 'date': ''}, ...]
    """
    url = search_bing(keyword, search_type)
    results = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        print(f"[Bing 검색] {search_type} '{keyword}' 검색 시작...")
        print(f"[URL] {url[:80]}...")
        
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Bing 웹 검색 결과 파싱
        if search_type == 'web':
            print(f"[파싱] 웹 검색 결과 파싱 중...")
            items = soup.select('.b_algo')
            print(f"[결과] {len(items)}개 발견")
            
            items = items[:limit]
            
            for idx, item in enumerate(items, 1):
                try:
                    title_elem = item.select_one('h2 a')
                    desc_elem = item.select_one('.b_snippet')
                    
                    if not title_elem:
                        continue
                    
                    title_text = title_elem.get_text(strip=True)
                    desc_text = desc_elem.get_text(strip=True) if desc_elem else ''
                    url_link = title_elem.get('href', '')
                    
                    if title_text and url_link:
                        results.append({
                            'title': title_text,
                            'description': desc_text,
                            'url': url_link,
                            'date': '',
                            'source': 'Bing'
                        })
                        print(f"[{idx}] {title_text[:60]}...")
                
                except Exception as e:
                    print(f"[오류] 항목 파싱 실패: {e}")
                    continue
        
        # Bing 뉴스 검색 결과 파싱
        elif search_type == 'news':
            print(f"[파싱] 뉴스 검색 결과 파싱 중...")
            items = soup.select('.news-card')
            print(f"[결과] {len(items)}개 발견")
            
            items = items[:limit]
            
            for idx, item in enumerate(items, 1):
                try:
                    title_elem = item.select_one('a.title')
                    desc_elem = item.select_one('.snippet')
                    date_elem = item.select_one('.source, span.update-time')
                    
                    if not title_elem:
                        continue
                    
                    title_text = title_elem.get_text(strip=True)
                    desc_text = desc_elem.get_text(strip=True) if desc_elem else ''
                    url_link = title_elem.get('href', '')
                    date_text = date_elem.get_text(strip=True) if date_elem else ''
                    
                    if title_text and url_link:
                        results.append({
                            'title': title_text,
                            'description': desc_text,
                            'url': url_link,
                            'date': date_text,
                            'source': 'Bing News'
                        })
                        print(f"[{idx}] {title_text[:60]}...")
                
                except Exception as e:
                    print(f"[오류] 항목 파싱 실패: {e}")
                    continue
        
        else:
            print(f"[정보] {search_type} 검색은 URL 제공만 가능합니다.")
            results.append({
                'title': f'"{keyword}" Bing {search_type} 검색',
                'description': f'Bing에서 "{keyword}"의 {search_type} 검색 결과입니다.',
                'url': url,
                'date': '',
                'source': f'Bing {search_type}'
            })
        
    except Exception as e:
        print(f"[오류] Bing 검색 실패: {e}")
        # 오류 발생 시에도 URL은 제공
        results.append({
            'title': f'"{keyword}" Bing 검색',
            'description': f'Bing 검색 링크: {str(e)[:50]}',
            'url': url,
            'date': '',
            'source': 'Bing'
        })
    
    return results


def format_bing_results(results: List[Dict]) -> str:
    """
    Bing 검색 결과를 텍스트로 포맷팅
    
    Args:
        results: 검색 결과 리스트
    
    Returns:
        포맷팅된 텍스트
    """
    if not results:
        return "검색 결과가 없습니다."
    
    output = []
    for i, result in enumerate(results, 1):
        output.append(f"\n{i}. 🔍 {result['title']}")
        if result.get('description'):
            output.append(f"   📝 {result['description']}")
        if result.get('date'):
            output.append(f"   📅 {result['date']}")
        if result.get('url'):
            output.append(f"   🔗 {result['url']}")
    
    return '\n'.join(output)
