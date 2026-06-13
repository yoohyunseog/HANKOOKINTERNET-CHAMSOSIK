from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from yt_dlp import YoutubeDL


BASE_DIR = Path(__file__).resolve().parent
WEB_ROOT = BASE_DIR.parent
HOST = "localhost"
PORT = 8765
RUNS: dict[str, dict] = {}


def search_youtube(query: str, limit: int) -> list[dict]:
    limit = max(1, min(limit, 50))
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignoreerrors": True,
        "extract_flat": False,
    }

    with YoutubeDL(options) as ydl:
        data = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)

    videos = []
    for item in (data or {}).get("entries", []) or []:
        if not item:
            continue
        videos.append(
            {
                "id": item.get("id"),
                "title": item.get("title") or "",
                "channel": item.get("channel") or item.get("uploader") or "",
                "url": item.get("webpage_url") or item.get("url") or "",
                "viewCount": item.get("view_count") or 0,
                "uploadDate": item.get("upload_date") or "",
                "timestamp": item.get("timestamp"),
                "duration": item.get("duration") or 0,
                "thumbnail": item.get("thumbnail") or "",
            }
        )
    return videos


def run_keyword_analysis(params: dict) -> dict:
    youtube_enabled = (params.get("youtube") or ["false"])[0].strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["YOUTUBE_SEARCH_ENABLED"] = "true" if youtube_enabled else "false"

    for source, target in {
        "results": "YOUTUBE_SEARCH_RESULTS",
        "maxKeywords": "YOUTUBE_MAX_KEYWORDS",
        "timeout": "YOUTUBE_SEARCH_TIMEOUT_SECONDS",
    }.items():
        value = (params.get(source) or [""])[0].strip()
        if value:
            env[target] = value

    completed = subprocess.run(
        [sys.executable, "analyze_keywords_bot.py"],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=int((params.get("runTimeout") or ["900"])[0]),
    )

    latest_path = BASE_DIR / "analysis_results" / "latest_keyword_analysis.json"
    return {
        "ok": completed.returncode == 0,
        "returnCode": completed.returncode,
        "youtubeEnabled": youtube_enabled,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "latestPath": str(latest_path),
        "latestExists": latest_path.exists(),
    }


def build_analysis_env(params: dict) -> tuple[dict, bool]:
    youtube_enabled = (params.get("youtube") or ["false"])[0].strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    env = os.environ.copy()
    env["YOUTUBE_SEARCH_ENABLED"] = "true" if youtube_enabled else "false"

    for source, target in {
        "results": "YOUTUBE_SEARCH_RESULTS",
        "maxKeywords": "YOUTUBE_MAX_KEYWORDS",
        "timeout": "YOUTUBE_SEARCH_TIMEOUT_SECONDS",
    }.items():
        value = (params.get(source) or [""])[0].strip()
        if value:
            env[target] = value

    return env, youtube_enabled


def start_keyword_analysis(params: dict) -> dict:
    env, youtube_enabled = build_analysis_env(params)
    run_id = uuid.uuid4().hex
    state = {
        "id": run_id,
        "running": True,
        "ok": None,
        "returnCode": None,
        "youtubeEnabled": youtube_enabled,
        "startedAt": time.time(),
        "endedAt": None,
        "lines": [],
        "stderr": "",
    }
    RUNS[run_id] = state

    process = subprocess.Popen(
        [sys.executable, "-u", "analyze_keywords_bot.py"],
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    def worker() -> None:
        assert process.stdout is not None
        assert process.stderr is not None
        for line in process.stdout:
            state["lines"].append(line.rstrip())
        stderr = process.stderr.read()
        return_code = process.wait()
        state["stderr"] = stderr
        state["returnCode"] = return_code
        state["ok"] = return_code == 0
        state["running"] = False
        state["endedAt"] = time.time()

    threading.Thread(target=worker, daemon=True).start()
    return {"id": run_id, "running": True, "youtubeEnabled": youtube_enabled}


def get_run_status(run_id: str) -> dict:
    state = RUNS.get(run_id)
    if not state:
        return {"error": "run not found"}

    latest_path = BASE_DIR / "analysis_results" / "latest_keyword_analysis.json"
    return {
        **state,
        "latestPath": str(latest_path),
        "latestExists": latest_path.exists(),
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/youtube-search":
            params = parse_qs(parsed.query)
            query = (params.get("q") or [""])[0].strip()
            try:
                limit = int((params.get("limit") or ["5"])[0])
            except ValueError:
                limit = 5

            if not query:
                self.send_json(400, {"error": "Missing q parameter"})
                return

            try:
                videos = search_youtube(query, limit)
            except Exception as error:
                self.send_json(500, {"error": str(error)})
                return

            self.send_json(200, {"query": query, "count": len(videos), "videos": videos})
            return

        if parsed.path == "/api/run-keyword-analysis":
            params = parse_qs(parsed.query)
            try:
                result = run_keyword_analysis(params)
            except subprocess.TimeoutExpired:
                self.send_json(504, {"error": "analysis timed out"})
                return
            except Exception as error:
                self.send_json(500, {"error": str(error)})
                return

            self.send_json(200 if result["ok"] else 500, result)
            return

        if parsed.path == "/api/start-keyword-analysis":
            params = parse_qs(parsed.query)
            try:
                result = start_keyword_analysis(params)
            except Exception as error:
                self.send_json(500, {"error": str(error)})
                return
            self.send_json(200, result)
            return

        if parsed.path == "/api/keyword-analysis-status":
            params = parse_qs(parsed.query)
            run_id = (params.get("id") or [""])[0].strip()
            result = get_run_status(run_id)
            self.send_json(404 if "error" in result else 200, result)
            return

        super().do_GET()


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving http://{HOST}:{PORT}/NBVideoAnalyzer/youtube_search.html")
    server.serve_forever()
