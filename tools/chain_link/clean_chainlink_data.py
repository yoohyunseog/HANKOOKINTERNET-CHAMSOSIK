import json

INPUT_FILE = 'data.json'
OUTPUT_FILE = 'clean_chainlink_data.json'

# 정상 JSON 데이터만 추출
clean_results = []

with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    results = json.load(f)

for item in results:
    # JSON 배열/객체만 추출
    if isinstance(item, list):
        clean_results.extend(item)
    elif isinstance(item, dict):
        # 주요 필드가 모두 있으면 추가
        if all(k in item for k in ['timestamp', 'location', 'price', 'unit', 'source']):
            clean_results.append(item)
        # dict 내부에 배열이 있을 경우
        elif 'data' in item and isinstance(item['data'], list):
            clean_results.extend(item['data'])
        elif 'records' in item and isinstance(item['records'], list):
            clean_results.extend(item['records'])

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(clean_results, f, ensure_ascii=False, indent=2)

print(f"정상 Chainlink 데이터가 {OUTPUT_FILE}에 저장되었습니다.")
