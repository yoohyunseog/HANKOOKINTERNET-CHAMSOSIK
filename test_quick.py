#!/usr/bin/env python3
import requests
import time

print("=== 초고속 테스트 (max_tokens=5) ===\n")

prompt = "Hello"
print(f"프롬프트: {prompt}")

try:
    start = time.time()
    response = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': 'qwen2.5:72b',
            'prompt': prompt,
            'max_tokens': 5,
            'stream': False,
        },
        timeout=60  # 1분만 대기
    )
    elapsed = time.time() - start
    
    if response.status_code == 200:
        result = response.json()
        answer = result.get('response', '').strip()
        print(f"✓ 성공! ({elapsed:.1f}초)")
        print(f"응답: {answer}")
    else:
        print(f"✗ HTTP {response.status_code}: {response.text}")
except requests.exceptions.Timeout:
    print(f"✗ 타임아웃 (60초 초과)")
except Exception as e:
    print(f"✗ 오류: {e}")
