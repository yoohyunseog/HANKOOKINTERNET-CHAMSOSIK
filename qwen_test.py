import requests,sys,json
try:
    r = requests.post("http://localhost:11434/api/generate", json={"model":"qwen2.5:72b","prompt":"Hello","max_tokens":64}, timeout=180)
    print("STATUS:", r.status_code)
    print("HEADERS:")
    for k,v in r.headers.items():
        print(f"{k}: {v}")
    print("BODY:\n", r.text)
except Exception as e:
    import traceback
    print("EXCEPTION:", str(e))
    traceback.print_exc()
