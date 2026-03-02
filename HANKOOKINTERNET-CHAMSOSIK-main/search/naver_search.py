"""
네이버 검색 모듈
"""

import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from typing import List, Dict
import re


def search_naver(keyword: str, search_type: str = 'blog') -> str:
    """
    네이버 검색 URL 생성
    
    Args:
        keyword: 검색 키워드
        search_type: 검색 유형 ('blog', 'news', 'web', 'image', 'video')
    
    Returns:
        검색 URL
    """
    encoded_keyword = quote(keyword)
    
    url_map = {
        'blog': f'https://search.naver.com/search.naver?where=blog&query={encoded_keyword}&sm=tab_opt&sort=0',
        'news': f'https://search.naver.com/search.naver?where=news&query={encoded_keyword}&sm=tab_opt&sort=1&photo=0&field=0&pd=0&docid=&related=0&mynews=0&office_type=0&office_section_code=0&news_office_checked=&nso=so:dd,p:all,a:all',
        'web': f'https://search.naver.com/search.naver?where=nexearch&query={encoded_keyword}',
        'image': f'https://search.naver.com/search.naver?where=image&query={encoded_keyword}',
        'video': f'https://search.naver.com/search.naver?where=video&query={encoded_keyword}'
    }
    
    return url_map.get(search_type, url_map['blog'])


def get_naver_results(keyword: str, search_type: str = 'blog', limit: int = 5) -> List[Dict]:
    """
    네이버 검색 결과 크롤링
    
    Args:
        keyword: 검색 키워드
        search_type: 검색 유형
        limit: 결과 개수 제한
    
    Returns:
        검색 결과 리스트 [{'title': '', 'description': '', 'url': '', 'date': ''}, ...]
    """
    url = search_naver(keyword, search_type)
    results = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': 'https://www.naver.com/'
        }
        
        print(f"[검색] {search_type} '{keyword}' 검색 시작...")
        print(f"[URL] {url[:80]}...")
        
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 뉴스 검색 결과 파싱 (우선순위)
        if search_type == 'news':
            print(f"[파싱] 뉴스 검색 결과 파싱 중...")
            # 네이버 뉴스는 여러 선택자 시도
            items = soup.select('.news_area')
            print(f"[선택자1 .news_area] {len(items)}개 발견")
            
            if not items:
                items = soup.select('li.bx')
                print(f"[선택자2 li.bx] {len(items)}개 발견")
            if not items:
                items = soup.select('.group_news')
                print(f"[선택자3 .group_news] {len(items)}개 발견")
            
            items = items[:limit]
            
            for idx, item in enumerate(items, 1):
                try:
                    title_elem = item.select_one('.news_tit') or item.select_one('.tit') or item.select_one('a')
                    desc_elem = item.select_one('.news_dsc') or item.select_one('.dsc')
                    info_elem = item.select_one('.info') or item.select_one('.info_group')
                    
                    title_text = title_elem.get_text(strip=True) if title_elem else ''
                    desc_text = desc_elem.get_text(strip=True) if desc_elem else ''
                    url_link = title_elem.get('href', '') if title_elem else ''
                    date_text = info_elem.get_text(strip=True) if info_elem else ''
                    
                    # HTML 태그 제거
                    title_text = BeautifulSoup(title_text, 'html.parser').get_text()
                    desc_text = BeautifulSoup(desc_text, 'html.parser').get_text()
                    
                    # 부족한 설명 보충
                    if not desc_text or len(desc_text) < 30:
                        # 부모 요소에서 텍스트 추출
                        parent_text = item.get_text(strip=True)
                        if len(parent_text) > len(title_text):
                            desc_text = parent_text[len(title_text):][:200]
                    
                    result = {
                        'title': title_text[:100] if title_text else '',
                        'description': desc_text[:300] if desc_text else '',
                        'url': url_link,
                        'date': date_text[:50] if date_text else ''
                    }
                    
                    if result['title'] and len(result['title']) > 5:
                        print(f"[{idx}] {result['title'][:40]}... ({len(result['description'])}글자)")
                        results.append(result)
                except Exception as e:
                    print(f"[파싱 오류] {e}")
                    continue
        
        # 블로그 검색 결과 파싱
        elif search_type == 'blog':
            items = soup.select('.view_wrap')
            if not items:
                items = soup.select('.total_wrap')
            
            items = items[:limit]
            
            for item in items:
                title_elem = item.select_one('.title_link') or item.select_one('.link')
                desc_elem = item.select_one('.dsc_link') or item.select_one('.total_dsc')
                date_elem = item.select_one('.sub_time') or item.select_one('.sub_txt')
                
                title_text = title_elem.get_text(strip=True) if title_elem else ''
                desc_text = desc_elem.get_text(strip=True) if desc_elem else ''
                url_link = title_elem.get('href', '') if title_elem else ''
                date_text = date_elem.get_text(strip=True) if date_elem else ''
                
                # HTML 태그 제거
                title_text = BeautifulSoup(title_text, 'html.parser').get_text()
                desc_text = BeautifulSoup(desc_text, 'html.parser').get_text()
                
                result = {
                    'title': title_text,
                    'description': desc_text,
                    'url': url_link,
                    'date': date_text
                }
                
                if result['title']:
                    results.append(result)
        
        # 일반 웹 검색
        else:
            items = soup.select('.total_wrap')[:limit]
            
            for item in items:
                title_elem = item.select_one('.link_tit')
                desc_elem = item.select_one('.total_dsc')
                
                title_text = title_elem.get_text(strip=True) if title_elem else ''
                desc_text = desc_elem.get_text(strip=True) if desc_elem else ''
                url_link = title_elem.get('href', '') if title_elem else ''
                
                # HTML 태그 제거
                title_text = BeautifulSoup(title_text, 'html.parser').get_text()
                desc_text = BeautifulSoup(desc_text, 'html.parser').get_text()
                
                result = {
                    'title': title_text,
                    'description': desc_text,
                    'url': url_link,
                    'date': ''
                }
                
                if result['title']:
                    results.append(result)
        
        # 결과가 없으면 다른 선택자 시도
        if not results:
            print(f"[분석] 페이지 전체 구조 분석 중...")
            all_items = soup.find_all(['a', 'div', 'li'], limit=50)
            for item in all_items:
                text = item.get_text(strip=True)
                if len(text) > 20 and len(text) < 200 and not text.startswith('http'):
                    results.append({
                        'title': text[:100],
                        'description': '상세 내용을 보려면 링크를 방문하세요.',
                        'url': item.get('href', url) if item.name == 'a' else url,
                        'date': ''
                    })
                    if len(results) >= limit:
                        break
        
    except Exception as e:
        print(f"[오류] 네이버 검색 오류: {e}")
        # 오류 발생 시에도 검색 URL은 제공
        results.append({
            'title': f'"{keyword}" 네이버 검색',
            'description': f'{search_type} 검색 결과를 직접 확인하세요.',
            'url': url,
            'date': ''
        })
    
    return results


def fetch_page_content(url: str) -> Dict:
    """
    URL의 실제 페이지 내용 가져오기
    
    Args:
        url: 페이지 URL
    
    Returns:
        {'title': '', 'content': '', 'url': ''}
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        response.raise_for_status()
        
        text = response.text
        
        # title 추출
        title = ""
        if "<title>" in text:
            try:
                title = text.split("<title>", 1)[1].split("</title>", 1)[0].strip()
            except:
                pass
        
        # body 텍스트 추출
        # script, style 태그 제거
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        # 모든 HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        # 연속 공백 제거
        text = re.sub(r'\s+', ' ', text).strip()
        content = text[:1500]
        
        return {
            'title': title[:100],
            'content': content,
            'url': url
        }
    except Exception as e:
        print(f"[페이지 조회 오류] {url}: {e}")
        return {
            'title': '',
            'content': '',
            'url': url
        }


def get_latest_naver_news(limit: int = 3) -> List[Dict]:
    """
    네이버 뉴스 메인 페이지에서 최신 뉴스 가져오기
    
    Args:
        limit: 결과 개수
    
    Returns:
        뉴스 리스트
    """
    results = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # 네이버 뉴스 메인 페이지
        url = "https://news.naver.com"
        print(f"[최신뉴스] 네이버 뉴스 메인 페이지 로드 중...")
        
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 최신 뉴스 항목들 찾기
        # 다양한 선택자 시도
        items = soup.select('.list_body li')  # 일반 뉴스 리스트
        if not items:
            items = soup.select('article')
        if not items:
            items = soup.select('.list_item')
        
        print(f"[최신뉴스] {len(items)}개 항목 발견")
        
        for idx, item in enumerate(items[:limit * 3], 1):  # 더 많이 찾아서 유효한 것 추출
            if len(results) >= limit:
                break
            
            try:
                # 제목 찾기
                title_elem = item.select_one('a.list_title') or item.select_one('a') or item.select_one('.tit')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                link = title_elem.get('href', '')
                
                # 간단한 유효성 검사
                if not title or len(title) < 5 or len(title) > 200:
                    continue
                if not link or not link.startswith('https://'):
                    continue
                
                result = {
                    'title': title[:100],
                    'description': title[:50],  # 제목의 일부를 설명으로
                    'url': link,
                    'date': ''
                }
                
                print(f"[{len(results)+1}] {title[:50]}...")
                results.append(result)
                
            except Exception as e:
                continue
        
        print(f"[최신뉴스] 총 {len(results)}개 추출")
        
    except Exception as e:
        print(f"[최신뉴스] 오류: {e}")
    
    return results


def format_search_results(results: List[Dict]) -> str:
    """
    검색 결과를 텍스트로 포맷팅
    
    Args:
        results: 검색 결과 리스트
    
    Returns:
        포맷팅된 텍스트
    """
    if not results:
        return "검색 결과가 없습니다."
    
    output = []
    for i, result in enumerate(results, 1):
        output.append(f"\n[{i}] 📌 {result['title']}")
        
        if result['description'] and len(result['description']) > 10:
            output.append(f"    💬 {result['description']}")
        
        if result['date']:
            output.append(f"    📅 {result['date']}")
        
        if result['url']:
            output.append(f"    🔗 {result['url'][:70]}...")
    
    return '\n'.join(output)
