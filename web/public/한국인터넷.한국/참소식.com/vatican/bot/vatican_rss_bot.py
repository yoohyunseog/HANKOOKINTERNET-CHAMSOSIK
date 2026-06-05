"""
Vatican News RSS 피드 봇
- RSS 피드에서 뉴스 수집
- 원본 JSON 저장
- AI로 번역/요약
- 마크다운 정리
"""

import json
import os
import requests
from datetime import datetime
from urllib.parse import urlparse
import time
import xml.etree.ElementTree as ET

# --- 설정 ---
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://211.45.162.155:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "kimi-k2.5:cloud")

# 결과 저장 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_SAVE_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "vatican_rss_raw.json"))
TRANSLATED_SAVE_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "vatican_rss_translated.json"))
MARKDOWN_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "vatican_news_summary.md"))

# RSS 피드 URL
RSS_FEEDS = [
    {"name": "Vatican News 한국어", "url": "https://www.vaticannews.va/ko.rss.xml", "lang": "ko"},
    {"name": "가톨릭신문", "url": "http://www.catholicpress.kr/rss_view.php", "lang": "ko"},
]

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}


class OllamaLLM:
    """Ollama LLM 클라이언트"""
    
    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL):
        self.host = host
        self.model = model
    
    def check_connection(self) -> bool:
        """Ollama 서버 연결 확인"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                print(f"✓ Ollama 연결됨: {self.host}")
                print(f"  사용 가능한 모델: {', '.join(model_names)}")
                return True
        except Exception as e:
            print(f"✗ Ollama 연결 실패: {e}")
        return False
    
    def generate(self, prompt: str) -> str:
        """텍스트 생성"""
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 500}
                },
                timeout=60
            )
            if response.status_code == 200:
                return response.json().get("response", "").strip()
        except Exception as e:
            print(f"    LLM 오류: {e}")
        return ""
    
    def translate_to_korean(self, text: str) -> str:
        """텍스트를 한국어로 번역"""
        if not text:
            return ""
        prompt = f"""다음 텍스트를 한국어로 번역하세요. 번역 결과만 출력하세요.

텍스트: {text}

한국어 번역:"""
        return self.generate(prompt)
    
    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """텍스트를 한국어로 요약"""
        if not text:
            return ""
        prompt = f"""다음 텍스트를 한국어로 {max_sentences}문장 이내로 요약하세요. 핵심 내용만 간결하게 정리하세요.

텍스트: {text}

한국어 요약:"""
        return self.generate(prompt)


class RSSParser:
    """RSS 피드 파서"""
    
    @staticmethod
    def parse_feed(url: str, feed_name: str) -> list:
        """RSS 피드 파싱"""
        print(f"  RSS 피드 가져오는 중: {feed_name}")
        items = []
        
        try:
            response = requests.get(url, headers=REQUEST_HEADERS, timeout=15)
            response.raise_for_status()
            
            # XML 파싱
            root = ET.fromstring(response.content)
            
            # RSS 2.0 형식
            channel = root.find("channel")
            if channel is None:
                channel = root
            
            for item in channel.findall(".//item")[:10]:  # 최대 10개
                try:
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    description = item.findtext("description", "")
                    pub_date = item.findtext("pubDate", "")
                    
                    # 날짜 파싱
                    if pub_date:
                        try:
                            # RFC 2822 형식 파싱
                            from email.utils import parsedate_to_datetime
                            dt = parsedate_to_datetime(pub_date)
                            pub_date_iso = dt.isoformat()
                        except:
                            pub_date_iso = pub_date
                    else:
                        pub_date_iso = None
                    
                    if title and link:
                        items.append({
                            "title": title,
                            "url": link,
                            "description": description,
                            "pub_date": pub_date_iso,
                            "source": feed_name,
                            "feed_url": url
                        })
                except Exception as e:
                    print(f"    아이템 파싱 오류: {e}")
                    continue
            
            print(f"    {len(items)}개 항목 수집")
            
        except Exception as e:
            print(f"    RSS 피드 오류: {e}")
        
        return items


def sort_by_date(items: list) -> list:
    """날짜순 정렬 (최신순)"""
    def get_date(item):
        date_str = item.get("pub_date", "")
        if date_str:
            try:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except:
                pass
        return datetime(1970, 1, 1)
    
    return sorted(items, key=get_date, reverse=True)


def generate_markdown(items: list, output_path: str) -> str:
    """마크다운 생성"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    md = f"""# 📰 Vatican News RSS 피드 요약

**생성일:** {now}  
**총 기사:** {len(items)}개

---

"""
    
    current_date = None
    
    for i, item in enumerate(items, 1):
        # 날짜 헤더
        pub_date = item.get("pub_date", "")
        if pub_date:
            try:
                dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
            except:
                date_str = "날짜 없음"
        else:
            date_str = "날짜 없음"
        
        if date_str != current_date:
            current_date = date_str
            md += f"\n## 📅 {date_str}\n\n"
        
        # 기사 내용
        title = item.get("title_ko") or item.get("title", "제목 없음")
        title_orig = item.get("title", "")
        url = item.get("url", "")
        summary = item.get("summary_ko") or item.get("description", "")
        source = item.get("source", "")
        
        md += f"""### {i}. {title[:80]}{'...' if len(title) > 80 else ''}

- **원문:** {title_orig[:80]}{'...' if len(title_orig) > 80 else ''}
- **출처:** {source}
- **URL:** [{url[:60]}{'...' if len(url) > 60 else ''}]({url})

**요약:** {summary[:200]}{'...' if len(summary) > 200 else ''}

---

"""
    
    # 파일 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md)
    
    print(f"✓ 마크다운 저장: {output_path}")
    return md


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("  📰 Vatican News RSS 피드 봇")
    print("=" * 60)
    print(f"시작 시간: {datetime.now().isoformat()}")
    print(f"모델: {OLLAMA_MODEL}")
    print()
    
    # 초기화
    llm = OllamaLLM()
    
    # 연결 확인
    if not llm.check_connection():
        print("Ollama 연결 실패. 번역 없이 진행합니다.")
        use_llm = False
    else:
        use_llm = True
    
    # ========================================
    # 1단계: RSS 피드 수집
    # ========================================
    print("\n" + "=" * 60)
    print("  [1단계] RSS 피드 수집")
    print("=" * 60)
    
    all_items = []
    for feed in RSS_FEEDS:
        items = RSSParser.parse_feed(feed["url"], feed["name"])
        for item in items:
            item["lang"] = feed["lang"]
        all_items.extend(items)
        time.sleep(0.5)  # Rate limiting
    
    # 날짜순 정렬
    all_items = sort_by_date(all_items)
    
    print(f"\n총 {len(all_items)}개 기사 수집")
    
    # 원본 저장
    raw_data = {
        "stage": "rss_collected",
        "collected_at": datetime.now().isoformat(),
        "total_items": len(all_items),
        "feeds": [f["name"] for f in RSS_FEEDS],
        "items": all_items
    }
    
    with open(RAW_SAVE_PATH, 'w', encoding='utf-8') as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    print(f"✓ 원본 저장: {RAW_SAVE_PATH}")
    
    # ========================================
    # 2단계: LLM 번역 및 요약
    # ========================================
    if use_llm:
        print("\n" + "=" * 60)
        print("  [2단계] LLM 번역 및 요약")
        print("=" * 60)
        
        processed_items = []
        for i, item in enumerate(all_items[:10], 1):  # 최대 10개
            print(f"  처리 중 {i}/{min(len(all_items), 30)}: {item['title'][:50]}...")
            
            # 한국어가 아닌 경우만 번역
            if item.get("lang") != "ko":
                title_ko = llm.translate_to_korean(item["title"])
            else:
                title_ko = item["title"]
            
            # 요약
            summary_ko = llm.summarize(item.get("description", ""))
            
            processed_items.append({
                **item,
                "title_ko": title_ko,
                "summary_ko": summary_ko
            })
            
            time.sleep(0.3)  # Rate limiting
        
        # 번역된 결과 저장
        translated_data = {
            "stage": "llm_translated",
            "translated_at": datetime.now().isoformat(),
            "total_items": len(processed_items),
            "items": processed_items
        }
        
        with open(TRANSLATED_SAVE_PATH, 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)
        print(f"✓ 번역 저장: {TRANSLATED_SAVE_PATH}")
    else:
        processed_items = all_items
    
    # ========================================
    # 3단계: 마크다운 정리
    # ========================================
    print("\n" + "=" * 60)
    print("  [3단계] 마크다운 정리")
    print("=" * 60)
    
    md_content = generate_markdown(processed_items, MARKDOWN_PATH)
    
    # 미리보기
    print("\n[마크다운 미리보기]")
    print("-" * 40)
    lines = md_content.split("\n")[:30]
    print("\n".join(lines))
    if len(lines) >= 30:
        print("\n... (생략됨)")
    
    print("\n" + "=" * 60)
    print("  ✅ RSS 피드 봇 완료!")
    print(f"  - 원본: {RAW_SAVE_PATH}")
    print(f"  - 번역: {TRANSLATED_SAVE_PATH}")
    print(f"  - 마크다운: {MARKDOWN_PATH}")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit(main())