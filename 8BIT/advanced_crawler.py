"""
통합 웹 데이터 크롤러
크롤링 + 장르분류 + 요약 + 키워드추출을 한 번에 수행합니다.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime
from urllib.parse import urlparse

from genre_classifier import GenreClassifier
from text_summarizer import TextSummarizer
from keyword_extractor import KeywordExtractor


class AdvancedWebCrawler:
    def __init__(self, headless=True):
        """통합 크롤러 초기화"""
        self.setup_driver(headless)
        self.collected_data = []
        
        # 각 모듈 초기화
        self.classifier = GenreClassifier()
        self.summarizer = TextSummarizer()
        self.extractor = KeywordExtractor()
        
        print("✅ 크롤러 초기화 완료")
        print("   - 장르 분류기: 준비")
        print("   - 텍스트 요약기: 준비")
        print("   - 키워드 추출기: 준비")
    
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
        페이지 크롤링 + 분석 통합 실행
        
        Args:
            url (str): 크롤링할 URL
            
        Returns:
            dict: 완전히 처리된 데이터
        """
        try:
            print(f"\n{'='*60}")
            print(f"📥 크롤링: {url}")
            
            # 1. 페이지 로드
            self.driver.get(url)
            time.sleep(2)
            
            # 2. HTML 파싱
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # 3. 기본 데이터 추출
            title = self.extract_title(soup)
            print(f"   제목: {title}")
            
            meta_desc = self.extract_meta_description(soup)
            paragraphs = self.extract_paragraphs(soup)
            
            # 본문 텍스트 결합
            content = ' '.join(paragraphs[:20])  # 앞부분 20개 단락만
            
            # 4. 장르 분류
            genre = self.classifier.classify(url, title, content)
            print(f"   장르: {genre}")
            
            # 5. 1줄 요약
            summary = self.summarizer.summarize(content, title, max_length=100)
            print(f"   요약: {summary}")
            
            # 6. 키워드 추출
            keywords = self.extractor.extract_keywords(content, title, max_keywords=7)
            print(f"   키워드: {', '.join(keywords)}")
            
            # 7. 최종 데이터 구성
            data = {
                'id': self.generate_id(),
                'url': url,
                'domain': urlparse(url).netloc,
                'title': title,
                'genre': genre,
                'summary': summary,
                'keywords': keywords,
                'meta_description': meta_desc,
                'paragraphs_count': len(paragraphs),
                'content_length': len(content),
                'crawled_at': datetime.now().isoformat(),
            }
            
            print(f"✅ 완료")
            return data
            
        except Exception as e:
            print(f"❌ 크롤링 실패: {url}")
            print(f"   오류: {str(e)}")
            return None
    
    def generate_id(self):
        """고유 ID 생성"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"crawl_{timestamp}_{len(self.collected_data) + 1}"
    
    def extract_title(self, soup):
        """페이지 제목 추출"""
        # 1. <title> 태그
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # 2. <h1> 태그
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        # 3. og:title 메타 태그
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        if og_title and og_title.get('content'):
            return og_title['content'].strip()
        
        return "제목 없음"
    
    def extract_meta_description(self, soup):
        """메타 설명 추출"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        return ""
    
    def extract_paragraphs(self, soup):
        """본문 단락 추출"""
        paragraphs = []
        
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            if text and len(text) > 20:
                paragraphs.append(text)
        
        return paragraphs
    
    def crawl_multiple(self, urls, delay=2):
        """
        여러 페이지 크롤링
        
        Args:
            urls (list): URL 리스트
            delay (int): 페이지 간 대기 시간 (초)
            
        Returns:
            list: 크롤링된 데이터 리스트
        """
        results = []
        total = len(urls)
        
        print("\n" + "="*60)
        print(f"🚀 크롤링 시작: 총 {total}개 페이지")
        print("="*60)
        
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{total}] 진행 중...")
            
            data = self.crawl_page(url)
            if data:
                results.append(data)
                self.collected_data.append(data)
            
            # 서버 부하 방지
            if i < total:
                time.sleep(delay)
        
        print("\n" + "="*60)
        print(f"✅ 크롤링 완료: {len(results)}개 성공")
        print("="*60)
        
        return results
    
    def save_to_json(self, filename=None):
        """
        수집한 데이터를 JSON 파일로 저장
        
        Args:
            filename (str): 저장할 파일명 (기본값: 자동 생성)
        """
        if not self.collected_data:
            print("❌ 저장할 데이터가 없습니다.")
            return
        
        # 파일명 자동 생성
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'data/crawled_data_{timestamp}.json'
        
        # 디렉토리 생성
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # 데이터 구성
        output = {
            'total_count': len(self.collected_data),
            'crawled_at': datetime.now().isoformat(),
            'stats': self.get_stats(),
            'data': self.collected_data
        }
        
        # JSON 저장
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 데이터 저장 완료")
        print(f"   파일: {filename}")
        print(f"   개수: {len(self.collected_data)}개")
        print(f"   크기: {os.path.getsize(filename):,} bytes")
    
    def get_stats(self):
        """통계 정보 생성"""
        if not self.collected_data:
            return {}
        
        # 장르별 개수
        genre_counts = {}
        total_keywords = 0
        
        for item in self.collected_data:
            genre = item.get('genre', '기타')
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
            total_keywords += len(item.get('keywords', []))
        
        return {
            'total_pages': len(self.collected_data),
            'total_keywords': total_keywords,
            'avg_keywords_per_page': round(total_keywords / len(self.collected_data), 1),
            'genre_distribution': genre_counts,
        }
    
    def print_summary(self):
        """수집 결과 요약 출력"""
        if not self.collected_data:
            print("\n수집된 데이터가 없습니다.")
            return
        
        stats = self.get_stats()
        
        print("\n" + "="*60)
        print("📊 크롤링 결과 요약")
        print("="*60)
        
        print(f"\n📄 총 페이지: {stats['total_pages']}개")
        print(f"🔍 총 키워드: {stats['total_keywords']}개")
        print(f"📈 페이지당 평균 키워드: {stats['avg_keywords_per_page']}개")
        
        print(f"\n🎯 장르별 분포:")
        for genre, count in stats['genre_distribution'].items():
            percentage = (count / stats['total_pages']) * 100
            print(f"   {genre}: {count}개 ({percentage:.1f}%)")
        
        print(f"\n📋 수집된 데이터 목록:")
        for i, item in enumerate(self.collected_data, 1):
            print(f"\n{i}. [{item['genre']}] {item['title']}")
            print(f"   URL: {item['url']}")
            print(f"   요약: {item['summary']}")
            print(f"   키워드: {', '.join(item['keywords'])}")
    
    def close(self):
        """브라우저 닫기"""
        if self.driver:
            self.driver.quit()
            print("\n🔒 브라우저 종료")


def main():
    """메인 실행 함수"""
    # 크롤링할 URL 리스트 (예제)
    urls = [
        'https://www.python.org',
        'https://github.com/trending',
        # 여기에 크롤링할 URL 추가
    ]
    
    print("=" * 60)
    print("🤖 통합 웹 데이터 크롤러")
    print("   - 크롤링, 장르분류, 요약, 키워드추출")
    print("=" * 60)
    
    crawler = AdvancedWebCrawler(headless=False)
    
    try:
        # 크롤링 실행
        crawler.crawl_multiple(urls, delay=2)
        
        # 결과 출력
        crawler.print_summary()
        
        # JSON 파일로 저장
        crawler.save_to_json()
        
    finally:
        crawler.close()


if __name__ == '__main__':
    main()
