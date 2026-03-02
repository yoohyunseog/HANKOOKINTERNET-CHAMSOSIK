#!/usr/bin/env python3
import requests
import time

API = 'http://localhost:11434/api/generate'
MODEL = 'neural-chat:latest'
HEADERS = {'Content-Type': 'application/json'}

prompts = [
    "안녕하세요! 간단히 자기소개해 주세요.",
    "오늘 서울의 날씨가 어떤지 알려줄래요? (짧게)",
    "짧은 한국어 2줄 시를 써줘."
]

print('=== neural-chat 대화형 테스트 ===\n')
for i, p in enumerate(prompts, 1):
    print(f'[입력 {i}] {p}')
    payload = {'model': MODEL, 'prompt': p, 'max_tokens': 64, 'temperature': 0.7, 'stream': False}
    try:
        start = time.time()
        r = requests.post(API, json=payload, timeout=120)
        elapsed = time.time() - start
        if r.status_code == 200:
            j = r.json()
            resp = j.get('response', '')
            print(f'[{i}] 응답 ({elapsed:.1f}s):\n{resp}\n')
        else:
            print(f'HTTP {r.status_code}: {r.text}\n')
    except Exception as e:
        print(f'오류: {e}\n')

print('=== 테스트 완료 ===')
