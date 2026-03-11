import sys
import requests
import json

OLLAMA_URL = "http://localhost:11434/v1/chat/completions"

def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_table_from_mmd.py <mmd_file> <output_file> [OLLAMA_MODEL]")
        sys.exit(1)
    mmd_file = sys.argv[1]
    output_file = sys.argv[2]
    OLLAMA_MODEL = sys.argv[3] if len(sys.argv) > 3 else "gpt-oss:120b-cloud"
    with open(mmd_file, 'r', encoding='utf-8') as f:
        mmd_content = f.read()
    # 결과 파일 디렉터리 자동 생성
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    prompt = (
        "아래는 mermaid .mmd 다이어그램입니다. 이 구조를 반드시 아래 예시처럼 item 배열(JSON)로 변환해줘. "
        "모든 노드와 관계는 item 배열에 담고, 각 item은 type(\"node\" 또는 \"edge\") 필드를 반드시 포함해야 해. "
        "필드명은 id, type, name, value, text, source, target, label, importance 중 해당되는 것만 사용.\n"
        "예시:\n"
        """
        [
          {"type": "node", "id": "A", "name": "KOSPI", "value": "5,532.59"},
          {"type": "node", "id": "B", "name": "KOSPI_설명", "text": "KOSPI가 5,532.59에 나타나고 있습니다."},
          {"type": "edge", "source": "A", "target": "B", "label": "중요", "importance": "high"}
        ]
        """
        "\n이 형식으로만 변환해서 반환해. 다른 설명, 마크다운, 코드블록 없이 item 배열(JSON)만 반환.\n\n"
        + mmd_content
    )
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(OLLAMA_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        try:
            data = response.json()
        except Exception as e:
            print(f"Ollama API 응답이 JSON이 아님: {e}\n응답 내용: {response.text}")
            sys.exit(2)
        # 응답 구조 확인
        if not data or "choices" not in data or not data["choices"]:
            print(f"Ollama API 응답에 choices가 없음. 전체 응답: {data}")
            sys.exit(2)
        result = data["choices"][0]["message"].get("content", "").strip()
        if not result:
            print(f"Ollama API 응답에 content가 비어있음. 전체 응답: {data}")
            sys.exit(2)
        # content에서 ```json 코드블록만 robust하게 추출
        import re
        json_block = None
        # 1. ```json ... ``` 블록 추출
        match = re.search(r"```json\s*([\s\S]+?)\s*```", result)
        if match:
            json_block = match.group(1)
        else:
            # 2. fallback: 첫 번째 { ... } 블록 추출
            match2 = re.search(r"{[\s\S]*}", result)
            if match2:
                json_block = match2.group(0)
        if not json_block:
            print(f"Ollama content에서 JSON 블록을 찾을 수 없음. content: {result}")
            sys.exit(2)
        try:
            result_json = json.loads(json_block)
        except Exception as e:
            print(f"Ollama content에서 추출한 JSON 파싱 실패: {e}\n추출된 JSON 블록: {json_block}")
            sys.exit(2)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, ensure_ascii=False, indent=2)
        print(f"변환 결과가 {output_file}에 저장되었습니다.")
    except Exception as e:
        print(f"Ollama API 호출 실패: {e}\n응답 내용: {getattr(e, 'response', None) and e.response.text}")
        sys.exit(2)

if __name__ == "__main__":
    main()