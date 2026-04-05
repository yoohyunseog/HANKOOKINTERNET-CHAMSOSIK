import json
import re
import time
import xml.etree.ElementTree as ET

import requests
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


OLLAMA_URL = "http://localhost:11434/v1/chat/completions"
OLLAMA_MODEL = "deepseek-v3.1:671b-cloud"
CHROME_DRIVER_PATH = "chromedriver.exe"
NEWS_FEED_URL = "https://xn--9l4b4xi9r.com/feed.xml"

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

TARGETS = [
    {
        "name": "KOSPI",
        "url": "https://finance.naver.com/sise/sise_index.naver?code=KOSPI",
        "selector": "#now_value",
        "type": "default",
    },
    {
        "name": "KOSDAQ",
        "url": "https://finance.naver.com/sise/sise_index.naver?code=KOSDAQ",
        "selector": "#now_value",
        "type": "default",
    },
    {
        "name": "S&P500",
        "url": "https://finance.yahoo.com/quote/%5EGSPC",
        "selector": 'fin-streamer[data-field="regularMarketPrice"]',
        "type": "yahoo",
    },
    {
        "name": "NASDAQ",
        "url": "https://finance.yahoo.com/quote/%5EIXIC",
        "selector": 'fin-streamer[data-field="regularMarketPrice"]',
        "type": "yahoo",
    },
    {
        "name": "DOWJONES",
        "url": "https://finance.yahoo.com/quote/%5EDJI",
        "selector": 'fin-streamer[data-field="regularMarketPrice"]',
        "type": "yahoo",
    },
    {
        "name": "Bitcoin",
        "url": "https://coinmarketcap.com/currencies/bitcoin/",
        "selector": None,
        "type": "coinmarketcap",
    },
    {
        "name": "Ethereum",
        "url": "https://coinmarketcap.com/currencies/ethereum/",
        "selector": None,
        "type": "coinmarketcap",
    },
    {
        "name": "USD/KRW",
        "url": "https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=FX_USDKRW",
        "selector": None,
        "type": "naver_fx",
    },
    {
        "name": "Gold",
        "url": "https://finance.naver.com/marketindex/goldDetail.naver",
        "selector": None,
        "type": "naver_gold",
    },
]


def ollama_explain(prompt, model=OLLAMA_MODEL, max_retries=2):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {"Content-Type": "application/json"}

    for attempt in range(max_retries + 1):
        try:
            response = requests.post(OLLAMA_URL, json=payload, headers=headers, timeout=45)
            if response.status_code == 404:
                time.sleep(1)
                continue
            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content")
            if isinstance(content, str) and content.strip():
                return content
            raise ValueError("empty ollama content")
        except Exception:
            if attempt < max_retries:
                time.sleep(1)
                continue
            return json.dumps(
                {
                    "value_krw": 0,
                    "explanation": "AI explanation is temporarily unavailable.",
                },
                ensure_ascii=False,
            )


def parse_float(value):
    try:
        return float(str(value).replace(",", "").replace("$", ""))
    except Exception:
        return None


def fetch_page_value(driver, target):
    target_type = target["type"]

    if target_type == "coinmarketcap":
        spans = driver.find_elements(By.TAG_NAME, "span")
        for span in spans:
            text = span.text.strip().replace(",", "")
            if text.startswith("$") and text[1:].replace(".", "").isdigit():
                return text
        raise ValueError("coinmarketcap price not found")

    if target_type == "naver_fx":
        match = re.search(r"(\d{1,3}(,\d{3})+\.\d+)", driver.page_source)
        if match:
            return match.group(1)
        raise ValueError("fx value not found")

    if target_type == "naver_gold":
        match = re.search(r"(\d{3,}(,\d{3})*\.\d+)", driver.page_source)
        if match:
            return match.group(1)
        raise ValueError("gold value not found")

    if target_type == "yahoo":
        try:
            elem = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, target["selector"]))
            )
            text = elem.text.strip().replace(",", "")
            if text and text.replace(".", "").replace("-", "").isdigit():
                return elem.text.strip()
        except Exception:
            pass

        elems = driver.find_elements(By.CSS_SELECTOR, target["selector"])
        for elem in elems:
            text = elem.text.strip().replace(",", "")
            if text and text.replace(".", "").replace("-", "").isdigit():
                return elem.text.strip()

        match = re.search(r">(\d{3,6}(?:,\d{3})*(?:\.\d+)?)<", driver.page_source)
        if match:
            return match.group(1)
        raise ValueError("yahoo price not found")

    elem = driver.find_element(By.CSS_SELECTOR, target["selector"])
    return elem.text.strip()


def get_value(driver, target, max_retries=3):
    url = target["url"]
    for attempt in range(max_retries):
        try:
            driver.get(url)
            time.sleep(2)
            return fetch_page_value(driver, target)
        except StaleElementReferenceException as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            print(f"[{url}] Error: {e}")
            return None
        except Exception as e:
            print(f"[{url}] Error: {e}")
            return None
    return None


def load_news_text():
    headlines = []
    try:
        resp = requests.get(NEWS_FEED_URL, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        for item in root.findall(".//item"):
            title = item.find("title")
            if title is not None and title.text:
                headlines.append(title.text.strip())
    except Exception as e:
        headlines.append(f"(news feed error: {e})")
    return "\n".join(headlines[:10])


def main():
    news_text = load_news_text()

    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    results = {}
    page_texts = {}
    raw_values = {}
    ollama_targets = {"KOSPI", "KOSDAQ", "S&P500", "NASDAQ", "DOWJONES", "Bitcoin", "Ethereum"}

    try:
        for target in TARGETS:
            value = get_value(driver, target)
            raw_values[target["name"]] = value

            if target["name"] == "USD/KRW" and value:
                results["USD/KRW (원/달러)"] = value
            elif target["name"] == "Gold" and value:
                results["Gold (g 또는 oz 단위, 원)"] = value
            else:
                results[target["name"]] = value

            print(f"{target['name']}: {value}")

            if target["name"] in ollama_targets:
                try:
                    body_elem = driver.find_element(By.TAG_NAME, "body")
                    page_texts[target["name"]] = body_elem.text
                except Exception:
                    page_texts[target["name"]] = driver.page_source[:3000]
    finally:
        driver.quit()

    usdkrw = parse_float(raw_values.get("USD/KRW"))
    if usdkrw:
        for key, source_key in [
            ("KOSPI_KRW", "KOSPI"),
            ("KOSDAQ_KRW", "KOSDAQ"),
            ("S&P500_KRW", "S&P500"),
            ("NASDAQ_KRW", "NASDAQ"),
            ("DOWJONES_KRW", "DOWJONES"),
            ("Bitcoin_KRW", "Bitcoin"),
            ("Ethereum_KRW", "Ethereum"),
        ]:
            val = parse_float(raw_values.get(source_key))
            if val is None:
                continue
            results[key] = int(val) if source_key in {"KOSPI", "KOSDAQ"} else int(val * usdkrw)

    all_keys = [
        "KOSPI",
        "KOSDAQ",
        "S&P500",
        "NASDAQ",
        "DOWJONES",
        "Bitcoin",
        "Ethereum",
        "Gold (g 또는 oz 단위, 원)",
        "USD/KRW (원/달러)",
    ]

    for key in all_keys:
        val = results.get(key)
        val_krw = results.get(f"{key}_KRW")
        page_text = page_texts.get(key, "")
        if not val:
            continue

        prompt = (
            f"{key}의 최신 값은 {val} 입니다. 환산값은 {val_krw} 입니다.\n"
            f"관련 페이지 텍스트:\n{page_text}\n\n"
            f"관련 뉴스 헤드라인:\n{news_text}\n\n"
            'JSON 형식으로 {"value_krw": 숫자 또는 문자열, "explanation": "설명"} 만 답하세요.'
        )
        ollama_result = ollama_explain(prompt)
        results[f"{key}_ollama"] = ollama_result
        print(f"{key}_ollama: {ollama_result}")
        time.sleep(1)

    with open("realtime_finance_data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Saved to realtime_finance_data.json")

    with open("realtime_finance_data.json", "r", encoding="utf-8") as f:
        all_json = f.read()

    summary_prompt = (
        "다음 금융 데이터 JSON을 한국어로 요약하고, JSON 형식으로만 답하세요. "
        '예시: {"summary": "요약", "details": {...}}\n\n'
        + all_json
    )
    summary_result = ollama_explain(summary_prompt)
    if summary_result is None:
        summary_result = json.dumps(
            {"summary": "AI summary unavailable", "details": results},
            ensure_ascii=False,
            indent=2,
        )
    elif not isinstance(summary_result, str):
        summary_result = str(summary_result)

    with open("realtime_finance_data_summary_kr.json", "w", encoding="utf-8") as f:
        f.write(summary_result)
    print("Saved to realtime_finance_data_summary_kr.json")


if __name__ == "__main__":
    main()
