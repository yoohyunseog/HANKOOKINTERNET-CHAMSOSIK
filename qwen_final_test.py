import requests, sys, json, time
start = time.time()
try:
    r = requests.post("http://localhost:11434/api/generate", 
        json={"model":"qwen2.5:72b","prompt":"Hello world, tell me about yourself in 50 words","max_tokens":100}, 
        timeout=300)
    elapsed = time.time() - start
    print(f"STATUS: {r.status_code} (elapsed: {elapsed:.1f}s)")
    if r.status_code == 200:
        print("✅ SUCCESS - qwen2.5:72b 모델 정상 작동!")
        lines = r.text.strip().split("\n")
        print(f"Response lines: {len(lines)}")
        for i, line in enumerate(lines[:5]):  # first 5 lines
            try:
                obj = json.loads(line)
                if "response" in obj:
                    print(f"[{i}] {obj['response']}", end="")
            except: pass
        print("\n")
    else:
        print(f"❌ ERROR: {r.status_code}")
        print(r.text[:500])
except Exception as e:
    print(f"❌ EXCEPTION: {str(e)}")
    import traceback
    traceback.print_exc()
