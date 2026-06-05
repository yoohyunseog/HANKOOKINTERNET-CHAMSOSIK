"""
위키문헌 (wikisource.org) 웹 스크래퍼
Playwright를 사용하여 크롬 브라우저로 데이터를 수집하고 자동으로 한국어 번역합니다.
한글 파일명으로 저장됩니다.
"""

import asyncio
import json
import os
import re
import sys
import time
import requests
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# 기본 경로
BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"
METADATA_DIR = BASE_DIR / "metadata"

# 디렉토리 생성
for d in [RAW_DIR, PROCESSED_DIR, METADATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# API 설정
KIMI_API = "https://api.moonshot.cn/v1"
KIMI_API_KEY = os.environ.get("KIMI_API_KEY", os.environ.get("MOONSHOT_API_KEY", ""))

# Ollama API 설정 (원격 서버) - 우선 사용
OLLAMA_API = os.environ.get("OLLAMA_API", "http://211.45.162.155:11434/api")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "glm-5:cloud")  # 클라우드 모델 사용

# API 확인 - Ollama 우선
def check_api_key():
    """API 확인 - Ollama를 우선 사용"""
    # Ollama 서버 먼저 확인
    try:
        response = requests.get(f"{OLLAMA_API.replace('/api', '')}/api/version", timeout=5)
        if response.status_code == 200:
            print(f"[Ollama API] 서버 연결됨: {OLLAMA_API.replace('/api', '')}")
            print(f"[Ollama Model] {OLLAMA_MODEL}")
            return "ollama"
    except:
        pass
    
    # Kimi API 확인
    if KIMI_API_KEY:
        print(f"[Kimi API] 키 확인됨")
        return "kimi"
    
    print("\n[경고] 번역 API를 사용할 수 없습니다.")
    print("       번역 없이 원문만 저장합니다.")
    print("       Ollama 서버 실행 확인 또는 Kimi API 키 설정 필요")
    return None

# 위키문헌 수집할 문헌 목록
WIKISOURCE_COLLECTIONS = {
    # 중국어 위키문헌
    "논어_위키": {
        "url": "https://zh.wikisource.org/wiki/論語",
        "chinese": "論語",
        "type": "유가",
        "period": "춘추전국",
        "lang": "zh",
        "description": "공자의 어록 - 위키문헌 버전"
    },
    "맹자_위키": {
        "url": "https://zh.wikisource.org/wiki/孟子",
        "chinese": "孟子",
        "type": "유가",
        "period": "춘추전국",
        "lang": "zh",
        "description": "맹자의 사상 - 위키문헌 버전"
    },
    "도덕경_위키": {
        "url": "https://zh.wikisource.org/wiki/道德經",
        "chinese": "道德經",
        "type": "도가",
        "period": "춘추전국",
        "lang": "zh",
        "description": "노자의 도덕경 - 위키문헌 버전"
    },
    "장자_위키": {
        "url": "https://zh.wikisource.org/wiki/莊子",
        "chinese": "莊子",
        "type": "도가",
        "period": "춘추전국",
        "lang": "zh",
        "description": "장자의 사상 - 위키문헌 버전"
    },
    "손자병법_위키": {
        "url": "https://zh.wikisource.org/wiki/孫子兵法",
        "chinese": "孫子兵法",
        "type": "병가",
        "period": "춘추전국",
        "lang": "zh",
        "description": "손자의 병법서 - 위키문헌 버전"
    },
    "시경_위키": {
        "url": "https://zh.wikisource.org/wiki/詩經",
        "chinese": "詩經",
        "type": "유가",
        "period": "서주",
        "lang": "zh",
        "description": "중국 최초의 시집 - 위키문헌 버전"
    },
    "삼국연의_위키": {
        "url": "https://zh.wikisource.org/wiki/三國演義",
        "chinese": "三國演義",
        "type": "소설",
        "period": "명대",
        "lang": "zh",
        "description": "나관중의 삼국지연의 - 위키문헌 버전"
    },
    "수호전_위키": {
        "url": "https://zh.wikisource.org/wiki/水滸傳",
        "chinese": "水滸傳",
        "type": "소설",
        "period": "명대",
        "lang": "zh",
        "description": "시내암의 수호지 - 위키문헌 버전"
    },
    "서유기_위키": {
        "url": "https://zh.wikisource.org/wiki/西遊記",
        "chinese": "西遊記",
        "type": "소설",
        "period": "명대",
        "lang": "zh",
        "description": "오승은의 서유기 - 위키문헌 버전"
    },
    "홍루몽_위키": {
        "url": "https://zh.wikisource.org/wiki/紅樓夢",
        "chinese": "紅樓夢",
        "type": "소설",
        "period": "청대",
        "lang": "zh",
        "description": "조설근의 홍루몽 - 위키문헌 버전"
    },
    # 한국어 위키문헌
    "삼국유사_위키": {
        "url": "https://ko.wikisource.org/wiki/삼국유사",
        "chinese": "三國遺事",
        "type": "역사",
        "period": "고려",
        "lang": "ko",
        "description": "일연의 삼국유사 - 한국어 위키문헌"
    },
    "훈민정음_위키": {
        "url": "https://ko.wikisource.org/wiki/훈민정음",
        "chinese": "訓民正音",
        "type": "어학",
        "period": "조선",
        "lang": "ko",
        "description": "세종대왕의 훈민정음 - 한국어 위키문헌"
    }
}


def translate_with_kimi(text: str, max_retries: int = 3) -> str:
    """
    Kimi API를 사용하여 한국어로 번역합니다.
    """
    if not KIMI_API_KEY:
        return ""
    
    if not text or len(text.strip()) < 10:
        return ""
    
    # 텍스트가 너무 길면 분할
    if len(text) > 3000:
        return translate_long_text(text, method="kimi")
    
    prompt = f"""다음 한문을 한국어로 번역하세요. 
- 원문의 의미를 정확하게 전달하세요
- 자연스러운 현대 한국어로 번역하세요
- 번역 결과만 출력하세요

한문 원문:
{text}

한국어 번역:"""

    headers = {
        "Authorization": f"Bearer {KIMI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "kimi-k2.5",
        "messages": [
            {
                "role": "system",
                "content": "당신은 중국 고전 문헌을 한국어로 번역하는 전문 번역가입니다. 한문 원문을 정확하고 자연스러운 한국어로 번역하세요."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{KIMI_API}/chat/completions",
                headers=headers,
                json=data,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            translation = result["choices"][0]["message"]["content"].strip()
            
            # 번역 결과 정리
            translation = re.sub(r'^(한국어 번역:|번역:)\s*', '', translation)
            
            return translation
        
        except requests.RequestException as e:
            print(f"    [번역 재시도 {attempt+1}/{max_retries}] {e}")
            time.sleep(2)
    
    return ""


def translate_with_ollama(text: str, max_retries: int = 3) -> str:
    """
    Ollama API를 사용하여 한국어로 번역합니다.
    """
    if not text or len(text.strip()) < 10:
        return ""
    
    # 텍스트가 너무 길면 분할
    if len(text) > 3000:
        return translate_long_text(text, method="ollama")
    
    prompt = f"""다음 한문을 한국어로 번역하세요. 
- 원문의 의미를 정확하게 전달하세요
- 자연스러운 현대 한국어로 번역하세요
- 번역 결과만 출력하세요

한문 원문:
{text}

한국어 번역:"""

    # Ollama API는 /api/generate 사용
    data = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{OLLAMA_API}/generate",
                json=data,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            translation = result.get("response", "").strip()
            
            # 번역 결과 정리
            translation = re.sub(r'^(한국어 번역:|번역:)\s*', '', translation)
            
            return translation
        
        except requests.RequestException as e:
            print(f"    [번역 재시도 {attempt+1}/{max_retries}] {e}")
            time.sleep(2)
    
    return ""


def translate_text(text: str, method: str = "auto") -> str:
    """
    텍스트를 번역합니다.
    method: "auto" (Ollama 우선), "ollama", "kimi"
    """
    if method == "auto":
        # Ollama 우선 사용
        return translate_with_ollama(text)
    elif method == "ollama":
        return translate_with_ollama(text)
    elif method == "kimi":
        return translate_with_kimi(text)
    return ""


def translate_long_text(text: str, method: str = "auto") -> str:
    """
    긴 텍스트를 분할하여 번역합니다.
    """
    # 문단 단위로 분할
    paragraphs = text.split('\n\n')
    translations = []
    
    for i, para in enumerate(paragraphs):
        if para.strip():
            print(f"    번역 중... ({i+1}/{len(paragraphs)})")
            if method == "kimi":
                translation = translate_with_kimi(para)
            else:
                translation = translate_with_ollama(para)
            translations.append(translation)
            time.sleep(1)  # API 속도 제한
    
    return '\n\n'.join(translations)


def clean_text(text: str) -> str:
    """
    스크래핑한 텍스트를 정리합니다.
    """
    if not text:
        return ""
    
    # 불필요한 공백 제거
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    # 위키문헌 특유의 불필요한 텍스트 제거
    text = re.sub(r'\[편집\]', '', text)
    text = re.sub(r'\[출처 필요\]', '', text)
    text = re.sub(r'위키문헌.*?에서', '', text)
    
    # 영어 메뉴/네비게이션 제거 (간단한 필터)
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        # 중국어/한국어가 포함된 라인만 유지
        if re.search(r'[\u4e00-\u9fff\uac00-\ud7a3]', line) or len(line) < 30:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


async def scrape_wikisource_page(page, url: str, book_name: str, chapter_name: str = None) -> dict:
    """
    위키문헌 페이지를 스크래핑합니다.
    """
    display_name = f"{book_name} - {chapter_name}" if chapter_name else book_name
    print(f"  스크래핑: {display_name}")
    print(f"  URL: {url}")
    
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(2)
        
        # 위키문헌 본문 추출
        content = await page.evaluate("""
            () => {
                // 위키문헌의 본문 영역
                const contentDiv = document.querySelector('.mw-parser-output, #mw-content-text');
                
                if (!contentDiv) {
                    return document.body.innerText;
                }
                
                // 불필요한 요소 제거
                const clone = contentDiv.cloneNode(true);
                const unwanted = clone.querySelectorAll('.mw-editsection, .reference, sup, .toc, .navbox, .infobox');
                unwanted.forEach(el => el.remove());
                
                return clone.innerText;
            }
        """)
        
        if not content or len(content) < 100:
            content = await page.evaluate("""
                () => document.body.innerText
            """)
        
        # 텍스트 정리
        content = clean_text(content)
        
        # 장 정보 추출
        chapter_info = await page.evaluate("""
            () => {
                const title = document.querySelector('h1, .firstHeading');
                return {
                    title: title ? title.innerText : '',
                    url: window.location.href
                };
            }
        """)
        
        return {
            "success": True,
            "content": content,
            "chapter": chapter_info
        }
    
    except Exception as e:
        print(f"  [ERROR] 스크래핑 실패: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def get_chapter_links(page, base_url: str, book_name: str) -> list:
    """
    문헌의 장(篇) 링크를 가져옵니다.
    """
    print(f"  장 목록 가져오는 중...")
    
    try:
        await page.goto(base_url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(2)
        
        # 장 링크 추출
        links = await page.evaluate("""
            () => {
                const links = [];
                // 위키문헌의 목차/장 링크
                const tocLinks = document.querySelectorAll('.toc a, #mw-content-text a');
                
                tocLinks.forEach(a => {
                    const href = a.href;
                    const text = a.innerText.trim();
                    
                    // 내부 링크이고 텍스트가 있는 경우
                    if (href && text && href.includes('wikisource.org/wiki')) {
                        // 중국어/한국어가 포함된 링크만
                        if (/[\\u4e00-\\u9fff\\uac00-\\ud7a3]/.test(text)) {
                            links.push({
                                url: href,
                                name: text
                            });
                        }
                    }
                });
                
                return links;
            }
        """)
        
        # 중복 제거
        seen = set()
        unique_links = []
        for link in links:
            if link['url'] not in seen:
                seen.add(link['url'])
                unique_links.append(link)
        
        print(f"  발견된 장: {len(unique_links)}개")
        return unique_links[:30]  # 최대 30개 장
        
    except Exception as e:
        print(f"  [ERROR] 장 목록 가져오기 실패: {e}")
        return []


async def scrape_book(browser, book_name: str, book_info: dict, translate_method: str = "auto") -> list:
    """
    한 문헌을 전체 스크래핑합니다.
    translate_method: "auto", "kimi", "ollama", None (번역 안함)
    """
    print(f"\n{'='*50}")
    print(f"문헌: {book_name} ({book_info['chinese']})")
    print(f"분류: {book_info['type']} / 시대: {book_info['period']}")
    print(f"언어: {book_info['lang']}")
    print(f"{'='*50}")
    
    page = await browser.new_page()
    results = []
    
    try:
        # 장 링크 가져오기
        chapter_links = await get_chapter_links(page, book_info['url'], book_name)
        
        if not chapter_links:
            # 장이 없으면 메인 페이지만 스크래핑
            print(f"  단일 페이지로 처리")
            chapter_links = [{"url": book_info['url'], "name": book_name}]
        
        for i, chapter in enumerate(chapter_links):
            print(f"\n[{i+1}/{len(chapter_links)}] {chapter['name']}")
            
            result = await scrape_wikisource_page(page, chapter['url'], book_name, chapter['name'])
            
            if result['success']:
                content = result['content']
                
                # 한국어 번역 (중국어 원문인 경우만)
                korean_translation = ""
                if translate_method and content and book_info['lang'] == 'zh':
                    print(f"  번역 중...")
                    korean_translation = translate_text(content, method=translate_method)
                    if korean_translation:
                        print(f"  ✓ 번역 완료 ({len(korean_translation)}자)")
                    else:
                        print(f"  ✗ 번역 실패")
                elif book_info['lang'] == 'ko':
                    # 한국어 위키문헌은 원문이 한국어
                    korean_translation = content
                    print(f"  ✓ 한국어 원문")
                
                entry = {
                    "id": f"{book_name}_{i+1:03d}",
                    "book": book_name,
                    "book_chinese": book_info['chinese'],
                    "chapter": chapter['name'],
                    "type": book_info['type'],
                    "period": book_info['period'],
                    "lang": book_info['lang'],
                    "description": book_info.get('description', ''),
                    "original": content,
                    "korean": korean_translation,
                    "source": chapter['url'],
                    "scraped_at": datetime.now().isoformat(),
                    "translated_at": datetime.now().isoformat() if korean_translation else None
                }
                
                results.append(entry)
                
                # 진행 상황 저장
                save_progress(book_name, results)
            
            await asyncio.sleep(1)  # 요청 간격
    
    finally:
        await page.close()
    
    return results


def save_progress(book_name: str, entries: list):
    """
    진행 상황을 저장합니다. (한글 파일명)
    """
    # JSONL 저장 (한글 파일명)
    jsonl_path = RAW_DIR / f"{book_name}.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    print(f"  저장: {jsonl_path.name} ({len(entries)}개 항목)")


def save_final_output(book_name: str, entries: list):
    """
    최종 출력을 저장합니다. (JSONL + JSON)
    """
    # JSONL 저장
    jsonl_path = PROCESSED_DIR / f"{book_name}_translated.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    # JSON 저장 (전체)
    json_path = PROCESSED_DIR / f"{book_name}_translated.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 저장 완료:")
    print(f"  - {jsonl_path.name}")
    print(f"  - {json_path.name}")


async def main():
    """
    메인 실행 함수
    """
    print("\n" + "="*60)
    print("   위키문헌 스크래퍼")
    print("   자동 수집 + 한국어 번역")
    print("="*60)
    
    # API 키 확인
    has_api_key = check_api_key()
    
    print(f"\n[Kimi API] 키 확인: {'설정됨' if KIMI_API_KEY else '없음'}")
    print(f"[저장 경로] {RAW_DIR}")
    print(f"[번역 경로] {PROCESSED_DIR}")
    
    # 수집할 문헌 선택
    print(f"\n수집 가능한 문헌:")
    
    # 중국어 위키문헌
    print(f"\n[중국어 위키문헌]")
    zh_items = [(k, v) for k, v in WIKISOURCE_COLLECTIONS.items() if v['lang'] == 'zh']
    for i, (name, info) in enumerate(zh_items, 1):
        print(f"  {i}. {name} ({info['chinese']}) - {info['type']}")
    
    # 한국어 위키문헌
    print(f"\n[한국어 위키문헌]")
    ko_items = [(k, v) for k, v in WIKISOURCE_COLLECTIONS.items() if v['lang'] == 'ko']
    for i, (name, info) in enumerate(ko_items, len(zh_items) + 1):
        print(f"  {i}. {name} ({info['chinese']}) - {info['type']}")
    
    print(f"\n  0. 전체 수집")
    print(f"  99. 종료")
    
    try:
        choice = input("\n선택 (번호): ").strip()
    except:
        choice = "0"
    
    if choice == "99":
        print("종료합니다.")
        return
    
    # 선택된 문헌 목록
    selected = []
    if choice == "0":
        selected = list(WIKISOURCE_COLLECTIONS.items())
    else:
        try:
            idx = int(choice) - 1
            all_items = list(WIKISOURCE_COLLECTIONS.items())
            if 0 <= idx < len(all_items):
                name = all_items[idx][0]
                selected = [(name, all_items[idx][1])]
        except:
            print("잘못된 선택입니다.")
            return
    
    if not selected:
        print("선택된 문헌이 없습니다.")
        return
    
    print(f"\n{len(selected)}개 문헌 수집 시작...")
    
    # Playwright 실행
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 브라우저 표시
        
        all_results = {}
        
        for book_name, book_info in selected:
            # 번역 방법 결정
            results = await scrape_book(browser, book_name, book_info, translate_method=has_api_key)
            all_results[book_name] = results
            
            # 최종 저장
            if results:
                save_final_output(book_name, results)
        
        await browser.close()
    
    # 요약
    print("\n" + "="*60)
    print("   수집 완료 요약")
    print("="*60)
    
    total_entries = 0
    total_translated = 0
    
    for book_name, entries in all_results.items():
        translated = sum(1 for e in entries if e.get('korean'))
        print(f"  {book_name}: {len(entries)}개 항목, {translated}개 번역")
        total_entries += len(entries)
        total_translated += translated
    
    print(f"\n총 {total_entries}개 항목 수집, {total_translated}개 번역 완료")
    print(f"\n저장 위치:")
    print(f"  - 원문: {RAW_DIR}")
    print(f"  - 번역: {PROCESSED_DIR}")


if __name__ == "__main__":
    asyncio.run(main())