#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹사이트 구조 분석 및 Mermaid 다이어그램 자동 생성 도구
Ollama AI를 사용하여 웹페이지를 분석하고 시각적 다이어그램을 생성합니다.
"""

import sys
import os
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import argparse
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# Ollama API 설정
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma3:4b")

# Selenium 설정
WAIT_TIME = 10  # 페이지 로딩 대기 시간 (초)
SCROLL_WAIT = 2  # 스크롤 후 대기 시간 (초)
DATA_LOAD_TIMEOUT = 100  # 데이터 로딩 최대 대기 시간 (초)

# HTML 템플릿
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - 웹사이트 구조 다이어그램</title>
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
        <h1>🌐 {title}</h1>
        <div class="meta-info">
            <div class="ai-badge">✨ Ollama AI로 자동 생성됨 ({model})</div>
            <div>생성 시간: {timestamp}</div>
        </div>
        
        <div class="url-info">
            <strong>📍 분석 웹사이트:</strong> <a href="{url}" target="_blank">{url}</a>
        </div>

        <div class="diagram-container">
            <div class="mermaid">
{mermaid_code}
            </div>
        </div>

        <div class="controls">
            <button class="btn" onclick="window.print()">🖨️ 인쇄하기</button>
            <button class="btn" onclick="location.reload()">🔄 새로고침</button>
        </div>

        <div class="footer">
            <p>이 다이어그램은 Ollama AI가 웹사이트 구조를 분석하여 자동으로 생성했습니다.</p>
            <p>Mermaid 다이어그램 엔진을 사용하여 렌더링됩니다.</p>
        </div>
    </div>

    <script>
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'default',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }}
        }});
    </script>
</body>
</html>
"""


def fetch_webpage(url, wait_time=WAIT_TIME):
    """웹페이지 HTML 가져오기 (Selenium 사용, JavaScript 실행 대기)"""
    driver = None
    try:
        print(f"🌐 웹페이지 가져오는 중: {url}")
        print(f"⏳ JavaScript 로딩을 위해 {wait_time}초 대기합니다...")
        
        # Chrome 옵션 설정
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')  # 헤드리스 모드
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 로그 비활성화
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_argument('--log-level=3')
        
        # WebDriver 초기화 (webdriver-manager 사용)
        print("🔧 ChromeDriver 설정 중...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(60)
        
        # 페이지 로드
        print("📥 페이지 로드 중...")
        driver.get(url)
        
        # JavaScript 실행 대기
        print(f'⏳ JavaScript 초기 로딩 대기 ({wait_time}초)...')
        time.sleep(wait_time)
        
        # 페이지 스크롤 (lazy loading 콘텐츠 로드)
        print('📜 페이지 스크롤하여 추가 콘텐츠 로드 중...')
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight/2);')
        time.sleep(SCROLL_WAIT)
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(SCROLL_WAIT)
        driver.execute_script('window.scrollTo(0, 0);')
        time.sleep(1)
        
        # "데이터 로딩 중..." 텍스트가 사라질 때까지 대기
        print('⏳ 데이터 로딩 완료 대기 중...')
        try:
            # "로딩 중..." 또는 "데이터 로딩 중..." 요소가 사라질 때까지 대기
            wait = WebDriverWait(driver, DATA_LOAD_TIMEOUT)
            
            # 로딩 텍스트를 포함하는 요소 찾기
            loading_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '로딩 중') or contains(text(), '데이터 로딩')]")
            
            if loading_elements:
                print(f'   찾은 로딩 요소: {len(loading_elements)}개')
                # 로딩 요소가 사라질 때까지 대기 (최대 60초)
                for i in range(DATA_LOAD_TIMEOUT):
                    time.sleep(1)
                    # 로딩 텍스트 재확인
                    remaining = driver.find_elements(By.XPATH, "//*[contains(text(), '로딩 중') or contains(text(), '데이터 로딩')]")
                    if not remaining:
                        print(f'✅ 데이터 로딩 완료! ({i+1}초 소요)')
                        break
                    if (i + 1) % 10 == 0:
                        print(f'   아직 로딩 중... ({i+1}초 경과)')
                else:
                    print('⚠️ 데이터 로딩 타임아웃 (100초 초과)')
            else:
                print('✅ 로딩 요소가 없거나 이미 로딩 완료')
            
            # 추가 안정화 대기
            time.sleep(3)
            
        except Exception as e:
            print(f'⚠️ 데이터 로딩 대기 중 예외 발생: {e}')
        
        # 최종 HTML 가져오기
        html_content = driver.page_source
        
        print(f"✅ 웹페이지 가져오기 성공 ({len(html_content)} 바이트)")
        
        return html_content
        
    except Exception as e:
        print(f"❌ 웹페이지 가져오기 실패: {e}")
        print(f"   에러 타입: {type(e).__name__}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass  # 종료 시 발생하는 에러 무시


def extract_page_content(html_content):
    """BeautifulSoup로 주요 내용 추출 (실제 데이터 콘텐츠 위주)"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # RSS 피드 여부 확인 (channel/item 구조)
        is_rss = bool(soup.find('rss')) or bool(soup.find('channel'))
        if is_rss:
            channel = soup.find('channel')
            title = channel.find('title').get_text(strip=True) if channel and channel.find('title') else "제목 없음"
            meta_desc = channel.find('description').get_text(strip=True) if channel and channel.find('description') else ""
            items = channel.find_all('item') if channel else []
            data_items = []
            links = []
            headings = []
            for item in items:
                item_title = item.find('title').get_text(strip=True) if item.find('title') else ""
                item_desc = item.find('description').get_text(strip=True) if item.find('description') else ""
                item_link = item.find('link').get_text(strip=True) if item.find('link') else ""
                # 주요 데이터는 제목+설명
                if item_title:
                    data_items.append(item_title)
                if item_desc:
                    data_items.append(item_desc)
                if item_link:
                    links.append(item_link)
            text_content = '\n'.join(data_items)
            print(f"   📦 추출된 RSS 데이터 아이템 수: {len(data_items)}")
            print(f"   📎 추출된 RSS 링크 수: {len(links)}")
            return {
                'title': title,
                'meta_description': meta_desc,
                'text_preview': text_content[:2000],
                'data_items': data_items,
                'links': links,
                'headings': headings,
                'has_real_data': len(data_items) > 0 or len(links) > 5
            }
        # 기존 HTML 파싱 로직 (변경 없음)
        # ...기존 코드...
        # 스크립트, 스타일 태그 제거
        for script in soup(["script", "style"]):
            script.decompose()
        # 제목
        title = soup.title.string if soup.title else "제목 없음"
        # 메타 설명
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag and meta_tag.get("content"):
            meta_desc = meta_tag["content"]
        # 주요 텍스트 추출 (전체, 나중에 필터링)
        text_content = soup.get_text(separator=' ', strip=True)
        text_content = ' '.join(text_content.split())
        # 실제 데이터 콘텐츠 추출 (뉴스 아이템, 카드 등)
        data_items = []
        possible_selectors = [
            {'class': ['news-item', 'article', 'post', 'item', 'card']},
            {'attrs': {'data-item': True}},
            {'attrs': {'data-article': True}},
        ]
        for selector_dict in possible_selectors:
            if 'class' in selector_dict:
                for class_name in selector_dict['class']:
                    items = soup.find_all(class_=lambda x: x and class_name in x if x else False)
                    for item in items[:30]:
                        item_text = item.get_text(strip=True)
                        if item_text and len(item_text) > 10 and '로딩' not in item_text:
                            data_items.append(item_text[:200])
            elif 'attrs' in selector_dict:
                items = soup.find_all(attrs=selector_dict['attrs'])
                for item in items[:30]:
                    item_text = item.get_text(strip=True)
                    if item_text and len(item_text) > 10 and '로딩' not in item_text:
                        data_items.append(item_text[:200])
        data_items = list(dict.fromkeys(data_items))

        # 최신 날짜순 정렬 (내림차순)
        import re
        from datetime import datetime
        def extract_date(text):
            # YYYY-MM-DD, YYYY.MM.DD, YYYY/MM/DD, YYYYMMDD 등 다양한 날짜 패턴 지원
            patterns = [
                r'(20\d{2}[.-/]\d{1,2}[.-/]\d{1,2})', # 2024-03-11, 2024.03.11, 2024/03/11
                r'(20\d{2}\d{2}\d{2})',                # 20240311
            ]
            for pat in patterns:
                m = re.search(pat, text)
                if m:
                    date_str = m.group(1)
                    # 정규화
                    date_str = date_str.replace('.', '-').replace('/', '-').replace(' ', '')
                    try:
                        if '-' in date_str:
                            return datetime.strptime(date_str, '%Y-%m-%d')
                        else:
                            return datetime.strptime(date_str, '%Y%m%d')
                    except Exception:
                        continue
            return None

        data_items = sorted(
            data_items,
            key=lambda x: extract_date(x) if extract_date(x) else datetime(1900,1,1),
            reverse=True
        )
        print(f"   📦 추출된 데이터 아이템 수: {len(data_items)}")
        links = []
        seen_hrefs = set()
        for a in soup.find_all('a', href=True):
            link_text = a.get_text(strip=True)
            link_href = a['href']
            excluded_keywords = ['카테고리', '메뉴', '필터', '정렬', '초기화', '전체', '정치', '경제', '사회', '문화']
            is_excluded = any(keyword in link_text for keyword in excluded_keywords)
            if link_href not in seen_hrefs and link_text and len(link_text) > 5 and not is_excluded:
                if not link_href.startswith(('#', 'javascript:')):
                    links.append(f"{link_text} → {link_href}")
                    seen_hrefs.add(link_href)
            if len(links) >= 50:
                break
        print(f"   📎 추출된 콘텐츠 링크 수: {len(links)}")
        headings = []
        for h in soup.find_all(['h1', 'h2', 'h3', 'h4'])[:30]:
            heading_text = h.get_text(strip=True)
            if heading_text and len(heading_text) > 0:
                headings.append(f"{h.name}: {heading_text}")
        print(f"   📋 추출된 헤딩 수: {len(headings)}")
        return {
            'title': title,
            'meta_description': meta_desc,
            'text_preview': text_content[:2000],
            'data_items': data_items,
            'links': links,
            'headings': headings,
            'has_real_data': len(data_items) > 0 or len(links) > 5
        }
    except Exception as e:
        print(f"⚠️ 내용 추출 중 오류: {e}")
        return None


def generate_diagram_with_ollama(url, page_content, model=OLLAMA_MODEL):
    """Ollama AI를 사용하여 Mermaid 다이어그램 코드 생성 (실제 데이터 기반)"""
    try:
        print(f"\n🤖 Ollama AI로 다이어그램 생성 중... (모델: {model})")
        
        # 실제 데이터 아이템 정보
        data_items_info = '\n'.join(page_content['data_items'][:15]) if page_content.get('data_items') else "데이터 없음"
        
        # 모든 데이터 아이템 사용, 출력 제한 해제, 마지막 줄까지 반드시 출력하도록 명시
        # 데이터 아이템 30개로 제한 (출력 잘림 방지)
        limited_items = page_content.get('data_items', [])[:30]
        limited_items_info = '\n'.join(limited_items) if limited_items else "데이터 없음"
        prompt = f"""다음은 웹사이트 '{url}'의 실제 데이터입니다. 아래 항목을 노드로 하는 Mermaid flowchart TD 코드를 생성하세요.\n- 노드 간 관계는 자유롭게 연결하고, 한글 레이블을 사용하세요.\n- 각 에지(화살표)에는 중요도를 [중요], [보통], [낮음] 중 하나로 표기하세요. 예시: A[뉴스] -> B[주가][중요]\n- Mermaid 코드에서 반드시 'A -> B' 형식(단일 하이픈)만 사용하세요. (예: A -> B, C -> D)\n- 부가 설명, 주석, 태그 없이 코드만 출력하세요.\n- 반드시 마지막 줄까지(마지막 classDef, class 등 포함) 모두 출력하세요.\n- 코드가 길어도 중간에 멈추지 말고 끝까지 출력하세요.\n\n{limited_items_info}"""

        # Ollama API 호출
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 2000  # 최대한 긴 출력 허용
            }
        }
        
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()

        # Ollama API 원본 응답 전체 출력 (디버깅용)
        print("\n[Ollama API 원본 응답]")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        mermaid_code = result.get('response', '').strip()

        # Mermaid 코드 정리 (```mermaid 태그 제거)
        if '```mermaid' in mermaid_code:
            mermaid_code = mermaid_code.split('```mermaid')[1].split('```')[0].strip()
        elif '```' in mermaid_code:
            mermaid_code = mermaid_code.split('```')[1].split('```')[0].strip()

        # flowchart로 시작하지 않으면 추가
        if not mermaid_code.startswith('flowchart') and not mermaid_code.startswith('graph'):
            mermaid_code = "flowchart TD\n" + mermaid_code


        # 노드 라벨 불필요 접두어 및 불필요 텍스트 제거
        patterns_to_remove = [
            r'카테고리\s*:\s*일반',
            r'유형\s*:?\s*텍스트',
            r'유형\s*:?\s*',
            r'텍스트일반\s*:?\s*',
            r'조회수\s*:?\s*\d+',
            r'일반 카테고리',
            r'카테고리',
            r'유형',
            r'텍스트',
            r'조회수'
        ]
        for pat in patterns_to_remove:
            mermaid_code = re.sub(pat, '', mermaid_code)



        # 중복 에지/노드 제거 + 모든 에지 'A -> B' 형태로 변환 및 중요도 표기 보정
        def dedup_and_fix_edges_and_importance(code):
            lines = code.split('\n')
            seen = set()
            fixed_lines = []
            # 다양한 Mermaid 에지 패턴 허용 (--> , --o->, --x-> 등)
            edge_pattern = re.compile(r'^(\s*[^\s-][^\n]*?)\s*[-]+[a-zA-Z]*>\s*(.*)$')
            importance_pattern = re.compile(r'\[(중요|보통|낮음)\]$')
            for line in lines:
                m = edge_pattern.match(line)
                if m:
                    left = m.group(1).strip()
                    right = m.group(2).strip()
                    # 중요도 추출 또는 기본값 부여
                    if right:
                        # 오른쪽 노드에 중요도 표기 없으면 [보통] 추가
                        if not importance_pattern.search(right):
                            right = right.rstrip(';') + ' [보통]'
                    else:
                        right = '"" [보통]'
                    edge = (left, right)
                    line_str = f"{left} -> {right}"
                    if edge not in seen:
                        fixed_lines.append(line_str)
                        seen.add(edge)
                else:
                    # 노드 정의/기타 라인도 중복 방지
                    if line.strip() and line not in seen:
                        fixed_lines.append(line)
                        seen.add(line)
            return '\n'.join(fixed_lines)

        mermaid_code = dedup_and_fix_edges_and_importance(mermaid_code)

        print(f"✅ 다이어그램 생성 완료 ({len(mermaid_code)} 바이트)")
        print(f"\n【생성된 Mermaid 코드 전체】\n{mermaid_code}\n")

        return mermaid_code
        
    except Exception as e:
        print(f"❌ Ollama AI 다이어그램 생성 실패: {e}")
        # 기본 다이어그램 반환
        return f"""flowchart TD
    A[{page_content['title']}] --> B[메인 페이지]
    A --> C[콘텐츠 영역]
    B --> D[네비게이션]
    C --> E[정보 표시]
    
    classDef mainStyle fill:#667eea,stroke:#333,color:#fff
    class A mainStyle"""


def save_diagram_files(mermaid_code, url, page_content, output_path, model=OLLAMA_MODEL):
    """생성된 Mermaid 다이어그램을 HTML과 .mmd 파일로 저장"""
    import re
    def get_mermaid_truncation_prompt(mermaid_code: str) -> str:
        """
        Ollama AI에게 Mermaid 코드의 정상/잘림 여부를 판별하도록 요청하는 프롬프트를 반환합니다.
        """
        return f"""아래는 Mermaid 다이어그램 코드입니다.\n\n{mermaid_code}\n\n이 코드가 중간에 잘려서 불완전하게 생성된 것인지, 아니면 정상적으로 끝까지 생성된 것인지 판별해 주세요.\n\n판별 기준:\n- flowchart 또는 graph로 시작하는지\n- 노드(대괄호 [ ] 포함) 2개 이상, 에지(--> 포함) 1개 이상인지\n- 마지막 10줄 이내에 classDef 또는 class 문이 있는지\n- 중간에 대괄호 [가 열리고 ]로 닫히지 않은 라인이 있는지\n\n결과를 아래 형식으로 답변해 주세요.\n1. 잘림 여부: (예/아니오)\n2. 사유: (간단한 이유)\n"""

    # 간단한 코드 기반 잘림 감지 함수 추가
    def is_truncated_mermaid(mermaid_code: str) -> bool:
        """
        Mermaid 코드가 비었거나, 노드/에지 개수가 너무 적거나, 괄호 불일치 등 명백한 잘림/불완전 여부만 간단히 감지합니다.
        '->' 형식과 중요도([중요], [보통], [낮음]) 표기도 인식합니다.
        """
        code = mermaid_code.strip()
        if not code or code == 'flowchart TD':
            return True
        # 노드(대괄호 [ ]) 2개 미만, 에지(->) 1개 미만
        node_count = code.count('[')
        edge_count = code.count('->')
        # 중요도 표기 포함 여부
        importance_count = sum(code.count(f'[{imp}]') for imp in ['중요', '보통', '낮음'])
        if node_count < 2 or edge_count < 1:
            return True
        # 대괄호 불일치
        if code.count('[') != code.count(']'):
            return True
        # 중요도 표기가 하나도 없으면 잘림으로 간주
        if importance_count < 1:
            return True
        return False

    try:
        timestamp = datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")

        # HTML 파일 저장
        html_content = HTML_TEMPLATE.format(
            title=page_content['title'],
            url=url,
            timestamp=timestamp,
            model=model,
            mermaid_code=mermaid_code
        )

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\n✅ HTML 파일 저장 완료: {output_path}")

        # .mmd 파일 저장 (다이어그램 코드만)
        mmd_path = output_path.replace('.html', '.mmd')
        # Mermaid 코드가 잘렸거나 불완전하면 기존 파일 유지
        if mermaid_code.strip() == 'flowchart TD' or is_truncated_mermaid(mermaid_code):
            print(f"⚠️ 새 다이어그램이 비거나 잘려서 기존 .mmd 파일을 유지합니다: {mmd_path}")
        else:
            with open(mmd_path, 'w', encoding='utf-8') as f:
                f.write(mermaid_code)
            print(f"✅ Mermaid 파일 저장 완료: {mmd_path}")

        # .json 파일 저장 (에지와 중요도: 1~100)
        json_path = output_path.replace('.html', '.json')
        edges = []
        # Mermaid 코드에서 에지 추출: A -> B [중요] (graph/flowchart 모두 지원, 다양한 화살표)
        edge_pattern = re.compile(r'^(\s*[^\s-][^\n]*?)\s*[-]+[a-zA-Z]*>\s*([^\[]+?)\s*\[(중요|보통|낮음)\]', re.UNICODE)
        importance_map = {'중요': 100, '보통': 50, '낮음': 1}
        for line in mermaid_code.split('\n'):
            m = edge_pattern.match(line)
            if m:
                source = m.group(1).strip()
                target = m.group(2).strip()
                importance_label = m.group(3)
                importance = importance_map.get(importance_label, 50)
                edges.append({
                    'source': source,
                    'target': target,
                    'importance': importance
                })
        json_obj = {
            'edges': edges,
            'generated_at': timestamp,
            'url': url,
            'title': page_content.get('title', ''),
        }
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_obj, f, ensure_ascii=False, indent=2)
            print(f"✅ JSON 파일 저장 완료: {json_path}")
        except Exception as je:
            print(f"❌ JSON 파일 저장 실패: {je}")

        return True

    except Exception as e:
        print(f"❌ 파일 저장 실패: {e}")
        return False


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description='웹사이트 구조를 분석하고 Mermaid 다이어그램 HTML을 생성합니다.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python generate_website_diagram.py https://참소식.com
  python generate_website_diagram.py https://example.com -o diagram.html
  python generate_website_diagram.py https://example.com -m qwen2.5:7b
  python generate_website_diagram.py https://example.com -w 15  # 15초 대기
        """
    )
    
    parser.add_argument('url', help='분석할 웹사이트 URL')
    parser.add_argument('-o', '--output', 
                        help='출력 HTML 파일 경로 (기본: website_diagram_YYYYMMDD_HHMMSS.html)',
                        default=None)
    parser.add_argument('-m', '--model',
                        help=f'사용할 Ollama 모델 (기본: {OLLAMA_MODEL})',
                        default=OLLAMA_MODEL)
    parser.add_argument('-w', '--wait',
                        help=f'JavaScript 로딩 대기 시간 (초, 기본: {WAIT_TIME})',
                        type=int,
                        default=WAIT_TIME)
    
    args = parser.parse_args()

    # 강제로 gemma3:4b 사용
    args.model = "gemma3:4b"

    # URL 정규화
    url = args.url
    if not url.startswith('http'):
        url = 'https://' + url

    # 출력 파일명 설정
    if args.output:
        output_path = args.output
    else:
        # 고정된 경로 설정
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, 'web', 'public', '한국인터넷.한국', '참소식.com')
        output_path = os.path.join(output_dir, 'website_diagram.html')
        
        # 디렉토리가 없으면 생성
        os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 70)
    print("🌐 웹사이트 구조 다이어그램 자동 생성 도구")
    print("=" * 70)
    print(f"📍 대상 URL: {url}")
    print(f"🤖 AI 모델: {args.model}")
    print(f"⏳ 로딩 대기: {args.wait}초 (JavaScript 실행 대기)")
    print(f"💾 출력 파일: {output_path}")
    print("=" * 70)
    
    # 1단계: 웹페이지 가져오기
    html_content = fetch_webpage(url, wait_time=args.wait)
    if not html_content:
        print("\n❌ 웹페이지를 가져올 수 없어 종료합니다.")
        return 1
    
    # 2단계: 페이지 내용 추출
    print("\n📊 페이지 내용 분석 중...")
    page_content = extract_page_content(html_content)
    if not page_content:
        print("⚠️ 내용 추출 실패, 기본 정보로 진행합니다.")
        page_content = {
            'title': url,
            'meta_description': '',
            'text_preview': html_content[:1000],
            'data_items': [],
            'links': [],
            'headings': [],
            'has_real_data': False
        }
    else:
        print(f"✅ 페이지 분석 완료")
        print(f"   - 제목: {page_content['title']}")
        print(f"   - 데이터 아이템: {len(page_content.get('data_items', []))}개")
        print(f"   - 콘텐츠 링크: {len(page_content['links'])}개")
        print(f"   - 헤딩: {len(page_content['headings'])}개")
    
    # 실제 데이터가 있는지 확인
    if not page_content.get('has_real_data', False):
        print("\n" + "=" * 70)
        print("❌ 오류: 실제 데이터 콘텐츠를 찾을 수 없습니다!")
        print("=" * 70)
        print("\n웹사이트에 데이터가 로드되지 않았거나,")
        print("데이터 로딩이 완료되지 않았습니다.")
        print("\n해결 방법:")
        print("  1. 대기 시간을 늘려보세요: -w 30 또는 -w 60")
        print("  2. 브라우저에서 직접 확인해보세요: {}".format(url))
        print("  3. 웹사이트가 실제로 데이터를 표시하는지 확인하세요")
        print("\n다이어그램 생성을 중단합니다.")
        print("=" * 70)
        return 1
    
    # 3단계: Ollama AI로 다이어그램 생성
    mermaid_code = generate_diagram_with_ollama(url, page_content, args.model)
    
    # 4단계: HTML과 .mmd 파일 저장
    print("\n💾 다이어그램 파일 생성 중...")
    success = save_diagram_files(mermaid_code, url, page_content, output_path, args.model)
    
    if success:
        print("\n" + "=" * 70)
        print("✨ 다이어그램 생성 완료!")
        print("=" * 70)
        print(f"📁 파일 위치: {os.path.abspath(output_path)}")
        print(f"🌐 브라우저로 열기: file:///{os.path.abspath(output_path)}")
        print("=" * 70)
        return 0
    else:
        print("\n❌ HTML 파일 생성에 실패했습니다.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
