#!/usr/bin/env python3
import os
import json
from pathlib import Path

print("=== Ollama 모델 위치 찾기 ===\n")

# 확인할 경로들
paths_to_check = [
    r'C:\Users\dbghw\.ollama',
    r'C:\Users\dbghw\.ollama.bak',
    r'E:\ollama',
]

for path in paths_to_check:
    print(f"\n[{path}]")
    p = Path(path)
    
    # 경로 존재 확인
    if not p.exists():
        print("  ✗ 없음")
        continue
        
    # 심볼릭 링크 또는 junction 확인
    try:
        if p.is_symlink():
            target = os.readlink(p)
            print(f"  → 심볼릭 링크: {target}")
    except:
        pass
    
    # 파일 크기 계산
    try:
        total_size = 0
        file_count = 0
        dir_count = 0
        
        for root, dirs, files in os.walk(path):
            dir_count += len(dirs)
            for f in files:
                file_count += 1
                try:
                    size = os.path.getsize(os.path.join(root, f))
                    total_size += size
                except:
                    pass
        
        print(f"  디렉토리: {dir_count}, 파일: {file_count}")
        print(f"  용량: {total_size / (1024**3):.2f}GB")
        
        # models/blobs 확인
        blobs_path = os.path.join(path, 'models', 'blobs')
        if os.path.exists(blobs_path):
            blob_files = len(os.listdir(blobs_path))
            print(f"  → models/blobs: {blob_files}개 파일")
            
            # 최초 몇 개 파일명 표시
            for i, f in enumerate(os.listdir(blobs_path)[:3]):
                print(f"    • {f}")
    except Exception as e:
        print(f"  ERROR: {e}")

# Ollama 환경변수 확인
print("\n\n=== 환경 변수 ===")
for var in ['OLLAMA_HOME', 'OLLAMA_MODELS']:
    val = os.environ.get(var)
    print(f"{var}: {val if val else '(설정 안됨)'}")

# 실행 중인 ollama 프로세스 확인
print("\n\n=== Ollama 프로세스 ===")
try:
    import subprocess
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ollama.exe'], 
                          capture_output=True, text=True, encoding='utf-8', errors='ignore')
    print(result.stdout)
except:
    print("(프로세스 확인 불가)")

# Ollama API 확인
print("\n=== Ollama API ===")
try:
    import urllib.request
    import urllib.error
    
    url = 'http://localhost:11434/api/tags'
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read())
            models = data.get('models', [])
            print(f"로드된 모델: {len(models)}")
            for m in models[:3]:
                print(f"  • {m.get('name')}")
    except urllib.error.URLError as e:
        print(f"API 연결 실패: {e}")
except:
    print("urllib 오류")
