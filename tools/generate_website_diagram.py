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
        
        # 다양한 선택자로 콘텐츠 아이템 찾기
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
                            data_items.append(item_text[:200])  # 각 아이템 최대 200자
            elif 'attrs' in selector_dict:
                items = soup.find_all(attrs=selector_dict['attrs'])
                for item in items[:30]:
                    item_text = item.get_text(strip=True)
                    if item_text and len(item_text) > 10 and '로딩' not in item_text:
                        data_items.append(item_text[:200])
        
        # 중복 제거
        data_items = list(dict.fromkeys(data_items))
        print(f"   📦 추출된 데이터 아이템 수: {len(data_items)}")
        
        # 링크 추출 (데이터 콘텐츠 링크만)
        links = []
        seen_hrefs = set()
        for a in soup.find_all('a', href=True):
            link_text = a.get_text(strip=True)
            link_href = a['href']
            
            # 카테고리/메뉴가 아닌 실제 콘텐츠 링크만 추출
            excluded_keywords = ['카테고리', '메뉴', '필터', '정렬', '초기화', '전체', '정치', '경제', '사회', '문화']
            is_excluded = any(keyword in link_text for keyword in excluded_keywords)
            
            if link_href not in seen_hrefs and link_text and len(link_text) > 5 and not is_excluded:
                if not link_href.startswith(('#', 'javascript:')):
                    links.append(f"{link_text} → {link_href}")
                    seen_hrefs.add(link_href)
                    
            if len(links) >= 50:
                break
        
        print(f"   📎 추출된 콘텐츠 링크 수: {len(links)}")
        
        # 주요 헤딩
        headings = []
        for h in soup.find_all(['h1', 'h2', 'h3', 'h4'])[:30]:  # 최대 30개
            heading_text = h.get_text(strip=True)
            if heading_text and len(heading_text) > 0:
                headings.append(f"{h.name}: {heading_text}")
        
        print(f"   📋 추출된 헤딩 수: {len(headings)}")
        
        return {
            'title': title,
            'meta_description': meta_desc,
            'text_preview': text_content[:2000],  # 2000자로 제한
            'data_items': data_items,  # 실제 데이터 아이템
            'links': links,
            'headings': headings,
            'has_real_data': len(data_items) > 0 or len(links) > 5  # 실제 데이터 존재 여부
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
        
        # 프롬프트 생성 (실제 콘텐츠만, 링크/메타 정보 제외)
        prompt = f"""다음은 웹사이트 '{url}'의 실제 콘텐츠 데이터입니다:

【웹사이트 제목】
{page_content['title']}

【실제 데이터 아이템 ({len(page_content.get('data_items', []))}개)】
{data_items_info}

---

위 정보를 바탕으로 이 웹사이트의 **실제 콘텐츠만**을 보여주는 **Mermaid 플로우차트 다이어그램 코드**를 생성해주세요.

**중요 요구사항:**
1. 반드시 Mermaid flowchart 문법만 사용 (```mermaid 태그 없이, 코드만)
2. flowchart TD 또는 flowchart LR로 시작
3. **실제 데이터의 제목과 내용만 노드로 표현** (구조적 노드 제외)
4. 실제 콘텐츠 간의 주제 관계를 화살표로 표현
5. 한글 레이블 사용 (노드 ID는 영문)
6. **최소 12개 이상의 노드 포함** (실제 데이터 아이템 기반)
7. 스타일링 추가 (classDef, class 사용)
8. **마지막에 AI 분석 노드 추가**: 트렌드 분석, 예상/예측, 결론, 인사이트
9. 부가 설명이나 주석 없이 Mermaid 코드만 출력

**반드시 제외해야 할 것들:**
- "홈페이지", "메인", "최신 뉴스", "뉴스 섹션" 같은 일반적 구조 노드
- "링크", "검색", "다운로드", "URL" 같은 메타 정보
- "조회수 TOP", "인기 검색어" 같은 통계 정보
- "네이버", "구글", "드라이브" 같은 외부 서비스
- "정치", "경제", "사회" 같은 단순 카테고리명

**반드시 포함해야 할 것들:**
- 실제 뉴스/게시물의 구체적인 제목
- 데이터의 실제 내용과 세부사항
- 콘텐츠 간의 주제 연관성
- **마지막 섹션: AI 분석 결과 (트렌드, 예측, 결론, 인사이트)**

**출력 형식 (예시):**
flowchart TD
    A[트럼프 이란 공습 작전 발표] --> B[헤그세스 장관 암살 시도]
    C[미국 이란 관계 악화] --> A
    D[중동 긴장 고조] --> C
    E[이란 핵 시설 타격] --> F[국제 원유 가격 급등]
    
    %% AI 분석 섹션
    G[AI 트렌드 분석: 중동 정세 불안 심화] --> H[예측: 원유 공급 차질 우려]
    H --> I[결론: 국제 경제 영향 불가피]
    
    classDef newsStyle fill:#e3f2fd,stroke:#1976d2,color:#000
    classDef aiStyle fill:#fff3e0,stroke:#f57c00,color:#000,stroke-width:3px
    class A,B,C,D,E,F newsStyle
    class G,H,I aiStyle

지금 바로 Mermaid 다이어그램 코드를 생성하세요:"""

        # Ollama API 호출
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 1500  # 더 긴 출력 허용
            }
        }
        
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        mermaid_code = result.get('response', '').strip()
        
        # Mermaid 코드 정리 (```mermaid 태그 제거)
        if '```mermaid' in mermaid_code:
            mermaid_code = mermaid_code.split('```mermaid')[1].split('```')[0].strip()
        elif '```' in mermaid_code:
            mermaid_code = mermaid_code.split('```')[1].split('```')[0].strip()
        
        # flowchart로 시작하지 않으면 추가
        if not mermaid_code.startswith('flowchart') and not mermaid_code.startswith('graph'):
            mermaid_code = "flowchart TD\n" + mermaid_code

        # 노드 라벨 불필요 접두어 제거
        mermaid_code = re.sub(r'텍스트일반\s*:\s*', '', mermaid_code)
        
        print(f"✅ 다이어그램 생성 완료 ({len(mermaid_code)} 바이트)")
        print(f"\n【생성된 Mermaid 코드】\n{mermaid_code[:300]}...\n")
        
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
        with open(mmd_path, 'w', encoding='utf-8') as f:
            f.write(mermaid_code)
        
        print(f"✅ Mermaid 파일 저장 완료: {mmd_path}")
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
