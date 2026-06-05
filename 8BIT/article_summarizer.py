"""
최신 기사 요약 AI
- 다양한 뉴스 사이트에서 최신 기사 크롤링
- Ollama AI를 사용한 기사 요약
- JSON 형식으로 저장
"""

import json
import os
import time
import re
from datetime import datetime
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 기존 모듈
try:
    from text_summarizer import TextSummarizer
    from keyword_extractor import KeywordExtractor
except ImportError:
    from .text_summarizer import TextSummarizer
    from .keyword_extractor import KeywordExtractor


class ArticleSummarizer:
    """최신 기사 요약 AI 클래스"""
    
    def __init__(self, use_ollama=True, ollama_url="http://localhost:11434", ollama_model=""):
        """
        초기화
        
        Args:
            use_ollama (bool): Ollama AI 사용 여부
            ollama_url (str): Ollama 서버 URL
            ollama_model (str): 사용할 모델명 (빈 문자열이면 자동 선택)
        """
        self.use_ollama = use_ollama
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.summarizer = TextSummarizer()
        self.extractor = KeywordExtractor()
        
        # 뉴스 사이트 설정
        self.news_sites = [
            {
                "name": "네이버 뉴스",
                "url": "https://news.naver.com",
                "type": "portal",
                "enabled": True
            },
            {
                "name": "다음 뉴스",
                "url": "https://news.daum.net",
                "type": "portal",
                "enabled": True
            },
            {
                "name": "연합뉴스",
                "url": "https://www.yna.co.kr",
                "type": "agency",
                "enabled": True
            },
            {
                "name": "KBS 뉴스",
                "url": "https://news.kbs.co.kr",
                "type": "broadcast",
                "enabled": True
            }
        ]
        
        # 출력 디렉토리
        self.output_dir = os.path.join("data", "article_summaries")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Ollama 모델 자동 선택
        if self.use_ollama and not self.ollama_model:
            self.ollama_model = self._get_default_model()
        
        print(f"✅ 기사 요약 AI 초기화 완료")
        print(f"   - Ollama 사용: {self.use_ollama}")
        if self.use_ollama:
            print(f"   - 모델: {self.ollama_model}")
    
    def _get_default_model(self):
        """Ollama 기본 모델 가져오기"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            models = data.get("models", [])
            if models:
                # 우선순위: gemma > mistral > llama > 기타
                preferred = ["gemma", "mistral", "llama", "qwen"]
                for model in models:
                    name = model.get("name", "")
                    for pref in preferred:
                        if pref in name.lower():
                            return name
                return models[0].get("name", "")
        except Exception as e:
            print(f"⚠️ Ollama 모델 조회 실패: {e}")
        return ""
    
    def _call_ollama(self, prompt, timeout=120):
        """Ollama API 호출"""
        if not self.ollama_model:
            return None
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except Exception as e:
            print(f"⚠️ Ollama 호출 실패: {e}")
            return None
    
    def _summarize_with_ai(self, title, content, keywords):
        """AI를 사용한 기사 요약"""
        if not self.use_ollama or not self.ollama_model:
            return None
        
        prompt = f"""다음 뉴스 기사를 요약해주세요.

제목: {title}

본문:
{content[:2000]}

키워드: {', '.join(keywords)}

요약 조건:
1. 핵심 내용을 3-5문장으로 요약
2. 중요한 사실 위주로 작성
3. 객관적이고 명확하게 작성
4. 한국어로 작성

요약:"""
        
        return self._call_ollama(prompt)
    
    def _fetch_article_content(self, url):
        """URL에서 기사 내용 추출"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 제목 추출
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # 메타 설명
            description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '').strip()
            
            # 본문 추출 (일반적인 뉴스 사이트 구조)
            content = ""
            
            # 네이버 뉴스
            article_body = soup.find('div', {'id': 'articleBodyContents'}) or \
                          soup.find('div', {'class': 'article_body'}) or \
                          soup.find('article', {'class': 'article'})
            
            if article_body:
                # 불필요한 태그 제거
                for tag in article_body.find_all(['script', 'style', 'iframe', 'img']):
                    tag.decompose()
                content = article_body.get_text().strip()
            
            # 일반적인 article 태그
            if not content:
                article = soup.find('article') or soup.find('div', {'class': 'content'}) or \
                         soup.find('div', {'class': 'article-content'})
                if article:
                    for tag in article.find_all(['script', 'style', 'iframe', 'img']):
                        tag.decompose()
                    content = article.get_text().strip()
            
            # 본문이 없으면 본문 텍스트 사용
            if not content:
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            
            # 여전히 없으면 body 텍스트
            if not content:
                body = soup.find('body')
                if body:
                    for tag in body.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                        tag.decompose()
                    content = body.get_text().strip()
            
            # 텍스트 정리
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r'[\n\r]+', ' ', content)
            
            return {
                "url": url,
                "title": title,
                "description": description,
                "content": content[:5000]  # 최대 5000자
            }
            
        except Exception as e:
            print(f"⚠️ 기사 내용 추출 실패 ({url}): {e}")
            return None
    
    def crawl_news_site(self, site_config, max_articles=5):
        """
        뉴스 사이트에서 최신 기사 크롤링
        
        Args:
            site_config (dict): 사이트 설정
            max_articles (int): 최대 기사 수
            
        Returns:
            list: 기사 URL 리스트
        """
        articles = []
        
        try:
            print(f"📰 {site_config['name']} 크롤링 중...")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(site_config['url'], headers=headers, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 뉴스 링크 추출
            links = []
            
            # 일반적인 뉴스 링크 패턴
            for a in soup.find_all('a', href=True):
                href = a.get('href', '')
                
                # 뉴스 관련 URL 패턴
                if any(pattern in href for pattern in ['/article/', '/news/', '/view/', '/read/']):
                    if href.startswith('http'):
                        links.append(href)
                    elif href.startswith('/'):
                        links.append(f"{site_config['url']}{href}")
            
            # 중복 제거
            links = list(set(links))[:max_articles * 2]  # 여유분
            
            print(f"   발견된 링크: {len(links)}개")
            
            return links
            
        except Exception as e:
            print(f"⚠️ {site_config['name']} 크롤링 실패: {e}")
            return []
    
    def process_article(self, url):
        """
        단일 기사 처리
        
        Args:
            url (str): 기사 URL
            
        Returns:
            dict: 처리된 기사 데이터
        """
        print(f"   📄 처리 중: {url[:60]}...")
        
        # 기사 내용 추출
        article_data = self._fetch_article_content(url)
        if not article_data:
            return None
        
        title = article_data.get('title', '')
        content = article_data.get('content', '')
        
        if not content:
            print(f"   ⚠️ 본문 없음")
            return None
        
        # 키워드 추출
        keywords = self.extractor.extract_keywords(content, title, max_keywords=7)
        
        # 기본 요약 (규칙 기반)
        basic_summary = self.summarizer.summarize(content, title, max_length=200)
        
        # AI 요약
        ai_summary = self._summarize_with_ai(title, content, keywords)
        
        # 결과 데이터
        result = {
            "url": url,
            "title": title,
            "description": article_data.get('description', ''),
            "keywords": keywords,
            "basic_summary": basic_summary,
            "ai_summary": ai_summary,
            "content_length": len(content),
            "crawled_at": datetime.now().isoformat(),
            "source": urlparse(url).netloc
        }
        
        return result
    
    def summarize_latest_articles(self, max_articles_per_site=3, save_json=True):
        """
        최신 기사 요약 실행
        
        Args:
            max_articles_per_site (int): 사이트당 최대 기사 수
            save_json (bool): JSON 저장 여부
            
        Returns:
            dict: 요약 결과
        """
        print("\n" + "="*60)
        print("🤖 최신 기사 요약 AI 시작")
        print("="*60)
        
        all_articles = []
        
        # 각 뉴스 사이트 크롤링
        for site in self.news_sites:
            if not site.get('enabled', True):
                continue
            
            # 기사 링크 수집
            links = self.crawl_news_site(site, max_articles_per_site)
            
            # 각 기사 처리
            for link in links[:max_articles_per_site]:
                article = self.process_article(link)
                if article:
                    all_articles.append(article)
                    time.sleep(1)  # 요청 간격
        
        # 결과 정리
        result = {
            "summary_time": datetime.now().isoformat(),
            "total_articles": len(all_articles),
            "articles": all_articles,
            "statistics": {
                "sites_processed": len([s for s in self.news_sites if s.get('enabled', True)]),
                "total_keywords": sum(len(a.get('keywords', [])) for a in all_articles),
                "ai_summarized": sum(1 for a in all_articles if a.get('ai_summary'))
            }
        }
        
        # JSON 저장
        if save_json and all_articles:
            self._save_to_json(result)
        
        print("\n" + "="*60)
        print(f"✅ 완료! 총 {len(all_articles)}개 기사 처리됨")
        print("="*60)
        
        return result
    
    def _save_to_json(self, data):
        """결과를 JSON 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"article_summaries_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 저장 완료: {filepath}")
        
        # 최신 파일도 저장 (항상 같은 이름으로)
        latest_path = os.path.join(self.output_dir, "latest_article_summaries.json")
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def summarize_custom_urls(self, urls, save_json=True):
        """
        지정된 URL 목록 요약
        
        Args:
            urls (list): URL 리스트
            save_json (bool): JSON 저장 여부
            
        Returns:
            dict: 요약 결과
        """
        print("\n" + "="*60)
        print("🤖 커스텀 URL 기사 요약 시작")
        print("="*60)
        
        all_articles = []
        
        for url in urls:
            article = self.process_article(url)
            if article:
                all_articles.append(article)
            time.sleep(1)
        
        result = {
            "summary_time": datetime.now().isoformat(),
            "total_articles": len(all_articles),
            "articles": all_articles,
            "statistics": {
                "urls_processed": len(urls),
                "successful": len(all_articles),
                "total_keywords": sum(len(a.get('keywords', [])) for a in all_articles),
                "ai_summarized": sum(1 for a in all_articles if a.get('ai_summary'))
            }
        }
        
        if save_json and all_articles:
            self._save_to_json(result)
        
        return result


def main():
    """메인 실행 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='최신 기사 요약 AI')
    parser.add_argument('--max', type=int, default=3, help='사이트당 최대 기사 수')
    parser.add_argument('--no-ai', action='store_true', help='AI 요약 비활성화')
    parser.add_argument('--model', type=str, default='', help='Ollama 모델명')
    parser.add_argument('--urls', type=str, nargs='+', help='직접 지정할 URL들')
    
    args = parser.parse_args()
    
    # 요약기 초기화
    summarizer = ArticleSummarizer(
        use_ollama=not args.no_ai,
        ollama_model=args.model
    )
    
    # 실행
    if args.urls:
        result = summarizer.summarize_custom_urls(args.urls)
    else:
        result = summarizer.summarize_latest_articles(max_articles_per_site=args.max)
    
    # 결과 출력
    print("\n📊 요약 결과:")
    print(f"   - 총 기사 수: {result['total_articles']}")
    print(f"   - AI 요약 수: {result['statistics']['ai_summarized']}")
    
    for i, article in enumerate(result['articles'][:3], 1):
        print(f"\n{i}. {article['title'][:50]}...")
        print(f"   키워드: {', '.join(article['keywords'][:5])}")
        if article.get('ai_summary'):
            print(f"   AI 요약: {article['ai_summary'][:100]}...")
        else:
            print(f"   기본 요약: {article['basic_summary'][:100]}...")


if __name__ == "__main__":
    main()