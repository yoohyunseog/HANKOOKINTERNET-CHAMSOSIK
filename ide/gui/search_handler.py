"""
검색 기능 처리
"""

import sys
import os
import re
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from .config import SEARCH_KEYWORDS
from .utils import log_debug

# 검색 모듈 import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from search import (
    search_naver, get_naver_results, search_youtube, get_youtube_results,
    search_bing, get_bing_results, format_bing_results,
    get_naver_results_smart, get_bing_results_smart,
    get_naver_news_smart, multi_search
)
from search.naver_search import format_search_results
from search.youtube_search import format_youtube_results


class SearchHandler:
    """검색 요청 처리"""
    
    def __init__(self, ai_handler=None):
        self.ai_handler = ai_handler
    
    def is_search_needed(self, prompt: str) -> bool:
        """검색이 필요한지 판단"""
        return any(keyword in prompt for keyword in SEARCH_KEYWORDS)
    
    def perform_auto_search(self, keyword: str) -> str:
        """자동 검색 실행 - 다중 검색"""
        try:
            log_debug(f"[검색] 다중 검색 시작: '{keyword}'")
            
            # 다중 검색 실행
            search_results = multi_search(
                keyword=keyword,
                sources=['naver', 'bing', 'news'],
                limit=3
            )
            
            search_context = ""
            has_results = False
            
            # 뉴스 결과 (가장 중요)
            if search_results.get('news') and len(search_results['news']) > 0:
                search_context += "📰 최신 뉴스:\n"
                search_context += "─" * 60 + "\n"
                
                for result in search_results['news'][:3]:
                    title = result.get('title', '')
                    date = result.get('date', '')
                    if title and len(title) > 5:
                        search_context += f"• {title}\n"
                        if date:
                            search_context += f"  📅 {date}\n"
                        has_results = True
                search_context += "\n"
            
            # 네이버 검색 결과
            if search_results.get('naver') and len(search_results['naver']) > 0:
                search_context += "🔍 네이버 검색 결과:\n"
                search_context += "─" * 60 + "\n"
                
                for result in search_results['naver'][:3]:
                    title = result.get('title', '')
                    desc = result.get('description', '')[:80]
                    if title and len(title) > 5:
                        search_context += f"• {title}\n"
                        if desc:
                            search_context += f"  {desc}\n"
                        has_results = True
                search_context += "\n"
            
            # Bing 검색 결과
            if search_results.get('bing') and len(search_results['bing']) > 0:
                search_context += "🌐 Bing 검색 결과:\n"
                search_context += "─" * 60 + "\n"
                
                for result in search_results['bing'][:2]:
                    title = result.get('title', '')
                    desc = result.get('description', '')[:80]
                    if title and len(title) > 5:
                        search_context += f"• {title}\n"
                        if desc:
                            search_context += f"  {desc}\n"
                        has_results = True
                search_context += "\n"
            
            # 유튜브
            youtube_url = search_youtube(keyword)
            search_context += "📺 유튜브:\n"
            search_context += "─" * 60 + "\n"
            search_context += f"    {youtube_url}\n"
            
            log_debug(f"[검색] 완료, {len(search_context)}글자, 결과: {has_results}")
            return search_context if search_context and has_results else f"📊 '검색 결과 없음' - 키워드: {keyword}"
            
        except Exception as e:
            log_debug(f"[오류] perform_auto_search: {e}")
            return f"검색 중 오류: {str(e)[:100]}"
    
    def fetch_search_page_text(self, url: str, max_chars: int = 4000) -> str:
        """검색 결과 페이지 HTML 다운로드"""
        try:
            use_selenium = any(host in url for host in ['search.naver.com', 'bing.com'])
            if use_selenium:
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)

                driver = None
                try:
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
                    driver.set_page_load_timeout(30)
                    driver.get(url)

                    try:
                        wait = WebDriverWait(driver, 15)
                        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                    except Exception:
                        log_debug(f"[페이지 대기] 렌더링 시간 초과: {url}")

                    page_source = driver.page_source
                finally:
                    if driver:
                        driver.quit()

                soup = BeautifulSoup(page_source, 'html.parser')
            else:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
                }
                response = requests.get(url, headers=headers, timeout=20)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()
            text = soup.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)
            return text[:max_chars]
        except Exception as e:
            log_debug(f"[페이지 다운로드 오류] {url}: {e}")
            return ''
    
    def summarize_search_pages(self, keyword: str, pages: list, model: str) -> str:
        """검색 결과 페이지를 AI로 요약"""
        chunks = []
        for item in pages:
            source = item.get('source')
            url = item.get('url')
            content = item.get('content')
            if not content:
                continue
            chunks.append(f"[{source}]\nURL: {url}\nCONTENT: {content}")

        if not chunks:
            return "검색 결과 페이지 내용을 가져오지 못했습니다."

        if not self.ai_handler:
            return "AI 핸들러가 설정되지 않았습니다."

        prompt = (
            "다음은 검색 결과 페이지에서 추출한 텍스트입니다.\n"
            "검색된 뉴스와 정보를 읽고, 주요 소식들을 간결한 문장으로 정리하세요.\n\n"
            "지시사항:\n"
            "1. 검색 결과에서 실제 뉴스 제목과 내용만 추출하세요\n"
            "2. 각 소식을 1-2개 문장으로 간결하게 요약하세요\n"
            "3. UI 요소(버튼, 메뉴, 검색옵션 등)는 무시하세요\n"
            "4. 형식: '주제 - 내용입니다' 또는 '주제: 내용입니다'\n"
            "5. 최대 5-8개 주요 소식만 선별하세요\n"
            "6. 각 소식 앞에 번호를 붙이지 마세요 (•나 - 사용)\n"
            "7. **반드시 한국어로 요약하세요**\n\n"
            f"검색어: {keyword}\n\n" + "\n\n".join(chunks) +
            "\n\n위 검색 결과에서 주요 소식만 간결한 문장으로 한국어로 정리:"
        )

        return self.ai_handler.generate_simple(prompt, model)
    
    def build_search_page_summary_text(self, keyword: str, model: str) -> str:
        """검색 페이지 요약 텍스트 생성"""
        from datetime import datetime
        
        pages = [
            {
                'source': 'Naver Web',
                'url': search_naver(keyword, 'web')
            },
            {
                'source': 'Naver News',
                'url': search_naver(keyword, 'news')
            },
            {
                'source': 'Bing Web',
                'url': search_bing(keyword, 'web')
            }
        ]

        for page in pages:
            page['content'] = self.fetch_search_page_text(page['url'])

        summary = self.summarize_search_pages(keyword, pages, model)

        today = datetime.now().strftime("%Y년 %m월 %d일")
        results_text = f"\n📄 검색 페이지 요약 [{today}]\n" + "─" * 60 + "\n"
        results_text += summary.strip() + "\n"
        results_text += "\n🔗 참고 URL\n" + "─" * 60 + "\n"
        for page in pages:
            results_text += f"• {page['source']}: {page['url']}\n"

        return results_text
    
    def execute_manual_search(self, command: str, filter_callback=None) -> str:
        """수동 검색 명령어 실행"""
        try:
            # 명령어 파싱
            if command.startswith('/네이버 '):
                keyword = command.replace('/네이버 ', '', 1).strip()
                search_type = 'naver'
            elif command.startswith('/빙 '):
                keyword = command.replace('/빙 ', '', 1).strip()
                search_type = 'bing'
            elif command.startswith('/뉴스 '):
                keyword = command.replace('/뉴스 ', '', 1).strip()
                search_type = 'news'
            elif command.startswith('/유튜브 '):
                keyword = command.replace('/유튜브 ', '', 1).strip()
                search_type = 'youtube'
            else:  # /검색
                keyword = command.replace('/검색 ', '', 1).strip()
                search_type = 'multi'
            
            if not keyword:
                return "❌ 검색어를 입력해주세요."
            
            results_text = f"\n🔍 '{keyword}' 검색 결과:\n"
            results_text += "━" * 60 + "\n"
            
            # 다중 검색
            if search_type == 'multi':
                # build_search_page_summary_text는 외부에서 호출됨
                return None  # 외부에서 처리
            
            # 개별 검색 - 네이버
            elif search_type == 'naver':
                news_results = get_naver_results(keyword, 'news', limit=5)
                
                if news_results:
                    results_text += "\n📰 네이버 뉴스\n" + "─" * 60 + "\n"
                    results_text += format_search_results(news_results)
                else:
                    results_text += "\n📝 검색 결과 없음\n"
            
            # 개별 검색 - Bing
            elif search_type == 'bing':
                bing_results = get_bing_results_smart(keyword, 'web', limit=5, use_selenium=True)
                
                if bing_results:
                    results_text += "\n🌐 Bing 검색 결과\n" + "─" * 60 + "\n"
                    results_text += format_bing_results(bing_results)
                else:
                    results_text += "\n⚠️ 검색 결과 없음\n"
            
            # 개별 검색 - 뉴스
            elif search_type == 'news':
                news_results = get_naver_news_smart(keyword, limit=5, use_selenium=True)
                if filter_callback:
                    news_results = filter_callback(news_results)
                
                if news_results:
                    results_text += "\n📰 뉴스 검색 결과\n" + "─" * 60 + "\n"
                    for i, result in enumerate(news_results, 1):
                        results_text += f"\n{i}. {result.get('title', 'N/A')}\n"
                        if result.get('date'):
                            results_text += f"   📅 {result['date']}\n"
                        if result.get('description'):
                            results_text += f"   📝 {result['description'][:100]}\n"
                        if result.get('url'):
                            results_text += f"   🔗 {result['url'][:80]}\n"
                else:
                    results_text += "\n⚠️ 오늘 뉴스 없음\n"
            
            # 개별 검색 - 유튜브
            elif search_type == 'youtube':
                youtube_results = get_youtube_results(keyword, limit=3)
                
                if youtube_results:
                    results_text += "\n📺 유튜브 검색\n" + "─" * 60 + "\n"
                    results_text += format_youtube_results(youtube_results)
            
            results_text += "\n" + "━" * 60 + "\n"
            return results_text
            
        except Exception as e:
            log_debug(f"[오류] execute_manual_search: {e}")
            return f"❌ 검색 오류: {e}"
