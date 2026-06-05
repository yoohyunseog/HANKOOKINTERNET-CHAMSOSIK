"""
원문 텍스트를 JSONL 형식으로 변환하는 스크립트
RAG 및 파인튜닝용 데이터 생성
"""

import json
import re
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# 기본 경로
BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"
METADATA_DIR = BASE_DIR / "metadata"

# 문헌 메타데이터
BOOK_METADATA = {
    "논어": {
        "book": "논어",
        "chinese": "論語",
        "type": "유가",
        "period": "춘추전국",
        "author": "공자 및 제자",
        "chapters": ["학이", "위정", "팔일", "이인", "공야장", "옹야", "술이", "태백", "자한", "향당", "선진", "안연", "자로", "헌문", "위령공", "계씨", "양화", "미자", "자장", "요왈"]
    },
    "맹자": {
        "book": "맹자",
        "chinese": "孟子",
        "type": "유가",
        "period": "춘추전국",
        "author": "맹자",
        "chapters": ["양혜왕 상", "양혜왕 하", "공손추 상", "공손추 하", "등문공 상", "등문공 하", "이루 상", "이루 하", "만장 상", "만장 하", "고자 상", "고자 하", "진심 상", "진심 하"]
    },
    "순자": {
        "book": "순자",
        "chinese": "荀子",
        "type": "유가",
        "period": "춘추전국",
        "author": "순자",
        "chapters": ["권학", "수신", "불구", "영악", "비상", "비자", "중니", "유좌", "왕제", "왕패", "군도", "신앙", "예론", "악론", "치사", "강국", "천론", "정론", "예론", "악론", "해폐", "정명", "성악", "군자", "비상", "지사", "자도", "요문", "견문"]
    },
    "사기": {
        "book": "사기",
        "chinese": "史記",
        "type": "정사",
        "period": "한대",
        "author": "사마천",
        "chapters": []
    },
    "한서": {
        "book": "한서",
        "chinese": "漢書",
        "type": "정사",
        "period": "한대",
        "author": "반고",
        "chapters": []
    },
    "삼국지": {
        "book": "삼국지",
        "chinese": "三國志",
        "type": "정사",
        "period": "삼국시대",
        "author": "진수",
        "chapters": ["위서", "촉서", "오서"]
    },
    "사기_초한": {
        "book": "사기",
        "chinese": "史記",
        "type": "정사",
        "period": "초한쟁패",
        "author": "사마천",
        "chapters": ["항우본기", "고조본기", "회음후열전", "유후세가", "소상국세가"]
    }
}

# 인물 데이터 (초기 데이터)
PEOPLE_DATA = [
    {"id": "confucius", "name": "공자", "chinese": "孔子", "period": "춘추시대", "type": "사상가"},
    {"id": "mencius", "name": "맹자", "chinese": "孟子", "period": "춘추전국", "type": "사상가"},
    {"id": "xunzi", "name": "순자", "chinese": "荀子", "period": "춘추전국", "type": "사상가"},
    {"id": "simaqian", "name": "사마천", "chinese": "司馬遷", "period": "한대", "type": "역사가"},
    {"id": "banggu", "name": "반고", "chinese": "班固", "period": "한대", "type": "역사가"},
    {"id": "chenshou", "name": "진수", "chinese": "陳壽", "period": "서진", "type": "역사가"},
    {"id": "xiangyu", "name": "항우", "chinese": "項羽", "period": "초한쟁패", "type": "군주"},
    {"id": "liubang", "name": "유방", "chinese": "劉邦", "period": "초한쟁패", "type": "군주"},
    {"id": "hanxin", "name": "한신", "chinese": "韓信", "period": "초한쟁패", "type": "장군"},
    {"id": "zhangliang", "name": "장량", "chinese": "張良", "period": "초한쟁패", "type": "모사"},
    {"id": "caocao", "name": "조조", "chinese": "曹操", "period": "삼국시대", "type": "군주"},
    {"id": "liubei", "name": "유비", "chinese": "劉備", "period": "삼국시대", "type": "군주"},
    {"id": "sunquan", "name": "손권", "chinese": "孫權", "period": "삼국시대", "type": "군주"},
]

# 시대 데이터
PERIODS_DATA = [
    {"id": "spring_autumn", "name": "춘추시대", "chinese": "春秋時代", "year_range": "BC 770-476"},
    {"id": "warring_states", "name": "전국시대", "chinese": "戰國時代", "year_range": "BC 475-221"},
    {"id": "qin", "name": "진나라", "chinese": "秦朝", "year_range": "BC 221-206"},
    {"id": "chu_han", "name": "초한쟁패", "chinese": "楚漢爭霸", "year_range": "BC 206-202"},
    {"id": "western_han", "name": "전한", "chinese": "西漢", "year_range": "BC 202-AD 8"},
    {"id": "eastern_han", "name": "후한", "chinese": "東漢", "year_range": "AD 25-220"},
    {"id": "three_kingdoms", "name": "삼국시대", "chinese": "三國時代", "year_range": "AD 220-280"},
]

# 키워드 데이터
KEYWORDS_DATA = [
    {"keyword": "군자", "chinese": "君子", "category": "유가사상"},
    {"keyword": "인", "chinese": "仁", "category": "유가사상"},
    {"keyword": "의", "chinese": "義", "category": "유가사상"},
    {"keyword": "예", "chinese": "禮", "category": "유가사상"},
    {"keyword": "지", "chinese": "智", "category": "유가사상"},
    {"keyword": "신", "chinese": "信", "category": "유가사상"},
    {"keyword": "효", "chinese": "孝", "category": "유가사상"},
    {"keyword": "충", "chinese": "忠", "category": "유가사상"},
    {"keyword": "천명", "chinese": "天命", "category": "유가사상"},
    {"keyword": "수양", "chinese": "修身", "category": "유가사상"},
    {"keyword": "치국", "chinese": "治國", "category": "정치"},
    {"keyword": "평천하", "chinese": "平天下", "category": "정치"},
    {"keyword": "왕도", "chinese": "王道", "category": "정치"},
    {"keyword": "패도", "chinese": "霸道", "category": "정치"},
    {"keyword": "전쟁", "chinese": "戰爭", "category": "군사"},
    {"keyword": "모략", "chinese": "謀略", "category": "군사"},
    {"keyword": "병법", "chinese": "兵法", "category": "군사"},
]


def parse_lunyu(text: str) -> List[Dict]:
    """
    논어 텍스트를 파싱하여 JSONL 형식으로 변환합니다.
    """
    entries = []
    lines = text.strip().split("\n")
    
    current_chapter = "학이"
    current_section = 1
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 장 구분 (예: "學而第一" 또는 "학이 제1")
        chapter_match = re.match(r'^(學而|為政|八佾|里仁|公冶長|雍也|述而|泰伯|子罕|鄉黨|先進|顏淵|子路|憲問|衛靈公|季氏|陽貨|微子|子張|堯曰)', line)
        if chapter_match:
            chapter_chinese = chapter_match.group(1)
            # 한국어 장명 매핑
            chapter_map = {
                "學而": "학이", "為政": "위정", "八佾": "팔일", "里仁": "이인",
                "公冶長": "공야장", "雍也": "옹야", "述而": "술이", "泰伯": "태백",
                "子罕": "자한", "鄉黨": "향당", "先進": "선진", "顏淵": "안연",
                "子路": "자로", "憲問": "헌문", "衛靈公": "위령공", "季氏": "계씨",
                "陽貨": "양화", "微子": "미자", "子張": "자장", "堯曰": "요왈"
            }
            current_chapter = chapter_map.get(chapter_chinese, chapter_chinese)
            current_section = 1
            continue
        
        # 구절 파싱 (간단한 형식)
        # 예: "子曰：學而時習之，不亦說乎？"
        if "曰" in line or "子" in line:
            entry = {
                "id": f"lunyu_{current_chapter}_{current_section:03d}",
                "book": "논어",
                "chapter": current_chapter,
                "type": "유가",
                "period": "춘추전국",
                "original": line,
                "korean": "",  # 번역은 별도 처리
                "people": extract_people(line),
                "keywords": extract_keywords(line)
            }
            entries.append(entry)
            current_section += 1
    
    return entries


def parse_shiji(text: str, chapter_name: str = None) -> List[Dict]:
    """
    사기 텍스트를 파싱하여 JSONL 형식으로 변환합니다.
    """
    entries = []
    
    # 문단 단위로 분리
    paragraphs = re.split(r'\n\s*\n', text.strip())
    
    section_num = 1
    for para in paragraphs:
        para = para.strip()
        if not para or len(para) < 10:  # 너무 짧은 문단 제외
            continue
        
        # 문장 단위 분리 (간단히)
        sentences = re.split(r'[。！？\n]', para)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        for i, sentence in enumerate(sentences):
            if len(sentence) < 5:  # 너무 짧은 문장 제외
                continue
            
            entry = {
                "id": f"shiji_{chapter_name or 'unknown'}_{section_num:03d}_{i+1:02d}",
                "book": "사기",
                "chapter": chapter_name or "미상",
                "type": "정사",
                "period": "한대",
                "original": sentence,
                "korean": "",
                "people": extract_people(sentence),
                "keywords": extract_keywords(sentence)
            }
            entries.append(entry)
        
        section_num += 1
    
    return entries


def parse_sanguozhi(text: str) -> List[Dict]:
    """
    삼국지 텍스트를 파싱하여 JSONL 형식으로 변환합니다.
    """
    entries = []
    
    # 위서, 촉서, 오서 구분
    sections = {
        "위서": None,
        "촉서": None,
        "오서": None
    }
    
    current_section = "위서"
    paragraphs = text.strip().split("\n")
    
    section_num = 1
    for line in paragraphs:
        line = line.strip()
        if not line:
            continue
        
        # 섹션 구분
        if "魏書" in line or "위서" in line:
            current_section = "위서"
            continue
        elif "蜀書" in line or "촉서" in line:
            current_section = "촉서"
            continue
        elif "吳書" in line or "오서" in line:
            current_section = "오서"
            continue
        
        # 문장 처리
        if len(line) > 10:
            entry = {
                "id": f"sanguozhi_{current_section}_{section_num:03d}",
                "book": "삼국지",
                "chapter": current_section,
                "type": "정사",
                "period": "삼국시대",
                "original": line,
                "korean": "",
                "people": extract_people(line),
                "keywords": extract_keywords(line)
            }
            entries.append(entry)
            section_num += 1
    
    return entries


def extract_people(text: str) -> List[str]:
    """
    텍스트에서 인물명을 추출합니다.
    """
    people = []
    
    # 알려진 인물 패턴
    known_people = [
        ("공자", "孔子"), ("맹자", "孟子"), ("순자", "荀子"),
        ("항우", "項羽"), ("유방", "劉邦"), ("한신", "韓信"),
        ("장량", "張良"), ("조조", "曹操"), ("유비", "劉備"),
        ("손권", "孫權"), ("관우", "關羽"), ("장비", "張飛"),
        ("제갈량", "諸葛亮"), ("주유", "周瑜"), ("여포", "呂布"),
    ]
    
    for korean, chinese in known_people:
        if chinese in text or korean in text:
            people.append(korean)
    
    return people


def extract_keywords(text: str) -> List[str]:
    """
    텍스트에서 키워드를 추출합니다.
    """
    keywords = []
    
    keyword_patterns = [
        ("군자", "君子"), ("인", "仁"), ("의", "義"), ("예", "禮"),
        ("지", "智"), ("신", "信"), ("효", "孝"), ("충", "忠"),
        ("전쟁", "戰爭"), ("모략", "謀略"), ("병법", "兵法"),
        ("천명", "天命"), ("왕도", "王道"),
    ]
    
    for korean, chinese in keyword_patterns:
        if chinese in text or korean in text:
            keywords.append(korean)
    
    return keywords


def convert_file(input_path: Path, book_key: str, chapter: str = None) -> List[Dict]:
    """
    단일 파일을 JSONL로 변환합니다.
    """
    print(f"[변환] {input_path.name}")
    
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    # 문헌별 파서 선택
    if book_key.startswith("논어") or "lunyu" in input_path.name.lower():
        return parse_lunyu(text)
    elif book_key.startswith("사기") or "shiji" in input_path.name.lower():
        return parse_shiji(text, chapter)
    elif book_key.startswith("삼국지") or "sanguozhi" in input_path.name.lower():
        return parse_sanguozhi(text)
    else:
        # 기본 파서 (문장 단위 분리)
        entries = []
        sentences = re.split(r'[。！？\n]', text)
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) > 5:
                entry = {
                    "id": f"{book_key}_{i+1:04d}",
                    "book": book_key,
                    "chapter": chapter or "미상",
                    "type": "미상",
                    "period": "미상",
                    "original": sentence,
                    "korean": "",
                    "people": extract_people(sentence),
                    "keywords": extract_keywords(sentence)
                }
                entries.append(entry)
        
        return entries


def save_jsonl(entries: List[Dict], output_path: Path):
    """
    JSONL 파일로 저장합니다.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    print(f"[SAVED] {output_path} ({len(entries)}개 항목)")


def init_metadata():
    """
    메타데이터 파일을 초기화합니다.
    """
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 인물 데이터
    people_path = METADATA_DIR / "people.json"
    if not people_path.exists():
        with open(people_path, "w", encoding="utf-8") as f:
            json.dump(PEOPLE_DATA, f, ensure_ascii=False, indent=2)
        print(f"[CREATED] {people_path}")
    
    # 시대 데이터
    periods_path = METADATA_DIR / "periods.json"
    if not periods_path.exists():
        with open(periods_path, "w", encoding="utf-8") as f:
            json.dump(PERIODS_DATA, f, ensure_ascii=False, indent=2)
        print(f"[CREATED] {periods_path}")
    
    # 키워드 데이터
    keywords_path = METADATA_DIR / "keywords.json"
    if not keywords_path.exists():
        with open(keywords_path, "w", encoding="utf-8") as f:
            json.dump(KEYWORDS_DATA, f, ensure_ascii=False, indent=2)
        print(f"[CREATED] {keywords_path}")


def main():
    """
    메인 실행 함수
    """
    print("="*60)
    print("원문 → JSONL 변환기")
    print("="*60)
    
    # 메타데이터 초기화
    init_metadata()
    
    # raw 폴더의 파일 목록
    raw_files = list(RAW_DIR.glob("*.txt"))
    
    if not raw_files:
        print("\n[WARN] raw 폴더에 변환할 파일이 없습니다.")
        print("먼저 fetch_ctext.py, fetch_wikisource.py, fetch_gutenberg.py를 실행하세요.")
        return
    
    print(f"\n변환 가능한 파일 ({len(raw_files)}개):")
    for i, f in enumerate(raw_files, 1):
        print(f"  {i}. {f.name}")
    
    print(f"\n  {len(raw_files)+1}. 전체 변환")
    
    choice = input("\n선택 (번호): ").strip()
    
    try:
        choice_num = int(choice)
        
        if 1 <= choice_num <= len(raw_files):
            # 단일 파일 변환
            file_path = raw_files[choice_num - 1]
            book_key = file_path.stem
            
            entries = convert_file(file_path, book_key)
            
            if entries:
                output_path = PROCESSED_DIR / f"{book_key}.jsonl"
                save_jsonl(entries, output_path)
        
        elif choice_num == len(raw_files) + 1:
            # 전체 변환
            for file_path in raw_files:
                book_key = file_path.stem
                entries = convert_file(file_path, book_key)
                
                if entries:
                    output_path = PROCESSED_DIR / f"{book_key}.jsonl"
                    save_jsonl(entries, output_path)
        
        else:
            print("[ERROR] 잘못된 선택입니다.")
    
    except ValueError:
        print("[ERROR] 숫자를 입력하세요.")
    
    print("\n" + "="*60)
    print("변환 완료!")
    print("="*60)


if __name__ == "__main__":
    main()