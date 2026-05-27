import json
import os
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import ollama
import time

# --- 설정 ---
# 직접 접속할 컴퓨터/IT 사이트
SOURCE_PAGES = [
    {"name": "Tom's Hardware", "url": "https://www.tomshardware.com/news"},
    {"name": "TechPowerUp", "url": "https://www.techpowerup.com/"},
    {"name": "VideoCardz", "url": "https://videocardz.com/"},
    {"name": "ServeTheHome", "url": "https://www.servethehome.com/"},
    {"name": "BleepingComputer", "url": "https://www.bleepingcomputer.com/news/"},
    {"name": "Ars Technica", "url": "https://arstechnica.com/gadgets/"},
    {"name": "PCMag", "url": "https://www.pcmag.com/categories/computers"},
    {"name": "The Verge", "url": "https://www.theverge.com/tech"},
    {"name": "Engadget", "url": "https://www.engadget.com/computing/"},
    {"name": "Digital Trends", "url": "https://www.digitaltrends.com/computing/"},
    {"name": "AnandTech", "url": "https://www.anandtech.com/"},
    {"name": "Quasarzone", "url": "https://quasarzone.com/bbs/qn_hardware"},
    {"name": "Coolenjoy", "url": "https://coolenjoy.net/bbs/38"},
    {"name": "ZDNet Korea", "url": "https://zdnet.co.kr/news/?lstcode=0050"},
    {"name": "ITWorld Korea", "url": "https://www.itworld.co.kr/news"},
    {"name": "KBench", "url": "https://kbench.com/"},
    {"name": "Giggle Hardware", "url": "https://gigglehd.com/gg/"},
]

# 우선순위 IT 전문 사이트
TRUSTED_SOURCES = [
    "tomshardware.com", "anandtech.com", "theverge.com", 
    "videocardz.com", "gamerntweaks.com", "techpowerup.com",
    "digitaltrends.com", "engadget.com", "servethehome.com",
    "bleepingcomputer.com", "arstechnica.com", "pcmag.com",
    "quasarzone.com", "coolenjoy.net", "zdnet.co.kr",
    "itworld.co.kr", "kbench.com", "gigglehd.com"
]

HARDWARE_TERMS = [
    "gpu", "graphics", "geforce", "radeon", "rtx", "nvidia", "amd",
    "intel", "cpu", "processor", "ryzen", "core-ultra", "lunar-lake",
    "arrow-lake", "motherboard", "ssd", "memory", "ddr", "pc", "laptop",
    "hardware", "benchmark", "chip", "ai", "accelerator",
    "cpu", "gpu", "그래픽", "그래픽카드", "브가", "vga", "메인보드",
    "반도체", "컴퓨터", "노트북", "서버", "나스", "nas", "스토리지",
    "보안", "해킹", "악성코드", "취약점", "벤치", "벤치마크", "라이젠",
    "지포스", "라데온", "인텔", "엔비디아", "amd"
]

MAX_ARTICLES = int(os.getenv("NEWS_BOT_MAX_ARTICLES", "5"))
MAX_CANDIDATE_LINKS = int(os.getenv("NEWS_BOT_MAX_CANDIDATES", "20"))
SKIP_AI = os.getenv("NEWS_BOT_SKIP_AI", "0") == "1"
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# Ollama 모델 설정
MODEL_NAME = "deepseek-v4-flash:cloud"
# 결과 저장 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "news_data.json"))

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # 더 실제 브라우저 같은 User-Agent 설정
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    # 자동화 감지 방지 스크립트 실행
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """
    })
    return driver

def normalize_url(base_url, href):
    if not href:
        return None
    url = urljoin(base_url, href.split("#")[0])
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return None
    return url

def is_trusted_article_url(url):
    parsed = urlparse(url)
    host = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.strip("/").lower()
    if not path or len(path) < 8:
        return False
    if any(skip in path for skip in [
        "/tag/", "/author/", "/about", "/contact", "/privacy", "/video",
        "/login", "/signup", "/search", "/category", "/page/", "/rss",
        "/member", "/notice", "/event", "/shop", "/cart"
    ]):
        return False
    return any(source.replace("www.", "") in host for source in TRUSTED_SOURCES)

def score_hardware_link(title, url):
    text = f"{title} {url}".lower()
    return sum(1 for term in HARDWARE_TERMS if term in text)

def collect_direct_article_links(driver):
    """Google 검색 대신 원본 사이트에 직접 접속해서 기사 링크를 수집한다."""
    candidates = []
    seen = set()

    for source in SOURCE_PAGES:
        source_url = source["url"]
        print(f"Opening source page: {source_url}")
        try:
            response = requests.get(source_url, headers=REQUEST_HEADERS, timeout=12)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            anchors = soup.select("a[href]")
        except Exception as e:
            print(f"  Requests failed, trying browser: {e}")
            try:
                driver.get(source_url)
                time.sleep(2)
                anchors = driver.find_elements(By.CSS_SELECTOR, "a[href]")
            except Exception as browser_error:
                print(f"  Error opening source page: {browser_error}")
                continue

        for anchor in anchors:
            get_attribute = getattr(anchor, "get_attribute", None)
            if callable(get_attribute):
                href = anchor.get_attribute("href")
                title = (anchor.text or "").strip()
            else:
                href = anchor.get("href")
                title = " ".join(anchor.get_text(" ", strip=True).split())
                title = title or anchor.get("title", "") or anchor.get("aria-label", "")

            url = normalize_url(source_url, href)
            if not url or url in seen or not is_trusted_article_url(url):
                continue

            score = score_hardware_link(title, url)
            if score <= 0:
                continue

            seen.add(url)
            candidates.append({
                "url": url,
                "title": title,
                "score": score,
                "source": source["name"],
            })

    candidates.sort(key=lambda item: item["score"], reverse=True)
    links = [item["url"] for item in candidates[:MAX_CANDIDATE_LINKS]]
    print(f"Collected {len(links)} direct article links.")
    return links

def extract_article_content(driver, url):
    """해당 URL에 접속하여 본문 텍스트 추출"""
    try:
        driver.get(url)
        time.sleep(2)
        paragraphs = driver.find_elements(By.TAG_NAME, "p")
        content = "\n".join([p.text for p in paragraphs if len(p.text) > 20])
        title = driver.title
        comments = extract_visible_comments(driver)
        return {"title": title, "content": content, "comments": comments, "url": url}
    except Exception as e:
        print(f"  ⚠️ Error extracting {url}: {e}")
        return None

def extract_visible_comments(driver):
    """페이지에 바로 노출된 댓글/반응 텍스트를 최대한 수집한다."""
    selectors = [
        "[class*='comment']",
        "[id*='comment']",
        "[class*='reply']",
        "[id*='reply']",
        "[class*='reaction']",
        "[class*='opinion']",
        ".cmt",
        ".reply",
        ".comment",
        ".comments",
    ]
    snippets = []
    seen = set()

    for selector in selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
        except Exception:
            continue

        for element in elements[:20]:
            text = " ".join((element.text or "").split())
            if len(text) < 12 or len(text) > 500:
                continue
            lowered = text.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            snippets.append(text)
            if len(snippets) >= 12:
                return snippets

    return snippets

def translate_and_summarize_with_ai(article):
    """영어 본문을 AI에게 전달하여 한국어 뉴스 포스팅으로 변환"""
    print(f"AI is translating and summarizing: {article['title'][:30]}...")
    article_content = article["content"][:5000]
    visible_comments = "\n".join(article.get("comments") or [])[:2500]
    comments_block = visible_comments or "No visible comments were available. Infer likely community reaction from the article, but clearly mark it as inferred."
    
    prompt = f"""
    You are a professional IT hardware journalist. 
    Translate the following English article into a high-quality Korean news post for a tech community.
    
    [Original Title]: {article['title']}
    [Original Content]: {article_content}
    [Visible Comments or Reactions]: {comments_block}
    
    Please provide the result in the following JSON format:
    {{
        "translated_title": "Catchy Korean title that attracts hardware enthusiasts",
        "summary": "A 3-5 sentence professional summary in Korean",
        "full_post": "A detailed Korean news post (bullet points allowed) explaining the key points, specs, and implications",
        "category": "GPU/CPU/Laptop/AI/Other",
        "importance": "High/Medium/Low",
        "comment_mood": "Positive/Negative/Mixed/Neutral/No visible comments",
        "comment_summary": "A Korean summary of visible comment atmosphere. If there were no comments, say this is an inferred likely reaction.",
        "product_tags": ["specific product/model tag 1", "specific product/model tag 2", "specific product/model tag 3"],
        "reaction_keywords": ["short Korean keyword 1", "short Korean keyword 2", "short Korean keyword 3"]
    }}
    
    Ensure the tone is professional yet engaging, like a tech blog.
    Product tags must be product-centered: model names, brands, chip names, standards, or concrete product lines from the article. Avoid generic tags like "AI", "hardware", "performance", or "news".
    Do not invent direct quotes. Separate visible comment analysis from inferred community reaction.
    """

    try:
        if SKIP_AI:
            raise RuntimeError("AI skipped by NEWS_BOT_SKIP_AI=1")

        response = ollama.generate(model=MODEL_NAME, prompt=prompt, format="json")
        return json.loads(response['response'])
    except Exception as e:
        print(f"  ❌ AI Error: {e}")
        return fallback_news_post(article)

def fallback_news_post(article):
    title = article["title"].replace(" | Tom's Hardware", "").replace(" | TechPowerUp", "")
    summary = f"원문 기사 '{title}'를 수집했습니다. 자세한 내용은 원문 링크에서 확인할 수 있습니다."
    comment_count = len(article.get("comments") or [])
    if comment_count:
        comment_mood = "Mixed"
        comment_summary = f"페이지에서 댓글 또는 반응 텍스트 {comment_count}개를 확인했습니다. 상세 반응 분석은 AI 요약 실행 시 보강됩니다."
    else:
        comment_mood = "No visible comments"
        comment_summary = "페이지에서 바로 확인 가능한 댓글을 찾지 못했습니다. 커뮤니티 반응은 추가 수집 후 판단이 필요합니다."
    return {
        "translated_title": title,
        "summary": summary,
        "full_post": summary,
        "category": guess_category(article),
        "importance": "Medium",
        "comment_mood": comment_mood,
        "comment_summary": comment_summary,
        "product_tags": guess_product_tags(article),
        "reaction_keywords": guess_reaction_keywords(article)
    }

def guess_product_tags(article):
    text = f"{article['title']} {article['url']} {article['content'][:1200]}"
    patterns = [
        r"\bRTX\s?\d{4}(?:\s?Ti|\s?Super)?\b",
        r"\bGTX\s?\d{4}(?:\s?Ti)?\b",
        r"\bRX\s?\d{4}(?:\s?XT|\s?XTX)?\b",
        r"\bRyzen\s?(?:AI\s?)?\d(?:\s?\d{3,4}[A-Z0-9]*)?\b",
        r"\bCore\s?(?:Ultra\s?)?[iI]?\d[-\s]?\d{3,5}[A-Z]*\b",
        r"\bXeon\s?[A-Z0-9 -]{2,18}\b",
        r"\bDDR[45]\b",
        r"\bPCIe\s?\d(?:\.\d)?\b",
        r"\bFSR\s?\d(?:\.\d)?\b",
        r"\bDLSS\s?\d(?:\.\d)?\b",
        r"\b12V-?2x6\b",
        r"\b12VHPWR\b",
    ]
    tags = []
    seen = set()
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            tag = " ".join(match.split())
            key = tag.lower()
            if key not in seen:
                seen.add(key)
                tags.append(tag)
            if len(tags) >= 8:
                return tags

    category = guess_category(article)
    if category == "GPU":
        return ["그래픽카드", "GPU", "전원 커넥터"]
    if category == "CPU":
        return ["프로세서", "CPU", "메인보드"]
    if category == "Laptop":
        return ["노트북", "모바일 프로세서", "디스플레이"]
    if category == "Server":
        return ["서버", "스토리지", "네트워크"]
    return ["PC 부품", "컴퓨터 제품", "테크 제품"]

def normalize_tags(value, fallback):
    if isinstance(value, list):
        tags = [str(item).strip() for item in value if str(item).strip()]
    elif isinstance(value, str):
        tags = [item.strip() for item in value.split(",") if item.strip()]
    else:
        tags = []
    return tags[:8] if tags else fallback

def guess_reaction_keywords(article):
    category = guess_category(article)
    if category == "GPU":
        return ["성능", "가격", "전력"]
    if category == "CPU":
        return ["코어 수", "플랫폼", "가격"]
    if category == "Security":
        return ["취약점", "패치", "주의"]
    if category == "Server":
        return ["안정성", "확장성", "전력"]
    return ["관심", "검증", "후속 소식"]

def guess_category(article):
    text = f"{article['title']} {article['url']} {article['content'][:500]}".lower()
    if any(term in text for term in ["gpu", "rtx", "radeon", "geforce", "graphics", "vga", "그래픽"]):
        return "GPU"
    if any(term in text for term in ["cpu", "ryzen", "intel", "processor", "라이젠", "인텔"]):
        return "CPU"
    if any(term in text for term in ["laptop", "notebook", "노트북"]):
        return "Laptop"
    if any(term in text for term in ["security", "malware", "hack", "보안", "해킹", "취약점"]):
        return "Security"
    if any(term in text for term in ["server", "nas", "storage", "서버", "스토리지"]):
        return "Server"
    return "Other"

def main():
    print("🚀 Starting Global Hardware News Curator Bot...")
    driver = setup_driver()
    final_news_list = []
    processed_urls = set()
    
    try:
        links = collect_direct_article_links(driver)
        for link in links:
            if len(final_news_list) >= MAX_ARTICLES:
                break
            if link in processed_urls:
                continue
            processed_urls.add(link)

            article = extract_article_content(driver, link)
            if article and len(article['content']) > 200:
                ai_result = translate_and_summarize_with_ai(article)
                if ai_result:
                    final_news_list.append({
                        "original_title": article['title'],
                        "translated_title": ai_result.get('translated_title', article['title']),
                        "summary": ai_result.get('summary', ''),
                        "full_post": ai_result.get('full_post', ''),
                        "url": article['url'],
                        "category": ai_result.get('category', 'Other'),
                        "importance": ai_result.get('importance', 'Medium'),
                        "comment_mood": ai_result.get('comment_mood', 'No visible comments'),
                        "comment_summary": ai_result.get('comment_summary', ''),
                        "product_tags": normalize_tags(ai_result.get('product_tags'), guess_product_tags(article)),
                        "reaction_keywords": ai_result.get('reaction_keywords', []),
                        "visible_comment_count": len(article.get('comments') or []),
                        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output_data = {
            "last_updated": timestamp,
            "total_count": len(final_news_list),
            "news": final_news_list
        }
        
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
            
        print(f"\n✅ Successfully collected and translated {len(final_news_list)} articles!")
        print(f"Saved to: {SAVE_PATH}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()

