"""
Ollama 로컬 처리 스크립트
- latest_trend_data.json 에서 키워드 추출
- 질문형 변환 + 요약/제목/본문 생성 (Ollama)
- 결과 JSON 저장
"""

import json
import os
import time
from datetime import datetime
from urllib.parse import quote

import requests

DATA_PATH = os.path.join("data", "naver_creator_trends", "latest_trend_data.json")
OUTPUT_DIR = os.path.join("data", "revenue_content")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def load_trend_keywords(limit):
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"트렌드 파일 없음: {DATA_PATH}")

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    trends = data.get("trend_data", [])
    keywords = []
    for item in trends:
        raw_text = (item.get("raw_text") or item.get("title") or "").strip()
        keyword = raw_text.split("\n")[0].strip()
        if not keyword or keyword == "-":
            continue
        keywords.append(keyword[:60])

    return keywords[:limit]


def call_ollama(prompt, model):
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=120
    )
    response.raise_for_status()
    data = response.json()
    return (data.get("response") or "").strip()


def get_default_model():
    if OLLAMA_MODEL:
        return OLLAMA_MODEL
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        response.raise_for_status()
        data = response.json()
        models = data.get("models", [])
        if models:
            return models[0].get("name") or ""
    except Exception:
        return ""
    return ""


def safe_json(text):
    try:
        return json.loads(text)
    except Exception:
        return None


def fetch_page_text(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        res.encoding = "utf-8"
        text = res.text
    except Exception:
        return {"url": url, "title": "", "description": "", "text": ""}

    title = ""
    desc = ""
    if "<title>" in text.lower():
        try:
            title = text.split("<title>", 1)[1].split("</title>", 1)[0].strip()
        except Exception:
            title = ""
    if "description" in text.lower():
        try:
            desc = text.split("name=\"description\"", 1)[1].split("content=\"", 1)[1].split("\"", 1)[0]
        except Exception:
            desc = ""

    clean = (
        text.replace("\n", " ")
        .replace("\r", " ")
    )
    clean = " ".join(clean.split())[:1200]

    return {
        "url": url,
        "title": title,
        "description": desc,
        "text": clean
    }


def build_content(keyword, question, naver_info, youtube_info, model):
    prompt = "\n".join([
        "다음 정보를 참고해 한국어 JSON만 출력해줘.",
        "필드: title, summary, body",
        f"키워드: {keyword}",
        f"질문: {question}",
        f"네이버 텍스트: {naver_info.get('title', '')} {naver_info.get('description', '')} {naver_info.get('text', '')}",
        f"유튜브 텍스트: {youtube_info.get('title', '')} {youtube_info.get('description', '')} {youtube_info.get('text', '')}",
        "제목은 40자 이내, summary는 2문장, body는 3~5문장으로 작성."
    ])

    response = call_ollama(prompt, model)
    parsed = safe_json(response)
    if parsed and parsed.get("title") and parsed.get("summary") and parsed.get("body"):
        return parsed

    return {
        "title": f"{keyword} 관련 요약",
        "summary": response[:220],
        "body": response
    }


def run(limit=5, model=None):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    model = model or get_default_model()
    if not model:
        raise RuntimeError("Ollama 모델을 찾을 수 없습니다. /api/tags를 확인하세요.")

    keywords = load_trend_keywords(limit)
    if not keywords:
        raise RuntimeError("추출된 키워드가 없습니다.")

    results = []
    for keyword in keywords:
        naver_url = f"https://search.naver.com/search.naver?query={quote(keyword)}"
        youtube_url = f"https://www.youtube.com/results?search_query={quote(keyword)}"

        question_prompt = f"키워드: {keyword}\n요구사항: 한국어 질문형 한 문장만 출력."
        try:
            question = call_ollama(question_prompt, model)
        except Exception:
            question = f"{keyword}에 대해 알고 싶어요."

        naver_info = fetch_page_text(naver_url)
        youtube_info = fetch_page_text(youtube_url)
        content = build_content(keyword, question, naver_info, youtube_info, model)

        results.append({
            "keyword": keyword,
            "question": question,
            "search": {"naver": naver_url, "youtube": youtube_url},
            "source_text": {"naver": naver_info, "youtube": youtube_info},
            "generated": content
        })

        time.sleep(0.4)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "model": model,
        "count": len(results),
        "results": results
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(OUTPUT_DIR, f"trend_ai_{timestamp}.json")
    latest_path = os.path.join(OUTPUT_DIR, "latest_trend_ai.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"✅ 저장 완료: {output_path}")
    print(f"✅ 최신 파일: {latest_path}")


if __name__ == "__main__":
    run()
