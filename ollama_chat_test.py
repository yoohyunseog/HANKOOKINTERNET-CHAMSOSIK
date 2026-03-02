import requests

OLLAMA_URL = "http://localhost:11434"

# 간단한 채팅 테스트 함수
def ollama_chat(prompt, model="mistral"):
    url = f"{OLLAMA_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        print("응답:", data.get("response", "No response"))
    except Exception as e:
        print("오류:", e)

if __name__ == "__main__":
    ollama_chat("안녕, Ollama!")
