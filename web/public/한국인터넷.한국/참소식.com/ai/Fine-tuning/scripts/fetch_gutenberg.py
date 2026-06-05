"""
Project Gutenberg 원문 수집 스크립트
삼국지, 삼국지연의 등 공개 텍스트를 수집합니다.
"""

import requests
import json
import time
import re
from pathlib import Path
from urllib.parse import quote

# 기본 설정
RAW_DIR = Path(__file__).parent.parent / "raw"
GUTENBERG_API = "https://gutendex.com"
GUTENBERG_BASE = "https://www.gutenberg.org"

# 수집할 문헌 목록 (Gutenberg ID)
BOOKS = {
    "삼국지_정사": {
        "title": "San Guo Zhi",
        "author": "Chen Shou",
        "gutenberg_id": None,  # 직접 검색 필요
        "chinese": "三國志",
        "note": "진수의 정사 삼국지"
    },
    "삼국지연의": {
        "title": "Romance of the Three Kingdoms",
        "author": "Luo Guanzhong",
        "gutenberg_id": None,
        "chinese": "三國志演義",
        "note": "나관중의 삼국지연의"
    },
    "한서_영문": {
        "title": "History of the Former Han Dynasty",
        "author": "Ban Gu",
        "gutenberg_id": None,
        "chinese": "漢書",
        "note": "반고의 한서 영문 번역"
    }
}

# 알려진 Gutenberg ID (검증 필요)
KNOWN_IDS = {
    # 삼국지 관련
    "sanguozhi_chinese": None,  # 중문 원문은 없을 수 있음
    "three_kingdoms_en": 25606,  # 영문 번역
    
    # 기타 중국 고전 영문 번역
    "analects_en": 735,  # 논어 영문
    "mencius_en": 736,   # 맹자 영문
}


def search_gutenberg(query: str, lang: str = None) -> list:
    """
    Project Gutenberg에서 책을 검색합니다.
    
    Args:
        query: 검색어
        lang: 언어 코드 (zh, en 등)
    
    Returns:
        검색 결과 리스트
    """
    params = {"search": query}
    if lang:
        params["languages"] = lang
    
    try:
        response = requests.get(f"{GUTENBERG_API}/books", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("results", [])
    except requests.RequestException as e:
        print(f"[ERROR] 검색 실패: {e}")
        return []


def get_book_by_id(book_id: int) -> dict:
    """
    Gutenberg ID로 책 정보를 가져옵니다.
    """
    try:
        response = requests.get(f"{GUTENBERG_API}/books/{book_id}", timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"[ERROR] 책 정보 가져오기 실패: {e}")
        return None


def download_book(book_id: int, format_type: str = "txt") -> str:
    """
    Project Gutenberg에서 책을 다운로드합니다.
    
    Args:
        book_id: Gutenberg 책 ID
        format_type: 형식 (txt, html, epub 등)
    
    Returns:
        책 내용 텍스트
    """
    # 먼저 책 정보를 가져와서 다운로드 URL 확인
    book_info = get_book_by_id(book_id)
    if not book_info:
        return None
    
    # 형식별 URL 찾기
    formats = book_info.get("formats", {})
    
    # 텍스트 형식 우선
    format_urls = {
        "txt": [
            "text/plain; charset=utf-8",
            "text/plain; charset=us-ascii",
            "text/plain",
        ],
        "html": [
            "text/html; charset=utf-8",
            "text/html; charset=us-ascii",
            "text/html",
        ]
    }
    
    download_url = None
    for fmt in format_urls.get(format_type, []):
        if fmt in formats:
            download_url = formats[fmt]
            break
    
    if not download_url:
        # 대안: 직접 URL 구성
        if format_type == "txt":
            download_url = f"{GUTENBERG_BASE}/files/{book_id}/{book_id}-0.txt"
            # 또는
            download_url = f"{GUTENBERG_BASE}/cache/epub/{book_id}/pg{book_id}.txt"
    
    if not download_url:
        print(f"[ERROR] 다운로드 URL을 찾을 수 없습니다.")
        return None
    
    try:
        print(f"  다운로드 중: {download_url}")
        response = requests.get(download_url, timeout=60)
        response.raise_for_status()
        
        # 인코딩 처리
        content = response.content
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = content.decode("iso-8859-1")
            except:
                text = content.decode("utf-8", errors="ignore")
        
        return text
    
    except requests.RequestException as e:
        print(f"[ERROR] 다운로드 실패: {e}")
        return None


def clean_gutenberg_text(text: str) -> str:
    """
    Gutenberg 텍스트에서 헤더/푸터를 제거합니다.
    """
    if not text:
        return ""
    
    # Gutenberg 헤더 제거
    start_markers = [
        "*** START OF THIS PROJECT GUTENBERG EBOOK",
        "*** START OF THE PROJECT GUTENBERG EBOOK",
        "\*\*\* START OF",
    ]
    
    for marker in start_markers:
        pattern = re.escape(marker) + r".*?\n"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            text = text[match.end():]
            break
    
    # Gutenberg 푸터 제거
    end_markers = [
        "*** END OF THIS PROJECT GUTENBERG EBOOK",
        "*** END OF THE PROJECT GUTENBERG EBOOK",
        "\*\*\* END OF",
        "End of the Project Gutenberg",
    ]
    
    for marker in end_markers:
        pattern = re.escape(marker) + r".*"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            text = text[:match.start()]
            break
    
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


def collect_book(book_key: str, book_info: dict):
    """
    Project Gutenberg에서 책을 수집합니다.
    """
    print(f"\n{'='*50}")
    print(f"[수집 시작] {book_key}")
    print(f"{'='*50}")
    
    # 검색
    query = book_info.get("title", book_key)
    print(f"  검색어: {query}")
    
    results = search_gutenberg(query)
    
    if not results:
        print(f"[WARN] 검색 결과 없음")
        return
    
    # 결과 표시
    print(f"\n  검색 결과 ({len(results)}개):")
    for i, result in enumerate(results[:10], 1):
        title = result.get("title", "제목 없음")
        author = result.get("authors", [{}])[0].get("name", "저자 미상") if result.get("authors") else "저자 미상"
        lang = ", ".join(result.get("languages", ["?"]))
        print(f"    {i}. [{lang}] {title} - {author}")
    
    # 사용자 선택
    choice = input("\n  수집할 번호 (0=건너뛰기): ").strip()
    
    try:
        choice_num = int(choice)
        if choice_num == 0:
            return
        if 1 <= choice_num <= len(results):
            selected = results[choice_num - 1]
            book_id = selected.get("id")
            
            if book_id:
                print(f"\n  다운로드 중...")
                text = download_book(book_id)
                
                if text:
                    cleaned = clean_gutenberg_text(text)
                    save_raw_text(book_key, cleaned, "_gutenberg")
                else:
                    print(f"[ERROR] 다운로드 실패")
        else:
            print("[ERROR] 잘못된 선택")
    except ValueError:
        print("[ERROR] 숫자를 입력하세요.")


def main():
    """
    메인 실행 함수
    """
    print("="*60)
    print("Project Gutenberg 원문 수집기")
    print("="*60)
    print("\n[주의] Project Gutenberg은 퍼블릭 도메인 도서만 제공합니다.")
    print("대부분 영문 번역본이며, 중문 원문은 제한적입니다.\n")
    
    # 수집할 문헌 선택
    print("수집할 문헌:")
    for i, (key, info) in enumerate(BOOKS.items(), 1):
        print(f"  {i}. {key} ({info['note']})")
    print(f"  {len(BOOKS)+1}. 직접 검색")
    print(f"  {len(BOOKS)+2}. 알려진 ID로 다운로드")
    
    choice = input("\n선택 (번호): ").strip()
    
    try:
        choice_num = int(choice)
        
        if 1 <= choice_num <= len(BOOKS):
            # 미리 정의된 문헌 수집
            book_key = list(BOOKS.keys())[choice_num - 1]
            collect_book(book_key, BOOKS[book_key])
        
        elif choice_num == len(BOOKS) + 1:
            # 직접 검색
            query = input("검색어: ").strip()
            lang = input("언어 코드 (zh/en, 선택사항): ").strip() or None
            
            results = search_gutenberg(query, lang)
            print(f"\n검색 결과 ({len(results)}개):")
            for i, result in enumerate(results[:10], 1):
                title = result.get("title", "제목 없음")
                author = result.get("authors", [{}])[0].get("name", "저자 미상") if result.get("authors") else "저자 미상"
                print(f"  {i}. {title} - {author}")
            
            if results:
                doc_choice = input("\n수집할 번호: ").strip()
                try:
                    doc_idx = int(doc_choice) - 1
                    if 0 <= doc_idx < len(results):
                        selected = results[doc_idx]
                        book_id = selected.get("id")
                        if book_id:
                            text = download_book(book_id)
                            if text:
                                cleaned = clean_gutenberg_text(text)
                                safe_title = re.sub(r'[\\/:*?"<>|]', '_', selected.get("title", "unknown"))
                                save_raw_text(safe_title, cleaned, "_gutenberg")
                except ValueError:
                    print("[ERROR] 숫자를 입력하세요.")
        
        elif choice_num == len(BOOKS) + 2:
            # 알려진 ID로 다운로드
            print("\n알려진 Gutenberg ID:")
            for i, (key, gid) in enumerate(KNOWN_IDS.items(), 1):
                if gid:
                    print(f"  {i}. {key} (ID: {gid})")
            
            id_choice = input("\n번호 또는 직접 ID 입력: ").strip()
            try:
                if id_choice.isdigit():
                    idx = int(id_choice) - 1
                    keys = [k for k, v in KNOWN_IDS.items() if v]
                    if 0 <= idx < len(keys):
                        key = keys[idx]
                        book_id = KNOWN_IDS[key]
                        text = download_book(book_id)
                        if text:
                            cleaned = clean_gutenberg_text(text)
                            save_raw_text(key, cleaned, "_gutenberg")
                else:
                    book_id = int(id_choice)
                    text = download_book(book_id)
                    if text:
                        cleaned = clean_gutenberg_text(text)
                        save_raw_text(f"gutenberg_{book_id}", cleaned, "")
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