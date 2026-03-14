# Chainlink 데이터 추출 및 연동 자동화

# 이 스크립트는 크롬 브라우저로 https://참소식.com 사이트를 열고, Ollama AI를 통해 데이터를 추출하여 JSON 파일로 저장합니다. Chainlink 연동을 위해 AI 프롬프트는 별도의 파일로 분리되어 있습니다.

import subprocess
import json
import os

PROMPT_FILE = os.path.join(os.path.dirname(__file__), 'ollama_prompt.txt')
DATA_TXT = os.path.join(os.path.dirname(__file__), 'data.txt')
DATA_JSON = os.path.join(os.path.dirname(__file__), 'data.json')

# 1. 크롬으로 사이트 열기 (headless로 크롤링)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def fetch_site_html(url):
    options = Options()
    # headless 옵션 제거: 실제 브라우저 창을 띄움
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    import time
    time.sleep(3)  # 페이지 로딩 후 15초 대기
    html = driver.page_source
    driver.quit()
    # body 태그의 텍스트만 추출 (HTML 태그 제거)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    body = soup.body
    return body.get_text(separator='\n', strip=True) if body else ''

# 2. Ollama AI로 데이터 추출 (프롬프트 분리)


def extract_data_with_ollama(html, prompt_path=None, prompt_str=None, model="gpt-oss:120b-cloud", timeout=120):

    import re
    # 프롬프트 준비
    if prompt_str:
        prompt = prompt_str
    elif prompt_path:
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt = f.read()
    else:
        raise ValueError("prompt_path 또는 prompt_str 필요")

    full_input = f"""

                {prompt}

                Return ONLY valid JSON.
                Do not explain.
                Do not include thinking.

                HTML:
                {html}
                """

    cmd = ["ollama", "run", model]

    try:
        result = subprocess.run(
            cmd,
            input=full_input.encode("utf-8"),
            capture_output=True,
            timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}

    stdout = result.stdout.decode("utf-8", errors="replace").strip()

    if not stdout:
        return {"error": "empty_output"}

    # ANSI escape code 제거
    stdout_clean = re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', stdout)

    print("[AI 출력 preview]")
    print(stdout_clean[:400])

    # JSON 배열 탐색 (우선)
    arr_match = re.search(r"\[[\s\S]*\]", stdout_clean)
    if arr_match:
        try:
            return json.loads(arr_match.group())
        except Exception as e:
            print(f"[JSON 배열 파싱 실패] {e}")

    # JSON 객체 탐색
    obj_match = re.search(r"\{[\s\S]*\}", stdout_clean)
    if obj_match:
        try:
            return json.loads(obj_match.group())
        except Exception as e:
            print(f"[JSON 객체 파싱 실패] {e}")

    return {
        "error": "json_parse_failed",
        "raw": stdout_clean[:2000]
    }

if __name__ == '__main__':
    url = 'https://참소식.com'
    html = fetch_site_html(url)

    with open(DATA_TXT, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'페이지 HTML이 {DATA_TXT}에 저장되었습니다.')

    html_chunk_size = len(html) // 10
    results = []

    for i in range(10):
        html_chunk = html[i*html_chunk_size:(i+1)*html_chunk_size] if i < 4 else html[i*html_chunk_size:]

        print(f'AI 분석 실행 {i+1}/10')

        data = extract_data_with_ollama(html_chunk, prompt_path=PROMPT_FILE)

        # 실제 JSON 배열/객체일 경우 바로 추가
        if isinstance(data, list):
            results.append(data)
        elif isinstance(data, dict):
            # dict에 주요 데이터가 있으면 바로 추가
            if all(k in data for k in ['timestamp', 'location', 'price', 'unit']):
                results.append(data)
            elif 'error' in data and 'raw' in data:
                results.append({
                    'error': True,
                    'raw': data.get('raw', ''),
                    'stderr': data.get('stderr', '')
                })
            else:
                results.append(data)
        else:
            results.append({
                'error': True,
                'raw': str(data)[:2000],
                'stderr': ''
            })

    with open(DATA_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f'AI 분석 결과가 {DATA_JSON}에 통합 저장되었습니다.')
