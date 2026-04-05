#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube monitor keyword updater

- Google Trends Korea RSS
- Naver News sections
- Daum breaking news

Collects Korea- and US-related headlines, removes North Korea topics and
person-name-heavy phrases, generates up to 15 keywords, and overwrites
monitor_keywords.txt.
"""

import argparse
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests

try:
    from selenium import webdriver
    from selenium.common.exceptions import TimeoutException, WebDriverException
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.common.by import By
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from selenium.webdriver.edge.service import Service as EdgeService
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
except ImportError:
    webdriver = None


SCRIPT_DIR = Path(__file__).parent.resolve()
KEYWORDS_FILE = SCRIPT_DIR / "monitor_keywords.txt"
LOG_FILE = SCRIPT_DIR / "logs" / "keyword_update.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("KEYWORD_BOT_MODEL", "deepseek-v3.1:671b-cloud")
MAX_KEYWORDS = 15
GOOGLE_TRENDS_RSS_URL = "https://trends.google.co.kr/trending/rss?geo=KR"

SOURCE_URLS = [
    ("daum_breaking", "https://news.daum.net/breakingnews"),
    ("naver_politics", "https://news.naver.com/section/100"),
    ("naver_economy", "https://news.naver.com/section/101"),
    ("naver_society", "https://news.naver.com/section/102"),
    ("naver_world", "https://news.naver.com/section/104"),
]

KOREA_MARKERS = {
    "한국", "국내", "서울", "정부", "국회", "여당", "야당", "검찰", "법원", "대통령",
    "한국은행", "한은", "금리", "환율", "코스피", "코스닥", "반도체", "수출", "관세",
    "부동산", "의대", "의정", "추경", "삼성", "sk", "현대", "네이버", "카카오",
}

US_MARKERS = {
    "미국", "미 증시", "뉴욕증시", "나스닥", "다우", "s&p", "연준", "fed", "fomc",
    "관세", "트럼프", "백악관", "미 대선", "달러", "미중", "워싱턴", "월가",
}

NORTH_KOREA_MARKERS = {
    "북한", "북한군", "북핵", "평양", "김정은", "김여정", "노동당", "미사일 도발",
    "핵실험", "조선중앙", "북러", "북미사일",
}

STOPWORDS = {
    "뉴스", "속보", "단독", "영상", "라이브", "실시간", "현장", "오늘", "내일", "이번",
    "관련", "대한", "통해", "있다", "있어", "기자", "정부", "한국", "국내", "미국",
    "정치", "경제", "사회", "산업", "시장", "이슈", "논란", "분석", "전망", "발표",
    "서울", "뉴욕", "워싱턴", "증시", "월가",
}

PERSON_NAME_PATTERNS = [
    re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b"),
    re.compile(r"[가-힣]{2,4}\s*(대통령|대표|회장|장관|총리|의장|후보|의원|감독|선수|배우|가수)"),
    re.compile(r"(대통령|대표|회장|장관|총리|의장|후보|의원|감독|선수|배우|가수)\s*[가-힣]{2,4}"),
]

ROLE_WORDS = {
    "대통령", "대표", "회장", "장관", "총리", "의장", "후보", "의원", "감독", "선수", "배우", "가수"
}


def log(message: str) -> None:
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def sanitize_title(text: str) -> str:
    text = re.sub(r"\[[^\]]+\]", " ", text)
    text = re.sub(r"\([^)]+\)", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -|/\t\r\n")


def normalize_keyword(text: str) -> str:
    text = sanitize_title(text)
    text = re.sub(r"^\d+\.\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_google_trends_rss(limit: int = 20) -> List[str]:
    response = requests.get(GOOGLE_TRENDS_RSS_URL, timeout=20)
    response.raise_for_status()

    root = ET.fromstring(response.text)
    titles: List[str] = []
    seen = set()
    for item in root.findall(".//item"):
        title = sanitize_title(item.findtext("title", default=""))
        if not title or title in seen:
            continue
        seen.add(title)
        titles.append(title)
        if len(titles) >= limit:
            break
    return titles


def build_driver(browser: str, driver_path: Optional[str], headless: bool):
    if webdriver is None:
        raise RuntimeError("selenium is not installed. Run `pip install selenium` first.")

    browser = browser.lower().strip()
    if browser == "edge":
        options = EdgeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--lang=ko-KR")
        options.add_argument("--window-size=1440,2200")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        service = EdgeService(executable_path=driver_path) if driver_path else None
        return webdriver.Edge(service=service, options=options)

    options = ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--lang=ko-KR")
    options.add_argument("--window-size=1440,2200")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    service = ChromeService(executable_path=driver_path) if driver_path else None
    return webdriver.Chrome(service=service, options=options)


def wait_for_page(driver, css_selector: str, timeout: int = 12) -> None:
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
    )


def extract_lines_from_elements(driver, selectors: List[str], limit: int = 30) -> List[str]:
    lines: List[str] = []
    seen = set()
    for selector in selectors:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        for element in elements:
            text = sanitize_title(" ".join(element.text.split()))
            if len(text) < 6 or text in seen:
                continue
            seen.add(text)
            lines.append(text)
            if len(lines) >= limit:
                return lines
    return lines


def contains_marker(text: str, markers: set[str]) -> bool:
    lowered = text.lower()
    return any(marker.lower() in lowered for marker in markers)


def strip_person_names(text: str) -> str:
    result = text
    for pattern in PERSON_NAME_PATTERNS:
        result = pattern.sub(" ", result)
    result = re.sub(r"\s+", " ", result).strip()
    return result


def is_person_name_heavy(text: str) -> bool:
    original = normalize_keyword(text)
    stripped = strip_person_names(original)
    if not stripped:
        return True
    if len(stripped) <= 2:
        return True
    if stripped in ROLE_WORDS:
        return True
    return False


def is_allowed_topic(text: str) -> bool:
    if contains_marker(text, NORTH_KOREA_MARKERS):
        return False
    if contains_marker(text, KOREA_MARKERS) or contains_marker(text, US_MARKERS):
        return True
    if re.search(r"[가-힣]{2,}", text):
        return True
    return False


def collect_source_items(driver) -> List[Dict[str, str]]:
    all_items: List[Dict[str, str]] = []

    try:
        log(f"google_trends_rss fetch start: {GOOGLE_TRENDS_RSS_URL}")
        trend_lines = fetch_google_trends_rss(limit=25)
        for line in trend_lines:
            all_items.append({"source": "google_trends_rss", "text": line})
        log(f"google_trends_rss fetch done: {len(trend_lines)} items")
    except Exception as e:
        log(f"google_trends_rss fetch failed: {e}")

    for source_name, url in SOURCE_URLS:
        try:
            log(f"{source_name} collect start: {url}")
            driver.get(url)
            time.sleep(2.5)

            if "news.naver.com" in url:
                wait_for_page(driver, "body")
                lines = extract_lines_from_elements(
                    driver,
                    ["a.sa_text_title", "strong.sa_text_strong", "a._cds_link", "div.section_article a", "ul li a"],
                    limit=30,
                )
            else:
                wait_for_page(driver, "body")
                lines = extract_lines_from_elements(
                    driver,
                    ["strong.tit_txt", "a.link_txt", "div.item_issue a", "ul li a"],
                    limit=30,
                )

            for line in lines:
                all_items.append({"source": source_name, "text": line})

            log(f"{source_name} collect done: {len(lines)} items")
        except (TimeoutException, WebDriverException) as e:
            log(f"{source_name} collect failed: {e}")
        except Exception as e:
            log(f"{source_name} processing error: {e}")

    return all_items


def dedupe_items(items: List[Dict[str, str]]) -> List[str]:
    seen = set()
    results: List[str] = []
    for item in items:
        text = normalize_keyword(item["text"])
        if not text or text in seen:
            continue
        seen.add(text)
        results.append(text)
    return results


def filter_topic_items(lines: List[str]) -> List[str]:
    filtered: List[str] = []
    for line in lines:
        if not is_allowed_topic(line):
            continue
        if is_person_name_heavy(line):
            continue
        filtered.append(line)
    return filtered


def extract_candidate_phrases(text: str) -> List[str]:
    text = strip_person_names(text)
    normalized = re.sub(r"[^0-9A-Za-z가-힣\s]", " ", text)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    words = [word for word in normalized.split() if len(word) >= 2]

    phrases: List[str] = []
    for size in (2, 3):
        for idx in range(len(words) - size + 1):
            phrase = " ".join(words[idx:idx + size]).strip()
            if any(token.lower() in STOPWORDS for token in phrase.split()):
                continue
            if contains_marker(phrase, NORTH_KOREA_MARKERS):
                continue
            if len(phrase) < 4 or len(phrase) > 26:
                continue
            phrases.append(phrase)
    return phrases


def heuristic_keywords(lines: List[str], limit: int) -> List[str]:
    counter: Counter = Counter()
    for line in lines:
        for phrase in extract_candidate_phrases(line):
            score = 1
            if contains_marker(phrase, KOREA_MARKERS):
                score += 2
            if contains_marker(phrase, US_MARKERS):
                score += 2
            counter[phrase] += score

    keywords: List[str] = []
    for phrase, _ in counter.most_common(limit * 6):
        candidate = normalize_keyword(strip_person_names(phrase))
        if not candidate or candidate in keywords:
            continue
        if contains_marker(candidate, NORTH_KOREA_MARKERS):
            continue
        if is_person_name_heavy(candidate):
            continue
        if re.fullmatch(r"[0-9A-Za-z]+", candidate):
            continue
        keywords.append(candidate)
        if len(keywords) >= limit:
            break
    return keywords


def generate_keywords_with_ollama(lines: List[str], model: str, limit: int) -> List[str]:
    joined = "\n".join(f"- {line}" for line in lines[:80])
    prompt = f"""다음은 한국 및 미국 관련 뉴스 헤드라인과 트렌드 목록이다.
유튜브 검색용 한국어 키워드를 최대 {limit}개 생성하라.

입력:
{joined}

규칙:
1. 한국 또는 미국 관련 이슈만 반영
2. 북한 관련 이슈는 절대 제외
3. 특정 인물 실명은 절대 쓰지 말 것
4. 한 줄에 하나씩만 출력
5. 2~6단어 검색어 형태
6. 너무 일반적인 단어 단독 사용 금지
7. 정치, 경제, 사회, 산업, 증시, 외교 이슈 우선
8. 중복 금지
9. 설명 없이 키워드만 출력
"""

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.25,
                "top_p": 0.9,
                "num_predict": 180,
            },
        },
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    raw = payload.get("response", "")

    keywords: List[str] = []
    seen = set()
    for line in raw.splitlines():
        text = normalize_keyword(strip_person_names(line))
        if not text or text in seen:
            continue
        if contains_marker(text, NORTH_KOREA_MARKERS):
            continue
        if is_person_name_heavy(text):
            continue
        if len(text) < 3 or len(text) > 30:
            continue
        if any(char.isdigit() for char in text[:2]):
            continue
        seen.add(text)
        keywords.append(text)
        if len(keywords) >= limit:
            break
    return keywords


def save_keywords(keywords: List[str]) -> List[str]:
    unique_keywords: List[str] = []
    seen = set()
    for keyword in keywords:
        clean = normalize_keyword(strip_person_names(keyword))
        if not clean or clean.startswith("#") or clean in seen:
            continue
        if contains_marker(clean, NORTH_KOREA_MARKERS):
            continue
        if is_person_name_heavy(clean):
            continue
        seen.add(clean)
        unique_keywords.append(clean)
        if len(unique_keywords) >= MAX_KEYWORDS:
            break

    with open(KEYWORDS_FILE, "w", encoding="utf-8") as f:
        for keyword in unique_keywords:
            f.write(f"{keyword}\n")

    return unique_keywords


def run_keyword_update(
    model: str,
    keyword_limit: int,
    browser: str,
    driver_path: Optional[str],
    headless: bool,
) -> List[str]:
    keyword_limit = max(1, min(keyword_limit, MAX_KEYWORDS))
    driver = build_driver(browser=browser, driver_path=driver_path, headless=headless)

    try:
        collected_items = collect_source_items(driver)
    finally:
        driver.quit()

    collected_lines = dedupe_items(collected_items)
    filtered_lines = filter_topic_items(collected_lines)

    log(f"collected lines: {len(collected_lines)}")
    log(f"filtered topic lines: {len(filtered_lines)}")

    if not filtered_lines:
        raise RuntimeError("No eligible news or trend items were collected.")

    try:
        keywords = generate_keywords_with_ollama(filtered_lines, model=model, limit=keyword_limit)
        log(f"ollama keyword generation done: {len(keywords)}")
        if not keywords:
            log("ollama returned no keywords, using heuristic fallback")
            keywords = heuristic_keywords(filtered_lines, limit=keyword_limit)
    except Exception as e:
        log(f"ollama keyword generation failed, using heuristic fallback: {e}")
        keywords = heuristic_keywords(filtered_lines, limit=keyword_limit)

    if not keywords:
        raise RuntimeError("No keywords were generated.")

    saved_keywords = save_keywords(keywords)
    log(f"keywords saved: {len(saved_keywords)} -> {KEYWORDS_FILE}")
    return saved_keywords


def main() -> int:
    parser = argparse.ArgumentParser(description="Update youtube monitor_keywords.txt")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model (default: {DEFAULT_MODEL})")
    parser.add_argument("--count", type=int, default=MAX_KEYWORDS, help=f"Keyword count (max: {MAX_KEYWORDS})")
    parser.add_argument("--browser", choices=["chrome", "edge"], default="chrome", help="Browser type")
    parser.add_argument("--driver-path", help="ChromeDriver or EdgeDriver path")
    parser.add_argument("--show-browser", action="store_true", help="Disable headless mode")
    args = parser.parse_args()

    try:
        keywords = run_keyword_update(
            model=args.model,
            keyword_limit=min(args.count, MAX_KEYWORDS),
            browser=args.browser,
            driver_path=args.driver_path,
            headless=not args.show_browser,
        )
    except Exception as e:
        log(f"run failed: {e}")
        return 1

    print("\nUpdated keywords:")
    for idx, keyword in enumerate(keywords, 1):
        print(f"{idx:02d}. {keyword}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
