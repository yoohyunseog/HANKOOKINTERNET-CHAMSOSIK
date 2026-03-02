import requests
r = requests.post("http://localhost:11434/api/generate", json={"model":"mistral:latest","prompt":"Hi","max_tokens":20}, timeout=60)
print(f"Mistral status: {r.status_code}")
