"""
Selenium 기반 네이버 뉴스 크롤링 (개선版)
페이지 렌더링 후 실제 뉴스 항목 파싱
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import quote
import time
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _is_valid_news_title(title: str) -> bool:
    if not title or len(title) < 6:
        return False
    blocked = [
        '서비스 영역', 'NAVER', '메뉴', '바로가기', '로그인', '전체메뉴',
        '검색', '광고', '공지', '언론사', '뉴스홈', '구독', '구독하기'
    ]
    return not any(word in title for word in blocked)


def _is_news_url(url: str) -> bool:
    return url.startswith('http') and 'news.naver.com' in url


def _extract_news_links(soup: BeautifulSoup, limit: int) -> List[Dict]:
    results = []
    seen = set()

    for link in soup.select('a[href]'):
        try:
            href = link.get('href', '')
            title = link.get_text(strip=True)

            if not _is_news_url(href) or not _is_valid_news_title(title):
                continue

            if href in seen:
                continue

            seen.add(href)
            results.append({
                'title': title[:100],
                'description': '',
                'url': href,
                'date': '',
                'source': 'Naver News'
            })

            if len(results) >= limit:
                break
        except Exception:
            continue

    return results


def get_chrome_driver_advanced():
    """고급 Chrome 드라이버 설정"""
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        
        logger.info("✅ Chrome 드라이버 시작")
        return driver
    except Exception as e:
        logger.error(f"❌ Chrome 드라이버 실패: {e}")
        return None


def get_naver_news_by_category(category_id: int = None, limit: int = 10) -> List[Dict]:
    """
    네이버 뉴스 카테고리별 크롤링 (Selenium)
    
    Args:
        category_id: 카테고리 ID
                    None = 메인 뉴스
                    100 = 정치
                    101 = 경제
                    102 = 사회
                    103 = 생활/문화
                    105 = IT/과학
                    etc...
        limit: 수집할 뉴스 개수
    
    Returns:
        뉴스 리스트
    """
    driver = None
    results = []
    
    try:
        driver = get_chrome_driver_advanced()
        if not driver:
            logger.error("드라이버 생성 실패")
            return []
        
        # URL 구성
        if category_id is None:
            url = 'https://news.naver.com/main/main.naver'
        else:
            url = f'https://news.naver.com/section/{category_id}'
        
        logger.info(f"[Selenium] 네이버 뉴스 크롤링 시작 (카테고리: {category_id})")
        logger.info(f"[URL] {url}")
        
        # 페이지 로드
        driver.get(url)
        time.sleep(3)  # 페이지 로딩 대기
        
        # JavaScript 렌더링 대기
        try:
            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.nclicks')))
        except Exception as e:
            logger.warning(f"⚠️  렌더링 대기 시간 초과: {e}")
        
        # 페이지 소스 파싱
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        logger.info("[파싱] 뉴스 항목 파싱 중...")
        
        # 방법 1: 현재 구조 분석 - 뉴스 링크 찾기
        logger.info("[분석] 페이지 구조 분석...")
        
        # 뉴스 항목 찾기 (여러 가능한 selector)
        articles = None
        selectors = [
            'div.list_body article',  # 메인 페이지
            'div.list_item',  # 대체 구조
            'li.item',  # 또 다른 구조
            'div.article_list li',
        ]
        
        for selector in selectors:
            articles = soup.select(selector)
            if articles:
                logger.info(f"[발견] selector '{selector}' - {len(articles)}개 항목")
                break
        
        if not articles:
            logger.warning("[경고] 표준 selector로 항목을 찾지 못했습니다. 링크 기반 추출 시도...")
            results.extend(_extract_news_links(soup, limit))
        
        else:
            # 표준 selector로 발견한 경우
            for idx, article in enumerate(articles[:limit], 1):
                try:
                    # 제목 찾기
                    title_elem = article.select_one('a, strong, h2')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    url_link = title_elem.get('href', '')
                    
                    # 설명 찾기
                    desc_elem = article.select_one('.article_content, .news_contents, p')
                    desc = desc_elem.get_text(strip=True)[:150] if desc_elem else ''
                    
                    # 날짜 찾기
                    date_elem = article.select_one('span.date, .time')
                    date = date_elem.get_text(strip=True) if date_elem else ''
                    
                    if _is_valid_news_title(title):
                        results.append({
                            'title': title[:100],
                            'description': desc,
                            'url': url_link if url_link.startswith('http') else f'https://news.naver.com{url_link}',
                            'date': date,
                            'source': 'Naver News (Category)'
                        })
                        logger.info(f"[{idx}] {title[:60]}...")
                
                except Exception as e:
                    logger.debug(f"[파싱 오류] {e}")
                    continue

        if len(results) < limit:
            extra = _extract_news_links(soup, limit)
            for item in extra:
                if len(results) >= limit:
                    break
                if all(item['url'] != existing['url'] for existing in results):
                    results.append(item)
        
        logger.info(f"✅ 총 {len(results)}개 뉴스 수집 완료")
        return results
    
    except Exception as e:
        logger.error(f"❌ 크롤링 오류: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("✅ 드라이버 종료")
            except:
                pass


def get_naver_news_search_selenium(keyword: str, limit: int = 10) -> List[Dict]:
    """
    네이버 뉴스 검색 (Selenium으로 페이지 렌더링 후 파싱)
    
    Args:
        keyword: 검색 키워드
        limit: 결과 개수
    
    Returns:
        뉴스 리스트
    """
    driver = None
    results = []
    
    try:
        driver = get_chrome_driver_advanced()
        if not driver:
            logger.error("드라이버 생성 실패")
            return []
        
        encoded_keyword = quote(keyword)
        url = f'https://search.naver.com/search.naver?where=news&query={encoded_keyword}&sm=tab_opt&sort=1'
        
        logger.info(f"[Selenium] 뉴스 검색 시작: '{keyword}'")
        logger.info(f"[URL] {url[:90]}")
        
        driver.get(url)
        time.sleep(3)  # 페이지 로딩 대기
        
        # 렌더링 대기
        try:
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.news_area, a.news_tit, li.bx')))
        except:
            logger.warning("⚠️  렌더링 대기 시간 초과")
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        logger.info("[파싱] 검색 결과 파싱 중...")
        
        # 뉴스 항목 찾기
        items = soup.select('div.news_area')
        logger.info(f"[발견] news_area: {len(items)}개")
        
        if not items:
            items = soup.select('li.bx')
            logger.info(f"[발견] li.bx: {len(items)}개")
        
        for idx, item in enumerate(items[:limit], 1):
            try:
                # 제목 - 다양한 selector 시도
                title_elem = item.select_one('a.news_tit, a[href*="news.naver.com"], a.tit, a')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                url_link = title_elem.get('href', '')
                
                # 설명 - li.bx 구조에 맞는 selector
                desc = ''
                desc_elem = item.select_one('div.dsc, span.lede, div.news_dsc, p.dsc')
                if desc_elem:
                    desc = desc_elem.get_text(strip=True)[:150]
                
                # 날짜/출처 - 다양한 selector
                info = ''
                info_elem = item.select_one('span.info, span.date, span.time')
                if info_elem:
                    info = info_elem.get_text(strip=True)
                
                if _is_valid_news_title(title):
                    results.append({
                        'title': title[:100],
                        'description': desc,
                        'url': url_link if url_link.startswith('http') else url_link,
                        'date': info[:30],
                        'source': 'Naver News Search'
                    })
                    logger.info(f"[{len(results)}] {title[:60]}...")
                    
                    if len(results) >= limit:
                        break
            
            except Exception as e:
                logger.debug(f"[파싱 오류] {e}")
                continue
        
        if len(results) < limit:
            extra = _extract_news_links(soup, limit)
            for item in extra:
                if len(results) >= limit:
                    break
                if all(item['url'] != existing['url'] for existing in results):
                    results.append(item)

        logger.info(f"✅ 총 {len(results)}개 뉴스 발견")
        return results
    
    except Exception as e:
        logger.error(f"❌ 검색 오류: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("✅ 드라이버 종료")
            except:
                pass


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🧪 Selenium 기반 네이버 뉴스 크롤링 테스트")
    print("="*70)
    
    # 1. 메인 뉴스
    print("\n📰 네이버 뉴스 메인 (Selenium)")
    results = get_naver_news_by_category(category_id=None, limit=5)
    print(f"\n✅ 수집된 뉴스: {len(results)}개")
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r['title']}")
        if r.get('date'):
            print(f"    📅 {r['date']}")
    
    # 2. 경제 뉴스
    print("\n\n📊 경제 뉴스 (카테고리: 101)")
    results = get_naver_news_by_category(category_id=101, limit=5)
    print(f"\n✅ 수집된 뉴스: {len(results)}개")
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r['title']}")
    
    # 3. 검색 결과
    print("\n\n🔍 검색: '주요 뉴스'")
    results = get_naver_news_search_selenium("주요 뉴스", limit=5)
    print(f"\n✅ 수집된 뉴스: {len(results)}개")
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r['title']}")
        if r.get('description'):
            print(f"    📝 {r['description'][:80]}")
    
    print("\n" + "="*70 + "\n")
