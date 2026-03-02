#!/usr/bin/env python3
import requests
import time

API = 'http://localhost:11434'
HEADERS = {'Content-Type': 'application/json'}
PROMPT = '간단히 인사해 주세요.'

print('=== 모델 일괄 테스트 ===\n')

try:
    tags = requests.get(f'{API}/api/tags', timeout=10).json()
    models = [m['name'] for m in tags.get('models', [])]
except Exception as e:
    print('모델 목록 조회 실패:', e)
    raise SystemExit(1)

if not models:
    print('등록된 모델이 없습니다.')
    raise SystemExit(0)

for m in models:
    print(f'--- 테스트: {m} ---')
    payload = {
        'model': m,
        'prompt': PROMPT,
        'max_tokens': 16,
        'stream': False
    }
    start = time.time()
    try:
        r = requests.post(f'{API}/api/generate', json=payload, timeout=120)
        elapsed = time.time() - start
        if r.status_code == 200:
            j = r.json()
            resp = j.get('response') or j
            print(f'응답 ({elapsed:.1f}s):', (resp if isinstance(resp, str) else str(resp))[:1000])
        else:
            print(f'HTTP {r.status_code}:', r.text[:1000])
    except requests.exceptions.Timeout:
        print('타임아웃 (120s)')
    except Exception as e:
        print('오류:', e)
    print('')

print('=== 테스트 완료 ===')
