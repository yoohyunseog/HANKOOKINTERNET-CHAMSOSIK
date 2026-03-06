#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube 키워드 지속 모니터링 시스템
- 정치, 주식, 비트코인 관련 최신 뉴스/논란 키워드 10개씩 검색
- JSON + 마크다운 보고서 자동 생성
- 날짜별 폴더에 저장
"""

import os
import sys
import json
import time
import argparse
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

# RSS 피드 URL - 정치, 주식, 비트코인 위주
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=정치+논란&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=주식+급등&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=코스피+주요뉴스&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=환율+경제+뉴스&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=국회+이슈&hl=ko&gl=KR&ceid=KR:ko",
    "https://news.google.com/rss/search?q=기업+실적+전망&hl=ko&gl=KR&ceid=KR:ko",
]

OLLAMA_URL = "http://localhost:11434"
DATABASE_BASE_URL = os.getenv("DATABASE_BASE_URL", "https://xn--9l4b4xi9r.com")
DATABASE_SAVE_ENABLED = os.getenv("DATABASE_SAVE_ENABLED", "1") == "1"
DATABASE_OPEN_PAGE = os.getenv("DATABASE_OPEN_PAGE", "0") == "1"
DATABASE_OPEN_MODE = os.getenv("DATABASE_OPEN_MODE", "popup").strip().lower()
YOUTUBE_CC_FALLBACK = os.getenv("YOUTUBE_CC_FALLBACK", "0") == "1"
SCRIPT_DIR = Path(__file__).parent.resolve()
REPORTS_BASE_DIR = SCRIPT_DIR / "reports"
LOGS_DIR = SCRIPT_DIR / "logs"
SUBTITLE_FAILURE_LOG_FILE = LOGS_DIR / "subtitle_failures.log"
DATABASE_SAVE_LOG_FILE = LOGS_DIR / "database_save.log"
KEYWORDS_FILE = SCRIPT_DIR / "monitor_keywords.txt"
FIXED_KEYWORD = "오늘의 주요 뉴스"
SUBTITLE_BLOCK_WARNED = False
CURRENT_OLLAMA_MODEL = None  # 런타임에 설정됨

LOGS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DYNAMIC_KEYWORDS = [
    "정치 논란"
]


class SilentYtDlpLogger:
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


def get_today_report_dir() -> Path:
    """오늘 날짜 폴더 경로 반환 (예: reports/2026-03-06/)"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    report_dir = REPORTS_BASE_DIR / today_str
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def load_keywords_from_file(max_keywords: int = 0) -> List[str]:
    """키워드 파일에서 동적 키워드 불러오기 (고정 키워드 제외, max_keywords<=0이면 전체)"""
    try:
        if not KEYWORDS_FILE.exists():
            return []

        with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        loaded_keywords = []
        seen = set()
        for keyword in lines:
            if keyword == FIXED_KEYWORD:
                continue
            if keyword not in seen:
                seen.add(keyword)
                loaded_keywords.append(keyword)
            if max_keywords > 0 and len(loaded_keywords) >= max_keywords:
                break

        return loaded_keywords
    except Exception as e:
        print(f"[WARN] 키워드 파일 로드 실패: {e}")
        return []


def save_keywords_to_file(keywords: List[str]) -> None:
    """키워드 자동 저장 비활성화 (수동 관리 전용)"""
    return


def normalize_summary_text(text: str) -> str:
    """요약 텍스트 정리: 별표/마크다운 기호 제거"""
    if not text:
        return text

    cleaned = text.replace("**", "")
    cleaned = cleaned.replace("*", "")
    cleaned = cleaned.replace("#", "")

    normalized_lines = []
    for line in cleaned.split("\n"):
        normalized = line.strip()
        while normalized.startswith(("-", ":")):
            normalized = normalized[1:].strip()
        if normalized:
            normalized_lines.append(normalized)

    return "\n".join(normalized_lines).strip()


def format_summary_with_ollama(keyword: str, upload_date: str, summary: str) -> str:
    """올라마가 요약을 포맷팅: 키워드에 맞는 메시지 + 핵심 내용 1줄"""
    global CURRENT_OLLAMA_MODEL
    
    if not CURRENT_OLLAMA_MODEL or not summary:
        return normalize_summary_text(summary)

    # 올라마가 요약을 단일 소식 1문장으로 생성
    prompt = f"""다음 요약을 보고 '가장 중요한 소식 1개'만 한국어 한 문장으로 작성하라.

입력 키워드: {keyword}
입력 요약: {summary}

엄격 규칙:
1) 결과는 반드시 한 문장만 출력
2) 결과는 반드시 대괄호로 감쌀 것. 예: [여기에 한 문장]
3) 번호(1. 2. 3.), 줄바꿈, 불릿, 제목/채널명/조회수/날짜 제거
4) 여러 내용이 있으면 가장 중요한 1개만 선택
5) 괄호 포함 전체 길이는 90~140자 (즉, 문장 본문은 88~138자)
6) 설명/접두어/추가 문장 절대 금지

출력: 대괄호 한 문장 1개만"""
    
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": CURRENT_OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3,
            },
            timeout=20,
        )
        response.raise_for_status()
        
        result = response.json()
        formatted = result.get("response", "").strip()

        if formatted:
            import re
            min_body_len = 88
            max_body_len = 138

            one_line = " ".join(formatted.split())

            # 1) 대괄호 문장 우선 추출
            bracket_match = re.search(r"\[(.*?)\]", one_line)
            if bracket_match:
                sentence = bracket_match.group(1).strip()
            else:
                # 2) 첫 문장만 사용
                first_sentence = re.split(r"(?<=[.!?。！？])\s+", one_line)[0].strip()
                sentence = first_sentence

            # 번호/불릿 제거
            sentence = re.sub(r"^\s*[\-•*#]+\s*", "", sentence)
            sentence = re.sub(r"^\s*\d+[\.)]\s*", "", sentence)
            sentence = sentence.replace("[", " ").replace("]", " ")
            sentence = re.sub(r"\s+", " ", sentence)
            sentence = sentence.strip(" []")
            sentence = sentence.split("[")[0].strip()

            # 흔한 잡문구 제거
            sentence = sentence.replace("을 3줄로 요약한 내용입니다.", "")
            sentence = sentence.replace("3줄로 요약한 내용입니다.", "")
            sentence = sentence.replace("3줄 요약", "")
            sentence = re.sub(r"\s+", " ", sentence).strip(" ,;:-")

            if sentence:
                # 너무 길면 단어 경계 기준으로 잘라 최대 길이 맞춤
                if len(sentence) > max_body_len:
                    cut = sentence[:max_body_len]
                    last_space = cut.rfind(" ")
                    if last_space >= min_body_len:
                        cut = cut[:last_space]
                    sentence = cut.rstrip(" ,;:-")

                # 여전히 짧으면 자연스러운 패딩 문구 추가
                if len(sentence) < min_body_len:
                    filler = "관련 파장이 확산되고 있습니다."
                    sentence = f"{sentence} {filler}".strip()

                # 최종 안전 장치
                if len(sentence) > max_body_len:
                    cut = sentence[:max_body_len]
                    last_space = cut.rfind(" ")
                    if last_space >= 0:
                        cut = cut[:last_space]
                    sentence = cut.rstrip(" ,;:-")

                return f"[{sentence}]"
    except Exception as e:
        print(f"[WARN] Ollama 포맷팅 실패: {e}")
    
    # 올라마 실패 시 기본 정리 사용
    return normalize_summary_text(summary)


def log_subtitle_failure(
    video_id: str,
    video_title: str,
    source: str,
    reason: str,
    upload_date: str = "",
) -> None:
    """자막 추출 실패 원인을 logs/subtitle_failures.log에 기록"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        safe_title = (video_title or "").replace("\n", " ").strip()
        safe_reason = (reason or "")[:1000].replace("\n", " ").strip()
        safe_upload_date = (upload_date or "-").strip() or "-"

        with open(SUBTITLE_FAILURE_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(
                f"[{timestamp}] source={source} video_id={video_id or '-'} "
                f"upload_date={safe_upload_date} title={safe_title or '-'} reason={safe_reason or '-'}\n"
            )
    except Exception:
        pass


def log_database_save(message: str) -> None:
    """참소식 DB 저장 로그 기록"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(DATABASE_SAVE_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


def resolve_upload_date_by_video_id(video_id: str) -> str:
    """video_id로 실제 업로드일(YYYY-MM-DD) 조회"""
    if not video_id:
        return ""
    try:
        import yt_dlp

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "socket_timeout": 15,
            "extract_flat": False,
            "logger": SilentYtDlpLogger(),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)

        raw_upload_date = (info or {}).get("upload_date", "")
        if raw_upload_date and len(raw_upload_date) == 8:
            return f"{raw_upload_date[:4]}-{raw_upload_date[4:6]}-{raw_upload_date[6:8]}"
    except Exception:
        pass
    return ""


UNAVAILABLE_SUMMARIES = {
    "자막 미분석",
    "자막 없음",
    "자막 파싱 실패",
    "자막 내용 부족",
    "요약 내용 부족",
    "요약 생성 시간초과",
    "Ollama 연결 실패",
    "요약 생성 오류",
    "요약 생성 실패",
    "오늘 날짜 영상 아님(건너뜀)",
    "구글 검색 실패",
    "구글 검색 결과 없음",
    "구글 요약 실패",
    "빙 검색 실패",
    "빙 검색 결과 없음",
    "빙 요약 실패",
    "네이버 검색 실패",
    "네이버 검색 결과 없음",
    "네이버 요약 실패",
    "줌 검색 실패",
    "줌 검색 결과 없음",
    "줌 요약 실패",
    "유튜브 자막 추출 실패",
}


def is_summary_eligible_for_db(summary: str) -> bool:
    summary = normalize_summary_text(summary or "")
    return bool(summary) and summary not in UNAVAILABLE_SUMMARIES


def open_database_page(url: str) -> str:
    """DB 저장 페이지 열기 (Windows 우선: 팝업형 창)"""
    if not url:
        return "skip-empty-url"

    try:
        # popup 모드: Chrome app-window 형태로 오픈 (탭/주소창 최소화)
        if os.name == "nt" and DATABASE_OPEN_MODE == "popup":
            chrome_candidates = []

            chrome_binary = os.getenv("CHROME_BINARY", "").strip()
            if chrome_binary:
                chrome_candidates.append(chrome_binary)

            chrome_candidates.extend([
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                str(Path.home() / "AppData/Local/Google/Chrome/Application/chrome.exe"),
            ])

            for exe in chrome_candidates:
                if exe and Path(exe).exists():
                    subprocess.Popen([
                        exe,
                        "--new-window",
                        f"--app={url}",
                        "--window-size=560,900",
                    ])
                    return "popup"

        import webbrowser
        webbrowser.open(url, new=1, autoraise=True)
        return "browser"
    except Exception as e:
        return f"error:{str(e)[:120]}"


def save_single_summary_to_database(keyword: str, video: Dict[str, Any]) -> bool:
    """단일 영상 요약을 참소식 DB에 즉시 저장"""
    if not DATABASE_SAVE_ENABLED:
        return False

    # 올라마로 포맷팅된 요약 생성
    title = (video.get("title") or "")[:120]
    raw_summary = video.get("subtitle_summary", "")
    upload_date = video.get("upload_date") or ""
    summary = format_summary_with_ollama(keyword, upload_date, raw_summary)
    
    if not is_summary_eligible_for_db(summary):
        return False

    # DB 저장: 간단한 형식 (키워드와 요약만)
    payload_text = f"{summary}"
    payload_text = payload_text[:900]
    params = {"nb": payload_text, "end": "5s"}

    try:
        request_url = requests.Request(
            "GET",
            f"{DATABASE_BASE_URL}/database.html",
            params=params,
        ).prepare().url

        response = requests.get(
            f"{DATABASE_BASE_URL}/database.html",
            params=params,
            timeout=12,
        )
        if 200 <= response.status_code < 400:
            log_database_save(f"SUCCESS status={response.status_code} title={title}")

            if DATABASE_OPEN_PAGE and request_url:
                try:
                    open_result = open_database_page(request_url)
                    log_database_save(f"OPENED page title={title} mode={open_result}")
                except Exception as e:
                    log_database_save(f"OPEN_FAIL title={title} reason={str(e)[:200]}")

            return True
        log_database_save(f"FAIL status={response.status_code} title={title}")
        return False
    except Exception as e:
        log_database_save(f"ERROR title={title} reason={str(e)[:200]}")
        return False


def save_completed_summaries_to_database(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """요약 완료된 자막만 참소식 DB 엔드포인트로 전송"""
    stats = {"sent": 0, "failed": 0, "skipped": 0}

    if not DATABASE_SAVE_ENABLED:
        log_database_save("DB 저장 비활성화(DATABASE_SAVE_ENABLED=0)")
        return stats

    for kw_data in results:
        keyword = kw_data.get("keyword", "")
        for video in kw_data.get("videos", []) or []:
            summary = normalize_summary_text(video.get("subtitle_summary", ""))
            if video.get("db_saved") is True:
                stats["skipped"] += 1
                continue

            if not is_summary_eligible_for_db(summary):
                stats["skipped"] += 1
                continue

            saved = save_single_summary_to_database(keyword, video)
            video["db_saved"] = saved
            if saved:
                stats["sent"] += 1
            else:
                stats["failed"] += 1
            time.sleep(0.2)

    return stats


def is_within_last_24_hours(upload_date: str) -> bool:
    """YYYY-MM-DD 날짜가 현재 시각 기준 최근 24시간 범위에 해당하는지(날짜 단위 근사)"""
    if not upload_date:
        return False

    try:
        date_obj = datetime.strptime(upload_date, "%Y-%m-%d")
    except ValueError:
        return False

    now = datetime.now()
    window_start = now - timedelta(hours=24)

    # 업로드 시각이 없으므로 해당 날짜의 마지막 시각(23:59:59) 기준으로 판정
    latest_possible = date_obj.replace(hour=23, minute=59, second=59)
    return latest_possible >= window_start


def is_today_video_with_ollama(video: Dict[str, Any], model: str) -> bool:
    """영상 날짜/조회수 텍스트를 Ollama에 보내 최근 24시간 영상인지 판정"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    upload_date = (video.get("upload_date") or "").strip()

    if not upload_date:
        resolved_date = resolve_upload_date_by_video_id(video.get("video_id", ""))
        if resolved_date:
            upload_date = resolved_date
            video["upload_date"] = resolved_date

    info_text = (
        f"제목: {video.get('title', '')}\n"
        f"업로드일: {upload_date or '알 수 없음'}\n"
        f"조회수: {video.get('views', 0):,}\n"
    )

    # 날짜 정보가 명확히 최근 24시간이 아니면 바로 제외
    if upload_date and not is_within_last_24_hours(upload_date):
        return False

    if not model:
        return True

    prompt = f"""다음 유튜브 영상 정보가 '현재 시각({now_str}) 기준 최근 24시간 이내 업로드 영상'인지 판정하세요.

영상 정보:
{info_text}

규칙:
1) 업로드일이 최근 24시간 이내로 판단되면 YES
2) 업로드일이 24시간을 초과하면 NO
3) 업로드일이 없어서 판단 불가면 NO

출력: YES 또는 NO 중 하나만"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 5,
                    "top_p": 0.1,
                },
            },
            timeout=20,
        )
        response.raise_for_status()
        result = response.json()
        verdict = (result.get("response", "") or "").strip().upper()
        return verdict.startswith("YES")
    except Exception:
        # Ollama 판정 실패 시 보수적으로 업로드일 기준으로만 판단
        return bool(upload_date and is_within_last_24_hours(upload_date))


def get_next_report_number(report_dir: Path) -> int:
    """해당 날짜 폴더의 다음 보고서 번호 반환"""
    existing_reports = list(report_dir.glob("report_*.json"))
    if not existing_reports:
        return 1
    
    numbers = []
    for report_file in existing_reports:
        try:
            num = int(report_file.stem.split("_")[1])
            numbers.append(num)
        except (IndexError, ValueError):
            continue
    
    return max(numbers) + 1 if numbers else 1


def get_latest_report_keywords(max_keywords: int = 8) -> Dict[str, Any]:
    """최신 리포트에서 상위 키워드들과 분석 데이터 추출
    Returns: {"keywords": [...], "info": "..."}
    """
    try:
        if not REPORTS_BASE_DIR.exists():
            return {"keywords": [], "info": ""}
        
        # 날짜별 폴더 목록 (최신순)
        date_folders = sorted(REPORTS_BASE_DIR.iterdir(), reverse=True)
        
        if not date_folders:
            return {"keywords": [], "info": ""}
        
        # 각 폴더에서 가장 최신 리포트 찾기
        for date_folder in date_folders:
            if not date_folder.is_dir():
                continue
                
            report_files = sorted(date_folder.glob("report_*.json"), reverse=True)
            
            if not report_files:
                continue
            
            latest_report = report_files[0]
            
            try:
                with open(latest_report, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 상위 키워드 추출 (오늘의 주요 뉴스 제외)
                keywords = []
                if isinstance(data, dict) and "keywords" in data:
                    all_keywords = data["keywords"]
                    for kw in all_keywords:
                        if kw.get("keyword") != "오늘의 주요 뉴스":
                            keywords.append(kw.get("keyword", ""))
                        if len(keywords) >= max_keywords:
                            break
                
                if keywords:
                    # 상위 키워드들로 정보 문자열 생성
                    keywords_str = ", ".join(keywords[:5])
                    return {
                        "keywords": keywords,
                        "info": f"최근 인기 주제: {keywords_str}"
                    }
            
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARN] 리포트 파싱 오류: {latest_report} - {e}")
                continue
        
        return {"keywords": [], "info": ""}
        
    except Exception as e:
        print(f"[WARN] 최신 리포트 검색 오류: {e}")
        return {"keywords": [], "info": ""}


def collect_rss_titles(rss_urls: List[str], max_per_feed: int = 20) -> List[str]:
    """RSS 피드에서 최신 뉴스 제목 수집"""
    all_titles = []
    
    # Google 자동 요청 차단 방지 위한 User-Agent 설정
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    for url in rss_urls:
        try:
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
            time.sleep(0.3)  # RSS 피드 요청 간 딜레이
            
            root = ET.fromstring(response.content)
            items = root.findall(".//item")[:max_per_feed]
            
            for item in items:
                title_elem = item.find("title")
                if title_elem is not None and title_elem.text:
                    all_titles.append(title_elem.text)
        
        except Exception as e:
            print(f"[WARN] RSS 피드 오류: {url[:250]}... - {e}")
            continue
    
    return all_titles


def get_available_ollama_models() -> List[str]:
    """설치된 Ollama 모델 목록 조회"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
        data = response.json()
        return [model["name"] for model in data.get("models", [])]
    except Exception as e:
        print(f"[WARN] Ollama 모델 조회 실패: {e}")
        return []


def choose_ollama_model(requested_model: str) -> str:
    """Ollama 모델 선택 (폴백 지원)"""
    installed = get_available_ollama_models()
    
    if requested_model in installed:
        return requested_model
    
    # 폴백 우선순위 (gemma3 모델 중심)
    fallback_order = [
        "gemma3:12b",      # 추천: 높은 성능 + 안정성
        "gemma3:4b",       # 빠르고 안정적
        "gemma3:27b",      # 강력하지만 느림
        "gemma3:1b",       # 라이트급
        "qwen2.5:latest",  # 고성능 대체 모델
        "mistral:latest",  # 안정적인 모델
        "gpt-oss:20b",     # 파워풀하지만 느림
    ]
    for model in fallback_order:
        if model in installed:
            print(f"[INFO] 모델 폴백: {requested_model} -> {model}")
            return model
    
    if installed:
        print(f"[INFO] 기본 모델 사용: {installed[0]}")
        return installed[0]
    
    raise Exception("사용 가능한 Ollama 모델이 없습니다.")


def generate_keywords_with_ollama(titles: List[str], model: str, count: int = 10) -> List[str]:
    """Ollama를 사용해 뉴스 제목에서 유튜브 검색 키워드 생성 ("오늘의 주요 뉴스" 고정 포함)"""
    # "오늘의 주요 뉴스"는 항상 첫 번째 키워드로 고정
    fixed_keyword = FIXED_KEYWORD
    
    # 나머지 키워드 생성
    titles_text = "\n".join(titles[:25])  # 최대 25개 제목만 사용 (50개→25개로 감소)
    remaining_count = count - 1  # "오늘의 주요 뉴스" 제외
    
    # 문장 형태 키워드 생성 프롬프트 - 상세 진술형
    prompt = f"""다음 뉴스를 분석하여 유튜브 검색용 상세 진술형 키워드 {remaining_count}개 생성:

{titles_text}

생성 조건:
1. 형식: "주제 + 상세 설명" (3-6단어 구문)
   예: "비트코인 가격 급등 전망", "부동산 시장 정책 변화 분석"
2. 각 키워드는 뉴스의 핵심 내용을 직접 반영
3. 정치/주식/경제 이슈 우선순위 높음, 비트코인/가상화폐 비중은 낮게 유지
4. 한국어만 사용, 중복 없음
5. 한 줄에 하나씩 (번호나 특수문자 제외)
6. 자연스러운 구검색어 형태

예시:
- 비트코인 가격 급등 전망 분석
- 주식 시장 급락 원인과 대응
- 부동산 규제 정책 논쟁
- 국회 정치 갈등 이슈
- 금리 인상 경제 영향

생성 키워드:"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.5,  # 0.7→0.5로 낮춤 (더 빠른 응답)
                    "top_p": 0.9,
                    "num_predict": 200,  # 최대 토큰 제한
                }
            },
            timeout=120  # 60초→120초로 증가
        )
        response.raise_for_status()
        result = response.json()
        
        keywords_text = result.get("response", "")
        
        # "생성 키워드:" 이후의 내용만 추출 (프롬프트 텍스트 제거)
        if "생성 키워드:" in keywords_text:
            keywords_text = keywords_text.split("생성 키워드:")[-1]
        elif "생성:" in keywords_text:
            keywords_text = keywords_text.split("생성:")[-1]
        
        generated_keywords = [
            line.strip()
            for line in keywords_text.split("\n")
            if isinstance(line, str) and line.strip() 
            and not line.strip().startswith("#") 
            and not line.strip().startswith("-")
            and not any(x in line for x in ["다음", "분석", "유튜브", "조건", "예시", "생성"])
        ]
        
        # 중복 제거 및 정리
        seen = set()
        unique_keywords = []
        for kw in generated_keywords:
            if not isinstance(kw, str):
                continue
                
            kw_clean = kw.strip().strip("\"'`*-:[]{}").strip()
            
            # 길이 체크 및 중복 제거
            if kw_clean and len(kw_clean) > 1 and kw_clean not in seen:
                # 숫자나 특수 문자만으로 이루어진 키워드 제외
                if not kw_clean[0].isdigit():
                    seen.add(kw_clean)
                    unique_keywords.append(kw_clean)
        
        # 비트코인/가상화폐 키워드는 최대 1개로 제한
        crypto_markers = ["비트코인", "코인", "가상화폐", "암호화폐"]
        crypto_count = 0
        filtered_keywords = []
        for keyword in unique_keywords:
            is_crypto = any(marker in keyword for marker in crypto_markers)
            if is_crypto:
                if crypto_count >= 1:
                    continue
                crypto_count += 1
            filtered_keywords.append(keyword)

        # "오늘의 주요 뉴스"를 첫 번째에 배치하고 나머지 키워드 추가
        final_keywords = [fixed_keyword] + filtered_keywords[:remaining_count]
        
        # 키워드가 부족한 경우 기본 키워드 추가
        if len(final_keywords) < count:
            file_keywords = load_keywords_from_file(max_keywords=remaining_count)
            default_keywords = file_keywords if file_keywords else DEFAULT_DYNAMIC_KEYWORDS
            for default_kw in default_keywords:
                if len(final_keywords) >= count:
                    break
                if default_kw not in final_keywords:
                    final_keywords.append(default_kw)
        
        return final_keywords[:count]
    
    except Exception as e:
        print(f"[ERROR] Ollama 키워드 생성 실패: {e}")
        print(f"[INFO] 키워드 파일/기본 키워드로 폴백합니다.")

        remaining_count = max(0, count - 1)
        file_keywords = load_keywords_from_file(max_keywords=remaining_count)
        fallback_dynamic = file_keywords if file_keywords else DEFAULT_DYNAMIC_KEYWORDS
        fallback_keywords = [FIXED_KEYWORD] + fallback_dynamic[:remaining_count]
        return fallback_keywords[:count]


def get_video_subtitles(video_id: str) -> str:
    """유튜브 영상의 자막 가져오기 (youtube-transcript-api 우선, yt_dlp 폴백)"""
    global SUBTITLE_BLOCK_WARNED
    transcript_error = None

    def _is_blocked_or_invalid(content: str) -> bool:
        if not content or len(content.strip()) < 20:
            return True
        lowered = content.lower()
        blocked_markers = [
            "<html",
            "<!doctype html",
            "<title>sorry",
            "unusual traffic",
            "recaptcha",
            "자동 요청",
            "our systems have detected unusual traffic",
        ]
        return any(marker in lowered for marker in blocked_markers)

    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        api = YouTubeTranscriptApi()
        language_sets = [
            ["ko", "en", "ja", "zh"],
            ["ko"],
            ["en"],
            None,
        ]

        for languages in language_sets:
            try:
                if languages is None:
                    transcript = api.fetch(video_id)
                else:
                    transcript = api.fetch(video_id, languages=languages)

                if not transcript:
                    continue

                if hasattr(transcript, "to_raw_data"):
                    raw_items = transcript.to_raw_data()
                    text = " ".join(item.get("text", "") for item in raw_items if isinstance(item, dict))
                else:
                    parts = []
                    for item in transcript:
                        if isinstance(item, dict):
                            parts.append(item.get("text", ""))
                        else:
                            parts.append(getattr(item, "text", ""))
                    text = " ".join(parts)

                text = text.strip()
                if text and not _is_blocked_or_invalid(text):
                    return text[:10000]
            except Exception as e:
                transcript_error = e
                continue
    except Exception as e:
        transcript_error = e

    # 폴백: yt_dlp 사용
    try:
        import yt_dlp

        video_url = f"https://www.youtube.com/watch?v={video_id}"

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        http_headers = {
            "User-Agent": user_agent,
            "Referer": "https://www.youtube.com/",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        cookie_file = os.getenv("YTDLP_COOKIES_FILE", "").strip()
        browser_name = os.getenv("YTDLP_BROWSER", "chrome").strip().lower()

        browser_candidates = [None]
        if os.getenv("USE_BROWSER_COOKIES", "0") == "1":
            browser_candidates.append(browser_name if browser_name else "chrome")

        for browser in browser_candidates:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "writesubtitles": True,
                "writeautomaticsub": True,
                "subtitleslangs": ["ko", "en", "ja", "zh"],
                "subtitlesformat": "vtt/best",
                "socket_timeout": 20,
                "http_headers": http_headers,
                "extractor_retries": 2,
                "sleep_interval_requests": 1,
                "ignoreerrors": True,
                "logger": SilentYtDlpLogger(),
            }

            if cookie_file and Path(cookie_file).exists():
                ydl_opts["cookiefile"] = cookie_file

            if browser:
                ydl_opts["cookiesfrombrowser"] = (browser,)

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)

                subtitles = info.get("subtitles", {}) if info else {}
                automatic_captions = info.get("automatic_captions", {}) if info else {}

                for lang in ["ko", "en", "ja", "zh"]:
                    if lang in subtitles:
                        try:
                            subtitle_url = subtitles[lang][0]["url"]
                            response = requests.get(subtitle_url, timeout=10, headers=http_headers)
                            content = response.text[:10000]
                            if content.strip() and not _is_blocked_or_invalid(content):
                                time.sleep(0.5)
                                return content
                        except Exception:
                            pass

                    if lang in automatic_captions:
                        try:
                            subtitle_url = automatic_captions[lang][0]["url"]
                            response = requests.get(subtitle_url, timeout=10, headers=http_headers)
                            content = response.text[:10000]
                            if content.strip() and not _is_blocked_or_invalid(content):
                                time.sleep(0.5)
                                return content
                        except Exception:
                            pass

                # URL 방식 실패 시: 자막 파일을 임시 폴더에 실제 다운로드 후 읽기
                try:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        outtmpl = str(Path(temp_dir) / "%(id)s.%(ext)s")
                        download_opts = dict(ydl_opts)
                        download_opts["outtmpl"] = outtmpl

                        with yt_dlp.YoutubeDL(download_opts) as ydl:
                            ydl.download([video_url])

                        subtitle_exts = ["*.vtt", "*.srt", "*.srv3", "*.xml", "*.ttml"]
                        for ext in subtitle_exts:
                            for subtitle_file in Path(temp_dir).glob(ext):
                                try:
                                    content = subtitle_file.read_text(encoding="utf-8", errors="ignore")[:20000]
                                    if content.strip() and not _is_blocked_or_invalid(content):
                                        time.sleep(0.5)
                                        return content
                                except Exception:
                                    continue
                except Exception:
                    pass
            except Exception:
                continue
    except Exception:
        pass

    if transcript_error and not SUBTITLE_BLOCK_WARNED:
        err_text = str(transcript_error)
        if "IpBlocked" in err_text or "RequestBlocked" in err_text or "Too Many Requests" in err_text:
            print("[WARN] YouTube 자막 요청이 차단되었습니다 (429/IP 차단). 잠시 후 재실행하거나 네트워크/IP를 변경해 주세요.")
            SUBTITLE_BLOCK_WARNED = True
    
    reason = "youtube_transcript_api/yt_dlp 자막 추출 실패"
    if transcript_error:
        reason = f"{reason} | last_error={str(transcript_error)[:300]}"
    log_subtitle_failure(video_id, "", "subtitles", reason)
    return ""


def analyze_subtitles_with_ollama(subtitles_text: str, model: str, video_title: str) -> str:
    """Ollama로 자막 내용 분석 및 요약 (VTT/XML 포맷 모두 지원)"""
    import re
    
    if not subtitles_text or len(subtitles_text) < 50:
        return "자막 없음"
    
    # 텍스트 추출
    text_lines = []
    
    # VTT 형식 처리
    if "WEBVTT" in subtitles_text:
        lines = subtitles_text.split("\n")
        for line in lines:
            line = line.strip()
            # 타임스탬프, 메타데이터, 빈줄 제외
            if (line and 
                not line.startswith("WEBVTT") and 
                "-->" not in line and 
                not line.isdigit() and
                not line.startswith("Kind:") and
                not line.startswith("Language:") and
                len(line) > 2):
                text_lines.append(line)
    
    # XML 형식 처리 (자동 생성 자막)
    elif "<text" in subtitles_text:
        # <text> 태그에서 텍스트 추출
        text_pattern = r'<text[^>]*>([^<]+)</text>'
        matches = re.findall(text_pattern, subtitles_text)
        for match in matches:
            text = (match.strip()
                   .replace("&amp;", "&")
                   .replace("&lt;", "<")
                   .replace("&gt;", ">")
                   .replace("&#39;", "'")
                   .replace("&quot;", '"'))
            if text and len(text) > 2:
                text_lines.append(text)
    
    # 일반 텍스트 처리
    else:
        for line in subtitles_text.split("\n"):
            line = line.strip()
            if line and len(line) > 2 and not line.isdigit():
                text_lines.append(line)
    
    if not text_lines:
        return "자막 파싱 실패"
    
    # 처음 100줄, 최대 1500자로 제한
    subtitle_content = " ".join(text_lines[:100])[:1500]
    
    if len(subtitle_content) < 20:
        return "자막 내용 부족"
    
    # 프롬프트
    prompt = f"""다음 영상의 자막을 3줄로 요약하시오:

제목: {video_title[:250]}
자막: {subtitle_content}

요약:"""
    
    # 재시도 로직 (타임아웃 시 3번까지 재시도)
    max_retries = 3
    for attempt in range(max_retries + 1):
        try:
            # 재시도 시에도 충분한 타임아웃 유지
            timeout = 180  # 180초 (3분)
            
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.2,  # 더 정확한 요약을 위해 낮은 온도
                        "num_predict": 500,  # 더 긴 요약 생성
                        "top_p": 0.8,  # 다양성 감소
                    }
                },
                timeout=timeout
            )
            response.raise_for_status()
            result = response.json()
            summary = result.get("response", "").strip()
            
            if summary and len(summary) > 3:
                # 프롬프트 텍스트 제거 (요약 시작 부분)
                # "다음은", "다음 영상", "이 영상", "요약:" 등의 프롬프트 부분을 찾아 제거
                prompt_phrases = [
                    "다음은 영상의 자막",
                    "다음은 영상 자막",
                    "다음 영상의 자막",
                    "이 영상의 자막",
                    "요약:\n\n",
                    "요약:\n",
                    "# 요약",
                ]
                
                for phrase in prompt_phrases:
                    if phrase in summary:
                        # 프롬프트 뒤의 실제 내용 추출
                        idx = summary.find(phrase)
                        summary = summary[idx + len(phrase):].strip()
                        # 첫 줄의 구두점 제거
                        for char in [":", "-", "*", "#"]:
                            if summary.startswith(char):
                                summary = summary[1:].strip()
                        break
                
                # 불릿 포인트 형식 정리 (* 또는 - 로 시작하는 줄들)
                if summary.startswith(("*", "-")):
                    lines = summary.split("\n")
                    cleaned_lines = []
                    for line in lines:
                        line = line.strip()
                        if line.startswith(("*", "-")):
                            line = line[1:].strip()
                            # 굵은 텍스트 마크다운 제거
                            line = line.replace("**", "")
                        if line:
                            cleaned_lines.append(line)
                    summary = " ".join(cleaned_lines)
                
                # 요약 길이 제한 (전체 표시하되, 너무 길면 줄 단위로 제한)
                if len(summary) > 3000:
                    # 최대 30줄까지
                    lines = summary.split("\n")
                    summary = "\n".join(lines[:30])
                
                summary = normalize_summary_text(summary)
                return summary if summary and len(summary) > 10 else "요약 내용 부족"
            else:
                if attempt < max_retries:
                    wait_time = 2 + attempt
                    print(f"            [WAIT] {wait_time}초 대기 후 재시도...")
                    time.sleep(wait_time)
                    continue
                else:
                    return "요약 생성 실패"
        
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                wait_time = 2 + attempt
                print(f"            [TIMEOUT] {wait_time}초 대기 후 재시도...")
                time.sleep(wait_time)
                continue
            else:
                return "요약 생성 시간초과"
        except requests.exceptions.ConnectionError:
            if attempt < max_retries:
                time.sleep(0.5)
                continue
            else:
                return "Ollama 연결 실패"
        except Exception as e:
            if attempt < max_retries:
                time.sleep(0.5)
                continue
            else:
                return "요약 생성 오류"
    
    return "요약 생성 실패"


def analyze_with_google(video_title: str, keyword: str, model: str) -> str:
    """ChromeDriver(Selenium)로 Google 검색 후 영상 분석"""
    from urllib.parse import quote_plus
    import time

    try:
        search_count = max(1, min(int(os.getenv("SEARCH_COUNT", "5")), 10))
    except ValueError:
        search_count = 5

    # AI가 검색어 생성
    query_prompt = f"""다음 YouTube 영상에 대한 최적의 검색 쿼리를 생성하세요.

영상 제목: {video_title[:200]}
키워드: {keyword}

핵심 이슈와 사실관계를 파악하기 위한 검색어를 한국어로 간결하게 작성하세요.
출력: 검색어만 (20자 이내, 설명 없이)"""

    question = f'"{video_title[:100]}" {keyword}'  # 기본값
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": query_prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 50}
            },
            timeout=15
        )
        if response.status_code == 200:
            ai_query = response.json().get("response", "").strip()
            if ai_query and 5 <= len(ai_query) <= 100:
                question = ai_query
    except Exception:
        pass  # 실패 시 기본값 사용

    search_url = f"https://www.google.com/search?q={quote_plus(question)}&hl=ko"
    sources = []

    driver = None
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager

        options = Options()
        if os.getenv("SEARCH_HEADLESS", "1") == "1":
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1280,1800")
        options.add_argument("--lang=ko-KR")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        chrome_binary = os.getenv("CHROME_BINARY", "").strip()
        if chrome_binary:
            options.binary_location = chrome_binary

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(25)
        driver.get(search_url)

        # 페이지 로드 대기 (더 견고한 방식)
        time.sleep(3)  # 기본 로드 시간
        wait = WebDriverWait(driver, 15)
        
        # 다양한 선택자로 결과 대기
        try:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.g")))
        except Exception:
            try:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-sokoban-container]")))
            except Exception:
                pass
        
        time.sleep(2)  # 추가 로딩 시간
        
        # 여러 선택자로 결과 수집 시도
        results = driver.find_elements(By.CSS_SELECTOR, "div.g")
        if not results:
            results = driver.find_elements(By.CSS_SELECTOR, "div[data-sokoban-container]")
        if not results:
            results = driver.find_elements(By.CSS_SELECTOR, "div.Gx5Zd")

        for result in results[:search_count]:
            title = ""
            snippet = ""
            try:
                # 제목 찾기 (여러 위치 시도)
                try:
                    title = result.find_element(By.CSS_SELECTOR, "h3").text.strip()
                except Exception:
                    try:
                        title = result.find_element(By.TAG_NAME, "h3").text.strip()
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                # 스니펫 찾기 (여러 클래스 시도)
                try:
                    snippet = result.find_element(By.CSS_SELECTOR, "div.VwiC3b").text.strip()
                except Exception:
                    try:
                        snippet = result.find_element(By.CSS_SELECTOR, "span.st").text.strip()
                    except Exception:
                        try:
                            snippet = result.find_element(By.CSS_SELECTOR, "div.lEBKkf").text.strip()
                        except Exception:
                            # 첫 번째 paragraph 찾기
                            try:
                                snippet = result.find_element(By.TAG_NAME, "p").text.strip()
                            except Exception:
                                pass
            except Exception:
                pass
            if title or snippet:
                sources.append(f"- {title}: {snippet}")

    except Exception as e:
        # 디버그용 (주석 처리했지만 필요시 활성화)
        # print(f"      [DEBUG] Google 검색 오류: {str(e)[:100]}")
        return "구글 검색 실패"
    finally:
        if driver:
            try:
                time.sleep(10)  # 결과 로딩 완료 대기
                driver.quit()
            except Exception:
                pass

    if not sources:
        return "구글 검색 결과 없음"

    sources_text = "\n".join(sources)[:4000]
    prompt = f"""다음은 Google 웹 검색 결과입니다.
영상 제목과 관련 정보를 바탕으로 한국어 3줄로 핵심만 요약하세요.

[영상 제목]
{video_title[:250]}

[검색 결과]
{sources_text}

요약 형식:
1) 핵심 이슈
2) 배경/맥락
3) 체크 포인트
"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 400,
                    "top_p": 0.8,
                }
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        summary = result.get("response", "").strip()
        if summary and len(summary) > 10:
            return summary[:1500]
    except Exception:
        pass

    fallback = " ".join(item.replace("- ", "", 1) for item in sources[:3])
    return fallback[:1000] if fallback else "구글 요약 실패"


def analyze_with_naver(video_title: str, keyword: str, model: str) -> str:
    """ChromeDriver(Selenium)로 Naver 검색 후 영상 분석"""
    from urllib.parse import quote_plus
    import time

    try:
        search_count = max(1, min(int(os.getenv("SEARCH_COUNT", "5")), 10))
    except ValueError:
        search_count = 5

    # AI가 검색어 생성
    query_prompt = f"""다음 YouTube 영상에 대한 최적의 검색 쿼리를 생성하세요.

영상 제목: {video_title[:200]}
키워드: {keyword}

핵심 이슈와 사실관계를 파악하기 위한 검색어를 한국어로 간결하게 작성하세요.
출력: 검색어만 (20자 이내, 설명 없이)"""

    question = f'"{video_title[:100]}" {keyword}'  # 기본값
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": query_prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 50}
            },
            timeout=15
        )
        if response.status_code == 200:
            ai_query = response.json().get("response", "").strip()
            if ai_query and 5 <= len(ai_query) <= 100:
                question = ai_query
    except Exception:
        pass  # 실패 시 기본값 사용

    search_url = f"https://search.naver.com/search.naver?query={quote_plus(question)}&where=web"
    sources = []

    driver = None
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager

        options = Options()
        if os.getenv("SEARCH_HEADLESS", "1") == "1":
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1280,1800")
        options.add_argument("--lang=ko-KR")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        chrome_binary = os.getenv("CHROME_BINARY", "").strip()
        if chrome_binary:
            options.binary_location = chrome_binary

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(25)
        driver.get(search_url)

        # 페이지 로드 대기 (더 견고한 방식)
        time.sleep(3)  # 기본 로드 시간
        wait = WebDriverWait(driver, 15)
        
        # 다양한 선택자로 결과 대기
        try:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.bx")))
        except Exception:
            try:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.api_list")))
            except Exception:
                pass
        
        time.sleep(2)  # 추가 로딩 시간
        
        # 여러 선택자로 결과 수집 시도
        results = driver.find_elements(By.CSS_SELECTOR, "li.bx")
        if not results:
            results = driver.find_elements(By.CSS_SELECTOR, "div.api_list")
        if not results:
            results = driver.find_elements(By.CSS_SELECTOR, "div.site_link_area")

        for result in results[:search_count]:
            title = ""
            snippet = ""
            try:
                # 제목 찾기
                try:
                    title = result.find_element(By.CSS_SELECTOR, "a.title").text.strip()
                except Exception:
                    try:
                        title = result.find_element(By.CSS_SELECTOR, "a[class*='title']").text.strip()
                    except Exception:
                        try:
                            title = result.find_element(By.TAG_NAME, "a").text.strip()
                        except Exception:
                            pass
            except Exception:
                pass
            try:
                # 스니펫 찾기
                try:
                    snippet = result.find_element(By.CSS_SELECTOR, "div.dsc").text.strip()
                except Exception:
                    try:
                        snippet = result.find_element(By.CSS_SELECTOR, "div.desc").text.strip()
                    except Exception:
                        try:
                            snippet = result.find_element(By.CSS_SELECTOR, "div[class*='desc']").text.strip()
                        except Exception:
                            pass
            except Exception:
                pass
            if title or snippet:
                sources.append(f"- {title}: {snippet}")

    except Exception as e:
        # 디버그용 (주석 처리했지만 필요시 활성화)
        # print(f"      [DEBUG] Naver 검색 오류: {str(e)[:100]}")
        return "네이버 검색 실패"
    finally:
        if driver:
            try:
                time.sleep(10)  # 결과 로딩 완료 대기
                driver.quit()
            except Exception:
                pass

    if not sources:
        return "네이버 검색 결과 없음"

    sources_text = "\n".join(sources)[:4000]
    prompt = f"""다음은 Naver 웹 검색 결과입니다.
영상 제목과 관련 정보를 바탕으로 한국어 3줄로 핵심만 요약하세요.

[영상 제목]
{video_title[:250]}

[검색 결과]
{sources_text}

요약 형식:
1) 핵심 이슈
2) 배경/맥락
3) 체크 포인트
"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 400,
                    "top_p": 0.8,
                }
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        summary = result.get("response", "").strip()
        if summary and len(summary) > 10:
            return summary[:1500]
    except Exception:
        pass

    fallback = " ".join(item.replace("- ", "", 1) for item in sources[:3])
    return fallback[:1000] if fallback else "네이버 요약 실패"


def analyze_with_bing(video_title: str, keyword: str, model: str) -> str:
    """ChromeDriver(Selenium)로 Bing 검색 후 영상 분석"""
    from urllib.parse import quote_plus
    import time

    try:
        search_count = max(1, min(int(os.getenv("SEARCH_COUNT", "5")), 10))
    except ValueError:
        search_count = 5

    # AI가 검색어 생성
    query_prompt = f"""다음 YouTube 영상에 대한 최적의 검색 쿼리를 생성하세요.

영상 제목: {video_title[:200]}
키워드: {keyword}

핵심 이슈와 사실관계를 파악하기 위한 검색어를 한국어로 간결하게 작성하세요.
출력: 검색어만 (20자 이내, 설명 없이)"""

    question = f'"{video_title[:100]}" {keyword}'  # 기본값
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": query_prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 50}
            },
            timeout=15
        )
        if response.status_code == 200:
            ai_query = response.json().get("response", "").strip()
            if ai_query and 5 <= len(ai_query) <= 100:
                question = ai_query
    except Exception:
        pass  # 실패 시 기본값 사용

    search_url = f"https://www.bing.com/search?q={quote_plus(question)}&setlang=ko-KR&cc=KR"
    sources = []

    driver = None
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager

        options = Options()
        if os.getenv("SEARCH_HEADLESS", "1") == "1":
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1280,1800")
        options.add_argument("--lang=ko-KR")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        chrome_binary = os.getenv("CHROME_BINARY", "").strip()
        if chrome_binary:
            options.binary_location = chrome_binary

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(25)
        driver.get(search_url)

        # 페이지 로드 대기 (더 견고한 방식)
        time.sleep(3)  # 기본 로드 시간
        wait = WebDriverWait(driver, 15)
        
        # 다양한 선택자로 결과 대기
        try:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.b_algo")))
        except Exception:
            try:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.b_result")))
            except Exception:
                pass
        
        time.sleep(2)  # 추가 로딩 시간
        
        # 여러 선택자로 결과 수집 시도
        results = driver.find_elements(By.CSS_SELECTOR, "li.b_algo")
        if not results:
            results = driver.find_elements(By.CSS_SELECTOR, "div.b_result")
        if not results:
            results = driver.find_elements(By.CSS_SELECTOR, "li.b_res")

        for result in results[:search_count]:
            title = ""
            snippet = ""
            try:
                # 제목 찾기
                try:
                    title = result.find_element(By.CSS_SELECTOR, "h2").text.strip()
                except Exception:
                    try:
                        title = result.find_element(By.CSS_SELECTOR, "h3").text.strip()
                    except Exception:
                        try:
                            title = result.find_element(By.TAG_NAME, "a").text.strip()
                        except Exception:
                            pass
            except Exception:
                pass
            try:
                # 스니펫 찾기
                try:
                    snippet = result.find_element(By.CSS_SELECTOR, "p").text.strip()
                except Exception:
                    try:
                        snippet = result.find_element(By.CSS_SELECTOR, "div.b_caption").text.strip()
                    except Exception:
                        try:
                            snippet = result.find_element(By.CSS_SELECTOR, "div[class*='desc']").text.strip()
                        except Exception:
                            pass
            except Exception:
                pass
            if title or snippet:
                sources.append(f"- {title}: {snippet}")

    except Exception as e:
        # 디버그용 (주석 처리했지만 필요시 활성화)
        # print(f"      [DEBUG] Bing 검색 오류: {str(e)[:100]}")
        return "빙 검색 실패"
    finally:
        if driver:
            try:
                time.sleep(10)  # 결과 로딩 완료 대기
                driver.quit()
            except Exception:
                pass

    if not sources:
        return "빙 검색 결과 없음"

    sources_text = "\n".join(sources)[:4000]
    prompt = f"""다음은 Bing 웹 검색 결과입니다.
영상 제목과 관련 정보를 바탕으로 한국어 3줄로 핵심만 요약하세요.

[영상 제목]
{video_title[:250]}

[검색 결과]
{sources_text}

요약 형식:
1) 핵심 이슈
2) 배경/맥락
3) 체크 포인트
"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 400,
                    "top_p": 0.8,
                }
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        summary = result.get("response", "").strip()
        if summary and len(summary) > 10:
            return summary[:1500]
    except Exception:
        pass

    fallback = " ".join(item.replace("- ", "", 1) for item in sources[:3])
    return fallback[:1000] if fallback else "빙 요약 실패"


def analyze_with_zum(video_title: str, keyword: str, model: str) -> str:
    """ChromeDriver(Selenium)로 Zum 검색 후 영상 분석"""
    from urllib.parse import quote_plus
    import time

    try:
        search_count = max(1, min(int(os.getenv("SEARCH_COUNT", "5")),  10))
    except ValueError:
        search_count = 5

    # AI가 검색어 생성
    query_prompt = f"""다음 YouTube 영상에 대한 최적의 검색 쿼리를 생성하세요.

영상 제목: {video_title[:200]}
키워드: {keyword}

핵심 이슈와 사실관계를 파악하기 위한 검색어를 한국어로 간결하게 작성하세요.
출력: 검색어만 (20자 이내, 설명 없이)"""

    question = f'"{video_title[:100]}" {keyword}'  # 기본값
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": query_prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 50}
            },
            timeout=15
        )
        if response.status_code == 200:
            ai_query = response.json().get("response", "").strip()
            if ai_query and 5 <= len(ai_query) <= 100:
                question = ai_query
    except Exception:
        pass  # 실패 시 기본값 사용

    search_url = f"https://search.zum.com/search.zum?method=uni&option=accu&qm=f_nx&rd=1&query={quote_plus(question)}"
    sources = []

    driver = None
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager

        options = Options()
        if os.getenv("SEARCH_HEADLESS", "1") == "1":
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1280,1800")
        options.add_argument("--lang=ko-KR")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        chrome_binary = os.getenv("CHROME_BINARY", "").strip()
        if chrome_binary:
            options.binary_location = chrome_binary

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(25)
        driver.get(search_url)

        # 페이지 로드 대기 (더 견고한 방식)
        time.sleep(3)  # 기본 로드 시간
        wait = WebDriverWait(driver, 15)
        
        # 다양한 선택자로 결과 대기
        try:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.d_cmn_list")))
        except Exception:
            try:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.c-list-base")))
            except Exception:
                pass
        
        time.sleep(2)  # 추가 로딩 시간
        
        # 여러 선택자로 결과 수집 시도
        results = driver.find_elements(By.CSS_SELECTOR, "div.d_cmn_list")
        if not results:
            results = driver.find_elements(By.CSS_SELECTOR, "div.c-list-base")
        if not results:
            results = driver.find_elements(By.CSS_SELECTOR, "ul.d_list li")

        for result in results[:search_count]:
            title = ""
            snippet = ""
            try:
                # 제목 찾기
                try:
                    title = result.find_element(By.CSS_SELECTOR, "a.d_tit").text.strip()
                except Exception:
                    try:
                        title = result.find_element(By.CSS_SELECTOR, "a.tit-info").text.strip()
                    except Exception:
                        try:
                            title = result.find_element(By.CSS_SELECTOR, "strong.tit").text.strip()
                        except Exception:
                            pass
            except Exception:
                pass
            try:
                # 스니펫 찾기
                try:
                    snippet = result.find_element(By.CSS_SELECTOR, "p.d_txt").text.strip()
                except Exception:
                    try:
                        snippet = result.find_element(By.CSS_SELECTOR, "p.desc").text.strip()
                    except Exception:
                        try:
                            snippet = result.find_element(By.CSS_SELECTOR, "div.txt").text.strip()
                        except Exception:
                            pass
            except Exception:
                pass
            if title or snippet:
                sources.append(f"- {title}: {snippet}")

    except Exception as e:
        # 디버그용 (주석 처리했지만 필요시 활성화)
        # print(f"      [DEBUG] Zum 검색 오류: {str(e)[:100]}")
        return "줌 검색 실패"
    finally:
        if driver:
            try:
                time.sleep(10)  # 결과 로딩 완료 대기
                driver.quit()
            except Exception:
                pass

    if not sources:
        return "줌 검색 결과 없음"

    sources_text = "\n".join(sources)[:4000]
    prompt = f"""다음은 Zum 웹 검색 결과입니다.
영상 제목과 관련 정보를 바탕으로 한국어 3줄로 핵심만 요약하세요.

[영상 제목]
{video_title[:250]}

[검색 결과]
{sources_text}

요약 형식:
1) 핵심 이슈
2) 배경/맥락
3) 체크 포인트
"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 400,
                    "top_p": 0.8,
                }
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        summary = result.get("response", "").strip()
        if summary and len(summary) > 10:
            return summary[:1500]
    except Exception:
        pass

    fallback = " ".join(item.replace("- ", "", 1) for item in sources[:3])
    return fallback[:1000] if fallback else "줌 요약 실패"


def analyze_with_youtube(video_id: str, video_title: str, keyword: str, model: str, upload_date: str = "") -> str:
    """ChromeDriver로 YouTube 자막 직접 추출 후 분석"""
    import time

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ChromeDriver 열기 전에 실제 업로드일 재확인
    verified_upload_date = resolve_upload_date_by_video_id(video_id)
    if verified_upload_date:
        if not is_within_last_24_hours(verified_upload_date):
            log_subtitle_failure(
                video_id,
                video_title,
                "youtube",
                f"크롬 진입 전 스킵: verified_upload_date={verified_upload_date}, now={now_str}, rule=24h",
                upload_date=verified_upload_date,
            )
            return "오늘 날짜 영상 아님(건너뜀)"
    elif upload_date and not is_within_last_24_hours(upload_date):
        log_subtitle_failure(
            video_id,
            video_title,
            "youtube",
            f"크롬 진입 전 스킵(검색일자 기준): upload_date={upload_date}, now={now_str}, rule=24h",
            upload_date=upload_date,
        )
        return "오늘 날짜 영상 아님(건너뜀)"
    
    driver = None
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager

        options = Options()
        if os.getenv("SEARCH_HEADLESS", "1") == "1":
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1280,1800")
        options.add_argument("--lang=ko-KR")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        chrome_binary = os.getenv("CHROME_BINARY", "").strip()
        if chrome_binary:
            options.binary_location = chrome_binary

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        
        # YouTube 영상 페이지 접속
        driver.get(f"https://www.youtube.com/watch?v={video_id}")
        time.sleep(5)  # 페이지 로드 대기
        
        subtitles_text = ""
        fail_reasons = []
        transcript_opened = False
        try:
            wait = WebDriverWait(driver, 20)
            
            # 1단계: "더보기" 버튼 클릭 (설명란 확장) - 여러 선택자 시도
            try:
                # 시도 1: 새 UI
                more_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "tp-yt-paper-button#expand")))
                more_button.click()
                time.sleep(2)
            except Exception:
                try:
                    # 시도 2: 구 UI
                    more_button = driver.find_element(By.XPATH, "//button[@aria-label='더보기' or contains(text(), '더보기')]")
                    more_button.click()
                    time.sleep(2)
                except Exception:
                    try:
                        # 시도 3: 영문
                        more_button = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Show more') or contains(text(), 'more')]")
                        more_button.click()
                        time.sleep(2)
                    except Exception:
                        pass

            # 2단계: "스크립트 표시" 텍스트를 찾아 클릭 (가장 중요!)
            def _panel_visible() -> bool:
                selectors = [
                    "ytd-transcript-renderer",
                    "ytd-transcript-search-panel-renderer",
                    "transcript-segment-view-model",
                    "ytd-engagement-panel-section-list-renderer[target-id*='transcript']",
                ]
                return any(driver.find_elements(By.CSS_SELECTOR, sel) for sel in selectors)

            def _safe_click(elem) -> bool:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elem)
                except Exception:
                    pass
                try:
                    elem.click()
                    return True
                except Exception:
                    try:
                        driver.execute_script("arguments[0].click();", elem)
                        return True
                    except Exception:
                        return False

            # 메뉴 기반 transcript 항목이 뜨는 UI를 대비해 메뉴 버튼 먼저 열기 시도
            menu_candidates = [
                "//button[contains(@aria-label,'더보기') or contains(@aria-label,'More actions') or contains(@aria-label,'작업 더보기')]",
                "//ytd-menu-renderer//button",
            ]
            for menu_xpath in menu_candidates:
                if transcript_opened:
                    break
                try:
                    for menu_btn in driver.find_elements(By.XPATH, menu_xpath)[:3]:
                        _safe_click(menu_btn)
                        time.sleep(0.5)
                        if _panel_visible():
                            transcript_opened = True
                            break
                except Exception:
                    pass

            transcript_locators = [
                (By.XPATH, "//button[contains(@aria-label, '스크립트 표시') or contains(., '스크립트 표시')]"),
                (By.XPATH, "//button[contains(@aria-label, '스크립트') or contains(., '스크립트')]"),
                (By.XPATH, "//button[contains(@aria-label, 'Show transcript') or contains(., 'Show transcript') or contains(@aria-label, 'transcript')]"),
                (By.CSS_SELECTOR, "ytd-video-description-transcript-section-renderer button"),
                (By.XPATH, "//*[self::tp-yt-paper-item or self::ytd-menu-service-item-renderer or self::yt-formatted-string][contains(., '스크립트 표시') or contains(., '스크립트') or contains(., 'Show transcript') or contains(., 'Transcript')]"),
            ]

            if not transcript_opened:
                for _ in range(3):
                    for by, locator in transcript_locators:
                        if transcript_opened:
                            break
                        try:
                            candidates = driver.find_elements(by, locator)
                            for candidate in candidates:
                                marker = ((candidate.text or "") + " " + (candidate.get_attribute("aria-label") or "")).lower()
                                if "스크립트" not in marker and "transcript" not in marker:
                                    continue
                                if _safe_click(candidate):
                                    time.sleep(1.2)
                                    if _panel_visible():
                                        transcript_opened = True
                                        break
                        except Exception:
                            continue

                    if transcript_opened:
                        break

                    # 최후 수단: JS 텍스트 탐색 클릭
                    try:
                        clicked = driver.execute_script("""
                            const nodes = Array.from(document.querySelectorAll('button, tp-yt-paper-item, ytd-menu-service-item-renderer, yt-formatted-string, a, span'));
                            const target = nodes.find(el => {
                                const t = (el.innerText || el.textContent || '').toLowerCase();
                                const a = (el.getAttribute && el.getAttribute('aria-label') || '').toLowerCase();
                                return t.includes('스크립트 표시') || t.includes('스크립트') || t.includes('show transcript') || t.includes('transcript') || a.includes('스크립트') || a.includes('transcript');
                            });
                            if (!target) return false;
                            try { target.scrollIntoView({block: 'center'}); } catch (e) {}
                            try { target.click(); } catch (e) { return false; }
                            return true;
                        """)
                        if clicked:
                            time.sleep(1.2)
                            transcript_opened = _panel_visible()
                    except Exception:
                        pass

            if not transcript_opened:
                fail_reasons.append("스크립트 표시 텍스트 탐색/클릭 실패")
            
            # 3단계: Transcript 패널에서 텍스트 추출
            if transcript_opened:
                try:
                    # Transcript 패널 찾기
                    time.sleep(2)

                    # 무한 로딩 감지: 일정 시간 내 자막 세그먼트가 안 뜨면 로딩 실패로 처리
                    try:
                        loading_timeout_sec = int(os.getenv("TRANSCRIPT_LOADING_TIMEOUT_SEC", "12"))
                    except ValueError:
                        loading_timeout_sec = 12

                    start_wait = time.time()
                    while time.time() - start_wait < loading_timeout_sec:
                        has_segments = bool(driver.find_elements(By.CSS_SELECTOR, "transcript-segment-view-model, ytd-transcript-segment-renderer"))
                        loading_visible = bool(driver.find_elements(By.CSS_SELECTOR, "tp-yt-paper-spinner-lite, ytd-transcript-renderer #spinner, yt-spec-touch-feedback-shape"))
                        if has_segments:
                            break
                        if not loading_visible:
                            break
                        time.sleep(0.8)

                    has_segments_after_wait = bool(driver.find_elements(By.CSS_SELECTOR, "transcript-segment-view-model, ytd-transcript-segment-renderer"))
                    if not has_segments_after_wait:
                        fail_reasons.append("스크립트 패널 무한 로딩 또는 세그먼트 미생성")
                    
                    # 방법 1: 신 구조 - transcript-segment-view-model의 실제 텍스트
                    try:
                        transcript_segments = driver.find_elements(By.CSS_SELECTOR, 
                            "transcript-segment-view-model yt-core-attributed-string[role='text']"
                        )
                        if transcript_segments and len(transcript_segments) > 0:
                            subtitles_text = " ".join([seg.text.strip() for seg in transcript_segments if seg.text.strip()])
                    except Exception:
                        pass
                    
                    # 방법 2: XPath로 모든 자막 세그먼트 수집
                    if not subtitles_text:
                        try:
                            transcript_segments = driver.find_elements(By.XPATH, 
                                "//transcript-segment-view-model//span[@role='text']"
                            )
                            if transcript_segments:
                                subtitles_text = " ".join([seg.text.strip() for seg in transcript_segments if seg.text.strip()])
                        except Exception:
                            pass
                    
                    # 방법 3: ytd-transcript-segment-renderer (구 구조)
                    if not subtitles_text:
                        try:
                            transcript_segments = driver.find_elements(By.CSS_SELECTOR, 
                                "ytd-transcript-segment-renderer yt-formatted-string"
                            )
                            if transcript_segments:
                                subtitles_text = " ".join([seg.text.strip() for seg in transcript_segments if seg.text.strip()])
                        except Exception:
                            pass
                    
                    # 방법 4: yt-formatted-string.segment-text
                    if not subtitles_text:
                        try:
                            transcript_segments = driver.find_elements(By.CSS_SELECTOR, 
                                "yt-formatted-string.segment-text"
                            )
                            if transcript_segments:
                                subtitles_text = " ".join([seg.text.strip() for seg in transcript_segments if seg.text.strip()])
                        except Exception:
                            pass
                    
                    # 방법 5: ytd-transcript-renderer이나 ytd-transcript-view 전체 텍스트
                    if not subtitles_text:
                        try:
                            transcript_container = driver.find_element(By.CSS_SELECTOR, 
                                "ytd-transcript-renderer, ytd-transcript-view"
                            )
                            if transcript_container:
                                # 전체 텍스트에서 타임스탐프 제거
                                full_text = transcript_container.text
                                # 타임스탐프 패턴 제거 (0:00, 1:23 등)
                                import re
                                subtitles_text = re.sub(r'\d+:\d{2}\s+', '', full_text).strip()
                        except Exception:
                            pass
                            
                except Exception:
                    fail_reasons.append("Transcript 패널 텍스트 추출 실패")
            
            # 4단계: 플레이어 자막 시도 (옵션 fallback)
            if not subtitles_text and transcript_opened and YOUTUBE_CC_FALLBACK:
                try:
                    # CC 버튼 클릭
                    cc_button = driver.find_element(By.CSS_SELECTOR, "button.ytp-subtitles-button")
                    cc_button.click()
                    time.sleep(3)
                    
                    # 자막 컨테이너에서 추출
                    subtitle_containers = driver.find_elements(By.CSS_SELECTOR, "div.ytp-caption-segment")
                    if subtitle_containers:
                        subtitles_text = " ".join([elem.text.strip() for elem in subtitle_containers if elem.text.strip()])
                except Exception:
                    fail_reasons.append("플레이어 CC 자막 추출 실패")
            
        except Exception as e:
            fail_reasons.append(f"자막 추출 단계 예외: {str(e)[:200]}")
        
        if not subtitles_text or len(subtitles_text) < 50:
            # Selenium UI 추출 실패 시 비-UI 자막 폴백(youtube_transcript_api/yt_dlp)
            fallback_subtitles = get_video_subtitles(video_id)
            if fallback_subtitles and len(fallback_subtitles) >= 50 and fallback_subtitles not in {"자막 없음", "자막 요청 제한(429)", "자막 추출 실패"}:
                return analyze_subtitles_with_ollama(fallback_subtitles, model, video_title)

            reason = " | ".join(fail_reasons) if fail_reasons else "자막 텍스트 없음 또는 길이 부족(<50)"
            log_subtitle_failure(
                video_id,
                video_title,
                "youtube",
                reason,
                upload_date=verified_upload_date or upload_date,
            )
            return "유튜브 자막 추출 실패"
            
        # Ollama로 요약
        return analyze_subtitles_with_ollama(subtitles_text, model, video_title)
        
    except Exception as e:
        log_subtitle_failure(
            video_id,
            video_title,
            "youtube",
            f"크롬드라이버 예외: {str(e)[:300]}",
            upload_date=verified_upload_date or upload_date,
        )
        return "유튜브 자막 추출 실패"
    finally:
        if driver:
            try:
                time.sleep(10)  # 결과 확인 대기
                driver.quit()
            except Exception:
                pass


def collect_youtube_data(
    keyword: str,
    limit: int = 10,
    model: str = None,
    analyze_subs: bool = False,
    analysis_source: str = "subtitles",
) -> Dict[str, Any]:
    """특정 키워드의 유튜브 영상 데이터 수집 (오늘 영상 우선, 최근 영상도 포함)"""
    try:
        import yt_dlp
        
        # Google 자동 요청 차단 방지 위한 User-Agent 설정
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        http_headers = {
            "User-Agent": user_agent,
            "Referer": "https://www.youtube.com/",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        
        # 1단계: extract_flat으로 빠르게 검색
        ydl_opts_flat = {
            "extract_flat": True,
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 15,
            "http_headers": http_headers,  # Google 요청 차단 방지
        }
        
        search_url = f"ytsearch{limit}:{keyword}"
        
        today_views = []
        recent_views = []
        today_videos = []
        recent_videos = []
        
        with yt_dlp.YoutubeDL(ydl_opts_flat) as ydl:
            info = ydl.extract_info(search_url, download=False)
            
            if not info or "entries" not in info:
                return {
                    "views": [], "video_count": 0, "videos": [],
                    "today_videos": [], "recent_videos": []
                }
            
            entries = info["entries"]
            
            # 모든 영상 수집 (오늘 영상과 최근 영상 분리)
            for entry in entries:
                if not entry:
                    continue
                
                upload_date = entry.get("upload_date", "")
                view_count = entry.get("view_count")
                
                if not view_count or not isinstance(view_count, int):
                    continue
                
                # 날짜 포맷팅 (YYYYMMDD → YYYY-MM-DD)
                formatted_date = ""
                if upload_date and len(upload_date) == 8:
                    formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
                
                video_data = {
                    "title": entry.get("title", "제목 없음"),
                    "video_id": entry.get("id", ""),
                    "views": view_count,
                    "upload_date": formatted_date,
                    "url": entry.get("url", ""),
                    "subtitle_summary": "자막 미분석"
                }
                
                # 최근 24시간 영상과 그 외 최근 영상 분리
                if is_within_last_24_hours(formatted_date):
                    today_views.append(view_count)
                    today_videos.append(video_data)
                else:
                    recent_views.append(view_count)
                    recent_videos.append(video_data)
            
            # 모든 영상 (오늘 + 최근, 오늘 우선)
            all_videos = today_videos + recent_videos
            all_views = today_views + recent_views
            
            # 2단계: 분석이 필요한 경우 모든 영상 분석 (전부 나와야 함)
            if analyze_subs and model and all_videos:
                for idx, video in enumerate(all_videos):  # 모든 영상 분석
                    video_id = video.get("video_id", "")
                    video_title = video.get("title", "제목 없음")
                    if not video_id:
                        continue

                    # 로그/판정 전에 video_id로 실제 업로드일 재보강
                    if not (video.get("upload_date") or "").strip():
                        resolved_date = resolve_upload_date_by_video_id(video_id)
                        if resolved_date:
                            video["upload_date"] = resolved_date

                    video_upload_date = video.get("upload_date", "") or "날짜 미상"

                    # 자막 분석 전: Ollama로 오늘 날짜 영상 여부 확인 (아니면 건너뜀)
                    if analysis_source in {"youtube", "subtitles", "auto"}:
                        is_today_video = is_today_video_with_ollama(video, model)
                        if not is_today_video:
                            summary = "오늘 날짜 영상 아님(건너뜀)"
                            video["subtitle_summary"] = summary
                            print(f"         자막 분석 건너뜀: [{idx+1}/{len(all_videos)}] {video_title} (업로드일: {video_upload_date}) ({summary})")
                            continue

                    if analysis_source == "google":
                        print(f"         Google 질의 분석 중: [{idx+1}/{len(all_videos)}] {video_title} (업로드일: {video_upload_date})")
                        summary = analyze_with_google(video["title"], keyword, model)
                    elif analysis_source == "bing":
                        print(f"         Bing 질의 분석 중: [{idx+1}/{len(all_videos)}] {video_title} (업로드일: {video_upload_date})")
                        summary = analyze_with_bing(video["title"], keyword, model)
                    elif analysis_source == "naver":
                        print(f"         Naver 질의 분석 중: [{idx+1}/{len(all_videos)}] {video_title} (업로드일: {video_upload_date})")
                        summary = analyze_with_naver(video["title"], keyword, model)
                    elif analysis_source == "zum":
                        print(f"         Zum 질의 분석 중: [{idx+1}/{len(all_videos)}] {video_title} (업로드일: {video_upload_date})")
                        summary = analyze_with_zum(video["title"], keyword, model)
                    elif analysis_source == "youtube":
                        print(f"         YouTube 자막 추출 중: [{idx+1}/{len(all_videos)}] {video_title} (업로드일: {video_upload_date})")
                        summary = analyze_with_youtube(
                            video_id,
                            video["title"],
                            keyword,
                            model,
                            upload_date=video.get("upload_date", ""),
                        )
                    elif analysis_source == "subtitles":
                        print(f"         자막 분석 중: [{idx+1}/{len(all_videos)}] {video_title} (업로드일: {video_upload_date})")
                        subtitles = get_video_subtitles(video_id)
                        if subtitles:
                            summary = analyze_subtitles_with_ollama(subtitles, model, video['title'])
                            max_retry = 3
                            retry_count = 0

                            while summary in ["요약 생성 시간초과", "Ollama 연결 실패", "요약 생성 오류", "요약 생성 실패"] and retry_count < max_retry:
                                retry_count += 1
                                print(f"            [RETRY {retry_count}/3] {summary} - 재시도 중...")
                                time.sleep(2)
                                summary = analyze_subtitles_with_ollama(subtitles, model, video['title'])
                        else:
                            summary = "자막 없음"
                    else:  # auto mode
                        print(f"         자막 분석 중: [{idx+1}/{len(all_videos)}] {video_title} (업로드일: {video_upload_date})")
                        subtitles = get_video_subtitles(video_id)
                        if subtitles:
                            summary = analyze_subtitles_with_ollama(subtitles, model, video['title'])
                            max_retry = 3
                            retry_count = 0

                            while summary in ["요약 생성 시간초과", "Ollama 연결 실패", "요약 생성 오류", "요약 생성 실패"] and retry_count < max_retry:
                                retry_count += 1
                                print(f"            [RETRY {retry_count}/3] {summary} - 재시도 중...")
                                time.sleep(2)
                                summary = analyze_subtitles_with_ollama(subtitles, model, video['title'])
                        else:
                            print("            → 자막 없음, Google 검색 분석으로 폴백")
                            summary = analyze_with_google(video["title"], keyword, model)

                    summary = normalize_summary_text(summary)
                    video["subtitle_summary"] = summary

                    if is_summary_eligible_for_db(summary):
                        saved = save_single_summary_to_database(keyword, video)
                        video["db_saved"] = saved
                        if saved:
                            print("            → 참소식 DB 저장 완료")
                        else:
                            print("            → 참소식 DB 저장 실패")

                    if is_summary_eligible_for_db(summary):
                        display_summary = summary
                        if len(display_summary) > 500:
                            lines = display_summary.split("\n")
                            if len(lines) > 5:
                                display_summary = "\n".join(lines[:5]) + "\n..."
                            else:
                                display_summary = display_summary[:500] + "..."
                        print(f"            → 요약: {display_summary}")
                    else:
                        print(f"            → {summary}")

                # 3단계: 분석 요약 실패 + 오늘 날짜 아님(최근 영상)인 경우 생략
                original_recent_count = len(recent_videos)
                recent_videos = [
                    video for video in recent_videos
                    if video.get("subtitle_summary") not in UNAVAILABLE_SUMMARIES
                ]
                skipped_recent_count = original_recent_count - len(recent_videos)
                if skipped_recent_count > 0:
                    print(f"         최근 영상 {skipped_recent_count}개 생략 (분석 요약 실패)")

                # 필터 반영 후 전체 목록/조회수 재구성
                all_videos = today_videos + recent_videos
                all_views = [video.get("views", 0) for video in all_videos if isinstance(video.get("views"), int)]
        
        return {
            "views": all_views,
            "video_count": len(all_views),
            "videos": all_videos,
            "today_videos": today_videos,
            "recent_videos": recent_videos,
            "today_count": len(today_videos),
            "recent_count": len(recent_videos)
        }
    
    except Exception as e:
        print(f"[ERROR] 데이터 수집 실패 ({keyword}): {e}")
        return {
            "views": [], "video_count": 0, "videos": [],
            "today_videos": [], "recent_videos": [],
            "today_count": 0, "recent_count": 0
        }


def calculate_nb_score(views: List[int]) -> Dict[str, Any]:
    """N/B 점수 계산 (bitCalculation.v.0.1.js의 calculateBit 알고리즘 사용)"""
    if not views or len(views) < 2:
        return {
            "max": 0,
            "min": 0,
            "nb_score": 0,
            "avg_views": 0,
            "total_views": 0
        }
    
    # calculateBit 함수의 Python 구현 (bitCalculation.v.0.1.js 포팅)
    def calculate_bit(nb: List[int], bit: float = 100, reverse: bool = False) -> float:
        """bitCalculation.v.0.1.js의 calculateBit 함수 포팅"""
        if len(nb) < 2:
            return bit / 100
        
        max_val = max(nb)
        min_val = min(nb)
        count_const = 50
        range_val = max_val - min_val
        
        # 음수와 양수 범위를 구분하여 증분 계산
        negative_range = abs(min_val) if min_val < 0 else 0
        positive_range = max_val if max_val > 0 else 0
        
        negative_increment = negative_range / (count_const * len(nb) - 1) if (count_const * len(nb) - 1) != 0 else 0
        positive_increment = positive_range / (count_const * len(nb) - 1) if (count_const * len(nb) - 1) != 0 else 0
        
        # 배열 초기화
        arrays = {
            'BIT_START_A50': [0] * (count_const * len(nb)),
            'BIT_START_A100': [0] * (count_const * len(nb)),
            'BIT_START_B50': [0] * (count_const * len(nb)),
            'BIT_START_B100': [0] * (count_const * len(nb)),
            'BIT_START_NBA100': [0] * (count_const * len(nb)),
        }
        
        count = 0
        total_sum = 0
        
        for value in nb:
            for i in range(count_const):
                bit_end = 1
                
                # 부호에 따른 A50, B50 계산
                if value < 0:
                    a50 = min_val + negative_increment * (count + 1)
                else:
                    a50 = min_val + positive_increment * (count + 1)
                
                a100 = (count + 1) * bit / (count_const * len(nb))
                
                if value < 0:
                    b50 = a50 - negative_increment * 2
                else:
                    b50 = a50 - positive_increment * 2
                
                if value < 0:
                    b100 = a50 + negative_increment
                else:
                    b100 = a50 + positive_increment
                
                nba100 = a100 / (len(nb) - bit_end) if (len(nb) - bit_end) != 0 else 0
                
                arrays['BIT_START_A50'][count] = a50
                arrays['BIT_START_A100'][count] = a100
                arrays['BIT_START_B50'][count] = b50
                arrays['BIT_START_B100'][count] = b100
                arrays['BIT_START_NBA100'][count] = nba100
                count += 1
            
            total_sum += value
        
        # Reverse 옵션 처리 (시간 역방향 흐름 분석)
        if reverse:
            arrays['BIT_START_NBA100'] = arrays['BIT_START_NBA100'][::-1]
        
        # NB50 계산 (시간 흐름 기반 가중치 분석)
        nb50 = 0
        for value in nb:
            for a in range(len(arrays['BIT_START_NBA100'])):
                if arrays['BIT_START_B50'][a] <= value <= arrays['BIT_START_B100'][a]:
                    nba_idx = min(a, len(arrays['BIT_START_NBA100']) - 1)
                    nb50 += arrays['BIT_START_NBA100'][nba_idx]
                    break
        
        # 평균 비율 기반 NB50 정규화
        bit_weight = max((10 - len(nb)) * 10, 1)
        average_ratio = (total_sum / (len(nb) * abs(max_val or 1))) * 100  # 절대값으로 계산
        nb50 = min((nb50 / 100) * average_ratio, bit)
        
        # 시간 흐름의 상한치(MAX)와 하한치(MIN) 보정
        if len(nb) == 2:
            return bit - nb50  # NB 분석 점수가 작을수록 시간 흐름 안정성이 높음
        
        return nb50
    
    # BIT_MAX_NB와 BIT_MIN_NB 호출 (global SUPER_BIT 없이 구현)
    bit_max = calculate_bit(views, 5.5, False)  # Forward Time Flow
    bit_min = calculate_bit(views, 5.5, True)   # Reverse Time Flow
    
    # 유효성 검증
    if not (isinstance(bit_max, (int, float)) and isinstance(bit_min, (int, float))):
        bit_max, bit_min = 0, 0.0001
    
    if not ((-100 <= bit_max <= 100) and (-100 <= bit_min <= 100)):
        bit_max, bit_min = 0, 0.0001
    
    avg_val = sum(views) / len(views)
    nb_score = abs(bit_max) / max(abs(bit_min), 0.0001)
    
    return {
        "max": round(bit_max, 4),
        "min": round(bit_min, 4),
        "nb_score": round(nb_score, 4),
        "avg_views": round(avg_val, 2),
        "total_views": sum(views),
        "video_count": len(views)
    }


def generate_report_with_ollama(report_data: Dict[str, Any], model: str) -> str:
    """Ollama AI가 분석 리포트를 마크다운 형식으로 작성"""
    try:
        # 리포트 데이터를 JSON으로 변환
        keywords_info = []
        for idx, kw_data in enumerate(report_data["keywords"], 1):
            keyword = kw_data['keyword']
            fixed_mark = " 🔒" if kw_data.get('is_fixed') else ""
            
            videos_info = []
            if kw_data.get("videos"):
                for video in kw_data["videos"]:
                    video_summary = {
                        "title": video['title'],
                        "views": video['views'],
                        "subtitle_summary": video.get('subtitle_summary', '자막 없음')
                    }
                    videos_info.append(video_summary)
            
            kw_info = {
                "rank": idx,
                "keyword": keyword + fixed_mark,
                "nb_score": kw_data['nb_score'],
                "max": kw_data['max'],
                "min": kw_data['min'],
                "video_count": kw_data['video_count'],
                "avg_views": kw_data['avg_views'],
                "views": kw_data['views'],
                "videos": videos_info
            }
            keywords_info.append(kw_info)
        
        # Ollama에 전달할 데이터
        data_json = json.dumps(keywords_info, ensure_ascii=False, indent=2)
        
        prompt = f"""다음은 YouTube 채널 키워드 분석 데이터입니다. 
이 데이터를 분석하여 전문적인 분석리포트를 마크다운 형식으로 작성해주세요.

=== 분석 데이터 ===
{data_json}

=== 작성 지침 ===
1. 제목: # YouTube 키워드 분석 보고서 (전문적이고 객관적인 톤)
2. 생성 시각: 현재날짜 시간
3. 구성:
   - 분석 요약: 전체 트렌드 분석 (2-3문단)
   - 상위 5개 키워드 심층 분석: 각 키워드별 1-2문단
   - 시사점 및 추천: 향후 전략 고려사항 (2-3문단)
   - 자막 분석 평가: 상위 영상들의 자막 내용 기반 인사이트
4. 한국어로 작성
5. 데이터 기반의 구체적인 분석 제공
6. N/B 스코어 해석 포함

전문적인 형식의 마크다운 리포트를 작성해주세요:"""
        
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 2000,
                }
            },
            timeout=180
        )
        response.raise_for_status()
        result = response.json()
        
        report_text = result.get("response", "")
        if report_text:
            return report_text
    
    except Exception as e:
        print(f"[WARN] Ollama 보고서 생성 실패: {e}")
    
    return None


def save_report(report_data: Dict[str, Any], report_dir: Path, report_num: int, model: str = None):
    """JSON + 마크다운 보고서 저장 (Ollama AI 분석 리포트 생성)"""
    # JSON 파일
    json_path = report_dir / f"report_{report_num:03d}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    # 마크다운 파일 생성
    md_path = report_dir / f"report_{report_num:03d}.md"
    
    # Ollama로 분석 리포트 생성 시도
    ai_report = None
    if model:
        print(f"[INFO] Ollama AI로 분석 리포트 생성 중... (모델: {model})")
        ai_report = generate_report_with_ollama(report_data, model)
    
    # AI 리포트가 생성되었다면 사용
    if ai_report:
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(ai_report)
        print(f"[SAVE] 보고서 저장 (AI 분석): {md_path.name}")
    else:
        # Fallback: 기본 형식의 보고서
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# YouTube 키워드 분석 보고서 #{report_num:03d}\n\n")
            f.write(f"**생성 시각**: {report_data['timestamp']}\n\n")
            f.write(f"**분석 키워드 수**: {len(report_data['keywords'])}\n\n")
            f.write(f"**분석 활성화**: {'활성화' if report_data.get('analyze_subtitles') else '비활성화'}\n")
            f.write(f"**분석 소스**: {report_data.get('analysis_source', 'subtitles')}\n\n")
            f.write("---\n\n")
            
            f.write("## 분석 결과\n\n")
            f.write("| 순위 | 키워드 | N/B Score | MAX | MIN | 영상 수 | 평균 조회수 |\n")
            f.write("|------|--------|-----------|-----|-----|---------|-------------|\n")
            
            for idx, kw_data in enumerate(report_data["keywords"], 1):
                keyword_display = kw_data['keyword']
                if kw_data.get('is_fixed'):
                    keyword_display += " 🔒"
                f.write(f"| {idx} | {keyword_display} | {kw_data['nb_score']} | "
                       f"{kw_data['max']} | {kw_data['min']} | {kw_data['video_count']} | "
                       f"{kw_data['avg_views']:,.0f} |\n")
            
            f.write("\n---\n\n")
            f.write("## 상세 조회수 데이터\n\n")
            
            for kw_data in report_data["keywords"]:
                keyword_display = kw_data['keyword']
                if kw_data.get('is_fixed'):
                    keyword_display += " (고정 키워드)"
                
                f.write(f"### {keyword_display}\n\n")
                
                if kw_data["views"]:
                    views_str = ", ".join([f"{v:,}" for v in kw_data["views"]])
                    f.write(f"**조회수**: {views_str}\n\n")
                    
                    if kw_data.get("videos"):
                        f.write("**영상 목록 및 분석 요약**:\n\n")
                        for vid_idx, video in enumerate(kw_data["videos"], 1):
                            f.write(f"{vid_idx}. **{video['title']}**\n")
                            f.write(f"   - 조회수: {video['views']:,}\n")
                            subtitle = video.get('subtitle_summary', '자막 미분석')
                            if subtitle and subtitle != "자막 미분석":
                                f.write(f"   - 분석 요약: {subtitle}\n")
                            f.write("\n")
                else:
                    f.write("오늘 업로드된 영상 없음\n\n")
        
        print(f"[SAVE] 보고서 저장 (기본 형식): {json_path.name}, {md_path.name}")


def run_monitoring_cycle(
    model: str,
    keyword_count: int = 10,
    video_limit: int = 10,
    analyze_subtitles: bool = True,
    analysis_source: str = "subtitles",
):
    """1회 모니터링 사이클 실행"""
    global CURRENT_OLLAMA_MODEL
    CURRENT_OLLAMA_MODEL = model
    
    # 한글 배너 출력
    print("\n" + "═"*55)
    print("║  YouTube 키워드 지속 모니터링 시스템           ║")
    print("═"*55)
    print()
    
    print(f"\n{'='*60}")
    print(f"[START] 모니터링 사이클 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 1. 키워드 파일에서 고정 키워드 로드 (자동 갱신/자동 저장 없음)
    print(f"\n[1/3] 키워드 파일에서 키워드 전체 로드 중...")
    print(f"[INFO] \"오늘의 주요 뉴스\" 키워드는 항상 고정됩니다.")

    dynamic_keywords = load_keywords_from_file(max_keywords=0)

    if not dynamic_keywords:
        dynamic_keywords = DEFAULT_DYNAMIC_KEYWORDS[:max(0, keyword_count - 1)]
        print("[WARN] 키워드 파일에서 동적 키워드를 찾지 못해 기본 키워드를 사용합니다.")

    keywords = [FIXED_KEYWORD] + dynamic_keywords
    
    print(f"[INFO] 생성된 키워드: {keywords}")
    print(f"[INFO] 최종 키워드 구성: {', '.join([f'{kw}' + ('🔒' if kw == FIXED_KEYWORD else '') for kw in keywords])}")
    
    # 2. 각 키워드별 유튜브 데이터 수집 및 N/B 분석
    analyze_subs_str = "활성화" if analyze_subtitles else "비활성화"
    print(f"\n[2/3] 키워드별 유튜브 데이터 수집 및 분석 중... (분석: {analyze_subs_str}, 소스: {analysis_source})")
    print(f"[INFO] {len(keywords)}개 키워드 분석 시작...\n")
    
    results = []
    for idx, keyword in enumerate(keywords, 1):
        is_fixed = (keyword == "오늘의 주요 뉴스")
        print(f"  [{idx}/{len(keywords)}] {keyword}{'🔒' if is_fixed else ''} 분석 중...")
        
        # 조회수 + 분석 데이터 수집
        data = collect_youtube_data(
            keyword,
            video_limit,
            model=model,
            analyze_subs=analyze_subtitles,
            analysis_source=analysis_source,
        )
        views = data["views"]
        video_count = data["video_count"]
        videos = data["videos"]
        today_videos = data.get("today_videos", [])
        recent_videos = data.get("recent_videos", [])
        today_count = data.get("today_count", 0)
        recent_count = data.get("recent_count", 0)
        
        nb_data = calculate_nb_score(views)
        
        result = {
            "keyword": keyword,
            "is_fixed": is_fixed,
            "views": views,
            "video_count": video_count,
            "videos": videos,
            **nb_data
        }
        results.append(result)
        
        # 상세 로그 출력
        if video_count > 0:
            print(f"       → 검색 결과: {video_count}개 영상 발견")
            
            # 오늘 영상 출력
            if today_count > 0:
                print(f"         [오늘] {today_count}개:")
                for v_idx, v in enumerate(today_videos, 1):
                    print(f"           {v_idx}. {v['title']} ({v['views']:,} 조회수)")
            
            # 최근 영상 출력
            if recent_count > 0:
                print(f"         [최근] {recent_count}개:")
                for v_idx, v in enumerate(recent_videos[:5], 1):  # 최근 영상은 최대 5개만 표시
                    date_str = v.get('upload_date', '날짜 미상')
                    print(f"           {v_idx}. {v['title']} ({v['views']:,} 조회수, {date_str})")
            
            # N/B Score 출력
            print(f"         N/B Score: {nb_data['nb_score']}")
            
            # 분석 완료 표시
            if analyze_subtitles and videos:
                analyzed_count = sum(1 for v in videos if v.get('subtitle_summary') and v['subtitle_summary'] != '자막 미분석')
                if analyzed_count > 0:
                    print(f"         영상 분석: {analyzed_count}개 완료")
        else:
            print(f"       → 검색 결과 없음")
        
        print(f"  [{idx}/{len(keywords)}] ✓ 완료\n")  # 각 키워드 완료 표시
        time.sleep(1)  # API 부하 방지
    
    # N/B Score 기준 정렬 (단, "오늘의 주요 뉴스"는 항상 상위 유지)
    fixed_results = [r for r in results if r.get("is_fixed")]
    other_results = [r for r in results if not r.get("is_fixed")]
    other_results.sort(key=lambda x: x["nb_score"], reverse=True)
    results = fixed_results + other_results
    
    # 4. 보고서 저장
    print(f"\n[3/3] 보고서 생성 중...")
    
    report_dir = get_today_report_dir()
    report_num = get_next_report_number(report_dir)
    
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "keyword_count": keyword_count,
        "analyze_subtitles": analyze_subtitles,
        "analysis_source": analysis_source,
        "keywords": results
    }
    
    save_report(report_data, report_dir, report_num, model=model)

    db_stats = save_completed_summaries_to_database(results)
    if DATABASE_SAVE_ENABLED:
        print(
            f"[DB] 참소식 저장 전송: 성공 {db_stats['sent']}건, "
            f"실패 {db_stats['failed']}건, 스킵 {db_stats['skipped']}건"
        )
    
    print(f"\n{'='*60}")
    print(f"[DONE] 보고서 #{report_num:03d} 생성 완료: {report_dir / f'report_{report_num:03d}.json'}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="YouTube 키워드 지속 모니터링")
    parser.add_argument("--model", default="qwen2.5:7b", help="Ollama 모델 (기본: qwen2.5:7b)")
    parser.add_argument("--keywords", type=int, default=10, help="키워드 개수 (기본: 10, '오늘의 주요 뉴스' 고정 포함)")
    parser.add_argument("--videos", type=int, default=10, help="키워드당 영상 수 (기본: 10)")
    parser.add_argument("--interval", type=int, default=30, help="모니터링 간격(분) (기본: 30분)")
    parser.add_argument("--subtitles", action="store_true", default=True, help="자막 분석 활성화 (기본: 활성화)")
    parser.add_argument("--no-subtitles", action="store_false", dest="subtitles", help="자막 분석 비활성화")
    parser.add_argument(
        "--analysis-source",
        choices=["subtitles", "google", "bing", "naver", "zum", "youtube", "auto"],
        default="youtube",
        help="분석 소스 선택 (subtitles|google|bing|naver|zum|youtube|auto)",
    )
    parser.add_argument("--once", action="store_true", help="1회만 실행하고 종료")
    
    args = parser.parse_args()
    
    # Ollama 모델 선택
    model = choose_ollama_model(args.model)
    
    print(f"""
╔═══════════════════════════════════════════════╗
║   YouTube 키워드 지속 모니터링 시스템        ║
╚═══════════════════════════════════════════════╝

설정:
- Ollama 모델: {model}
- 키워드 소스: {KEYWORDS_FILE} (파일 전체 로드, "오늘의 주요 뉴스" 고정 포함)
- 키워드 개수 옵션: {args.keywords} (파일 비어 있을 때만 기본 키워드 제한에 사용)
- 영상 수집 제한: {args.videos}개/키워드
- 자막 분석: {'활성화' if args.subtitles else '비활성화'}
- 분석 소스: {args.analysis_source}
- 모니터링 간격: {args.interval}분
- 보고서 저장: {REPORTS_BASE_DIR}
""")
    
    if args.once or args.interval <= 0:
        # 1회만 실행 (--once 또는 interval<=0)
        if args.interval <= 0 and not args.once:
            print("[INFO] interval이 0 이하이므로 1회 실행 후 종료합니다.")
        run_monitoring_cycle(model, args.keywords, args.videos, args.subtitles, args.analysis_source)
    else:
        # 지속적 모니터링
        cycle_count = 0
        while True:
            cycle_count += 1
            print(f"\n>>> 사이클 #{cycle_count}")
            
            try:
                run_monitoring_cycle(model, args.keywords, args.videos, args.subtitles, args.analysis_source)
            except Exception as e:
                print(f"[ERROR] 사이클 실행 오류: {e}")
            
            print(f"\n[WAIT] {args.interval}분 대기 중... (Ctrl+C로 중단)")
            time.sleep(args.interval * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[EXIT] 모니터링 종료")
        sys.exit(0)
