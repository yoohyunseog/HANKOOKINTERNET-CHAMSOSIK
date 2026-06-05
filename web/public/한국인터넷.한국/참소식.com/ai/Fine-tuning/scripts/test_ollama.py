"""Ollama API 테스트"""
import requests
import json

# Ollama API 테스트
url = 'http://211.45.162.155:11434/api/generate'
data = {
    'model': 'glm-5:cloud',
    'prompt': '다음 한문을 한국어로 번역하세요: 子曰學而時習之',
    'stream': False
}

print('Ollama API 테스트...')
print(f'URL: {url}')
print(f'Model: glm-5:cloud')
print()

try:
    response = requests.post(url, json=data, timeout=120)
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        result = response.json()
        print(f'Response: {result.get("response", "")[:500]}')
    else:
        print(f'Error: {response.text}')
except Exception as e:
    print(f'Exception: {e}')