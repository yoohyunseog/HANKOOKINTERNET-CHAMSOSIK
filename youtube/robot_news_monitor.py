#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로봇 뉴스 전용 YouTube 모니터링 시스템
- 해외 로봇 뉴스, 휴머노이드, 자동화 관련 영상 수집
- AI가 영상 분석 후 재미있는 뉴스로 요약
- 한국어 번역 및 뉴스 데이터 생성
"""

import os
import sys
import json
import time
import re
import argparse
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

# 로봇 뉴스 전용 키워드 (해외 + 국내)
ROBOT_KEYWORDS = [
    # 해외 로봇 기업
    "Boston Dynamics robot",
    "Tesla Optimus humanoid",
    "Figure AI robot",
    "Agility Robotics Digit",
    "Unitree robot",
    "Sanctuary AI robot",
    "Apptronik robot",
    "1X Technologies robot",
    
    # 로봇 기술 키워드
    "humanoid robot 2026",
    "robot breakthrough",
    "robot AI integration",
    "robot learning",
    "robot manipulation",
    "robot navigation",
    
    # 산업용 로봇
    "industrial robot automation",
    "warehouse robot",
    "factory robot",
    "manufacturing robot",
    
    # 서비스 로봇
    "service robot",
    "delivery robot",
    "restaurant robot",
    "hospital robot",
    
    # 드론
    "drone delivery",
    "autonomous drone",
    "drone AI",
    
    # 한국 로봇
    "로봇 기술",
    "휴머노이드 로봇",
    "산업용 로봇",
    "서비스 로봇",
    "자율주행 로봇",
    "로봇 개발",
]

# 로봇 뉴스 소스 RSS 피드
ROBOT_RSS_FEEDS = [
    # 영문 소스
    "https://news.google.com/rss/search?q=humanoid+robot&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=robot+breakthrough&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=industrial+robot+automation&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=service+robot&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=drone+delivery&hl=en&gl=US&ceid=US:en",
    # 한국어 소스
    "https://news.google.com/rss/search?q=로봇+기술&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=휴머노이드&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=산업용+로봇&hl=ko&gl=KR&ceid=KR:ko",
]

OLLAMA_URL = "http://localhost:11434"
SCRIPT_DIR = Path(__file__).parent.resolve()
REPORTS_BASE_DIR = SCRIPT_DIR / "robot_reports"
LOGS_DIR = SCRIPT_DIR / "logs"
ROBOT_NEWS_DATA_FILE = SCRIPT_DIR.parent / "web" / "public" / "한국인터넷.한국" / "참소식.com" / "robot" / "news_data.json"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_BASE_DIR.mkdir(parents=True, exist_ok=True)

# Ollama 모델 설정
AVAILABLE_MODELS = [
    "gemma4:31b-cloud",
    "kimi-k2.5:cloud",
    "qwen3:32b",
    "gemma3:latest",
    "mistral:latest",
    "neural-chat:latest",
]


class SilentYtDlpLogger:
    def debug(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        pass


def get_available_ollama_model() -> Optional[str]:
    """사용 가능한 Ollama 모델 확인"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            for model in AVAILABLE_MODELS:
                if any(model.split(":")[0] in m for m in models):
                    return model
            # 사용 가능한 모델이 있으면 첫 번째 반환
            if models:
                return models[0]
    except Exception as e:
        print(f"[WARN] Ollama 연결 실패: {e}")
    return None


def search_youtube_videos(keyword: str, max_results: int = 5) -> List[Dict]:
    """YouTube에서 로봇 관련 영상 검색 (yt-dlp 사용)"""
    videos = []
    
    try:
        import yt_dlp
        
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "logger": SilentYtDlpLogger(),
        }
        
        search_url = f"ytsearch{max_results}:{keyword}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(search_url, download=False)
            entries = result.get("entries", [])
            
            for entry in entries[:max_results]:
                if entry:
                    videos.append({
                        "title": entry.get("title", ""),
                        "url": f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                        "video_id": entry.get("id", ""),
                        "views": entry.get("view_count", 0),
                        "upload_date": entry.get("upload_date", ""),
                        "duration": entry.get("duration", 0),
                    })
    
    except Exception as e:
        print(f"[WARN] YouTube 검색 실패 ({keyword}): {e}")
    
    return videos


def get_video_subtitles(video_url: str) -> str:
    """YouTube 영상에서 자막 추출"""
    try:
        import yt_dlp
        
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en", "ko"],
            "skip_download": True,
            "logger": SilentYtDlpLogger(),
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # 자막 추출
            subtitles = info.get("subtitles", {}) or info.get("automatic_captions", {})
            
            for lang in ["ko", "en"]:
                if lang in subtitles and subtitles[lang]:
                    sub_url = subtitles[lang][0].get("url", "")
                    if sub_url:
                        try:
                            sub_response = requests.get(sub_url, timeout=10)
                            if sub_response.status_code == 200:
                                # VTT/SRT 파싱
                                lines = re.sub(r"<[^>]+>", "", sub_response.text)
                                lines = re.sub(r"\d{2}:\d{2}:\d{2}", "", lines)
                                lines = re.sub(r"^\s*$", "", lines, flags=re.MULTILINE)
                                subtitle_text = "\n".join(
                                    line.strip() for line in lines.split("\n") 
                                    if line.strip() and not line.strip().startswith("WEBVTT")
                                )[:3000]
                                return subtitle_text
                        except Exception:
                            pass
            
    except Exception as e:
        print(f"[WARN] 자막 추출 실패: {e}")
    
    return ""


def analyze_robot_video(video: Dict, model: str) -> Dict[str, Any]:
    """YouTube 로봇 영상 분석"""
    video_url = video.get("url", "")
    video_title = video.get("title", "")
    
    print(f"   📹 영상 분석 중: {video_title[:50]}...")
    
    # 자막 추출
    subtitle_text = get_video_subtitles(video_url)
    
    if not subtitle_text:
        # 자막이 없으면 제목만으로 분석
        subtitle_text = f"영상 제목: {video_title}"
    
    # AI 분석 (JSON format 사용 안 함)
    analysis_prompt = f"""다음은 로봇 관련 YouTube 영상 정보입니다.

영상 제목: {video_title}
내용: {subtitle_text[:1000]}

이 영상에 대해 다음을 분석해주세요:

1. 요약 (2-3문장, 한국어)
2. 카테고리 (Humanoid/Industrial/Service/Drone/Research 중 하나)
3. 흥미로운지 여부 (예/아니오)
4. 반응 (Positive/Negative/Mixed/Neutral 중 하나)
5. 키워드 3개 (쉼표로 구분)

답변 형식:
요약: [요약 내용]
카테고리: [카테고리]
흥미로운지: [예/아니오]
반응: [반응]
키워드: [키워드1, 키워드2, 키워드3]"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": analysis_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.5,
                    "num_predict": 500,
                }
            },
            timeout=90
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis_text = result.get("response", "")
            
            # 텍스트에서 정보 추출
            summary = "분석 실패"
            category = "Other"
            interesting = False
            mood = "Neutral"
            keywords = []
            
            lines = analysis_text.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith("요약:"):
                    summary = line.replace("요약:", "").strip()
                elif line.startswith("카테고리:"):
                    cat_text = line.replace("카테고리:", "").strip()
                    if "Humanoid" in cat_text or "휴머노이드" in cat_text:
                        category = "Humanoid"
                    elif "Industrial" in cat_text or "산업" in cat_text:
                        category = "Industrial"
                    elif "Service" in cat_text or "서비스" in cat_text:
                        category = "Service"
                    elif "Drone" in cat_text or "드론" in cat_text:
                        category = "Drone"
                    elif "Research" in cat_text or "연구" in cat_text:
                        category = "Research"
                elif line.startswith("흥미로운지:"):
                    interesting_text = line.replace("흥미로운지:", "").strip()
                    interesting = "예" in interesting_text or "yes" in interesting_text.lower()
                elif line.startswith("반응:"):
                    mood_text = line.replace("반응:", "").strip()
                    if "Positive" in mood_text or "긍정" in mood_text:
                        mood = "Positive"
                    elif "Negative" in mood_text or "부정" in mood_text:
                        mood = "Negative"
                    elif "Mixed" in mood_text or "혼합" in mood_text:
                        mood = "Mixed"
                elif line.startswith("키워드:"):
                    keyword_text = line.replace("키워드:", "").strip()
                    keywords = [k.strip() for k in keyword_text.split(",") if k.strip()][:5]
            
            return {
                "title": video_title,
                "url": video_url,
                "video_id": video.get("video_id", ""),
                "summary": summary,
                "interesting": interesting,
                "category": category,
                "mood": mood,
                "keywords": keywords,
                "views": video.get("views", 0),
                "upload_date": video.get("upload_date", ""),
                "duration": video.get("duration", 0),
            }
        
    except Exception as e:
        print(f"[ERROR] AI 분석 실패: {e}")
    
    return {
        "title": video_title,
        "url": video_url,
        "video_id": video.get("video_id", ""),
        "summary": "분석 실패",
        "interesting": False,
        "category": "Other",
        "mood": "Neutral",
        "keywords": [],
        "views": video.get("views", 0),
        "upload_date": video.get("upload_date", ""),
    }


def generate_news_data(analyzed_videos: List[Dict], model: str) -> Dict:
    """로봇 뉴스 데이터 생성"""
    # 흥미로운 영상 우선 선택
    interesting_videos = [v for v in analyzed_videos if v.get("interesting", False)]
    
    # 흥미로운 영상이 없으면 상위 10개 선택
    if not interesting_videos:
        interesting_videos = analyzed_videos[:10]
    
    news_items = []
    for idx, video in enumerate(interesting_videos[:15], 1):
        news_items.append({
            "id": idx,
            "title": video.get("title", ""),
            "summary": video.get("summary", ""),
            "category": video.get("category", "Other"),
            "mood": video.get("mood", "Neutral"),
            "keywords": video.get("keywords", []),
            "url": video.get("url", ""),
            "video_id": video.get("video_id", ""),
            "views": video.get("views", 0),
            "upload_date": video.get("upload_date", ""),
            "collected_at": datetime.now().strftime("%Y-%m-%d"),
            "interesting": video.get("interesting", False),
        })
    
    return {
        "last_updated": datetime.now().isoformat(),
        "total_count": len(news_items),
        "mood_analysis": {
            "Positive": len([n for n in news_items if n["mood"] == "Positive"]),
            "Negative": len([n for n in news_items if n["mood"] == "Negative"]),
            "Mixed": len([n for n in news_items if n["mood"] == "Mixed"]),
            "Neutral": len([n for n in news_items if n["mood"] == "Neutral"]),
        },
        "items": news_items,
    }


def main():
    parser = argparse.ArgumentParser(description="로봇 뉴스 YouTube 모니터링")
    parser.add_argument("--max-videos", type=int, default=3, help="키워드당 최대 영상 수")
    parser.add_argument("--keywords", type=int, default=5, help="검색할 키워드 수")
    parser.add_argument("--output", type=str, help="출력 JSON 파일 경로")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🤖 로봇 뉴스 YouTube 모니터링 시작")
    print("=" * 60)
    print()
    
    # Ollama 모델 확인
    model = get_available_ollama_model()
    if not model:
        print("[ERROR] 사용 가능한 Ollama 모델이 없습니다.")
        print("[INFO] Ollama가 실행 중인지 확인하세요: ollama serve")
        return 1
    
    print(f"✅ 사용 모델: {model}")
    print()
    
    # 로봇 키워드로 YouTube 검색
    all_videos = []
    search_keywords = ROBOT_KEYWORDS[:args.keywords]
    
    print(f"🔍 {len(search_keywords)}개 키워드로 YouTube 검색...")
    print()
    
    for idx, keyword in enumerate(search_keywords, 1):
        print(f"[{idx}/{len(search_keywords)}] 검색: {keyword}")
        videos = search_youtube_videos(keyword, args.max_videos)
        print(f"   → {len(videos)}개 영상 발견")
        all_videos.extend(videos)
        time.sleep(1)  # API 제한 방지
    
    # 중복 제거
    seen_urls = set()
    unique_videos = []
    for video in all_videos:
        if video["url"] not in seen_urls:
            seen_urls.add(video["url"])
            unique_videos.append(video)
    
    print()
    print(f"📊 총 {len(unique_videos)}개 고유 영상 수집")
    print()
    
    if not unique_videos:
        print("[WARN] 수집된 영상이 없습니다.")
        return 1
    
    # 영상 분석
    print("🤖 AI 분석 시작...")
    print()
    
    analyzed_videos = []
    for idx, video in enumerate(unique_videos[:15], 1):
        print(f"[{idx}/{min(15, len(unique_videos))}] ", end="")
        analysis = analyze_robot_video(video, model)
        if analysis:
            analyzed_videos.append(analysis)
        time.sleep(2)  # API 제한 방지
    
    print()
    
    if not analyzed_videos:
        print("[ERROR] 분석된 영상이 없습니다.")
        return 1
    
    # 뉴스 데이터 생성
    news_data = generate_news_data(analyzed_videos, model)
    
    # 저장
    output_path = Path(args.output) if args.output else ROBOT_NEWS_DATA_FILE
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    
    print("=" * 60)
    print("✅ 로봇 뉴스 데이터 저장 완료")
    print("=" * 60)
    print(f"📁 저장 위치: {output_path}")
    print(f"📊 총 {news_data['total_count']}개 뉴스")
    print(f"🎯 흥미로운 뉴스: {len([v for v in analyzed_videos if v.get('interesting')])}개")
    print()
    
    # 카테고리별 통계
    categories = {}
    for item in news_data["items"]:
        cat = item["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    print("📈 카테고리별 분포:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {cat}: {count}개")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())


class SilentYtDlpLogger:
    def debug(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        pass


def get_available_ollama_model() -> Optional[str]:
    """사용 가능한 Ollama 모델 확인"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            for model in AVAILABLE_MODELS:
                if any(model.split(":")[0] in m for m in models):
                    return model
            # 사용 가능한 모델이 있으면 첫 번째 반환
            if models:
                return models[0]
    except Exception as e:
        print(f"[WARN] Ollama 연결 실패: {e}")
    return None


def translate_to_korean(text: str, model: str) -> str:
    """영문 텍스트를 한국어로 번역"""
    if not text or not model:
        return text
    
    prompt = f"""다음 영문 로봇 뉴스를 한국어로 번역하라. 
기술 용어는 원어를 괄호에 병기하고, 자연스러운 뉴스 문체로 작성하라.

영문 원문:
{text}

한국어 번역:"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 1000,
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", text).strip()
    except Exception as e:
        print(f"[WARN] 번역 실패: {e}")
    
    return text


def analyze_robot_video(video_url: str, video_title: str, model: str) -> Dict[str, Any]:
    """YouTube 로봇 영상 분석"""
    try:
        import yt_dlp
    except ImportError:
        print("[ERROR] yt-dlp가 설치되지 않았습니다: pip install yt-dlp")
        return {}
    
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": ["en", "ko"],
        "skip_download": True,
        "logger": SilentYtDlpLogger(),
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # 자막 추출
            subtitles = info.get("subtitles", {}) or info.get("automatic_captions", {})
            subtitle_text = ""
            
            for lang in ["ko", "en"]:
                if lang in subtitles and subtitles[lang]:
                    sub_url = subtitles[lang][0].get("url", "")
                    if sub_url:
                        try:
                            sub_response = requests.get(sub_url, timeout=10)
                            if sub_response.status_code == 200:
                                # VTT/SRT 파싱
                                lines = re.sub(r"<[^>]+>", "", sub_response.text)
                                lines = re.sub(r"\d{2}:\d{2}:\d{2}", "", lines)
                                lines = re.sub(r"^\s*$", "", lines, flags=re.MULTILINE)
                                subtitle_text = "\n".join(
                                    line.strip() for line in lines.split("\n") 
                                    if line.strip() and not line.strip().startswith("WEBVTT")
                                )[:3000]
                                break
                        except Exception:
                            pass
            
            if not subtitle_text:
                return {
                    "title": video_title,
                    "url": video_url,
                    "summary": "자막을 찾을 수 없습니다.",
                    "category": "Robot",
                    "interesting": False,
                }
            
            # AI 분석
            analysis_prompt = f"""다음은 로봇 관련 YouTube 영상의 자막입니다. 이를 분석하여:

1. 핵심 내용을 2-3문장으로 요약 (한국어)
2. 이 뉴스가 흥미로운지 평가 (interesting: true/false)
3. 카테고리 분류 (Humanoid/Industrial/Service/Drone/Research/Other)
4. 반응 흐름 분석 (Positive/Negative/Mixed/Neutral)

자막:
{subtitle_text[:2000]}

JSON 형식으로 응답:
{{
  "summary": "요약 내용",
  "interesting": true/false,
  "category": "카테고리",
  "mood": "반응흐름",
  "keywords": ["키워드1", "키워드2"]
}}"""

            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": analysis_prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": 0.5,
                        "num_predict": 800,
                    }
                },
                timeout=90
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis_text = result.get("response", "{}")
                try:
                    analysis = json.loads(analysis_text)
                except json.JSONDecodeError:
                    analysis = {}
                
                return {
                    "title": video_title,
                    "url": video_url,
                    "summary": analysis.get("summary", "분석 실패"),
                    "interesting": analysis.get("interesting", False),
                    "category": analysis.get("category", "Robot"),
                    "mood": analysis.get("mood", "Neutral"),
                    "keywords": analysis.get("keywords", []),
                    "views": info.get("view_count", 0),
                    "upload_date": info.get("upload_date", ""),
                }
            
    except Exception as e:
        print(f"[ERROR] 영상 분석 실패: {e}")
    
    return {}


def search_robot_youtube_videos(keyword: str, max_results: int = 5) -> List[Dict]:
    """YouTube에서 로봇 관련 영상 검색"""
    videos = []
    
    try:
        import yt_dlp
        
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "logger": SilentYtDlpLogger(),
        }
        
        search_url = f"ytsearch{max_results}:{keyword}"
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(search_url, download=False)
            entries = result.get("entries", [])
            
            for entry in entries[:max_results]:
                if entry:
                    videos.append({
                        "title": entry.get("title", ""),
                        "url": f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                        "views": entry.get("view_count", 0),
                        "upload_date": entry.get("upload_date", ""),
                    })
    
    except Exception as e:
        print(f"[WARN] YouTube 검색 실패 ({keyword}): {e}")
    
    return videos


def fetch_rss_robot_news() -> List[Dict]:
    """RSS 피드에서 로봇 뉴스 수집"""
    news_items = []
    
    for feed_url in ROBOT_RSS_FEEDS:
        try:
            response = requests.get(feed_url, timeout=10)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for item in root.findall(".//item")[:5]:
                    title = item.find("title")
                    link = item.find("link")
                    pub_date = item.find("pubDate")
                    
                    if title is not None and link is not None:
                        news_items.append({
                            "title": title.text or "",
                            "url": link.text or "",
                            "pub_date": pub_date.text if pub_date is not None else "",
                            "source": "RSS",
                        })
        except Exception as e:
            print(f"[WARN] RSS 수집 실패 ({feed_url}): {e}")
    
    return news_items


def generate_news_data(analyzed_videos: List[Dict], model: str) -> Dict:
    """로봇 뉴스 데이터 생성"""
    interesting_videos = [v for v in analyzed_videos if v.get("interesting", False)]
    
    # 흥미로운 영상이 없으면 상위 5개 선택
    if not interesting_videos:
        interesting_videos = analyzed_videos[:5]
    
    news_items = []
    for idx, video in enumerate(interesting_videos[:10], 1):
        news_items.append({
            "id": idx,
            "title": video.get("title", ""),
            "summary": video.get("summary", ""),
            "category": video.get("category", "Robot"),
            "mood": video.get("mood", "Neutral"),
            "keywords": video.get("keywords", []),
            "url": video.get("url", ""),
            "views": video.get("views", 0),
            "upload_date": video.get("upload_date", ""),
            "collected_at": datetime.now().isoformat(),
        })
    
    return {
        "last_updated": datetime.now().isoformat(),
        "total_count": len(news_items),
        "mood_analysis": {
            "Positive": len([n for n in news_items if n["mood"] == "Positive"]),
            "Negative": len([n for n in news_items if n["mood"] == "Negative"]),
            "Mixed": len([n for n in news_items if n["mood"] == "Mixed"]),
            "Neutral": len([n for n in news_items if n["mood"] == "Neutral"]),
        },
        "items": news_items,
    }


def main():
    parser = argparse.ArgumentParser(description="로봇 뉴스 YouTube 모니터링")
    parser.add_argument("--max-videos", type=int, default=3, help="키워드당 최대 영상 수")
    parser.add_argument("--keywords", type=int, default=5, help="검색할 키워드 수")
    parser.add_argument("--output", type=str, help="출력 JSON 파일 경로")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🤖 로봇 뉴스 모니터링 시작")
    print("=" * 60)
    
    # Ollama 모델 확인
    model = get_available_ollama_model()
    if not model:
        print("[ERROR] 사용 가능한 Ollama 모델이 없습니다.")
        return 1
    
    print(f"✅ 사용 모델: {model}")
    
    # 로봇 키워드로 YouTube 검색
    all_videos = []
    search_keywords = ROBOT_KEYWORDS[:args.keywords]
    
    for keyword in search_keywords:
        print(f"\n🔍 검색: {keyword}")
        videos = search_robot_youtube_videos(keyword, args.max_videos)
        print(f"   → {len(videos)}개 영상 발견")
        all_videos.extend(videos)
        time.sleep(1)  # API 제한 방지
    
    # 중복 제거
    seen_urls = set()
    unique_videos = []
    for video in all_videos:
        if video["url"] not in seen_urls:
            seen_urls.add(video["url"])
            unique_videos.append(video)
    
    print(f"\n📊 총 {len(unique_videos)}개 고유 영상 수집")
    
    # 영상 분석
    analyzed_videos = []
    for idx, video in enumerate(unique_videos[:15], 1):
        print(f"\n[{idx}/{min(15, len(unique_videos))}] 분석: {video['title'][:50]}...")
        analysis = analyze_robot_video(video["url"], video["title"], model)
        if analysis:
            analyzed_videos.append(analysis)
        time.sleep(2)  # API 제한 방지
    
    # 뉴스 데이터 생성
    news_data = generate_news_data(analyzed_videos, model)
    
    # 저장
    output_path = Path(args.output) if args.output else ROBOT_NEWS_DATA_FILE
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 뉴스 데이터 저장: {output_path}")
    print(f"   - 총 {news_data['total_count']}개 뉴스")
    print(f"   - 흥미로운 뉴스: {len([v for v in analyzed_videos if v.get('interesting')])}개")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())