def google_search_and_extract(query, driver, wait_time=10):
    """
    구글 검색 후 첫 번째 결과 페이지의 주요 텍스트를 추출
    """
    from selenium.webdriver.common.keys import Keys
    import re
    search_url = f'https://www.google.com/search?q={query}'
    driver.get(search_url)
    time.sleep(2)
    # 첫 번째 검색 결과 클릭
    try:
        first_result = driver.find_element(By.CSS_SELECTOR, 'a h3')
        first_result.find_element(By.XPATH, '..').click()
    except Exception:
        return "(구글 검색 결과를 찾을 수 없음)"
    time.sleep(wait_time)
    try:
        body_elem = driver.find_element(By.TAG_NAME, 'body')
        text = body_elem.text
        # 너무 길면 앞부분만
        return text[:2000]
    except Exception:
        return "(구글 검색 페이지 텍스트 추출 실패)"
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
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:120b-cloud")

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
    driver = None
    try:
        print(f"🌐 웹페이지 가져오는 중: {url}")
        print(f"⏳ JavaScript 로딩을 위해 {wait_time}초 대기합니다...")
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        chrome_options.add_argument('--log-level=3')
        print("🔧 ChromeDriver 설정 중...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(60)
        print("📥 페이지 로드 중...")
        driver.get(url)
        print(f'⏳ JavaScript 초기 로딩 대기 ({wait_time}초)...')
        time.sleep(wait_time)
        print('📜 페이지 스크롤하여 추가 콘텐츠 로드 중...')
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight/2);')
        time.sleep(SCROLL_WAIT)
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(SCROLL_WAIT)
        driver.execute_script('window.scrollTo(0, 0);')
        time.sleep(1)
        print('⏳ 데이터 로딩 완료 대기 중...')
        try:
            wait = WebDriverWait(driver, DATA_LOAD_TIMEOUT)
            loading_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '로딩 중') or contains(text(), '데이터 로딩')]")
            if loading_elements:
                print(f'   찾은 로딩 요소: {len(loading_elements)}개')
                for i in range(DATA_LOAD_TIMEOUT):
                    time.sleep(1)
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
            time.sleep(3)
        except Exception as e:
            print(f'⚠️ 데이터 로딩 대기 중 예외 발생: {e}')
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
                pass

def extract_page_content(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
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
                if item_title:
                    data_items.append(item_title)
                if item_desc:
                    data_items.append(item_desc)
                if item_link:
                    links.append(item_link)
            text_content = '\n'.join(data_items)
            return {
                'title': title,
                'meta_description': meta_desc,
                'text_preview': text_content[:2000],
                'data_items': data_items,
                'links': links,
                'headings': headings,
                'has_real_data': len(data_items) > 0 or len(links) > 5
            }
        for script in soup(["script", "style"]):
            script.decompose()
        title = soup.title.string if soup.title else "제목 없음"
        meta_desc = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag and meta_tag.get("content"):
            meta_desc = meta_tag["content"]
        text_content = soup.get_text(separator=' ', strip=True)
        text_content = ' '.join(text_content.split())
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
        import re
        from datetime import datetime
        def extract_date(text):
            patterns = [
                r'(20\d{2}[.-/]\d{1,2}[.-/]\d{1,2})',
                r'(20\d{2}\d{2}\d{2})',
            ]
            for pat in patterns:
                m = re.search(pat, text)
                if m:
                    date_str = m.group(1)
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
        headings = []
        for h in soup.find_all(['h1', 'h2', 'h3', 'h4'])[:30]:
            heading_text = h.get_text(strip=True)
            if heading_text and len(heading_text) > 0:
                headings.append(f"{h.name}: {heading_text}")
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
    try:
        print(f"\n🤖 Ollama AI로 다이어그램 생성 중... (모델: {model})")
        price_nodes = []
        explanation_nodes = []
        google_texts = {}
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            finance_json_path = os.path.join(base_dir, 'web', 'public', '한국인터넷.한국', '참소식.com', 'realtime_finance_data.json')
            if os.path.exists(finance_json_path):
                with open(finance_json_path, 'r', encoding='utf-8') as f:
                    finance_json = json.load(f)
                # 크롬 드라이버 준비
                chrome_options = Options()
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                for k, v in finance_json.items():
                    if not k.endswith('_ollama'):
                        price_nodes.append(f"{k}: {v}")
                        # 지표별 구글 검색 및 텍스트 추출
                        google_query = f"{k} 지수 실시간" if '코스피' in k or 'KOSPI' in k or '지수' in k else f"{k} 실시간 시세"
                        google_text = google_search_and_extract(google_query, driver, wait_time=10)
                        google_texts[k] = google_text
                    if k.endswith('_ollama'):
                        try:
                            if isinstance(v, str) and v.strip().startswith('{'):
                                parsed = json.loads(v)
                                if 'value_krw' in parsed:
                                    price_nodes.append(f"{k.replace('_ollama','')}_가격: {parsed['value_krw']}")
                                if 'explanation' in parsed:
                                    explanation_nodes.append(f"{k.replace('_ollama','')}_설명: {parsed['explanation']}")
                            else:
                                explanation_nodes.append(f"{k.replace('_ollama','')}_설명: {v.strip()}")
                        except Exception:
                            explanation_nodes.append(f"{k.replace('_ollama','')}_설명: {v}")
                driver.quit()
        except Exception as e:
            print(f"⚠️ 금융 데이터 JSON 파싱/구글 검색 오류: {e}")
        # 항상 포함할 주요 지표 키워드 목록
        always_include = ['KOSPI', 'KOSDAQ', '코스피', '코스닥']
        always_items = []
        rest_items = []
        for item in price_nodes + explanation_nodes:
            # item이 예: 'KOSPI: 1234' 또는 'KOSPI_설명: ...' 형태이므로 키워드 포함 여부로 판단
            if any(key in item for key in always_include):
                always_items.append(item)
            else:
                rest_items.append(item)
        # 중복 제거(항상 포함 항목이 rest에도 있을 수 있음)
        always_items = list(dict.fromkeys(always_items))
        rest_items = [x for x in rest_items if x not in always_items]
        merged_items = always_items + rest_items
        merged_items = merged_items[:12]  # 최대 12개 유지
        import_path = os.path.join(os.path.dirname(__file__), 'diagram_prompt_template.txt')
        try:
            with open(import_path, 'r', encoding='utf-8') as pf:
                prompt_template = pf.read()
        except Exception as e:
            print(f"⚠️ 프롬프트 템플릿 로드 오류: {e}")
            prompt_template = None
        prompt = None
        if prompt_template:
            merged_items_info = '\n'.join(merged_items)
            google_info_lines = []
            for k, v in google_texts.items():
                v_short = v[:100].replace('\n', ' ')
                google_info_lines.append(f"[구글검색] {k}: {v_short} ...")
            google_info = '\n'.join(google_info_lines)
            prompt = prompt_template.replace('{merged_items_info}', merged_items_info + '\n' + google_info)
            prompt = prompt.replace('{url}', url)
            limited_items = page_content.get('data_items', [])[:12]
            limited_items_info = '\n'.join(limited_items) if limited_items else "데이터 없음"
            prompt = prompt.replace('{limited_items_info}', limited_items_info)
        if not prompt:
            raise RuntimeError('프롬프트 템플릿을 찾을 수 없습니다. tools/diagram_prompt_template.txt을 확인하세요.')
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 10000
            }
        }
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        print("\n[Ollama API 원본 응답]")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        mermaid_code = result.get('response', '').strip()
        if '```mermaid' in mermaid_code:
            mermaid_code = mermaid_code.split('```mermaid')[1].split('```')[0].strip()
        elif '```' in mermaid_code:
            mermaid_code = mermaid_code.split('```')[1].split('```')[0].strip()
        if not mermaid_code.startswith('flowchart') and not mermaid_code.startswith('graph'):
            mermaid_code = "flowchart TD\n" + mermaid_code
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
        return mermaid_code
    except Exception as e:
        print(f"❌ Ollama AI 다이어그램 생성 실패: {e}")
        return (
            f"flowchart TD\n"
            f"    A[{page_content['title']}] --> B[메인 페이지]\n"
            f"    A --> C[콘텐츠 영역]\n"
            f"    B --> D[네비게이션]\n"
            f"    C --> E[정보 표시]\n"
            f"    classDef mainStyle fill:#667eea,stroke:#333,color:#fff\n"
            f"    class A mainStyle"
        )

def save_diagram_files(mermaid_code, url, page_content, output_path, model=OLLAMA_MODEL):
    import re
    def is_truncated_mermaid(mermaid_code: str) -> bool:
        code = mermaid_code.strip()
        if not code or code == 'flowchart TD':
            return True
        node_count = code.count('[')
        edge_count = code.count('->')
        importance_count = sum(code.count(f'[{imp}]') for imp in ['중요', '보통', '낮음'])
        if node_count < 2 or edge_count < 1:
            return True
        if code.count('[') != code.count(']'):
            return True
        if importance_count < 1:
            return True
        return False
    try:
        timestamp = datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")
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
        mmd_path = output_path.replace('.html', '.mmd')
        if mermaid_code.strip() == 'flowchart TD' or is_truncated_mermaid(mermaid_code):
            print(f"⚠️ 새 다이어그램이 비거나 잘려서 기존 .mmd 파일을 유지합니다: {mmd_path}")
        else:
            with open(mmd_path, 'w', encoding='utf-8') as f:
                f.write(mermaid_code)
            print(f"✅ Mermaid 파일 저장 완료: {mmd_path}")
        json_path = output_path.replace('.html', '.json')
        edges = []
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
    parser = argparse.ArgumentParser(
        description='웹사이트 구조를 분석하고 Mermaid 다이어그램 HTML을 생성합니다.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "사용 예시:\n"
            "  python generate_website_diagram.py https://참소식.com\n"
            "  python generate_website_diagram.py https://example.com -o diagram.html\n"
            "  python generate_website_diagram.py https://example.com -m qwen2.5:7b\n"
            "  python generate_website_diagram.py https://example.com -w 15  # 15초 대기\n"
        )
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
    args.model = "gpt-oss:120b-cloud"
    url = args.url
    if not url.startswith('http'):
        url = 'https://' + url
    if args.output:
        output_path = args.output
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(base_dir, 'web', 'public', '한국인터넷.한국', '참소식.com')
        output_path = os.path.join(output_dir, 'website_diagram.html')
        os.makedirs(output_dir, exist_ok=True)
    print("=" * 70)
    print("🌐 웹사이트 구조 다이어그램 자동 생성 도구")
    print("=" * 70)
    print(f"📍 대상 URL: {url}")
    print(f"🤖 AI 모델: {args.model}")
    print(f"⏳ 로딩 대기: {args.wait}초 (JavaScript 실행 대기)")
    print(f"💾 출력 파일: {output_path}")
    print("=" * 70)
    html_content = fetch_webpage(url, wait_time=args.wait)
    if not html_content:
        print("\n❌ 웹페이지를 가져올 수 없어 종료합니다.")
        return 1
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
    if not page_content.get('has_real_data', False):
        print("\n" + "=" * 70)
        print("❌ 오류: 실제 데이터 콘텐츠를 찾을 수 없습니다!")
        print("=" * 70)
        print("\n웹사이트에 데이터가 로드되지 않았거나,")
        print("데이터 로딩이 완료되지 않았습니다.")
        print("\n해결 방법:")
        print("  1. 대기 시간을 늘려보세요: -w 30 또는 -w 60")
        print(f"  2. 브라우저에서 직접 확인해보세요: {url}")
        print("  3. 웹사이트가 실제로 데이터를 표시하는지 확인하세요")
        print("\n다이어그램 생성을 중단합니다.")
        print("=" * 70)
        return 1
    mermaid_code = generate_diagram_with_ollama(url, page_content, args.model)
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
