"""
한국어 번역 생성 스크립트
GPT API, Kimi API, Ollama를 사용하여 원문의 한국어 초벌 번역을 생성합니다.
"""

import json
import os
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional

# 기본 경로
BASE_DIR = Path(__file__).parent.parent
PROCESSED_DIR = BASE_DIR / "processed"
METADATA_DIR = BASE_DIR / "metadata"

# API 설정
OLLAMA_API = "http://localhost:11434/api"
OPENAI_API = "https://api.openai.com/v1"
KIMI_API = "https://api.moonshot.cn/v1"  # Kimi API endpoint

# 사용할 모델
DEFAULT_MODEL = "kimi-k2.5"  # Kimi K2.5 Cloud 기본


def translate_with_ollama(text: str, model: str = "qwen2:7b") -> str:
    """
    Ollama를 사용하여 번역합니다.
    """
    prompt = f"""다음 한문을 한국어로 번역하세요. 번역만 출력하세요.

한문: {text}

한국어 번역:"""

    try:
        response = requests.post(
            f"{OLLAMA_API}/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    
    except requests.RequestException as e:
        print(f"[ERROR] Ollama 번역 실패: {e}")
        return ""


def translate_with_openai(text: str, model: str = "gpt-4", api_key: str = None) -> str:
    """
    OpenAI API를 사용하여 번역합니다.
    """
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("[ERROR] OpenAI API 키가 없습니다.")
        return ""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "당신은 중국 고전 문헌을 한국어로 번역하는 전문 번역가입니다. 정확하고 자연스러운 번역을 제공하세요."
            },
            {
                "role": "user",
                "content": f"다음 한문을 한국어로 번역하세요. 번역만 출력하세요.\n\n한문: {text}"
            }
        ],
        "temperature": 0.3
    }
    
    try:
        response = requests.post(
            f"{OPENAI_API}/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    
    except requests.RequestException as e:
        print(f"[ERROR] OpenAI 번역 실패: {e}")
        return ""


def translate_with_kimi(text: str, model: str = "kimi-k2.5", api_key: str = None) -> str:
    """
    Kimi API (Moonshot AI)를 사용하여 번역합니다.
    Kimi K2.5 Cloud 모델을 사용합니다.
    """
    if not api_key:
        api_key = os.environ.get("KIMI_API_KEY") or os.environ.get("MOONSHOT_API_KEY")
    
    if not api_key:
        print("[ERROR] Kimi API 키가 없습니다.")
        print("환경 변수 KIMI_API_KEY 또는 MOONSHOT_API_KEY를 설정하세요.")
        return ""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "당신은 중국 고전 문헌을 한국어로 번역하는 전문 번역가입니다. 한문 원문을 정확하고 자연스러운 한국어로 번역하세요. 문맥을 고려하여 적절한 현대 한국어 표현을 사용하세요."
            },
            {
                "role": "user",
                "content": f"다음 한문을 한국어로 번역하세요. 번역만 출력하세요.\n\n한문: {text}"
            }
        ],
        "temperature": 0.3
    }
    
    try:
        response = requests.post(
            f"{KIMI_API}/chat/completions",
            headers=headers,
            json=data,
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    
    except requests.RequestException as e:
        print(f"[ERROR] Kimi 번역 실패: {e}")
        return ""


def translate_text(text: str, method: str = "kimi", model: str = None, api_key: str = None) -> str:
    """
    텍스트를 번역합니다.
    
    Args:
        text: 번역할 한문 텍스트
        method: 번역 방법 ("kimi", "openai", "ollama")
        model: 사용할 모델
        api_key: API 키 (선택사항)
    
    Returns:
        번역된 한국어 텍스트
    """
    if method == "ollama":
        return translate_with_ollama(text, model or "qwen2:7b")
    elif method == "kimi":
        return translate_with_kimi(text, model or "kimi-k2.5", api_key)
    else:
        return translate_with_openai(text, model or "gpt-4", api_key)


def process_jsonl_file(input_path: Path, output_path: Path, method: str = "openai", model: str = None, api_key: str = None):
    """
    JSONL 파일의 모든 항목에 번역을 추가합니다.
    """
    print(f"\n[처리] {input_path.name}")
    
    entries = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    
    print(f"  총 {len(entries)}개 항목")
    
    # 번역이 없는 항목만 처리
    untranslated = [e for e in entries if not e.get("korean")]
    
    if not untranslated:
        print("  모든 항목이 이미 번역되었습니다.")
        return
    
    print(f"  번역 필요: {len(untranslated)}개")
    
    # 번역 진행
    for i, entry in enumerate(untranslated):
        original = entry.get("original", "")
        
        if not original:
            continue
        
        print(f"  [{i+1}/{len(untranslated)}] 번역 중...")
        
        translation = translate_text(original, method, model, api_key)
        
        if translation:
            entry["korean"] = translation
            print(f"    원문: {original[:50]}...")
            print(f"    번역: {translation[:50]}...")
        
        # API 속도 제한 방지
        time.sleep(1)
    
    # 저장
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    print(f"[SAVED] {output_path}")


def batch_translate(entries: List[Dict], method: str = "openai", model: str = None, api_key: str = None, batch_size: int = 10) -> List[Dict]:
    """
    여러 항목을 배치로 번역합니다.
    """
    results = []
    
    for i in range(0, len(entries), batch_size):
        batch = entries[i:i+batch_size]
        
        # 배치 프롬프트 생성
        texts = [e.get("original", "") for e in batch]
        
        print(f"  배치 {i//batch_size + 1} 처리 중...")
        
        for j, entry in enumerate(batch):
            original = entry.get("original", "")
            if original:
                translation = translate_text(original, method, model, api_key)
                if translation:
                    entry["korean"] = translation
                time.sleep(0.5)  # 속도 제한
        
        results.extend(batch)
    
    return results


def main():
    """
    메인 실행 함수
    """
    print("="*60)
    print("한국어 번역 생성기")
    print("="*60)
    
    # API 키 설정 안내
    print("\n[설정] 번역 방법을 선택하세요:")
    print("  1. Kimi K2.5 Cloud (추천)")
    print("  2. OpenAI API (GPT-4)")
    print("  3. OpenAI API (GPT-3.5)")
    print("  4. Ollama (로컬)")
    
    method_choice = input("\n선택 (번호): ").strip()
    
    method = "kimi"
    model = "kimi-k2.5"
    
    if method_choice == "1":
        method = "kimi"
        model = "kimi-k2.5"
    elif method_choice == "2":
        method = "openai"
        model = "gpt-4"
    elif method_choice == "3":
        method = "openai"
        model = "gpt-3.5-turbo"
    elif method_choice == "4":
        method = "ollama"
        model = input("Ollama 모델명 (기본: qwen2:7b): ").strip() or "qwen2:7b"
    else:
        print("[ERROR] 잘못된 선택입니다.")
        return
    
    # API 키
    api_key = None
    if method == "kimi":
        api_key = os.environ.get("KIMI_API_KEY") or os.environ.get("MOONSHOT_API_KEY")
        if not api_key:
            print("\n[안내] Kimi API 키가 필요합니다.")
            print("환경 변수 KIMI_API_KEY 또는 MOONSHOT_API_KEY를 설정하세요.")
            print("또는 아래에 직접 입력하세요.")
            api_key = input("Kimi API 키: ").strip()
    elif method == "openai":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            api_key = input("OpenAI API 키: ").strip()
    
    # 처리할 파일 선택
    jsonl_files = list(PROCESSED_DIR.glob("*.jsonl"))
    
    if not jsonl_files:
        print("\n[WARN] processed 폴더에 JSONL 파일이 없습니다.")
        print("먼저 convert_to_jsonl.py를 실행하세요.")
        return
    
    print(f"\n처리 가능한 파일 ({len(jsonl_files)}개):")
    for i, f in enumerate(jsonl_files, 1):
        print(f"  {i}. {f.name}")
    
    print(f"  {len(jsonl_files)+1}. 전체 처리")
    
    choice = input("\n선택 (번호): ").strip()
    
    try:
        choice_num = int(choice)
        
        if 1 <= choice_num <= len(jsonl_files):
            # 단일 파일 처리
            file_path = jsonl_files[choice_num - 1]
            output_path = file_path  # 덮어쓰기
            
            process_jsonl_file(file_path, output_path, method, model, api_key)
        
        elif choice_num == len(jsonl_files) + 1:
            # 전체 처리
            for file_path in jsonl_files:
                process_jsonl_file(file_path, file_path, method, model, api_key)
                time.sleep(2)  # 파일 간 간격
        
        else:
            print("[ERROR] 잘못된 선택입니다.")
    
    except ValueError:
        print("[ERROR] 숫자를 입력하세요.")
    
    print("\n" + "="*60)
    print("번역 완료!")
    print("="*60)


if __name__ == "__main__":
    main()