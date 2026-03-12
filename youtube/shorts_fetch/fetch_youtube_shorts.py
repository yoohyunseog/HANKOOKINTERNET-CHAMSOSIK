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
    except Exception as e:
        print(f"[{datetime.now()}] Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    fetch_and_save()
