#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT_DIR = Path(__file__).resolve().parents[1]
PUBLIC_DIR = ROOT_DIR / "web" / "public"
UPLOAD_OUTPUT_PATH = PUBLIC_DIR / "world-monitor-ai.json"
FEED_URL = os.getenv("WORLD_MONITOR_FEED_URL", "https://xn--9l4b4xi9r.com/feed.xml")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("WORLD_MONITOR_MODEL", "deepseek-v3.1:671b-cloud")
SYNC_SCRIPT = ROOT_DIR / "sync_world_monitor_ai_json.bat"


def clean_text(text: str) -> str:
    return " ".join((text or "").strip().split())


def find_site_output_path() -> Path:
    for path in PUBLIC_DIR.rglob("world-monitor-ai.json"):
        if path.name == "world-monitor-ai.json" and path.parent != PUBLIC_DIR:
            return path
    for path in PUBLIC_DIR.rglob("index.html"):
        if any(ord(ch) > 127 for ch in path.parent.name):
            return path.parent / "world-monitor-ai.json"
    raise RuntimeError("Could not find site output directory for world-monitor-ai.json")


SITE_OUTPUT_PATH = find_site_output_path()


def fetch_feed_items(limit: int = 12) -> dict:
    response = requests.get(FEED_URL, timeout=20)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    channel = root.find("channel")
    if channel is None:
        raise RuntimeError("RSS channel not found in feed.xml")

    items = []
    for item in channel.findall("item")[:limit]:
        items.append(
            {
                "title": clean_text(item.findtext("title")),
                "description": clean_text(item.findtext("description")),
                "category": clean_text(item.findtext("category")) or "일반",
                "pubDate": clean_text(item.findtext("pubDate")),
                "link": clean_text(item.findtext("link")),
            }
        )

    return {
        "channel_title": clean_text(channel.findtext("title")),
        "channel_description": clean_text(channel.findtext("description")),
        "last_build_date": clean_text(channel.findtext("lastBuildDate")),
        "items": items,
    }


def ollama_generate(prompt: str, num_predict: int = 1200) -> str:
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": num_predict,
                "top_p": 0.9,
            },
        },
        timeout=180,
    )
    response.raise_for_status()
    return response.json().get("response", "").strip()


def parse_json_object(raw: str) -> dict:
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError(f"Failed to parse JSON from model response: {raw[:400]}")
    return json.loads(raw[start : end + 1])


def build_prompt(feed_data: dict) -> str:
    item_lines = []
    for index, item in enumerate(feed_data["items"], start=1):
        item_lines.append(
            "\n".join(
                [
                    f"[{index}] 제목: {item['title'][:280]}",
                    f"카테고리: {item['category']}",
                    f"발행시각: {item['pubDate']}",
                    f"설명: {item['description'][:600]}",
                ]
            )
        )

    items_text = "\n\n".join(item_lines)

    return f"""
너는 참소식.com의 이클립스 센츄어리 D.P 분석 AI다.
아래 RSS 피드를 보고 짧고 명확한 한국어 분석을 JSON으로만 출력하라.

[핵심 규칙]
1. 출력은 자연스러운 한국어만 사용한다.
2. 일본어, 중국어, 한자 혼용, 영어 번역투를 쓰지 않는다.
3. 입력에 외국어가 있어도 출력은 모두 한국어로 풀어 쓴다.
4. 과장하지 말고 실제로 반복되는 신호만 요약한다.
5. market_impact에는 코스피, 코스닥, 비트코인, 한국 증시 심리를 반드시 반영한다.
6. weighted_signal은 AI가 직접 계산한다.
7. score는 전체 종합 가중치 점수다.
8. upper_bound는 상승 또는 플러스 방향 요인의 총합 점수다.
9. lower_bound는 하락 또는 마이너스 방향 요인의 총합 점수다.
10. upper_factors는 플러스 요소 목록이고, lower_factors는 마이너스 요소 목록이다.
11. upper_factors와 lower_factors는 각각 '원유 가격 반등 +8' 또는 '증시 변동성 확대 -10' 같은 형식으로 쓴다.
12. score, upper_bound, lower_bound는 모두 0~100 정수다.
13. grade는 관심, 주의, 경계, 위험 중 하나만 쓴다.
14. JSON만 출력한다. 코드블록 금지.

[출력 JSON 스키마]
{{
  "headline": "짧은 헤드라인",
  "summary": "2~4문장 요약",
  "signals": ["핵심 신호 1", "핵심 신호 2", "핵심 신호 3"],
  "risks": ["리스크 1", "리스크 2", "리스크 3"],
  "market_impact": ["코스피 영향", "코스닥 영향", "비트코인 영향", "한국 증시 심리 영향"],
  "outlook": "짧은 전망",
  "quality_note": "피드 품질에 대한 짧은 평가",
  "weighted_signal": {{
    "score": 72,
    "upper_bound": 38,
    "lower_bound": 26,
    "grade": "경계",
    "upper_factors": ["에너지 반등 기대 +8", "방산 관심 확대 +6"],
    "lower_factors": ["군사 긴장 심화 -12", "해상 병목 우려 -9", "인플레이션 압력 -5"]
  }}
}}

[채널]
제목: {feed_data['channel_title']}
설명: {feed_data['channel_description']}
최종 갱신: {feed_data['last_build_date']}

[최신 항목]
{items_text}
""".strip()


def contains_non_korean_noise(value) -> bool:
    text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
    return any(
        (
            0x3040 <= ord(ch) <= 0x30FF
            or 0x31F0 <= ord(ch) <= 0x31FF
            or 0xFF66 <= ord(ch) <= 0xFF9F
        )
        for ch in text
    )


def rewrite_analysis_in_korean(analysis: dict) -> dict:
    prompt = f"""
다음 JSON을 의미는 유지하되 자연스러운 한국어로만 다시 써라.
일본어, 중국어, 한자 혼용, 영어 번역투를 모두 제거하라.
weighted_signal의 숫자와 구조는 유지하라.
upper_factors는 플러스 요소 목록, lower_factors는 마이너스 요소 목록으로 유지하라.
키 이름은 그대로 두고 JSON만 출력하라.

{json.dumps(analysis, ensure_ascii=False, indent=2)}
""".strip()
    raw = ollama_generate(prompt, num_predict=1000)
    return parse_json_object(raw)


def normalize_weighted_signal(weighted_signal: dict) -> dict:
    if not isinstance(weighted_signal, dict):
        weighted_signal = {}

    def to_int(value, default):
        try:
            return int(value)
        except Exception:
            return default

    score = max(0, min(100, to_int(weighted_signal.get("score"), 50)))
    upper_bound = max(0, min(100, to_int(weighted_signal.get("upper_bound"), 20)))
    lower_bound = max(0, min(100, to_int(weighted_signal.get("lower_bound"), 20)))
    grade = clean_text(weighted_signal.get("grade", "주의")) or "주의"
    upper_factors = [clean_text(x) for x in weighted_signal.get("upper_factors", []) if clean_text(x)]
    lower_factors = [clean_text(x) for x in weighted_signal.get("lower_factors", []) if clean_text(x)]

    return {
        "score": score,
        "upper_bound": upper_bound,
        "lower_bound": lower_bound,
        "grade": grade,
        "upper_factors": upper_factors[:5],
        "lower_factors": lower_factors[:5],
    }


def generate_analysis(feed_data: dict) -> dict:
    raw = ollama_generate(build_prompt(feed_data))
    if not raw:
        raise RuntimeError("Ollama returned an empty response")

    analysis = parse_json_object(raw)
    if contains_non_korean_noise(analysis):
        analysis = rewrite_analysis_in_korean(analysis)

    analysis["weighted_signal"] = normalize_weighted_signal(analysis.get("weighted_signal", {}))
    return analysis


def save_payload(feed_data: dict, analysis: dict) -> Path:
    payload = {
        "title": "이클립스 센츄어리 D.P 브리핑",
        "model": OLLAMA_MODEL,
        "source_feed": FEED_URL,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "feed_last_build_date": feed_data["last_build_date"],
        "item_count": len(feed_data["items"]),
        "headline": clean_text(analysis.get("headline", "")),
        "summary": clean_text(analysis.get("summary", "")),
        "signals": [clean_text(x) for x in analysis.get("signals", []) if clean_text(x)],
        "risks": [clean_text(x) for x in analysis.get("risks", []) if clean_text(x)],
        "market_impact": [clean_text(x) for x in analysis.get("market_impact", []) if clean_text(x)],
        "outlook": clean_text(analysis.get("outlook", "")),
        "quality_note": clean_text(analysis.get("quality_note", "")),
        "weighted_signal": normalize_weighted_signal(analysis.get("weighted_signal", {})),
        "items": feed_data["items"][:8],
    }

    for output_path in (SITE_OUTPUT_PATH, UPLOAD_OUTPUT_PATH):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    return SITE_OUTPUT_PATH


def maybe_upload() -> None:
    if os.getenv("WORLD_MONITOR_AUTO_UPLOAD", "1") != "1":
        print("[INFO] Auto upload disabled.")
        return
    if not SYNC_SCRIPT.exists():
        print(f"[WARN] Sync script not found: {SYNC_SCRIPT}")
        return

    print(f"[INFO] Uploading via {SYNC_SCRIPT.name} ...")
    completed = subprocess.run(
        ["cmd", "/c", str(SYNC_SCRIPT)],
        cwd=str(ROOT_DIR),
        check=False,
        stdin=subprocess.DEVNULL,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Upload script failed with code {completed.returncode}")


def main() -> int:
    try:
        feed_data = fetch_feed_items()
        analysis = generate_analysis(feed_data)
        output_path = save_payload(feed_data, analysis)
        print(f"[DONE] Saved {output_path}")
        if SITE_OUTPUT_PATH != UPLOAD_OUTPUT_PATH:
            shutil.copyfile(SITE_OUTPUT_PATH, UPLOAD_OUTPUT_PATH)
            print(f"[DONE] Mirrored {UPLOAD_OUTPUT_PATH}")
        maybe_upload()
        return 0
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
