"""
Selenium 기반 동적 웹 크롤링 - Naver/Bing 검색 개선
JavaScript 렌더링까지 처리 가능
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

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_chrome_driver():
    """Chrome 드라이버 생성 (헤드리스 모드)"""
    try:
        options = Options()
        options.add_argument('--headless')  # GUI 없이 실행
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        logger.info("✅ Chrome 드라이버 시작")
        return driver
    except Exception as e:
        logger.error(f"❌ Chrome 드라이버 실패: {e}")
        return None


def search_naver_selenium(keyword: str, search_type: str = 'news', limit: int = 5) -> List[Dict]:
    """
    Selenium을 사용한 네이버 검색 (JavaScript 렌더링 포함)
    
    Args:
        keyword: 검색 키워드
        search_type: 'news', 'web', 'blog'
        limit: 결과 개수
    
    Returns:
        검색 결과 리스트
    """
    driver = None
    results = []
    
    try:
        driver = get_chrome_driver()
        if not driver:
            logger.error("드라이버 생성 실패")
            return []
        
        # URL 구성
        encoded_keyword = quote(keyword)
        if search_type == 'news':
            url = f'https://search.naver.com/search.naver?where=news&query={encoded_keyword}&sm=tab_opt&sort=1'
        elif search_type == 'blog':
            url = f'https://search.naver.com/search.naver?where=blog&query={encoded_keyword}&sm=tab_opt&sort=0'
        else:
            url = f'https://search.naver.com/search.naver?where=nexearch&query={encoded_keyword}'
        
        logger.info(f"[Selenium] {search_type} '{keyword}' 검색 시작")
        logger.info(f"[URL] {url[:80]}...")
        
        # 페이지 로드
        driver.get(url)
        
        # JavaScript 렌더링 대기 (최대 10초)
        try:
            wait = WebDriverWait(driver, 10)
            if search_type == 'news':
                # 뉴스 검색 결과 대기
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.news_area, li.bx')))
            else:
                # 일반 검색 결과 대기
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.api_subject_bx, li.bx')))
        except:
            logger.warning("⚠️  렌더링 시간 초과 (계속 진행)")
        
        # 페이지 소스 파싱
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        if search_type == 'news':
            logger.info("[파싱] 뉴스 검색 결과 파싱 중...")
            # 뉴스 검색 결과 파싱
            items = soup.select('div.news_area')
            logger.info(f"[선택자1 .news_area] {len(items)}개 발견")
            
            if not items:
                items = soup.select('li.bx')
                logger.info(f"[선택자2 li.bx] {len(items)}개 발견")
            
            items = items[:limit]
            
            for idx, item in enumerate(items, 1):
                try:
                    # 제목
                    title_elem = item.select_one('.news_tit, .tit, a')
                    # 설명
                    desc_elem = item.select_one('.news_dsc, .dsc')
                    # 정보
                    info_elem = item.select_one('.info, .info_group')
                    
                    title = title_elem.get_text(strip=True) if title_elem else ''
                    desc = desc_elem.get_text(strip=True) if desc_elem else ''
                    url_link = title_elem.get('href', '') if title_elem else ''
                    date = info_elem.get_text(strip=True) if info_elem else ''
                    
                    # HTML 태그 제거
                    title = BeautifulSoup(title, 'html.parser').get_text()
                    desc = BeautifulSoup(desc, 'html.parser').get_text()
                    
                    if title and len(title) > 5:
                        results.append({
                            'title': title[:100],
                            'description': desc[:200],
                            'url': url_link if url_link.startswith('http') else f'https://naver.com{url_link}',
                            'date': date[:30],
                            'source': 'Naver News'
                        })
                        logger.info(f"[{idx}] {title[:60]}...")
                
                except Exception as e:
                    logger.debug(f"[파싱 오류] {e}")
                    continue
        
        else:  # web, blog
            logger.info("[파싱] 웹/블로그 검색 결과 파싱 중...")
            # 웹 검색 결과
            items = soup.select('div.api_subject_bx, li.bx')
            logger.info(f"[검색 항목] {len(items)}개 발견")
            
            items = items[:limit]
            
            for idx, item in enumerate(items, 1):
                try:
                    title_elem = item.select_one('a')
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    url_link = title_elem.get('href', '')
                    
                    # 설명 추출
                    desc_elem = item.select_one('div.api_txt_domain, .dsc')
                    desc = desc_elem.get_text(strip=True) if desc_elem else ''
                    
                    if title and len(title) > 5:
                        results.append({
                            'title': title[:100],
                            'description': desc[:200],
                            'url': url_link,
                            'date': '',
                            'source': f'Naver {search_type}'
                        })
                        logger.info(f"[{idx}] {title[:60]}...")
                
                except Exception as e:
                    logger.debug(f"[파싱 오류] {e}")
                    continue
        
        logger.info(f"✅ 총 {len(results)}개 결과 추출")
        return results
    
    except Exception as e:
        logger.error(f"❌ 검색 오류: {e}")
        return []
    
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("✅ 드라이버 종료")
            except:
                pass


def search_bing_selenium(keyword: str, search_type: str = 'web', limit: int = 5) -> List[Dict]:
    """
    Selenium을 사용한 Bing 검색 (JavaScript 렌더링 포함)
    
    Args:
        keyword: 검색 키워드
        search_type: 'web', 'news'
        limit: 결과 개수
    
    Returns:
        검색 결과 리스트
    """
    driver = None
    results = []
    
    try:
        driver = get_chrome_driver()
        if not driver:
            logger.error("드라이버 생성 실패")
            return []
        
        encoded_keyword = quote(keyword)
        if search_type == 'news':
            url = f'https://www.bing.com/news/search?q={encoded_keyword}'
        else:
            url = f'https://www.bing.com/search?q={encoded_keyword}'
        
        logger.info(f"[Selenium] Bing {search_type} '{keyword}' 검색 시작")
        logger.info(f"[URL] {url[:80]}...")
        
        # 페이지 로드
        driver.get(url)
        
        # 렌더링 대기
        try:
            wait = WebDriverWait(driver, 10)
            if search_type == 'news':
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.news-card')))
            else:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.b_algo')))
        except:
            logger.warning("⚠️  렌더링 시간 초과 (계속 진행)")
        
        time.sleep(2)  # 추가 로딩 시간
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        if search_type == 'news':
            logger.info("[파싱] 뉴스 검색 결과 파싱 중...")
            items = soup.select('div.news-card')
            logger.info(f"[결과] {len(items)}개 발견")
            
            items = items[:limit]
            
            for idx, item in enumerate(items, 1):
                try:
                    title_elem = item.select_one('a.title')
                    desc_elem = item.select_one('.snippet')
                    date_elem = item.select_one('.source, span.update-time')
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    desc = desc_elem.get_text(strip=True) if desc_elem else ''
                    url_link = title_elem.get('href', '')
                    date = date_elem.get_text(strip=True) if date_elem else ''
                    
                    if title and len(title) > 5:
                        results.append({
                            'title': title[:100],
                            'description': desc[:200],
                            'url': url_link,
                            'date': date[:30],
                            'source': 'Bing News'
                        })
                        logger.info(f"[{idx}] {title[:60]}...")
                
                except Exception as e:
                    logger.debug(f"[파싱 오류] {e}")
                    continue
        
        else:  # web
            logger.info("[파싱] 웹 검색 결과 파싱 중...")
            items = soup.select('div.b_algo')
            logger.info(f"[결과] {len(items)}개 발견")
            
            items = items[:limit]
            
            for idx, item in enumerate(items, 1):
                try:
                    title_elem = item.select_one('h2 a')
                    desc_elem = item.select_one('.b_snippet')
                    
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    desc = desc_elem.get_text(strip=True) if desc_elem else ''
                    url_link = title_elem.get('href', '')
                    
                    if title and len(title) > 5:
                        results.append({
                            'title': title[:100],
                            'description': desc[:200],
                            'url': url_link,
                            'date': '',
                            'source': 'Bing'
                        })
                        logger.info(f"[{idx}] {title[:60]}...")
                
                except Exception as e:
                    logger.debug(f"[파싱 오류] {e}")
                    continue
        
        logger.info(f"✅ 총 {len(results)}개 결과 추출")
        return results
    
    except Exception as e:
        logger.error(f"❌ 검색 오류: {e}")
        return []
    
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("✅ 드라이버 종료")
            except:
                pass


if __name__ == '__main__':
    print("\n🧪 Selenium 기반 검색 테스트\n")
    
    # Naver 뉴스 검색
    print("=" * 60)
    print("네이버 뉴스 검색")
    print("=" * 60)
    results = search_naver_selenium("파이썬", search_type='news', limit=3)
    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r['title']}")
        print(f"   {r['description'][:100]}")
        print(f"   {r['url'][:80]}")
    
    # Naver 웹 검색
    print("\n" + "=" * 60)
    print("네이버 웹 검색")
    print("=" * 60)
    results = search_naver_selenium("인공지능", search_type='web', limit=3)
    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r['title']}")
        print(f"   {r['url'][:80]}")
    
    # Bing 웹 검색
    print("\n" + "=" * 60)
    print("Bing 웹 검색")
    print("=" * 60)
    results = search_bing_selenium("python learning", search_type='web', limit=3)
    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r['title']}")
        print(f"   {r['description'][:100]}")
        print(f"   {r['url'][:80]}")
