#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""원격 Ollama 서버 API 테스트"""

import requests

OLLAMA_BASE = 'http://211.45.162.155:11434'

# 1. /api/tags - 모델 목록
print('=== /api/tags ===')
try:
    r = requests.get(f'{OLLAMA_BASE}/api/tags', timeout=10)
    print(f'Status: {r.status_code}')
    if r.status_code == 200:
        data = r.json()
        models = data.get('models', [])
        print(f'Models: {len(models)}')
        for m in models[:10]:
            name = m.get('name', 'unknown')
            print(f'  - {name}')
    else:
        print(f'Error: {r.text[:200]}')
except Exception as e:
    print(f'Error: {e}')

# 2. /api/generate - 생성 API
print()
print('=== /api/generate ===')
try:
    r = requests.post(
        f'{OLLAMA_BASE}/api/generate',
        json={'model': 'kimi-k2.6:cloud', 'prompt': 'hi', 'stream': False},
        timeout=10
    )
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text[:200]}')
except Exception as e:
    print(f'Error: {e}')

# 3. /api/chat - 채팅 API
print()
print('=== /api/chat ===')
try:
    r = requests.post(
        f'{OLLAMA_BASE}/api/chat',
        json={'model': 'kimi-k2.6:cloud', 'messages': [{'role': 'user', 'content': 'hi'}], 'stream': False},
        timeout=10
    )
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text[:200]}')
except Exception as e:
    print(f'Error: {e}')

# 4. /api/show - 모델 정보
print()
print('=== /api/show ===')
try:
    r = requests.post(
        f'{OLLAMA_BASE}/api/show',
        json={'name': 'kimi-k2.6:cloud'},
        timeout=10
    )
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text[:200]}')
except Exception as e:
    print(f'Error: {e}')