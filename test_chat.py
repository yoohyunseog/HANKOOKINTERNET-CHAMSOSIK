#!/usr/bin/env python3
import requests
import json
import time

print("=== Qwen2.5:72b 채팅 테스트 ===\n")

test_prompts = [
    "안녕하세요. 오늘 날씨는 어떨까요?",
    "Python으로 Hello World를 출력하는 코드를 작성해주세요.",
    "AI가 미래에 어떻게 발전할까요? (50단어 이내)"
]

for i, prompt in enumerate(test_prompts, 1):
    print(f"[테스트 {i}] 프롬프트: {prompt}")
    try:
        start = time.time()
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'qwen2.5:72b',
                'prompt': prompt,
                'max_tokens': 100,
                'stream': False,
                'temperature': 0.7
            },
            timeout=180  # 3분 타임아웃
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('response', '').strip()
            print(f"✓ 성공! ({elapsed:.1f}초)")
            print(f"응답: {answer}\n")
        else:
            print(f"✗ HTTP {response.status_code}: {response.text}\n")
    except requests.exceptions.Timeout:
        print(f"✗ 타임아웃 (180초 초과)\n")
    except Exception as e:
        print(f"✗ 오류: {e}\n")

print("\n=== 테스트 완료 ===")
