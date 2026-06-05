"""
위키문헌 (Wikisource) 원문/번역 수집 스크립트
한국어 위키문헌과 중국어 위키문헌에서 자유 저작물을 수집합니다.
"""

import requests
import json
import time
import re
from pathlib import Path
from urllib.parse import quote

# 기본 설정
RAW_DIR = Path(__file__).parent.parent / "raw"

# 위키문헌 API 엔드포인트
WIKISOURCE_KO = "https://ko.wikisource.org/w/api.php"
WIKISOURCE_ZH = "https://zh.wikisource.org/w/api.php"
WIKISOURCE_EN = "https://en.wikisource.org/w/api.php"

# 수집할 문헌 목록
DOCUMENTS = {
    "논어": {
        "ko": "논어",
        "zh": "论语",
        "wikisource_ko": "논어",
        "wikisource_zh": "论语"
    },
    "맹자": {
        "ko": "맹자",
        "zh": "孟子",
        "wikisource_ko": "맹자",
        "wikisource_zh": "孟子"
    },
    "사기": {
        "ko": "사기",
        "zh": "史记",
        "wikisource_ko": "사기",
        "wikisource_zh": "史记"
    },
    "한서": {
        "ko": "한서",
        "zh": "汉书",
        "wikisource_ko": "한서",
        "wikisource_zh": "汉书"
    },
    "삼국지": {
        "ko": "삼국지",
        "zh": "三国志",
        "wikisource_ko": "삼국지",
        "wikisource_zh": "三国志"
    }
}


def fetch_wikisource_page(title: str, lang: str = "ko") -> dict:
    """
    위키문헌에서 페이지 내용을 가져옵니다.
    
    Args:
        title: 문서 제목
        lang: 언어 코드 (ko, zh, en)
    
    Returns:
        API 응답 딕셔너리
    """
    api_url = {
        "ko": WIKISOURCE_KO,
        "zh": WIKISOURCE_ZH,
        "en": WIKISOURCE_EN
    }.get(lang, WIKISOURCE_KO)
    
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "extracts",
        "explaintext": True,
        "exsectionformat": "plain"
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"[ERROR] {title} ({lang}) 수집 실패: {e}")
        return None


def fetch_wikisource_raw(title: str, lang: str = "ko") -> str:
    """
    위키문헌에서 원본 위키 텍스트를 가져옵니다.
    """
    api_url = {
        "ko": WIKISOURCE_KO,
        "zh": WIKISOURCE_ZH,
        "en": WIKISOURCE_EN
    }.get(lang, WIKISOURCE_KO)
    
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main"
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # 페이지 ID 추출
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if page_id != "-1":  # 존재하는 페이지
                revisions = page_data.get("revisions", [])
                if revisions:
                    return revisions[0].get("slots", {}).get("main", {}).get("*", "")
        
        return None
    
    except requests.RequestException as e:
        print(f"[ERROR] {title} ({lang}) 원문 수집 실패: {e}")
        return None


def parse_wiki_text(wiki_text: str) -> str:
    """
    위키 텍스트에서 텍스트 내용을 추출합니다.
    간단한 파싱만 수행합니다.
    """
    if not wiki_text:
        return ""
    
    # 위키 링크 제거
    text = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]', r'\2', wiki_text)
    
    # 템플릿 제거
    text = re.sub(r'\{\{[^}]+\}\}', '', text)
    
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    
    # 주석 제거
    text = re.sub(r'<!--[^>]+-->', '', text)
    
    # 여러 공백 정리
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()


def save_raw_text(book_name: str, content: str, suffix: str = ""):
    """
    원문을 파일로 저장합니다.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    filename = f"{book_name}{suffix}.txt" if suffix else f"{book_name}.txt"
    filepath = RAW_DIR / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"[SAVED] {filepath}")
    return filepath


def collect_from_wikisource(book_key: str, doc_info: dict):
    """
    위키문헌에서 문헌을 수집합니다.
    """
    print(f"\n{'='*50}")
    print(f"[수집 시작] {book_key}")
    print(f"{'='*50}")
    
    # 한국어 위키문헌에서 수집
    if "wikisource_ko" in doc_info:
        print(f"  한국어 위키문헌에서 수집 중...")
        wiki_text = fetch_wikisource_raw(doc_info["wikisource_ko"], "ko")
        if wiki_text:
            content = parse_wiki_text(wiki_text)
            if content:
                save_raw_text(book_key, content, "_ko_wikisource")
        time.sleep(1)
    
    # 중국어 위키문헌에서 수집 (원문)
    if "wikisource_zh" in doc_info:
        print(f"  중국어 위키문헌에서 수집 중...")
        wiki_text = fetch_wikisource_raw(doc_info["wikisource_zh"], "zh")
        if wiki_text:
            content = parse_wiki_text(wiki_text)
            if content:
                save_raw_text(book_key, content, "_zh_wikisource")
        time.sleep(1)
    
    print(f"[완료] {book_key} 위키문헌 수집 완료")


def search_wikisource(query: str, lang: str = "ko") -> list:
    """
    위키문헌에서 문서를 검색합니다.
    """
    api_url = {
        "ko": WIKISOURCE_KO,
        "zh": WIKISOURCE_ZH,
        "en": WIKISOURCE_EN
    }.get(lang, WIKISOURCE_KO)
    
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "srlimit": 20
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("query", {}).get("search", [])
    except requests.RequestException as e:
        print(f"[ERROR] 검색 실패: {e}")
        return []


def main():
    """
    메인 실행 함수
    """
    print("="*60)
    print("위키문헌 원문/번역 수집기")
    print("="*60)
    print("\n[주의] 위키문헌은 자유 저작물만 게재합니다.")
    print("하지만 수집 전 라이선스를 확인하세요.\n")
    
    # 수집할 문헌 선택
    print("수집할 문헌:")
    for i, (key, info) in enumerate(DOCUMENTS.items(), 1):
        print(f"  {i}. {key}")
    print(f"  {len(DOCUMENTS)+1}. 전체 수집")
    print(f"  {len(DOCUMENTS)+2}. 검색 모드")
    
    choice = input("\n선택 (번호): ").strip()
    
    try:
        choice_num = int(choice)
        
        if 1 <= choice_num <= len(DOCUMENTS):
            # 단일 문헌 수집
            book_key = list(DOCUMENTS.keys())[choice_num - 1]
            collect_from_wikisource(book_key, DOCUMENTS[book_key])
        
        elif choice_num == len(DOCUMENTS) + 1:
            # 전체 수집
            for book_key, doc_info in DOCUMENTS.items():
                collect_from_wikisource(book_key, doc_info)
                time.sleep(2)
        
        elif choice_num == len(DOCUMENTS) + 2:
            # 검색 모드
            query = input("검색어: ").strip()
            lang = input("언어 (ko/zh/en): ").strip() or "ko"
            
            results = search_wikisource(query, lang)
            print(f"\n검색 결과 ({len(results)}개):")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result.get('title', '제목 없음')}")
            
            if results:
                doc_choice = input("\n수집할 문서 번호: ").strip()
                try:
                    doc_idx = int(doc_choice) - 1
                    if 0 <= doc_idx < len(results):
                        title = results[doc_idx]["title"]
                        wiki_text = fetch_wikisource_raw(title, lang)
                        if wiki_text:
                            content = parse_wiki_text(wiki_text)
                            # 파일명 정리
                            safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)
                            save_raw_text(safe_title, content, f"_{lang}_wikisource")
                except ValueError:
                    print("[ERROR] 숫자를 입력하세요.")
        
        else:
            print("[ERROR] 잘못된 선택입니다.")
    
    except ValueError:
        print("[ERROR] 숫자를 입력하세요.")
    
    print("\n" + "="*60)
    print("수집 완료!")
    print("="*60)


if __name__ == "__main__":
    main()