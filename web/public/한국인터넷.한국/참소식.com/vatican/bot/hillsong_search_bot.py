"""
Hillsong Worship 영상 검색 봇
- Hillsong Worship 관련 영상 검색
- JSON, 마크다운으로 저장
"""

import json
import os
import re
import requests
from datetime import datetime
from urllib.parse import quote

# --- 설정 ---
OLLAMA_HOST = "http://211.45.162.155:11434"
OLLAMA_MODEL = "kimi-k2.5:cloud"

# 결과 저장 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_JSON = os.path.abspath(os.path.join(BASE_DIR, "..", "hillsong_videos.json"))
OUTPUT_MD = os.path.abspath(os.path.join(BASE_DIR, "..", "hillsong_videos_summary.md"))

# Hillsong Worship 검색 키워드
HILLSONG_KEYWORDS = [
    "Hillsong Worship",
    "Hillsong United",
    "Hillsong LIVE",
    "Hillsong Praise",
    "What A Beautiful Name Hillsong",
    "Oceans Hillsong UNITED",
    "Mighty To Save Hillsong",
    "Shout To The Lord Hillsong",
    "Hillsong Worship Korean",
    "Hillsong Worship 한국어",
    "Hillsong Contemporary Worship",
    "Hillsong Best Worship Songs",
    "Hillsong Top Songs",
    "Hillsong Acoustic Worship",
    "Hillsong Live Worship",
]

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


class HillsongSearchBot:
    """Hillsong Worship 영상 검색 봇"""
    
    def __init__(self):
        """초기화"""
        print(f"✅ Hillsong Worship 영상 검색 봇 초기화 완료")
        print(f"   - 출력: {OUTPUT_JSON}")
        print(f"   - 키워드: {len(HILLSONG_KEYWORDS)}개")
    
    def search_youtube(self, query: str, max_results: int = 5) -> list:
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
                video["search_date"] = datetime.now().isoformat()
            
        except Exception as e:
            print(f"   ✗ 검색 실패: {e}")
        
        return videos
    
    def search_all_keywords(self, max_per_keyword: int = 3) -> dict:
        """모든 키워드에 대해 유튜브 검색"""
        all_videos = []
        seen_ids = set()  # 중복 제거용
        
        print(f"\n📺 Hillsong Worship 영상 검색 시작...")
        
        for i, keyword in enumerate(HILLSONG_KEYWORDS, 1):
            print(f"\n[{i}/{len(HILLSONG_KEYWORDS)}] {keyword}")
            
            # 유튜브 검색
            videos = self.search_youtube(keyword, max_per_keyword)
            
            for video in videos:
                vid = video['id']
                if vid not in seen_ids:
                    seen_ids.add(vid)
                    video['keyword'] = keyword
                    all_videos.append(video)
        
        result = {
            "search_time": datetime.now().isoformat(),
            "total_videos": len(all_videos),
            "total_keywords": len(HILLSONG_KEYWORDS),
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
        lines.append("# 🎵 Hillsong Worship 영상 모음")
        lines.append("")
        lines.append(f"**검색일:** {data['search_time']}")
        lines.append(f"**총 영상:** {data['total_videos']}개")
        lines.append(f"**검색 키워드:** {data['total_keywords']}개")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 키워드별로 그룹화
        from collections import defaultdict
        by_keyword = defaultdict(list)
        
        for video in data['videos']:
            by_keyword[video['keyword']].append(video)
        
        for keyword, videos in by_keyword.items():
            lines.append(f"## 🔍 {keyword}")
            lines.append("")
            
            for video in videos:
                vid = video['id']
                url = video['url']
                title = video.get('title', '제목 없음')
                thumbnail = video['thumbnail']
                
                lines.append(f"### [{title[:60]}]({url})")
                lines.append("")
                lines.append(f"[![썸네일]({thumbnail})]({url})")
                lines.append("")
                lines.append(f"- **영상 URL:** {url}")
                lines.append(f"- **영상 ID:** {vid}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        # 인기 영상 섹션
        lines.append("## ⭐ 인기 Hillsong Worship 영상")
        lines.append("")
        lines.append("### What A Beautiful Name")
        lines.append("[![What A Beautiful Name](https://img.youtube.com/vi/VPZ4L8i3hXk/mqdefault.jpg)](https://www.youtube.com/watch?v=VPZ4L8i3hXk)")
        lines.append("")
        lines.append("### Oceans (Where Feet May Fail)")
        lines.append("[![Oceans](https://img.youtube.com/vi/d_yXuWuQrBI/mqdefault.jpg)](https://www.youtube.com/watch?v=d_yXuWuQrBI)")
        lines.append("")
        lines.append("### Mighty To Save")
        lines.append("[![Mighty To Save](https://img.youtube.com/vi/0BkQYy0XjH8/mqdefault.jpg)](https://www.youtube.com/watch?v=0BkQYy0XjH8)")
        lines.append("")
        
        return '\n'.join(lines)
    
    def run(self):
        """실행"""
        print("\n" + "="*60)
        print("🎵 Hillsong Worship 영상 검색 봇 시작")
        print("="*60)
        
        # 유튜브 검색
        result = self.search_all_keywords(max_per_keyword=3)
        
        # 결과 저장
        self.save_results(result)
        
        print("\n" + "="*60)
        print(f"✅ 완료! 총 {result['total_videos']}개 영상 검색됨")
        print("="*60)


def main():
    """메인 실행"""
    bot = HillsongSearchBot()
    bot.run()


if __name__ == "__main__":
    main()
