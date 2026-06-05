"""
유튜브 영상 검색 봇
- article_news.json의 제목을 키워드로 사용
- 유튜브에서 관련 영상 검색
- JSON, 마크다운으로 저장
"""

import json
import os
import re
import requests
from datetime import datetime
from urllib.parse import quote, urlparse, parse_qs

# --- 설정 ---
OLLAMA_HOST = "http://211.45.162.155:11434"
OLLAMA_MODEL = "kimi-k2.5:cloud"

# 결과 저장 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_JSON = os.path.abspath(os.path.join(BASE_DIR, "..", "article_news.json"))
OUTPUT_JSON = os.path.abspath(os.path.join(BASE_DIR, "..", "youtube_videos.json"))
OUTPUT_MD = os.path.abspath(os.path.join(BASE_DIR, "..", "youtube_videos_summary.md"))

# 유튜브 검색 설정
YOUTUBE_SEARCH_URL = "https://www.youtube.com/results"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

def text_value(value) -> str:
    """YouTube text 객체를 일반 문자열로 변환."""
    if not isinstance(value, dict):
        return ""
    if value.get("simpleText"):
        return value["simpleText"]
    return "".join(run.get("text", "") for run in value.get("runs", []))


def parse_view_count(text: str) -> int:
    """한국어/영문 조회수 문구를 정수로 변환."""
    cleaned = text.replace(",", "")
    match = re.search(r"([\d.]+)\s*([천만억KMB]?)", cleaned, re.I)
    if not match:
        return 0
    number = float(match.group(1))
    unit = match.group(2).lower()
    multiplier = {"천": 1_000, "만": 10_000, "억": 100_000_000, "k": 1_000, "m": 1_000_000, "b": 1_000_000_000}
    return int(number * multiplier.get(unit, 1))


def find_video_renderers(value):
    """ytInitialData 내부의 videoRenderer를 순회."""
    if isinstance(value, dict):
        renderer = value.get("videoRenderer")
        if isinstance(renderer, dict):
            yield renderer
        for child in value.values():
            yield from find_video_renderers(child)
    elif isinstance(value, list):
        for child in value:
            yield from find_video_renderers(child)


def extract_video_results(html: str, max_results: int) -> list:
    """YouTube 구조화 검색 데이터에서 영상과 조회수를 추출."""
    match = re.search(r"var ytInitialData = ({.*?});</script>", html, re.S)
    if not match:
        return []
    initial_data = json.loads(match.group(1))
    videos = []
    seen = set()
    for renderer in find_video_renderers(initial_data):
        video_id = renderer.get("videoId")
        if not video_id or video_id in seen:
            continue
        seen.add(video_id)
        view_text = text_value(renderer.get("viewCountText")) or text_value(renderer.get("shortViewCountText"))
        videos.append({
            "id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
            "title": text_value(renderer.get("title"))[:100],
            "view_count": parse_view_count(view_text),
            "view_count_text": view_text,
        })
        if len(videos) >= max_results:
            break
    return videos


class YouTubeSearchBot:
    """유튜브 영상 검색 봇"""
    
    def __init__(self):
        """초기화"""
        print(f"✅ 유튜브 영상 검색 봇 초기화 완료")
        print(f"   - 입력: {INPUT_JSON}")
        print(f"   - 출력: {OUTPUT_JSON}")
    
    def load_article_titles(self) -> list:
        """기사 제목 로드"""
        if not os.path.exists(INPUT_JSON):
            print(f"✗ 입력 파일 없음: {INPUT_JSON}")
            return []
        
        with open(INPUT_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        items = data.get('items', [])
        titles = []
        
        for item in items:
            title = item.get('title', '').strip()
            if title:
                # 키워드 추출 (불필요한 단어 제거)
                keywords = self._extract_keywords(title)
                titles.append({
                    'title': title,
                    'keywords': keywords,
                    'source': item.get('source', ''),
                    'pub_date': item.get('pub_date', '')
                })
        
        print(f"✓ 기사 제목 로드: {len(titles)}개")
        return titles
    
    def _extract_keywords(self, title: str) -> str:
        """제목에서 검색 키워드 추출"""
        # 불필요한 단어 제거
        stop_words = ['[일반알현]', '[삼종기도]', '교황님들의 복음 해설:', '교황의', '6월', '2026년']
        
        keywords = title
        for word in stop_words:
            keywords = keywords.replace(word, '')
        
        # 특수문자 제거
        keywords = re.sub(r'[^\w\s가-힣]', ' ', keywords)
        keywords = ' '.join(keywords.split())
        
        # 너무 길면 앞부분만 사용
        if len(keywords) > 50:
            keywords = keywords[:50]
        
        return keywords.strip()
    
    def search_youtube(self, query: str, max_results: int = 3) -> list:
        """유튜브 검색 (웹 스크래핑)"""
        videos = []
        
        try:
            # 검색 URL 생성
            search_url = f"https://www.youtube.com/results?search_query={quote(query)}"
            
            print(f"   검색: {query[:40]}...")
            
            # 웹 페이지 요청
            response = requests.get(search_url, headers=REQUEST_HEADERS, timeout=15)
            response.raise_for_status()
            
            html = response.text
            videos = extract_video_results(html, max_results)
            for video in videos:
                video["query"] = query
            
        except Exception as e:
            print(f"   ✗ 검색 실패: {e}")
        
        return videos
    
    def search_all_articles(self, articles: list, max_per_article: int = 2) -> dict:
        """모든 기사에 대해 유튜브 검색"""
        all_videos = []
        
        print(f"\n📺 유튜브 영상 검색 시작...")
        
        for i, article in enumerate(articles, 1):
            title = article['title']
            keywords = article['keywords']
            
            print(f"\n[{i}/{len(articles)}] {title[:40]}...")
            
            # 유튜브 검색
            videos = self.search_youtube(keywords, max_per_article)
            
            for video in videos:
                video['article_title'] = title
                video['article_source'] = article.get('source', '')
                video['article_date'] = article.get('pub_date', '')
                all_videos.append(video)
        
        result = {
            "search_time": datetime.now().isoformat(),
            "total_videos": len(all_videos),
            "total_articles": len(articles),
            "videos": all_videos
        }
        
        return result
    
    def save_results(self, data: dict):
        """결과 저장"""
        # JSON 저장
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 JSON 저장: {OUTPUT_JSON}")
        
        # 마크다운 저장
        md_content = self._generate_markdown(data)
        with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"💾 마크다운 저장: {OUTPUT_MD}")
    
    def _generate_markdown(self, data: dict) -> str:
        """마크다운 형식으로 변환"""
        lines = []
        lines.append("# 📺 유튜브 영상 모음")
        lines.append("")
        lines.append(f"**검색일:** {data['search_time']}")
        lines.append(f"**총 영상:** {data['total_videos']}개")
        lines.append(f"**관련 기사:** {data['total_articles']}개")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 기사별로 그룹화
        from collections import defaultdict
        by_article = defaultdict(list)
        
        for video in data['videos']:
            by_article[video['article_title']].append(video)
        
        for article_title, videos in by_article.items():
            lines.append(f"## 📰 {article_title[:60]}")
            lines.append("")
            
            for video in videos:
                vid = video['id']
                url = video['url']
                title = video.get('title', '제목 없음')
                thumbnail = video['thumbnail']
                
                lines.append(f"### [{title[:50]}]({url})")
                lines.append("")
                lines.append(f"[![썸네일]({thumbnail})]({url})")
                lines.append("")
                lines.append(f"- **영상 URL:** {url}")
                lines.append(f"- **영상 ID:** {vid}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return '\n'.join(lines)
    
    def run(self):
        """실행"""
        print("\n" + "="*60)
        print("📺 유튜브 영상 검색 봇 시작")
        print("="*60)
        
        # 기사 제목 로드
        articles = self.load_article_titles()
        if not articles:
            print("✗ 처리할 데이터가 없습니다.")
            return
        
        # 유튜브 검색
        result = self.search_all_articles(articles, max_per_article=2)
        
        # 결과 저장
        self.save_results(result)
        
        print("\n" + "="*60)
        print(f"✅ 완료! 총 {result['total_videos']}개 영상 검색됨")
        print("="*60)


def main():
    """메인 실행"""
    bot = YouTubeSearchBot()
    bot.run()


if __name__ == "__main__":
    main()
