#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Mermaid diagram files from a website or RSS feed.

This script:
1. Loads the target page with Selenium.
2. Extracts meaningful content from HTML or RSS.
3. Adds finance JSON context and search snippets.
4. Sends a prompt to Ollama.
5. Saves HTML, MMD, and JSON outputs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from urllib.parse import quote_plus
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


OLLAMA_API_URL = "http://211.45.162.155:11434/api/generate"
OLLAMA_WEB_API_URL = "http://localhost:3000/api/ollama-chat"  # 웹 서버 API
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "kimi-k2.5:cloud")

WAIT_TIME = 10
SCROLL_WAIT = 2
DATA_LOAD_TIMEOUT = 100
HEADLESS_MODE = os.environ.get("SELENIUM_HEADLESS", "0").lower() in {"1", "true", "yes", "on"}

ROOT_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = ROOT_DIR / "web" / "public"
PROMPT_TEMPLATE_PATH = Path(__file__).resolve().parent / "diagram_prompt_template.txt"


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Website Diagram</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: 'Pretendard', 'Malgun Gothic', sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            background: white;
            border-radius: 16px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }}
        h1 {{
            color: #2d3748;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-align: center;
        }}
        .meta-info {{
            text-align: center;
            color: #718096;
            margin-bottom: 30px;
            font-size: 0.95em;
        }}
        .url-info {{
            background: #f7fafc;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }}
        .url-info strong {{
            color: #4a5568;
        }}
        .url-info a {{
            color: #667eea;
            text-decoration: none;
            word-break: break-all;
        }}
        .url-info a:hover {{
            text-decoration: underline;
        }}
        .diagram-container {{
            background: #ffffff;
            padding: 30px;
            border-radius: 12px;
            margin-top: 20px;
            border: 1px solid #e2e8f0;
            overflow-x: auto;
        }}
        .mermaid {{
            display: flex;
            justify-content: center;
            min-height: 400px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            color: #a0aec0;
            font-size: 0.9em;
        }}
        .ai-badge {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 0.85em;
            margin-bottom: 20px;
        }}
        .controls {{
            margin-top: 20px;
            text-align: center;
        }}
        .btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            margin: 5px;
            transition: all 0.3s ease;
        }}
        .btn:hover {{
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }}
        @media (max-width: 768px) {{
            .container {{
                padding: 20px;
            }}
            h1 {{
                font-size: 1.8em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="meta-info">
            <div class="ai-badge">Auto generated with Ollama ({model})</div>
            <div>Generated at: {timestamp}</div>
        </div>

        <div class="url-info">
            <strong>Source URL:</strong>
            <a href="{url}" target="_blank" rel="noopener">{url}</a>
        </div>

        <div class="diagram-container">
            <div class="mermaid">
{mermaid_code}
            </div>
        </div>

        <div class="controls">
            <button class="btn" onclick="window.print()">Print</button>
            <button class="btn" onclick="location.reload()">Reload</button>
        </div>

        <div class="footer">
            <p>This diagram was generated automatically from website content.</p>
            <p>Rendered with Mermaid.</p>
        </div>
    </div>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: "default",
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: "basis"
            }}
        }});
    </script>
</body>
</html>
"""


def find_site_dir() -> Path:
    candidates = list(PUBLIC_DIR.rglob("world-monitor-ai.json"))
    if not candidates:
        raise FileNotFoundError("Could not find world-monitor-ai.json under web/public")
    preferred = [p for p in candidates if "참소식.com" in str(p.parent)]
    if preferred:
        return preferred[0].parent

    # If multiple candidates exist, prefer the deepest directory over web/public root.
    return max(candidates, key=lambda p: len(p.parent.parts)).parent


SITE_DIR = find_site_dir()
FINANCE_JSON_PATH = SITE_DIR / "realtime_finance_data.json"


def build_driver(prefer_headless: bool | None = None) -> webdriver.Chrome:
    def create_options(headless: bool) -> Options:
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_argument("--log-level=3")
        # 세션 유지 설정
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("useAutomationExtension", False)
        # 추가 안정성 설정
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--ignore-certificate-errors")
        return options

    requested_headless = HEADLESS_MODE if prefer_headless is None else prefer_headless

    # Try requested mode first. If visible mode fails, retry once in headless mode.
    launch_modes = [requested_headless]
    if not requested_headless:
        launch_modes.append(True)

    last_error: Exception | None = None
    for headless in launch_modes:
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=create_options(headless))
            driver.set_page_load_timeout(60)
            # 세션 유지를 위한 추가 설정
            driver.implicitly_wait(10)
            # DevTools 연결 확인
            try:
                driver.current_url  # 세션 활성화 확인
            except Exception as e:
                print(f"[driver] session check failed: {e}")
                continue
            if headless and not requested_headless:
                print("[driver] visible mode failed, fell back to headless mode")
            return driver
        except Exception as exc:
            mode_name = "headless" if headless else "visible"
            print(f"[driver] {mode_name} launch failed: {exc}")
            last_error = exc

    if last_error:
        raise last_error
    raise RuntimeError("Failed to initialize Chrome driver")


def collect_search_results(driver: webdriver.Chrome, target: dict[str, Any]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    seen_hrefs: set[str] = set()

    for selector in target["selectors"]:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
        except Exception:
            continue

        for element in elements:
            try:
                anchor = element
                if element.tag_name.lower() != "a":
                    anchor = element.find_element(By.XPATH, "./ancestor::a[1]")

                href = (anchor.get_attribute("href") or "").strip()
                title = (element.text or anchor.text or "").strip()
                if not href or not title or href in seen_hrefs:
                    continue

                snippet = ""
                try:
                    container = anchor.find_element(By.XPATH, "./ancestor::*[self::div or self::li or self::article][1]")
                    snippet = container.text.strip()
                except Exception:
                    snippet = title

                snippet = re.sub(r"\s+", " ", snippet)
                title = re.sub(r"\s+", " ", title)
                results.append(
                    {
                        "title": title[:160],
                        "href": href,
                        "snippet": snippet[:280],
                    }
                )
                seen_hrefs.add(href)
                if len(results) >= 3:
                    return results
            except Exception:
                continue

    return results


def read_first_result_page(driver: webdriver.Chrome, href: str, wait_time: int) -> str:
    try:
        driver.get(href)
        time.sleep(min(wait_time, 5))
        body_text = driver.find_element(By.TAG_NAME, "body").text.strip()
        return re.sub(r"\s+", " ", body_text)[:1000]
    except Exception as exc:
        print(f"[search] first result page read failed: {exc}")
        return ""


def ollama_search_batch(queries: list[str], model: str = OLLAMA_MODEL) -> dict[str, str]:
    """여러 검색어를 한 번의 API 호출로 처리"""
    results = {}
    if not queries:
        return results
    
    try:
        print(f"[ollama-search-batch] queries: {len(queries)}개")
        print(f"[ollama-search-batch] model: {model}")
        
        # 모든 검색어를 하나의 프롬프트에 포함
        query_list = "\n".join([f"{i+1}. {q}" for i, q in enumerate(queries)])
        
        prompt = f"""다음 검색어들에 대해 각각 1-2문장으로 간단히 설명하세요.

검색어 목록:
{query_list}

조건:
1. 각 검색어에 대해 1-2문장으로만 설명
2. 핵심 정보만 포함 (현재 가격, 지수, 용어 설명 등)
3. 한국어로 작성
4. 각 설명은 새 줄에 작성
5. 형식: "검색어: 설명내용"

설명:"""

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 2000}
        }
        
        response = requests.post(
            OLLAMA_API_URL,
            json=payload,
            timeout=60
        )
        
        print(f"[ollama-search-batch] response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            # response 필드 확인 (일반 모델)
            text = data.get("response", "").strip()
            # response가 비어있으면 thinking 필드 확인 (thinking 모델)
            if not text:
                text = data.get("thinking", "").strip()
            
            if text:
                print(f"[ollama-search-batch] response length: {len(text)}")
                # 각 검색어에 대한 결과 파싱
                for query in queries:
                    # 검색어에 해당하는 설명 찾기
                    for line in text.split("\n"):
                        line = line.strip()
                        if ":" in line:
                            parts = line.split(":", 1)
                            if len(parts) == 2:
                                key = parts[0].strip()
                                value = parts[1].strip()
                                # 검색어가 포함된 키 찾기
                                for q in queries:
                                    if q.lower() in key.lower() or key.lower() in q.lower():
                                        results[q] = value
                                        break
                
                # 파싱 실패 시 전체 텍스트를 첫 번째 검색어에 할당
                if not results and queries:
                    results[queries[0]] = text[:200]
                
                print(f"[ollama-search-batch] parsed {len(results)} results")
            else:
                print(f"[ollama-search-batch] no result in response or thinking")
        else:
            print(f"[ollama-search-batch] error: {response.status_code}")
            
    except Exception as e:
        print(f"[ollama-search-batch] failed: {e}")
    
    return results


def ollama_search(query: str, model: str = OLLAMA_MODEL) -> str:
    """Ollama AI를 사용한 검색 결과 생성"""
    try:
        print(f"[ollama-search] query: {query}")
        print(f"[ollama-search] model: {model}")
        print(f"[ollama-search] API URL: {OLLAMA_API_URL}")
        
        # thinking 모델을 위한 명시적인 프롬프트
        prompt = f"""{query}에 대해 설명해주세요.

중요: 아래 조건을 반드시 따르세요.
1. 1-2문장으로만 간단하게 설명
2. 핵심 정보만 포함 (현재 가격, 지수 등)
3. 한국어로 작성
4. HTML 태그 없이 텍스트만 출력
5. "사용자가 요청했습니다" 같은 메타 설명 금지
6. 바로 설명 내용만 출력

예시:
KOSPI: 한국종합주가지수로, 한국 증권시장의 대표적인 주가 지수입니다.
Bitcoin: 암호화폐의 일종으로, 2009년 사토시 나카모토가 만든 디지털 화폐입니다.

{query}:"""

        # 원격 Ollama 서버 사용 (우선)
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 200}
        }
        print(f"[ollama-search] payload: model={payload['model']}, stream={payload['stream']}")
        
        response = requests.post(
            OLLAMA_API_URL,
            json=payload,
            timeout=30
        )
        
        print(f"[ollama-search] response status: {response.status_code}")
        print(f"[ollama-search] response text: {response.text[:200]}")
        
        if response.status_code == 200:
            data = response.json()
            # response 필드 확인 (일반 모델)
            result = data.get("response", "").strip()
            # response가 비어있으면 thinking 필드 확인 (thinking 모델)
            if not result:
                result = data.get("thinking", "").strip()
            if result:
                print(f"[ollama-search] result: {result[:100]}...")
                return result
            print(f"[ollama-search] no result in response or thinking")
            return ""
        
        # 웹 서버 API 사용 (백업)
        print(f"[ollama-search] remote failed: {response.status_code}, trying web API...")
        try:
            web_response = requests.post(
                OLLAMA_WEB_API_URL,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                },
                timeout=30
            )
            
            if web_response.status_code == 200:
                data = web_response.json()
                result = data.get("content", "") or data.get("response", "")
                if result:
                    print(f"[ollama-search] web API result: {result[:100]}...")
                    return result
        except Exception as e:
            print(f"[ollama-search] web API failed: {e}")
        
        print(f"[ollama-search] error: {response.status_code}")
        return ""
    except Exception as e:
        print(f"[ollama-search] failed: {e}")
        return ""


def search_result_and_extract(query: str, driver: webdriver.Chrome, wait_time: int = 10, model: str = OLLAMA_MODEL) -> str:
    """Ollama AI를 사용한 검색 결과 생성 (네이버/줌 검색 제거)"""
    print(f"[search] query: {query}")
    
    # Ollama AI 검색 사용
    result = ollama_search(query, model=model)
    
    if result:
        return f"[AI 검색] {result}"
    
    print("[search] no result from AI")
    return "(AI 검색 결과 없음)"


def fetch_webpage(url: str, wait_time: int = WAIT_TIME) -> str | None:
    """RSS/XML 피치는 requests 사용, 일반 웹페이지는 Selenium 사용"""
    
    # RSS/XML 피치인 경우 requests 사용
    if url.endswith(('.xml', '.rss', '/feed.xml', '/rss')):
        try:
            print(f"[fetch] url: {url}")
            print(f"[fetch] using requests (RSS/XML)")
            
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            print(f"[fetch] bytes: {len(response.text)}")
            return response.text
        except Exception as exc:
            print(f"[fetch] requests failed: {exc}")
            return None
    
    # 일반 웹페이지는 Selenium 사용
    driver = None
    try:
        print(f"[fetch] url: {url}")
        print(f"[fetch] wait_time: {wait_time}s")

        driver = build_driver()
        
        # 페이지 로드 전 세션 확인
        try:
            current_url = driver.current_url
            print(f"[fetch] session active: {current_url[:50] if current_url else 'empty'}")
        except Exception as e:
            print(f"[fetch] session check failed: {e}")
            return None
        
        driver.get(url)
        time.sleep(wait_time)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        time.sleep(SCROLL_WAIT)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_WAIT)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        try:
            loading_xpath = (
                "//*[contains(text(), '로딩 중') "
                "or contains(text(), 'Loading') "
                "or contains(text(), '데이터 로딩')]"
            )
            loading_elements = driver.find_elements(By.XPATH, loading_xpath)
            if loading_elements:
                print(f"[fetch] loading indicators: {len(loading_elements)}")
                for i in range(DATA_LOAD_TIMEOUT):
                    time.sleep(1)
                    remaining = driver.find_elements(By.XPATH, loading_xpath)
                    if not remaining:
                        print(f"[fetch] loading complete after {i + 1}s")
                        break
        except Exception as exc:
            print(f"[fetch] loading check skipped: {exc}")

        html_content = driver.page_source
        print(f"[fetch] bytes: {len(html_content)}")
        return html_content
    except Exception as exc:
        print(f"[fetch] failed: {exc}")
        return None
    finally:
        if driver:
            try:
                # 세션 정상 종료
                driver.close()
                driver.quit()
            except Exception as e:
                print(f"[fetch] driver cleanup warning: {e}")


def extract_date(text: str):
    patterns = [
        r"(20\d{2}[.-/]\d{1,2}[.-/]\d{1,2})",
        r"(20\d{2}\d{2}\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        date_str = match.group(1).replace(".", "-").replace("/", "-").replace(" ", "")
        try:
            if "-" in date_str:
                return datetime.strptime(date_str, "%Y-%m-%d")
            return datetime.strptime(date_str, "%Y%m%d")
        except Exception:
            continue
    return None


def extract_page_content(html_content: str) -> dict[str, Any] | None:
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        is_rss = bool(soup.find("rss")) or bool(soup.find("channel"))

        if is_rss:
            channel = soup.find("channel")
            title = channel.find("title").get_text(strip=True) if channel and channel.find("title") else "Untitled"
            meta_desc = channel.find("description").get_text(strip=True) if channel and channel.find("description") else ""
            items = channel.find_all("item") if channel else []

            data_items: list[str] = []
            links: list[str] = []
            for item in items:
                item_title = item.find("title").get_text(strip=True) if item.find("title") else ""
                item_desc = item.find("description").get_text(strip=True) if item.find("description") else ""
                item_link = item.find("link").get_text(strip=True) if item.find("link") else ""
                if item_title:
                    data_items.append(item_title)
                if item_desc:
                    data_items.append(item_desc)
                if item_link:
                    links.append(item_link)

            return {
                "title": title,
                "meta_description": meta_desc,
                "text_preview": "\n".join(data_items)[:2000],
                "data_items": data_items,
                "links": links,
                "headings": [],
                "has_real_data": len(data_items) > 0 or len(links) > 5,
            }

        for script in soup(["script", "style"]):
            script.decompose()

        title = soup.title.string if soup.title else "Untitled"
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag and meta_tag.get("content"):
            meta_desc = meta_tag["content"]

        text_content = " ".join(soup.get_text(separator=" ", strip=True).split())

        data_items: list[str] = []
        selector_groups = [
            {"class": ["news-item", "article", "post", "item", "card"]},
            {"attrs": {"data-item": True}},
            {"attrs": {"data-article": True}},
        ]

        for selector_dict in selector_groups:
            if "class" in selector_dict:
                for class_name in selector_dict["class"]:
                    items = soup.find_all(class_=lambda x: x and class_name in x if x else False)
                    for item in items[:30]:
                        item_text = item.get_text(strip=True)
                        if item_text and len(item_text) > 10 and "로딩" not in item_text:
                            data_items.append(item_text[:200])
            else:
                items = soup.find_all(attrs=selector_dict["attrs"])
                for item in items[:30]:
                    item_text = item.get_text(strip=True)
                    if item_text and len(item_text) > 10 and "로딩" not in item_text:
                        data_items.append(item_text[:200])

        data_items = sorted(
            list(dict.fromkeys(data_items)),
            key=lambda value: extract_date(value) if extract_date(value) else datetime(1900, 1, 1),
            reverse=True,
        )

        excluded_keywords = ["카테고리", "메뉴", "푸터", "정렬", "초기화", "전체", "정치", "경제", "사회", "문화"]
        links: list[str] = []
        seen_hrefs: set[str] = set()
        for anchor in soup.find_all("a", href=True):
            link_text = anchor.get_text(strip=True)
            link_href = anchor["href"]
            is_excluded = any(keyword in link_text for keyword in excluded_keywords)
            if (
                link_href not in seen_hrefs
                and link_text
                and len(link_text) > 5
                and not is_excluded
                and not link_href.startswith(("#", "javascript:"))
            ):
                links.append(f"{link_text} -> {link_href}")
                seen_hrefs.add(link_href)
            if len(links) >= 50:
                break

        headings: list[str] = []
        for heading in soup.find_all(["h1", "h2", "h3", "h4"])[:30]:
            heading_text = heading.get_text(strip=True)
            if heading_text:
                headings.append(f"{heading.name}: {heading_text}")

        return {
            "title": title,
            "meta_description": meta_desc,
            "text_preview": text_content[:2000],
            "data_items": data_items,
            "links": links,
            "headings": headings,
            "has_real_data": len(data_items) > 0 or len(links) > 5,
        }
    except Exception as exc:
        print(f"[extract] failed: {exc}")
        return None


def load_prompt_template() -> str | None:
    try:
        return PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"[prompt] template load failed: {exc}")
        return None


def load_finance_json() -> dict[str, Any]:
    if not FINANCE_JSON_PATH.exists():
        return {}
    try:
        return json.loads(FINANCE_JSON_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[finance] load failed: {exc}")
        return {}


def format_finance_value(value: Any) -> str:
    text = str(value).strip()
    if not text:
        return text

    prefix = ""
    if text.startswith("$"):
        prefix = "$"
        text = text[1:].strip()

    numeric = text.replace(",", "")
    if re.fullmatch(r"-?\d+", numeric):
        return f"{prefix}{int(numeric):,}"
    if re.fullmatch(r"-?\d+\.\d+", numeric):
        decimals = len(numeric.split(".", 1)[1])
        return f"{prefix}{float(numeric):,.{decimals}f}"
    return prefix + text


def enforce_finance_values_in_mermaid(mermaid_code: str) -> str:
    finance_json = load_finance_json()
    if not finance_json:
        return mermaid_code

    replacements: dict[str, str] = {}
    for key, value in finance_json.items():
        if key.endswith("_ollama"):
            base_key = key[:-7]
            try:
                parsed = json.loads(value) if isinstance(value, str) else value
            except Exception:
                parsed = None
            if isinstance(parsed, dict) and "value_krw" in parsed:
                replacements[f"{base_key}_price"] = format_finance_value(parsed["value_krw"])
            continue
        replacements[key] = format_finance_value(value)

    updated_code = mermaid_code
    for label, exact_value in replacements.items():
        pattern = re.compile(rf"(\[{re.escape(label)}:\s*)([^\]]+)(\])")
        updated_code, count = pattern.subn(rf"\g<1>{exact_value}\g<3>", updated_code)
        if count > 0:
            print(f"[finance] enforced {label} = {exact_value}")

    return updated_code


def build_finance_context(model: str = OLLAMA_MODEL) -> tuple[list[str], list[str], dict[str, str]]:
    price_nodes: list[str] = []
    explanation_nodes: list[str] = []
    search_texts: dict[str, str] = {}

    if not FINANCE_JSON_PATH.exists():
        print(f"[finance] file not found: {FINANCE_JSON_PATH}")
        return price_nodes, explanation_nodes, search_texts

    try:
        finance_json = json.loads(FINANCE_JSON_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[finance] parse failed: {exc}")
        return price_nodes, explanation_nodes, search_texts

    # 모든 검색어를 수집
    queries_to_keys: dict[str, str] = {}  # query -> key 매핑
    for key, value in finance_json.items():
        if not key.endswith("_ollama"):
            price_nodes.append(f"{key}: {value}")
            if any(token in key for token in ["KOSPI", "KOSDAQ", "S&P", "NASDAQ", "DOW"]):
                query = f"{key} live index"
            else:
                query = f"{key} live price"
            queries_to_keys[query] = key

    # 배치 검색 실행 (한 번의 API 호출로 모든 검색어 처리)
    if queries_to_keys:
        print(f"[finance] batch searching {len(queries_to_keys)} queries...")
        batch_results = ollama_search_batch(list(queries_to_keys.keys()), model=model)
        
        # 결과 매핑 - 가격 정보와 AI 설명을 결합
        for query, key in queries_to_keys.items():
            result_text = batch_results.get(query, "")
            price_value = finance_json.get(key, "")
            
            # 가격 + AI 설명 결합
            if result_text:
                # 가격 정보가 있으면 포함
                if price_value:
                    search_texts[key] = f"{price_value} - {result_text}"
                else:
                    search_texts[key] = f"[AI 검색] {result_text}"
            else:
                # AI 검색 결과가 없으면 가격만 표시
                if price_value:
                    search_texts[key] = f"{price_value}"
                else:
                    search_texts[key] = "(AI 검색 결과 없음)"
            
            value_preview = str(price_value)[:60].replace("\n", " ")
            result_preview = search_texts[key][:120].replace("\n", " ")
            print(f"[finance] {key} value: {value_preview}")
            print(f"[finance] {key} search preview: {result_preview}...")

    # _ollama 항목 처리
    for key, value in finance_json.items():
        if key.endswith("_ollama"):
            base_key = key.replace("_ollama", "")
            try:
                if isinstance(value, str) and value.strip().startswith("{"):
                    parsed = json.loads(value)
                    if "value_krw" in parsed:
                        price_nodes.append(f"{base_key}_price: {parsed['value_krw']}")
                    if "explanation" in parsed:
                        explanation_nodes.append(f"{base_key}_desc: {parsed['explanation']}")
                else:
                    explanation_nodes.append(f"{base_key}_desc: {str(value).strip()}")
            except Exception:
                explanation_nodes.append(f"{base_key}_desc: {value}")

    return price_nodes, explanation_nodes, search_texts


def build_prompt(url: str, page_content: dict[str, Any], prompt_template: str | None, model: str = OLLAMA_MODEL) -> str:
    price_nodes, explanation_nodes, search_texts = build_finance_context(model=model)

    always_include = ["KOSPI", "KOSDAQ", "S&P500", "NASDAQ", "DOWJONES", "Bitcoin"]
    always_items: list[str] = []
    rest_items: list[str] = []

    for item in price_nodes + explanation_nodes:
        if any(keyword in item for keyword in always_include):
            always_items.append(item)
        else:
            rest_items.append(item)

    always_items = list(dict.fromkeys(always_items))
    rest_items = [item for item in rest_items if item not in always_items]
    merged_items = (always_items + rest_items)[:16]

    search_lines = []
    for key, value in search_texts.items():
        short_text = value[:100].replace("\n", " ")
        search_lines.append(f"[AI 검색] {key}: {short_text} ...")

    merged_items_info = "\n".join(merged_items + search_lines)
    limited_items = page_content.get("data_items", [])[:12]
    limited_items_info = "\n".join(limited_items) if limited_items else "no data"

    if prompt_template:
        
        prompt = prompt_template.replace("{merged_items_info}", merged_items_info)
        prompt = prompt.replace("{url}", url)
        prompt = prompt.replace("{limited_items_info}", limited_items_info)
        return prompt

    return f"""
Return Mermaid flowchart TD code only.
Do not use code fences.
Include relation labels using one of: [중요], [보통], [낮음].

[URL]
{url}

[FINANCE_AND_SEARCH_CONTEXT]
{merged_items_info}

[PAGE_ITEMS]
{limited_items_info}
""".strip()


def clean_mermaid_code(mermaid_code: str) -> str:
    code = (mermaid_code or "").strip()
    if "```mermaid" in code:
        code = code.split("```mermaid", 1)[1].split("```", 1)[0].strip()
    elif "```" in code:
        code = code.split("```", 1)[1].split("```", 1)[0].strip()

    if not code.startswith("flowchart") and not code.startswith("graph"):
        code = "flowchart TD\n" + code

    patterns_to_remove = [
        r"카테고리\s*:\s*일반",
        r"유형\s*:\s*텍스트",
        r"유형\s*:",
        r"조회수\s*:\s*\d+",
        r"카테고리",
        r"조회수",
    ]
    for pattern in patterns_to_remove:
        code = re.sub(pattern, "", code)

    return code.strip()


def generate_diagram_with_ollama(url: str, page_content: dict[str, Any], model: str = OLLAMA_MODEL) -> str:
    try:
        print(f"[ollama] generating with model: {model}")
        prompt_template = load_prompt_template()
        prompt = build_prompt(url, page_content, prompt_template, model=model)

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 10000,
            },
        }

        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        print("[ollama] raw response received")
        return enforce_finance_values_in_mermaid(clean_mermaid_code(result.get("response", "")))
    except Exception as exc:
        print(f"[ollama] failed: {exc}")
        title = page_content.get("title", "Page")
        return (
            "flowchart TD\n"
            f"    A[{title}]\n"
            "    A --> B[Main Page]\n"
            "    A --> C[Content Area]\n"
            "    B --> D[Navigation]\n"
            "    C --> E[Data Section]\n"
            "    classDef mainStyle fill:#667eea,stroke:#333,color:#fff\n"
            "    class A mainStyle"
        )


def is_truncated_mermaid(mermaid_code: str) -> bool:
    code = mermaid_code.strip()
    if not code or code == "flowchart TD":
        return True
    if code.count("[") < 2 or code.count("->") < 1:
        return True
    if code.count("[") != code.count("]"):
        return True
    return False


def extract_edges_from_mermaid(mermaid_code: str) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    edge_pattern = re.compile(r"^\s*(.+?)\s*[-]+[a-zA-Z]*>\s*(.+?)\s*\[(중요|보통|낮음)\]", re.UNICODE)
    importance_map = {"중요": 100, "보통": 50, "낮음": 1}

    for line in mermaid_code.splitlines():
        match = edge_pattern.match(line)
        if not match:
            continue
        edges.append(
            {
                "source": match.group(1).strip(),
                "target": match.group(2).strip(),
                "importance": importance_map.get(match.group(3), 50),
            }
        )
    return edges


def save_diagram_files(mermaid_code: str, url: str, page_content: dict[str, Any], output_path: str, model: str) -> bool:
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_file = Path(output_path)

        html_content = HTML_TEMPLATE.format(
            title=page_content.get("title", "Untitled"),
            url=url,
            timestamp=timestamp,
            model=model,
            mermaid_code=mermaid_code,
        )
        output_file.write_text(html_content, encoding="utf-8")
        print(f"[save] html: {output_file}")

        mmd_path = output_file.with_suffix(".mmd")
        mmd_path.write_text(mermaid_code, encoding="utf-8")
        if mermaid_code.strip() == "flowchart TD" or is_truncated_mermaid(mermaid_code):
            print(f"[save] mmd written with warning (possibly invalid): {mmd_path}")
        else:
            print(f"[save] mmd: {mmd_path}")

        json_path = output_file.with_suffix(".json")
        json_payload = {
            "edges": extract_edges_from_mermaid(mermaid_code),
            "generated_at": timestamp,
            "url": url,
            "title": page_content.get("title", ""),
        }
        json_path.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[save] json: {json_path}")
        return True
    except Exception as exc:
        print(f"[save] failed: {exc}")
        return False


def build_output_path(output_arg: str | None) -> str:
    if output_arg:
        return output_arg
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    return str(SITE_DIR / "website_diagram.html")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Mermaid diagram files from a website.")
    parser.add_argument("url", help="Target website URL")
    parser.add_argument("-o", "--output", default=None, help="Output HTML path")
    parser.add_argument("-m", "--model", default=OLLAMA_MODEL, help="Ollama model")
    parser.add_argument("-w", "--wait", type=int, default=WAIT_TIME, help="JS wait time in seconds")
    args = parser.parse_args()

    url = args.url if args.url.startswith("http") else f"https://{args.url}"
    output_path = build_output_path(args.output)

    print("=" * 70)
    print("Website diagram generator")
    print("=" * 70)
    print(f"url: {url}")
    print(f"model: {args.model}")
    print(f"wait: {args.wait}s")
    print(f"output: {output_path}")
    print("=" * 70)

    html_content = fetch_webpage(url, wait_time=args.wait)
    if not html_content:
        print("[main] failed to fetch source page")
        return 1

    page_content = extract_page_content(html_content)
    if not page_content:
        print("[main] extraction failed, falling back to minimal content")
        page_content = {
            "title": url,
            "meta_description": "",
            "text_preview": html_content[:1000],
            "data_items": [],
            "links": [],
            "headings": [],
            "has_real_data": False,
        }
    else:
        print(f"[main] title: {page_content['title']}")
        print(f"[main] data_items: {len(page_content.get('data_items', []))}")
        print(f"[main] links: {len(page_content.get('links', []))}")
        print(f"[main] headings: {len(page_content.get('headings', []))}")

    if not page_content.get("has_real_data", False):
        print("[main] no real content detected")
        print("[main] try a longer wait time: -w 30 or -w 60")
        return 1

    mermaid_code = generate_diagram_with_ollama(url, page_content, args.model)
    success = save_diagram_files(mermaid_code, url, page_content, output_path, args.model)
    if not success:
        return 1

    print("[main] done")
    print(f"[main] open: file:///{os.path.abspath(output_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
