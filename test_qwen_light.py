#!/usr/bin/env python3
import requests
import time

print("=== 경량 테스트 ===")

try:
    print("\n[1] API 버전 확인")
    r = requests.get('http://localhost:11434/api/version', timeout=5)
    print(f"버전: {r.json()}")
except Exception as e:
    print(f"실패: {e}")

try:
    print("\n[2] 모델 목록")
    r = requests.get('http://localhost:11434/api/tags', timeout=5)
    models = r.json().get('models', [])
    print(f"로드됨: {len(models)}개")
    for m in models:
        print(f"  • {m['name']} ({m['size']/1e9:.1f}GB)")
except Exception as e:
    print(f"실패: {e}")

try:
    print("\n[3] 초단문 Generate (10토큰)")
    start = time.time()
    r = requests.post('http://localhost:11434/api/generate', 
                     json={'model': 'qwen2.5:72b', 'prompt': 'Hi', 'max_tokens': 10, 'stream': False},
                     timeout=120)
    elapsed = time.time() - start
    if r.status_code == 200:
        resp = r.json().get('response', '')
        print(f"✓ 성공! ({elapsed:.1f}초)")
        print(f"응답: {resp}")
    else:
        print(f"HTTP {r.status_code}: {r.text}")
except Exception as e:
    print(f"실패: {e}")
