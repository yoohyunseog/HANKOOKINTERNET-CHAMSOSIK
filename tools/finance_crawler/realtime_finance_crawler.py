
import time
import json
import requests
import xml.etree.ElementTree as ET
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
"""
🔄 업데이트 포인트 (실시간 이슈 맵 개선)
1. 실시간 데이터 반영
    - 최신 뉴스 기사와 트렌드 키워드가 자동으로 갱신되는지 확인 필요
    - 특정 이슈가 오래된 상태로 남아 있다면, 데이터 소스 업데이트 주기 조정 필요
2. 카테고리 정리
    - 에너지, 경제, 정치, 사회 등 주요 분야별로 카드가 구분되어야 함
    - 현재 카드가 단순 키워드 나열이라면, 주제별 그룹화 필요
3. 시각화 개선
    - 단순 텍스트보다 그래프·맵·타임라인 형태로 트렌드 흐름을 직관적으로 표시
    - 예: “에너지 산업” 관련 키워드가 급상승 중이라면, 상승 곡선을 시각적으로 표시

TODO:
- 실시간 뉴스/트렌드 API 연동 및 주기적 데이터 갱신
- 카드 데이터에 카테고리(분야) 필드 추가 및 그룹화 로직 구현
- 카드/이슈맵 시각화(그래프, 타임라인 등) 함수 추가
"""
# ollama REST API 연동 함수
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma3:1b"
def ollama_explain(prompt, model=OLLAMA_MODEL, max_retries=2):
    import time
    url = "http://localhost:11434/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    headers = {"Content-Type": "application/json"}
    for attempt in range(max_retries+1):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            if response.status_code == 404:
                time.sleep(1)
                continue
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt < max_retries:
                time.sleep(1)
                continue
            # 에러 발생 시에도 항상 정상적인 한글 JSON 안내 메시지 반환 (value_krw는 0, explanation은 고정)
            return '{"value_krw": 0, "explanation": "AI 해설을 일시적으로 가져올 수 없습니다. 네트워크 상태를 확인해 주세요."}'

# 크롬 드라이버 옵션 설정

chrome_options = Options()
chrome_options.add_argument('--headless')  # 창이 안 보이게 백그라운드 실행
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
# 일반 브라우저 User-Agent로 위장
chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

# 크롬 드라이버 경로 (환경에 맞게 수정)
CHROME_DRIVER_PATH = 'chromedriver.exe'

# 크롤링할 금융/암호화폐/환율 정보 (URL 및 셀렉터는 실제 사이트에 맞게 수정 필요)
TARGETS = [
    {
        'name': 'KOSPI',
        'url': 'https://finance.naver.com/sise/sise_index.naver?code=KOSPI',
        'selector': '#now_value',
        'type': 'default',
    },
    {
        'name': 'KOSDAQ',
        'url': 'https://finance.naver.com/sise/sise_index.naver?code=KOSDAQ',
        'selector': '#now_value',
        'type': 'default',
    },
    {
        'name': 'S&P500',
        'url': 'https://finance.yahoo.com/quote/%5EGSPC',
        'selector': 'fin-streamer[data-field="regularMarketPrice"]',
        'type': 'default',
    },
    {
        'name': 'NASDAQ',
        'url': 'https://finance.yahoo.com/quote/%5EIXIC',
        'selector': 'fin-streamer[data-field="regularMarketPrice"]',
        'type': 'default',
    },
    {
        'name': 'DOWJONES',
        'url': 'https://finance.yahoo.com/quote/%5EDJI',
        'selector': 'fin-streamer[data-field="regularMarketPrice"]',
        'type': 'default',
    },
    {
        'name': 'Bitcoin',
        'url': 'https://coinmarketcap.com/currencies/bitcoin/',
        'selector': None,
        'type': 'coinmarketcap',
    },
    {
        'name': 'Ethereum',
        'url': 'https://coinmarketcap.com/currencies/ethereum/',
        'selector': None,
        'type': 'coinmarketcap',
    },
    {
        'name': 'USD/KRW',
        'url': 'https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW',
        'selector': None,
        'type': 'naver_fx',
    },
    {
        'name': 'Gold',
        'url': 'https://finance.naver.com/marketindex/goldDetail.naver',
        'selector': None,
        'type': 'naver_gold',
    },
]

def get_value(driver, target):
    url = target['url']
    driver.get(url)
    time.sleep(2)
    try:
        if target.get('type') == 'coinmarketcap':
            # 가격이 $로 시작하는 span을 모두 찾고, 가장 첫 번째 값을 반환
            spans = driver.find_elements(By.TAG_NAME, 'span')
            for span in spans:
                text = span.text.strip().replace(',', '')
                if text.startswith('$') and text[1:].replace('.', '').isdigit():
                    return text
            raise Exception('가격 정보를 찾을 수 없음')
        elif target.get('type') == 'naver_fx':
            # 환율: 표에서 첫 번째 4자리 이상의 숫자(예: 1,474.50) 추출
            import re
            body = driver.page_source
            match = re.search(r'(\d{1,3}(,\d{3})+\.\d+)', body)
            if match:
                return match.group(1)
            raise Exception('환율 정보를 찾을 수 없음')
        elif target.get('type') == 'naver_gold':
            # 금: 표에서 5자리 이상의 숫자(예: 246,871.44) 추출
            import re
            body = driver.page_source
            match = re.search(r'(\d{3,}(,\d{3})*\.\d+)', body)
            if match:
                return match.group(1)
            raise Exception('금 정보를 찾을 수 없음')
        elif target.get('url', '').startswith('https://finance.yahoo.com/quote/'):
            # Yahoo Finance: 가격 엘리먼트가 로드될 때까지 최대 10초 대기
            try:
                elem = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, target['selector']))
                )
                text = elem.text.strip().replace(',', '')
                if text and text.replace('.', '').replace('-', '').isdigit():
                    return elem.text.strip()
            except Exception:
                pass
            # 백업: 여러 fin-streamer[data-field="regularMarketPrice"] 중 첫 번째 값 반환
            elems = driver.find_elements(By.CSS_SELECTOR, target['selector'])
            for elem in elems:
                text = elem.text.strip().replace(',', '')
                if text and text.replace('.', '').replace('-', '').isdigit():
                    return elem.text.strip()
            # 백업: 페이지 내에서 3~6자리 숫자(소수점 포함) 패턴 추출
            import re
            body = driver.page_source
            match = re.search(r'>(\d{3,6}(?:,\d{3})*(?:\.\d+)?)<', body)
            if match:
                return match.group(1)
            raise Exception('Yahoo Finance 가격 정보를 찾을 수 없음')
        else:
            elem = driver.find_element(By.CSS_SELECTOR, target['selector'])
            return elem.text.strip()
    except Exception as e:
        print(f"[{url}] Error: {e}")
        return None

def main():
    # 1. 주요 뉴스 헤드라인 추출 (RSS)
    NEWS_FEED_URL = "https://xn--9l4b4xi9r.com/feed.xml"
    news_headlines = []
    try:
        resp = requests.get(NEWS_FEED_URL, timeout=10)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall('.//item'):
                title = item.find('title')
                if title is not None and title.text:
                    news_headlines.append(title.text.strip())
        else:
            news_headlines.append("(뉴스 피드 불러오기 실패)")
    except Exception as e:
        news_headlines.append(f"(뉴스 피드 에러: {e})")
    news_text = '\n'.join(news_headlines[:10])  # 상위 10개 뉴스만 사용
    # 최신 selenium에서는 Service 객체로 드라이버 경로 지정
    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    results = {}
    ollama_targets = ["S&P500", "NASDAQ", "DOWJONES"]
    page_texts = {}
    raw_values = {}
    for target in TARGETS:
        value = get_value(driver, target)
        raw_values[target['name']] = value
        # 환율/금 항목은 단위 명확히 표기
        if target['name'] == 'USD/KRW' and value:
            results['USD/KRW (원/달러)'] = value
        elif target['name'] == 'Gold' and value:
            results['Gold (g 또는 oz 단위, 원)'] = value
        else:
            results[target['name']] = value
        print(f"{target['name']}: {value}")
        # S&P500, NASDAQ, DOWJONES는 페이지 텍스트도 추출
        if target['name'] in ollama_targets:
            try:
                # 본문 텍스트만 추출 (body 태그 기준)
                body_elem = driver.find_element(By.TAG_NAME, 'body')
                page_text = body_elem.text
            except Exception:
                page_text = driver.page_source[:3000]  # fallback: HTML 일부
            page_texts[target['name']] = page_text

    # 환율 기반 원화 환산
    def parse_float(val):
        try:
            return float(str(val).replace(",", "").replace("$", ""))
        except:
            return None

    usdkrw = parse_float(raw_values.get('USD/KRW'))
    if usdkrw:
        for key, src in [
            ('KOSPI_KRW', 'KOSPI'),  # 추가
            ('KOSDAQ_KRW', 'KOSDAQ'),  # 추가
            ('S&P500_KRW', 'S&P500'),
            ('NASDAQ_KRW', 'NASDAQ'),
            ('DOWJONES_KRW', 'DOWJONES'),
            ('Bitcoin_KRW', 'Bitcoin'),
            ('Ethereum_KRW', 'Ethereum'),
        ]:
            val = parse_float(raw_values.get(src))
            if val:
                # KOSPI, KOSDAQ은 이미 원화이므로 그냥 val 사용
                results[key] = int(val) if 'KOSPI' in key or 'KOSDAQ' in key else int(val * usdkrw)
        # Gold는 이미 원화 단위로 추출된 경우가 많으므로 별도 처리 생략
    driver.quit()

    # ollama로 해설 요청

    # 모든 주요 종목에 대해 ollama 해설 생성 (KOSPI, KOSDAQ, S&P500, NASDAQ, DOWJONES, Bitcoin, Ethereum, Gold, USD/KRW)
    all_keys = [
        'KOSPI', 'KOSDAQ', 'S&P500', 'NASDAQ', 'DOWJONES', 'Bitcoin', 'Ethereum', 'Gold (g 또는 oz 단위, 원)', 'USD/KRW (원/달러)'
    ]
    for key in all_keys:
        val = results.get(key)
        val_krw = results.get(f"{key}_KRW")
        page_text = page_texts.get(key, "")
        if val:
            prompt = (
                f"아래 값은 {key}의 실시간 최신 데이터입니다. 만약 달러 단위라면 환율({results.get('USD/KRW (원/달러)')}원/달러)로 원화(KRW)로 환산해서, "
                f"실제 투자 참고가 될 수 있도록 시장 상황, 변동성, 환율 영향, 최근 트렌드, 투자자 유의점 등도 함께 상세하게 한글로 해설해줘. "
                f"아래는 해당 종목의 최신 페이지 주요 텍스트입니다:\n{page_text}\n"
                f"또한 아래는 오늘의 주요 뉴스 헤드라인입니다. 뉴스와 지표가 연결되는 부분이 있다면 함께 해설해줘:\n{news_text}\n"
                f"예시: {{\"value_krw\": \"숫자(원)\", \"explanation\": \"실시간 시장 해설 및 투자 참고\"}}\n\n"
                f"값: {val}, 원화 환산값: {val_krw}"
            )
            ollama_result = ollama_explain(prompt)
            results[f"{key}_ollama"] = ollama_result
            print(f"{key}_ollama: {ollama_result}")
            time.sleep(1)

    # 전체 JSON을 ollama ai로 한글 요약/해설한 .json 생성
    with open('realtime_finance_data.json', 'r', encoding='utf-8') as f:
        all_json = f.read()
    summary_prompt = (
        "아래는 주요 금융/암호화폐/환율 데이터의 JSON입니다. 모든 값을 원화(KRW) 기준으로 한글로 요약/해설해서 새로운 JSON을 만들어줘. "
        "예시: {\"summary\": \"전체 요약\", \"details\": { ...종목별 해설... }}\n\nJSON:\n" + all_json
    )
    summary_result = ollama_explain(summary_prompt)
    with open('realtime_finance_data_summary_kr.json', 'w', encoding='utf-8') as f:
        f.write(summary_result)
    print('Saved to realtime_finance_data_summary_kr.json')
    # JSON 파일로 저장
    with open('realtime_finance_data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print('Saved to realtime_finance_data.json')

if __name__ == '__main__':
    main()
