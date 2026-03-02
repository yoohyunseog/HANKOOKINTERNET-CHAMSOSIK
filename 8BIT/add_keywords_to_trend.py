"""
키워드를 latest_trend_data.json에 추가하는 스크립트
"""

import json
import os
import sys
from datetime import datetime

def add_keywords_to_trend_data(keywords, category="custom"):
    """
    키워드 리스트를 latest_trend_data.json에 추가
    
    Args:
        keywords: 추가할 키워드 리스트
        category: 카테고리명 (비트코인, 주식, 애니메이션 등)
    """
    data_file = "data/naver_creator_trends/latest_trend_data.json"
    
    # JSON 파일 읽기
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        print(f"❌ {data_file} 파일이 없습니다.")
        return False
    
    # 기존 trend_data 확인
    if 'trend_data' not in data:
        data['trend_data'] = []
    
    # 마지막 index 찾기
    last_index = 0
    for item in data['trend_data']:
        if 'index' in item and item['index'] > last_index:
            last_index = item['index']
    
    # 새 키워드 추가
    added_count = 0
    timestamp = datetime.now().isoformat()
    
    for keyword in keywords:
        keyword = keyword.strip()
        if not keyword:
            continue
            
        # 중복 확인
        is_duplicate = False
        for item in data['trend_data']:
            if keyword in item.get('keywords', []):
                is_duplicate = True
                break
        
        if is_duplicate:
            print(f"⏭️ 건너뜀 (중복): {keyword}")
            continue
        
        # 새 항목 생성
        last_index += 1
        new_item = {
            "index": last_index,
            "timestamp": timestamp,
            "title": f"{category} 키워드",
            "keywords": [keyword],
            "metrics": {},
            "raw_text": keyword,
            "element_tag": "custom",
            "element_class": f"custom_{category}",
            "links": [],
            "category": category
        }
        
        data['trend_data'].append(new_item)
        added_count += 1
        print(f"✅ 추가됨: {keyword}")
    
    # JSON 파일 저장
    if added_count > 0:
        data['collection_time'] = datetime.now().isoformat()
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 총 {added_count}개 키워드가 추가되었습니다.")
        print(f"📁 파일 위치: {data_file}")
        return True
    else:
        print("\n⏭️ 추가된 키워드가 없습니다.")
        return False


def read_keywords_from_file(filename):
    """파일에서 키워드 읽기 (한 줄에 하나씩)"""
    if not os.path.exists(filename):
        return []
    
    with open(filename, 'r', encoding='utf-8') as f:
        keywords = [line.strip() for line in f.readlines()]
    
    return [k for k in keywords if k]  # 빈 줄 제거


def main():
    """메인 함수"""
    print("""
    ╔══════════════════════════════════════════════════╗
    ║       키워드 추가 스크립트                        ║
    ║   Add Keywords to Trend Data                     ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    # 명령줄 인자로 파일명과 카테고리 받기
    if len(sys.argv) >= 3:
        keyword_file = sys.argv[1]
        category = sys.argv[2]
        
        if os.path.exists(keyword_file):
            print(f"📂 파일 읽기: {keyword_file}")
            print(f"🏷️ 카테고리: {category}\n")
            
            keywords = read_keywords_from_file(keyword_file)
            if keywords:
                add_keywords_to_trend_data(keywords, category)
            else:
                print(f"❌ {keyword_file}에 키워드가 없습니다.")
        else:
            print(f"❌ 파일을 찾을 수 없습니다: {keyword_file}")
    else:
        print("사용법: py add_keywords_to_trend.py <키워드파일> <카테고리>")
        print("예시: py add_keywords_to_trend.py temp_bitcoin_keywords.txt 비트코인")


if __name__ == "__main__":
    main()
