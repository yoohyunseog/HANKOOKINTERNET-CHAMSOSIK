"""
뉴스 RSS 피드 모듈
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime
import re
import html


def clean_text(text: str) -> str:
    """
    텍스트에서 HTML 태그와 특수문자 제거
    
    Args:
        text: 정리할 텍스트
    
    Returns:
        정리된 텍스트
    """
    # HTML 엔티티 디코딩
    text = html.unescape(text)
    
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    
    # 추가 특수문자 정리
    # CDATA 제거
    text = text.replace('<![CDATA[', '').replace(']]>', '')
    
    # 여러 공백을 한 칸으로
    text = re.sub(r'\s+', ' ', text)
    
    # 앞뒤 공백 제거
    text = text.strip()
    
    return text


def normalize_date(date_str: str) -> str:
    """
    날짜 형식 정규화
    
    Args:
        date_str: 원본 날짜 문자열
    
    Returns:
        정규화된 날짜
    """
    if not date_str:
        return ''
    
    # 특수문자 제거
    date_str = clean_text(date_str)
    
    # 시간 정보만 표시 (예: "12시간 전", "2시간 전")
    if '전' in date_str or 'ago' in date_str.lower():
        return date_str
    
    # 날짜 포맷 간단히
    return date_str[:10] if len(date_str) > 10 else date_str


def get_naver_news_rss(keyword: str, limit: int = 5) -> List[Dict]:
    """
    네이버 뉴스 RSS 피드에서 검색 결과 가져오기
    
    Args:
        keyword: 검색 키워드
        limit: 결과 개수 제한
    
    Returns:
        뉴스 리스트 [{'title': '', 'description': '', 'url': '', 'date': ''}, ...]
    """
    results = []
    
    try:
        # 네이버 뉴스 RSS URL (기본: 정치 카테고리)
        # RSS 주소 대신 검색 API를 사용하는 것이 더 안정적
        from urllib.parse import quote
        
        keyword_encoded = quote(keyword)
        rss_url = f"https://news.naver.com/rss/search.naver?query={keyword_encoded}&sort=date"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"[RSS] 네이버 뉴스 RSS 피드 로드 중... ({rss_url})")
        response = requests.get(rss_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'xml')
        items = soup.find_all('item')
        
        print(f"[RSS] {len(items)}개 뉴스 항목 발견")
        
        for idx, item in enumerate(items, 1):
            if len(results) >= limit:
                break
            
            try:
                title = item.find('title')
                description = item.find('description')
                link = item.find('link')
                pub_date = item.find('pubDate')
                
                title_text = title.get_text(strip=True) if title else ''
                desc_text = description.get_text(strip=True) if description else ''
                url_text = link.get_text(strip=True) if link else ''
                date_text = pub_date.get_text(strip=True) if pub_date else ''
                
                # 텍스트 정리
                title_text = clean_text(title_text)
                desc_text = clean_text(desc_text)
                date_text = normalize_date(date_text)
                
                # 길이 제한
                title_text = title_text[:100]
                desc_text = desc_text[:250]
                
                result = {
                    'title': title_text,
                    'description': desc_text,
                    'url': url_text,
                    'date': date_text
                }
                
                if result['title'] and len(result['title']) > 5:
                    print(f"[{len(results)+1}] {result['title'][:50]}...")
                    results.append(result)
                    
            except Exception as e:
                print(f"[파싱 오류] {e}")
                continue
        
        print(f"[완료] 총 {len(results)}개 뉴스 추출됨")
        
    except Exception as e:
        print(f"[오류] RSS 로드 실패: {e}")
        print(f"[정보] RSS 사용 불가능, 웹 크롤링 방식 권장")
    
    return results


def get_news_by_category(category: str = 'politics', limit: int = 5) -> List[Dict]:
    """
    카테고리별 뉴스 가져오기
    
    Args:
        category: 카테고리 ('politics', 'economy', 'society', 'culture', 'tech')
        limit: 결과 개수
    
    Returns:
        뉴스 리스트
    """
    results = []
    
    category_codes = {
        'politics': '100',
        'economy': '101',
        'society': '102',
        'culture': '103',
        'tech': '105',
        'sports': '104',
        'world': '106'
    }
    
    code = category_codes.get(category, '100')
    
    try:
        rss_url = f"https://news.naver.com/rss/section.naver?sectCode={code}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        print(f"[RSS] {category} 뉴스 로드 중...")
        response = requests.get(rss_url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'xml')
        items = soup.find_all('item', limit=limit)
        
        for idx, item in enumerate(items, 1):
            try:
                title = item.find('title')
                description = item.find('description')
                link = item.find('link')
                pub_date = item.find('pubDate')
                
                title_text = title.get_text(strip=True) if title else ''
                desc_text = description.get_text(strip=True) if description else ''
                url_text = link.get_text(strip=True) if link else ''
                date_text = pub_date.get_text(strip=True) if pub_date else ''
                
                # 텍스트 정리
                title_text = clean_text(title_text)
                desc_text = clean_text(desc_text)
                date_text = normalize_date(date_text)
                
                # 길이 제한
                title_text = title_text[:100]
                desc_text = desc_text[:250]
                
                result = {
                    'title': title_text,
                    'description': desc_text,
                    'url': url_text,
                    'date': date_text
                }
                
                if result['title']:
                    results.append(result)
                    
            except Exception as e:
                print(f"[파싱 오류] {e}")
                continue
        
        print(f"[완료] {category} 카테고리 {len(results)}개 뉴스 추출")
        
    except Exception as e:
        print(f"[오류] {category} 카테고리 RSS 로드 실패: {e}")
    
    return results


def format_news_summary(results: List[Dict]) -> str:
    """
    뉴스를 요약 형식으로 포맷팅
    
    Args:
        results: 뉴스 리스트
    
    Returns:
        포맷팅된 텍스트
    """
    if not results:
        return "검색 결과가 없습니다."
    
    output = []
    for i, news in enumerate(results, 1):
        output.append(f"\n[{i}] {news['title']}")
        
        if news['description'] and len(news['description']) > 10:
            output.append(f"    {news['description']}")
        
        if news['date']:
            output.append(f"    {news['date']}")
    
    return '\n'.join(output)
