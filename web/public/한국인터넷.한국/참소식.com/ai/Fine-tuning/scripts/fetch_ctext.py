"""
Chinese Text Project (ctext.org) 원문 수집 스크립트
선진·한대 문헌의 원문을 수집합니다.
"""

import requests
import json
import time
import os
from pathlib import Path
from urllib.parse import quote

# 기본 설정
BASE_URL = "https://ctext.org"
API_URL = "https://api.ctext.org"
RAW_DIR = Path(__file__).parent.parent / "raw"

# 수집할 문헌 목록
COLLECTIONS = {
    "논어": {
        "id": "analects",
        "chinese": "論語",
        "type": "유가",
        "period": "춘추전국"
    },
    "맹자": {
        "id": "mengzi",
        "chinese": "孟子",
        "type": "유가",
        "period": "춘추전국"
    },
    "순자": {
        "id": "xunzi",
        "chinese": "荀子",
        "type": "유가",
        "period": "춘추전국"
    },
    "사기": {
        "id": "shiji",
        "chinese": "史記",
        "type": "정사",
        "period": "한대"
    },
    "한서": {
        "id": "hanshu",
        "chinese": "漢書",
        "type": "정사",
        "period": "한대"
    },
    "삼국지": {
        "id": "sanguozhi",
        "chinese": "三國志",
        "type": "정사",
        "period": "삼국시대"
    }
}

# 사기 중 초한 관련 편
CHU_HAN_CHAPTERS = [
    "항우본기",      # Xiang Yu Benji
    "고조본기",      # Gaozu Benji  
    "회음후열전",    # Huaiyin Hou Liezhuan
    "유후세가",      # Liu Hou Shijia
    "소상국세가",    # Xiao Xiangguo Shijia
    "진초지제월표"   # Qin Chu Zhi Yue Biao
]


def fetch_text_content(text_id: str, lang: str = "zh") -> dict:
    """
    Chinese Text Project API에서 텍스트 내용을 가져옵니다.
    
    Args:
        text_id: 텍스트 ID (예: "analects", "shiji")
        lang: 언어 코드 (zh: 중국어 원문)
    
    Returns:
        API 응답 딕셔너리
    """
    url = f"{API_URL}/gettext"
    params = {
        "urn": f"ctp:{text_id}",
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"[ERROR] {text_id} 수집 실패: {e}")
        return None


def fetch_chapter_list(text_id: str) -> list:
    """
    문헌의 장(篇) 목록을 가져옵니다.
    """
    url = f"{API_URL}/getchapters"
    params = {
        "urn": f"ctp:{text_id}",
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("chapters", [])
    except requests.RequestException as e:
        print(f"[ERROR] {text_id} 장 목록 가져오기 실패: {e}")
        return []


def fetch_chapter_content(text_id: str, chapter_id: str) -> dict:
    """
    특정 장의 내용을 가져옵니다.
    """
    url = f"{API_URL}/gettext"
    params = {
        "urn": f"ctp:{text_id}/{chapter_id}",
        "format": "json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"[ERROR] {text_id}/{chapter_id} 수집 실패: {e}")
        return None


def save_raw_text(book_name: str, content: str, chapter: str = None):
    """
    원문을 파일로 저장합니다.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    if chapter:
        filename = f"{book_name}_{chapter}.txt"
    else:
        filename = f"{book_name}.txt"
    
    filepath = RAW_DIR / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"[SAVED] {filepath}")
    return filepath


def collect_book(book_key: str, book_info: dict):
    """
    단일 문헌을 수집합니다.
    """
    print(f"\n{'='*50}")
    print(f"[수집 시작] {book_key} ({book_info['chinese']})")
    print(f"{'='*50}")
    
    text_id = book_info["id"]
    
    # 장 목록 가져오기
    chapters = fetch_chapter_list(text_id)
    
    if not chapters:
        print(f"[WARN] {book_key}의 장 목록을 찾을 수 없습니다. 전체 텍스트를 시도합니다.")
        data = fetch_text_content(text_id)
        if data and "content" in data:
            save_raw_text(book_key, data["content"])
        return
    
    # 각 장 수집
    all_content = []
    for chapter in chapters:
        chapter_id = chapter.get("id") or chapter.get("key", "")
        chapter_name = chapter.get("title", chapter_id)
        
        print(f"  - {chapter_name} 수집 중...")
        
        data = fetch_chapter_content(text_id, chapter_id)
        if data and "content" in data:
            content = data["content"]
            all_content.append(f"=== {chapter_name} ===\n{content}")
            
            # 개별 장 저장
            save_raw_text(book_key, content, chapter_id)
        
        # API 호출 간격 (서버 부하 방지)
        time.sleep(1)
    
    # 전체 문헌 저장
    if all_content:
        full_content = "\n\n".join(all_content)
        save_raw_text(book_key, full_content)
    
    print(f"[완료] {book_key} 수집 완료")


def collect_chu_han_sections():
    """
    사기에서 초한 관련 편만 따로 수집합니다.
    """
    print(f"\n{'='*50}")
    print("[수집 시작] 사기 초한 관련 편")
    print(f"{'='*50}")
    
    # 사기 장 목록 가져오기
    chapters = fetch_chapter_list("shiji")
    
    # 초한 관련 편 ID 매핑 (실제 API ID는 확인 필요)
    chu_han_ids = {
        "항우본기": "xiangyu",
        "고조본기": "gaozu",
        "회음후열전": "huaiyin",
        "유후세가": "liuhou",
        "소상국세가": "xiaoxiangguo"
    }
    
    for korean_name, chapter_id in chu_han_ids.items():
        print(f"  - {korean_name} 수집 중...")
        data = fetch_chapter_content("shiji", chapter_id)
        
        if data and "content" in data:
            save_raw_text("사기_초한", data["content"], korean_name)
        
        time.sleep(1)
    
    print("[완료] 사기 초한 관련 편 수집 완료")


def main():
    """
    메인 실행 함수
    """
    print("="*60)
    print("Chinese Text Project 원문 수집기")
    print("="*60)
    print("\n[주의] 이 스크립트는 ctext.org의 API를 사용합니다.")
    print("과도한 요청은 서버에 부하를 줄 수 있으니 적절한 간격을 두세요.\n")
    
    # 수집할 문헌 선택
    print("수집할 문헌:")
    for i, (key, info) in enumerate(COLLECTIONS.items(), 1):
        print(f"  {i}. {key} ({info['chinese']})")
    print(f"  {len(COLLECTIONS)+1}. 사기 초한 관련 편만")
    print(f"  {len(COLLECTIONS)+2}. 전체 수집")
    
    choice = input("\n선택 (번호): ").strip()
    
    try:
        choice_num = int(choice)
        
        if 1 <= choice_num <= len(COLLECTIONS):
            # 단일 문헌 수집
            book_key = list(COLLECTIONS.keys())[choice_num - 1]
            collect_book(book_key, COLLECTIONS[book_key])
        
        elif choice_num == len(COLLECTIONS) + 1:
            # 사기 초한 관련 편만
            collect_chu_han_sections()
        
        elif choice_num == len(COLLECTIONS) + 2:
            # 전체 수집
            for book_key, book_info in COLLECTIONS.items():
                collect_book(book_key, book_info)
                time.sleep(3)  # 문헌 간 간격
            
            collect_chu_han_sections()
        
        else:
            print("[ERROR] 잘못된 선택입니다.")
    
    except ValueError:
        print("[ERROR] 숫자를 입력하세요.")
    
    print("\n" + "="*60)
    print("수집 완료!")
    print("="*60)


if __name__ == "__main__":
    main()