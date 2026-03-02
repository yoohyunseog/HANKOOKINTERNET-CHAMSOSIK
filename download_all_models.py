#!/usr/bin/env python3
import subprocess
import time
import requests

models = ['neural-chat', 'dolphin-2.1-mistral-7b', 'llama2-13b']

print("=== 모든 모델 순차 다운로드 ===\n")
print("다운로드할 모델:")
for m in models:
    print(f"  • {m}")
print(f"\n총 예상 크기: ~16GB")
print(f"저장 위치: E:\\ollama\\models\\blobs\n")

for i, model in enumerate(models, 1):
    print(f"\n[{i}/{len(models)}] {model} 다운로드 시작...")
    try:
        # ollama pull 실행
        result = subprocess.run(['ollama', 'pull', model], capture_output=False, text=True, timeout=3600)
        if result.returncode == 0:
            print(f"✓ {model} 완료!")
        else:
            print(f"✗ {model} 실패 (코드: {result.returncode})")
    except subprocess.TimeoutExpired:
        print(f"✗ {model} 타임아웃")
    except Exception as e:
        print(f"✗ {model} 오류: {e}")
    
    time.sleep(2)  # 다음 모델 전 대기

print("\n=== 다운로드 완료 ===")
print("등록된 모든 모델 확인:")
try:
    r = requests.get('http://localhost:11434/api/tags', timeout=10)
    models = r.json().get('models', [])
    for m in models:
        size_gb = m['size'] / 1e9
        print(f"  • {m['name']:30s} - {size_gb:.1f}GB")
except Exception as e:
    print(f"모델 목록 조회 실패: {e}")
