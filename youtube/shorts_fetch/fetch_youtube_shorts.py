from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import sys
from datetime import datetime
from bs4 import BeautifulSoup

CHANNEL_ID = "UCEVf3QlL7lFRJxULWHux0mg"
RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
OUTPUT_PATH = "shorts_feed.xml"

def fetch_and_save():
    # 404 오류가 나오면 최대 10번까지 3초 대기 후 재시도
    max_retries = 10
    for attempt in range(1, max_retries + 1):
        try:
            chrome_options = Options()
            # chrome_options.add_argument('--headless')  # headless 제거: 창이 보이게
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--lang=ko_KR')
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(RSS_URL)
            time.sleep(2)  # 페이지 로딩 대기
            xml_source = driver.page_source
            driver.quit()
            # 404 오류 체크
            if '404' in xml_source or 'Not Found' in xml_source:
                print(f"[{datetime.now()}] 404 오류 발생, {attempt}번째 재시도...", file=sys.stderr)
                if attempt < max_retries:
                    time.sleep(3)
                    continue
                else:
                    print(f"[{datetime.now()}] 10회 시도 후에도 404 오류. 종료.", file=sys.stderr)
                    sys.exit(1)
            # BeautifulSoup으로 <feed> 태그만 추출
            soup = BeautifulSoup(xml_source, 'lxml-xml')
            feed = soup.find('feed')
            if feed:
                xml_content = '<?xml version="1.0" encoding="utf-8"?>\n' + feed.prettify()
            else:
                xml_content = xml_source  # fallback
            with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
                f.write(xml_content)
            print(f"[{datetime.now()}] Fetched and saved: {OUTPUT_PATH}")
            break
        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}", file=sys.stderr)
            if attempt < max_retries:
                time.sleep(3)
                continue
            else:
                print(f"[{datetime.now()}] 10회 시도 후에도 오류. 종료.", file=sys.stderr)
                sys.exit(1)

if __name__ == "__main__":
    fetch_and_save()
