"""
웹 데이터 크롤러
Selenium을 사용하여 웹페이지에서 데이터를 수집합니다.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from urllib.parse import urlparse

class WebCrawler:
    def __init__(self, headless=True):
        """
        웹 크롤러 초기화
        
        Args:
            headless (bool): 브라우저를 숨김 모드로 실행할지 여부
        """
        self.setup_driver(headless)
        self.collected_data = []
        
    def setup_driver(self, headless):
        """Chrome WebDriver 설정"""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def crawl_page(self, url):
        """
        단일 페이지 크롤링
        
        Args:
            url (str): 크롤링할 URL
            
        Returns:
            dict: 크롤링된 데이터
        """
        try:
            print(f"📥 크롤링 시작: {url}")
            
            # 페이지 로드
            self.driver.get(url)
            time.sleep(2)  # 페이지 로딩 대기
            
            # HTML 가져오기
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # 데이터 추출
            data = {
                'url': url,
                'domain': urlparse(url).netloc,
                'title': self.extract_title(soup),
                'meta_description': self.extract_meta_description(soup),
                'headings': self.extract_headings(soup),
                'paragraphs': self.extract_paragraphs(soup),
                'links': self.extract_links(soup, url),
                'images': self.extract_images(soup),
                'crawled_at': datetime.now().isoformat(),
            }
            
            print(f"✅ 크롤링 완료: {data['title']}")
            return data
            
        except Exception as e:
            print(f"❌ 크롤링 실패: {url}")
            print(f"   오류: {str(e)}")
            return None
    
    def extract_title(self, soup):
        """페이지 제목 추출"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return "제목 없음"
    
    def extract_meta_description(self, soup):
        """메타 설명 추출"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        meta_desc = soup.find('meta', attrs={'property': 'og:description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        return ""
    
    def extract_headings(self, soup):
        """제목 태그(h1-h6) 추출"""
        headings = []
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                text = heading.get_text().strip()
                if text:
                    headings.append({
                        'level': i,
                        'text': text
                    })
        return headings[:20]  # 최대 20개
    
    def extract_paragraphs(self, soup):
        """본문 단락 추출"""
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text and len(text) > 20:  # 20자 이상만
                paragraphs.append(text)
        return paragraphs[:50]  # 최대 50개
    
    def extract_links(self, soup, base_url):
        """링크 추출"""
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text().strip()
            
            # 상대 경로를 절대 경로로 변환
            if href.startswith('/'):
                parsed = urlparse(base_url)
                href = f"{parsed.scheme}://{parsed.netloc}{href}"
            
            if href.startswith('http') and text:
                links.append({
                    'url': href,
                    'text': text
                })
        
        return links[:30]  # 최대 30개
    
    def extract_images(self, soup):
        """이미지 추출"""
        images = []
        for img in soup.find_all('img', src=True):
            alt = img.get('alt', '').strip()
            src = img['src']
            
            images.append({
                'src': src,
                'alt': alt
            })
        
        return images[:20]  # 최대 20개
    
    def crawl_multiple(self, urls):
        """
        여러 페이지 크롤링
        
        Args:
            urls (list): URL 리스트
            
        Returns:
            list: 크롤링된 데이터 리스트
        """
        results = []
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] 크롤링 중...")
            
            data = self.crawl_page(url)
            if data:
                results.append(data)
                self.collected_data.append(data)
            
            # 서버 부하 방지를 위한 딜레이
            time.sleep(1)
        
        return results
    
    def save_to_json(self, filename='crawled_data.json'):
        """
        수집한 데이터를 JSON 파일로 저장
        
        Args:
            filename (str): 저장할 파일명
        """
        output = {
            'total_count': len(self.collected_data),
            'crawled_at': datetime.now().isoformat(),
            'data': self.collected_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 데이터 저장 완료: {filename}")
        print(f"   총 {len(self.collected_data)}개 페이지 수집")
    
    def close(self):
        """브라우저 닫기"""
        if self.driver:
            self.driver.quit()
            print("\n🔒 브라우저 종료")


def main():
    """메인 실행 함수"""
    # 크롤링할 URL 리스트
    urls = [
        'https://www.naver.com',
        'https://www.python.org',
        # 여기에 크롤링할 URL 추가
    ]
    
    print("=" * 60)
    print("🤖 웹 크롤러 시작")
    print("=" * 60)
    
    crawler = WebCrawler(headless=False)  # 브라우저 표시
    
    try:
        # 크롤링 실행
        crawler.crawl_multiple(urls)
        
        # JSON 파일로 저장
        crawler.save_to_json('data/crawled_data.json')
        
        # 결과 출력
        print("\n" + "=" * 60)
        print("📊 크롤링 결과 요약")
        print("=" * 60)
        
        for i, data in enumerate(crawler.collected_data, 1):
            print(f"{i}. {data['title']}")
            print(f"   URL: {data['url']}")
            print(f"   단락 수: {len(data['paragraphs'])}")
            print(f"   링크 수: {len(data['links'])}")
            print()
        
    finally:
        crawler.close()


if __name__ == '__main__':
    main()
