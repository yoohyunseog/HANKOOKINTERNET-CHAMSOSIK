#!/usr/bin/env python3
"""
Run a .bot definition that drafts a latest-robot blog post with Ollama.

Usage:
  py web/public/한국인터넷.한국/참소식.com/blog/bots/latest_robot_post_bot.py web/public/한국인터넷.한국/참소식.com/blog/bots/latest_robot_post_writer.bot --dry-run
  py web/public/한국인터넷.한국/참소식.com/blog/bots/latest_robot_post_bot.py web/public/한국인터넷.한국/참소식.com/blog/bots/latest_robot_post_writer.bot
"""

from __future__ import annotations

import argparse
import datetime as dt
import ftplib
import html
import json
import os
import posixpath
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import requests


def find_workspace_root() -> Path:
    for path in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]:
        if (path / "web").exists() and (path / "search").exists():
            return path
    return Path(__file__).resolve().parents[6]


ROOT = find_workspace_root()
BOT_DIR = Path(__file__).resolve().parent
DEFAULT_KEYWORD_PATH = BOT_DIR / "latest_robot_keywords.txt"


def log(message: str) -> None:
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{stamp}] {message}", flush=True)


def load_bot(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if data.get("schema") != "chamsosik.bot.v1":
        raise ValueError(f"Unsupported bot schema: {data.get('schema')}")
    return data


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_text(path: Path, max_chars: int | None = None) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[:max_chars] if max_chars else text


def read_keyword_context() -> str:
    keyword_path = Path(os.getenv("ROBOT_BLOG_KEYWORDS", str(DEFAULT_KEYWORD_PATH)))
    if not keyword_path.is_absolute():
        keyword_path = ROOT / keyword_path
    text = read_text(keyword_path, max_chars=12000).strip()
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def collect_weight_context(bot: dict[str, Any]) -> dict[str, Any]:
    site = bot["site"]
    config_path = ROOT / site["config_path"]
    main_page_path = ROOT / site["main_page_path"]
    log("reading main page weight context")

    config = read_json(config_path)
    main_text = read_text(main_page_path)

    max_values = [int(x) for x in re.findall(r"\bMAX:\s*([0-9]+)", main_text)]
    min_values = [int(x) for x in re.findall(r"\bMIN:\s*([0-9]+)", main_text)]

    return {
        "config_path": str(config_path.relative_to(ROOT)),
        "main_page_path": str(main_page_path.relative_to(ROOT)),
        "bit_min_value": config.get("bitMinValue"),
        "bit_max_value": config.get("bitMaxValue"),
        "observed_nb_max_min": min(max_values) if max_values else None,
        "observed_nb_max_max": max(max_values) if max_values else None,
        "observed_nb_min_min": min(min_values) if min_values else None,
        "observed_nb_min_max": max(min_values) if min_values else None,
        "observed_count": max(len(max_values), len(min_values)),
    }


def rss_search(query: str, limit: int) -> list[dict[str, str]]:
    feeds = [
        (
            "Google News",
            "https://news.google.com/rss/search?"
            f"q={requests.utils.quote(query)}&hl=en-US&gl=US&ceid=US:en",
        ),
        (
            "Bing News",
            "https://www.bing.com/news/search?"
            f"q={requests.utils.quote(query)}&format=rss",
        ),
    ]
    items: list[dict[str, str]] = []
    headers = {"User-Agent": "Mozilla/5.0 ChamsosikBot/1.0"}

    for source, url in feeds:
        try:
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            for item in root.findall(".//item")[:limit]:
                title = "".join(item.findtext("title", "")).strip()
                link = "".join(item.findtext("link", "")).strip()
                description = strip_html_summary(item.findtext("description", ""), max_chars=280)
                if title and link:
                    items.append(
                        {
                            "source": source,
                            "title": html.unescape(title),
                            "description": description,
                            "url": link,
                        }
                    )
        except Exception as exc:
            items.append(
                {
                    "source": source,
                    "title": "rss search failed",
                    "description": str(exc)[:180],
                    "url": url,
                }
            )

    return [item for item in items if item.get("title") != "rss search failed"][: limit * 2]


def is_useful_search_item(item: dict[str, str]) -> bool:
    title = item.get("title", "").strip()
    url = item.get("url", "").strip()
    if not title or not url:
        return False
    junk = ("메뉴 영역", "NAVER검색", "자동완성 레이어", "검색 레이어")
    return not any(marker in title for marker in junk)


def plain_search(query: str, limit: int) -> list[dict[str, str]]:
    """Use news RSS first, then the repo search module, then a search URL."""
    rss_results = rss_search(query, limit)
    if rss_results:
        return rss_results

    results: list[dict[str, str]] = []
    try:
        sys.path.insert(0, str(ROOT))
        from search import get_bing_results, get_naver_results  # type: ignore

        for source_name, fn in (("Bing", get_bing_results), ("Naver", get_naver_results)):
            try:
                for item in fn(query, search_type="web", limit=limit):
                    title = html.unescape(str(item.get("title", "")).strip())
                    description = html.unescape(str(item.get("description", "")).strip())
                    url = str(item.get("url", "")).strip()
                    item = {
                        "source": source_name,
                        "title": title,
                        "description": description,
                        "url": url,
                    }
                    if is_useful_search_item(item):
                        results.append(
                            item
                        )
            except Exception as exc:
                results.append(
                    {
                        "source": source_name,
                        "title": "search failed",
                        "description": str(exc)[:180],
                        "url": "",
                    }
                )
    except Exception as exc:
        results.append(
            {
                "source": "fallback",
                "title": "repository search module unavailable",
                "description": str(exc)[:180],
                "url": f"https://www.google.com/search?q={requests.utils.quote(query)}",
            }
        )

    if not results:
        results.append(
            {
                "source": "fallback",
                "title": query,
                "description": "검색 모듈이 결과를 반환하지 않아 직접 검색 URL을 기록합니다.",
                "url": f"https://www.google.com/search?q={requests.utils.quote(query)}",
            }
        )
    return results[: limit * 2]


def collect_search_context(bot: dict[str, Any]) -> list[dict[str, Any]]:
    search_cfg = bot.get("search", {})
    limit = int(search_cfg.get("limit_per_query", 4))
    packs = []
    for query in search_cfg.get("queries", []):
        log(f"searching latest robot sources: {query}")
        packs.append({"query": query, "results": plain_search(query, limit)})
    return packs


def strip_html_summary(text: str, max_chars: int = 4000) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def build_prompt(bot: dict[str, Any], weights: dict[str, Any], searches: list[dict[str, Any]]) -> str:
    reference_path = ROOT / bot["site"]["reference_post_path"]
    reference_summary = strip_html_summary(read_text(reference_path, max_chars=30000))
    keyword_context = read_keyword_context()
    today = dt.datetime.now().strftime("%Y-%m-%d")
    log("building Ollama prompt")

    return "\n".join(
        [
            "당신은 참소식.com의 한국어 기술 블로그 필자입니다.",
            f"작성일: {today}",
            "",
            "[작성 목표]",
            f"- 제목 힌트: {bot['article'].get('title_hint')}",
            f"- 형식: {bot['article'].get('format')}",
            f"- 분량 목표: 약 {bot['article'].get('target_length_words')}단어",
            f"- 문체: {bot['article'].get('tone')}",
            "",
            "[90달러 / 15년 관점]",
            bot["writing_lens"]["stance"],
            "",
            "[메인 페이지 가중치 정보]",
            json.dumps(weights, ensure_ascii=False, indent=2),
            "",
            "[검색 자료]",
            json.dumps(searches, ensure_ascii=False, indent=2),
            "",
            "[Keyword reference txt]",
            keyword_context or "(no keyword txt found)",
            "",
            "[기존 참고 포스팅 요약]",
            reference_summary,
            "",
            "[필수 지시]",
            "- 최신 로봇 모델은 검색 자료에 근거해서만 단정하세요.",
            "- 모호한 정보는 '현재 공개 정보 기준'이라고 표현하세요.",
            "- N/B MAX·MIN 또는 bitMaxValue·bitMinValue를 글의 관찰 프레임으로 연결하세요.",
            "- 마지막에 참고 URL 목록을 붙이세요.",
            "- 본문은 한국어 Markdown만 출력하세요.",
        ]
    )


def call_ollama(bot: dict[str, Any], prompt: str) -> str:
    ollama = bot["ollama"]
    host = os.getenv("OLLAMA_HOST", ollama.get("host", "http://localhost:11434")).rstrip("/")
    configured_model = ollama.get("model", "kimi-k2.5:cloud")
    model = os.getenv("OLLAMA_MODEL", configured_model)
    log(f"calling Ollama model: {model}")
    def raise_with_body(resp: requests.Response) -> None:
        try:
            body = resp.text[:500]
        except Exception:
            body = ""
        raise requests.HTTPError(
            f"{resp.status_code} Client Error for {resp.url}: {body}",
            response=resp,
        )

    def model_candidates(value: str, fallback: str) -> list[str]:
        candidates = [value, fallback]
        for item in list(candidates):
            if item.endswith(":cloud"):
                candidates.append(item.removesuffix(":cloud"))
        return list(dict.fromkeys(candidates))

    generate_payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": float(ollama.get("temperature", 0.45))},
    }
    timeout = int(ollama.get("timeout_seconds", 180))

    response = requests.post(f"{host}/api/generate", json=generate_payload, timeout=timeout)
    if response.status_code != 404:
        if not response.ok:
            raise_with_body(response)
        log("Ollama generate response received")
        return response.json().get("response", "").strip()

    last_response = response
    for candidate in model_candidates(model, configured_model):
        log(f"trying Ollama chat endpoint: {candidate}")
        chat_payload = {
            "model": candidate,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": float(ollama.get("temperature", 0.45))},
        }
        response = requests.post(f"{host}/api/chat", json=chat_payload, timeout=timeout)
        if response.ok:
            data = response.json()
            log("Ollama chat response received")
            return (data.get("message") or {}).get("content", "").strip()
        last_response = response

    raise_with_body(last_response)


def save_draft(bot: dict[str, Any], content: str) -> Path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from add_post_search_links import add_markdown_search_links

    out_dir = ROOT / bot["site"].get("draft_output_dir", "data/generated_posts")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"latest_robot_post_{stamp}.md"
    content = add_markdown_search_links(content.strip() + "\n", title=bot["article"].get("title_hint"))
    out_path.write_text(content, encoding="utf-8")
    log(f"draft markdown saved: {out_path}")
    return out_path


def strip_inline_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[*_`>#-]+", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def extract_markdown_title(content: str, fallback: str) -> tuple[str, str]:
    lines = content.strip().splitlines()
    for index, line in enumerate(lines[:12]):
        stripped = line.strip()
        if stripped.startswith("# "):
            title = strip_inline_html(stripped[2:])
            return title or fallback, clean_markdown_metadata("\n".join(lines[index + 1 :]).strip())
        bold_match = re.fullmatch(r"\*\*(.+?)\*\*", stripped)
        if bold_match:
            title = strip_inline_html(bold_match.group(1))
            return title or fallback, clean_markdown_metadata("\n".join(lines[index + 1 :]).strip())
    return fallback, clean_markdown_metadata(content.strip())


def clean_markdown_metadata(content: str) -> str:
    lines = content.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].strip() == "---":
        for index in range(1, min(len(lines), 20)):
            if lines[index].strip() == "---":
                return "\n".join(lines[index + 1 :]).strip()

    metadata_pattern = re.compile(r"^(markdown\s+)?(title|date|author|tags)\s*:", re.I)
    removed = 0
    while lines and removed < 12:
        stripped = lines[0].strip()
        if not stripped:
            lines.pop(0)
            continue
        if metadata_pattern.match(stripped):
            lines.pop(0)
            removed += 1
            continue
        break
    return "\n".join(lines).strip()


def slugify_title(title: str, stamp: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", title.lower())
    core = "-".join(words[:8]) if words else "latest-robot-post"
    return f"{dt.datetime.now().strftime('%Y-%m-%d')}-{core}-{stamp}.html"


def inline_markdown(text: str) -> str:
    placeholders: list[str] = []

    def keep_anchor(match: re.Match[str]) -> str:
        placeholders.append(match.group(0))
        return f"@@ANCHOR{len(placeholders) - 1}@@"

    text = re.sub(r"<a\b[^>]*>.*?</a>", keep_anchor, text, flags=re.I | re.S)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    for index, anchor in enumerate(placeholders):
        text = text.replace(f"@@ANCHOR{index}@@", anchor)
    return text


def markdown_to_html(content: str) -> str:
    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            blocks.append(f"<p>{inline_markdown(' '.join(paragraph))}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            items = "\n".join(f"        <li>{inline_markdown(item)}</li>" for item in list_items)
            blocks.append(f"<ul>\n{items}\n      </ul>")
            list_items = []

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            flush_list()
            continue
        if line == "---":
            flush_paragraph()
            flush_list()
            blocks.append("<hr>")
            continue
        heading = re.match(r"^(#{2,4})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            flush_list()
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{inline_markdown(heading.group(2))}</h{level}>")
            continue
        bullet = re.match(r"^[-*]\s+(.+)$", line)
        if bullet:
            flush_paragraph()
            list_items.append(bullet.group(1))
            continue
        paragraph.append(line)

    flush_paragraph()
    flush_list()
    return "\n      ".join(blocks)


def render_post_html(title: str, body_html: str, excerpt: str, slug: str) -> str:
    today = dt.datetime.now().strftime("%Y-%m-%d")
    escaped_title = html.escape(title)
    escaped_excerpt = html.escape(excerpt)
    canonical = f"https://xn--9l4b4xi9r.com/blog/posts/{slug}"
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="index, follow">
  <meta name="description" content="{escaped_excerpt}">
  <meta name="keywords" content="최신 로봇, 휴머노이드 로봇, Ollama, 로봇 모델, 15년 관점">
  <link rel="icon" href="../../favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="../../favicon.svg">
  <link rel="canonical" href="{canonical}">
  <meta property="og:type" content="article">
  <meta property="og:locale" content="ko_KR">
  <meta property="og:site_name" content="참소식.com">
  <meta property="og:url" content="{canonical}">
  <meta property="og:title" content="{escaped_title}">
  <meta property="og:description" content="{escaped_excerpt}">
  <meta property="og:image" content="https://xn--9l4b4xi9r.com/blog/assets/latest-humanoid-robots-2026-cover.png">
  <meta property="article:published_time" content="{today}">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{escaped_title}">
  <meta name="twitter:description" content="{escaped_excerpt}">
  <meta name="twitter:image" content="https://xn--9l4b4xi9r.com/blog/assets/latest-humanoid-robots-2026-cover.png">
  <title>{escaped_title} | 참소식.com 블로그</title>
  <link rel="stylesheet" href="../../common-site.css">
  <style>
    :root {{ color-scheme: dark; --page: #08111c; --ink: #f3f7fb; --muted: #b6c6d8; --line: rgba(180, 205, 230, 0.2); --blue: #75b7ff; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: linear-gradient(180deg, #050913 0%, var(--page) 58%, #0a101b 100%); color: var(--ink); font-family: Pretendard, "Noto Sans KR", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.82; }}
    .post-container {{ width: min(960px, calc(100% - 32px)); margin: 0 auto; padding: 42px 0 76px; }}
    .post-back {{ display: inline-flex; color: var(--blue); font-size: 14px; font-weight: 800; text-decoration: none; }}
    .post-back:hover {{ text-decoration: underline; }}
    .post-header {{ padding: 34px 0 24px; }}
    .post-meta {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 22px; }}
    .post-meta span {{ border: 1px solid var(--line); border-radius: 999px; color: var(--muted); font-size: 13px; padding: 4px 10px; }}
    .post-views {{ display: inline-flex; align-items: center; gap: 4px; border: 1px solid var(--line); border-radius: 999px; color: var(--muted); font-size: 13px; padding: 4px 10px; }}
    .post-views::before {{ content: '👁'; font-size: 12px; }}
    h1 {{ max-width: 880px; margin: 0 0 18px; font-size: clamp(34px, 5vw, 56px); line-height: 1.1; letter-spacing: 0; }}
    .post-subtitle {{ max-width: 760px; margin: 0; color: var(--muted); font-size: 19px; }}
    .post-hero {{ width: 100%; border-radius: 8px; border: 1px solid var(--line); margin: 14px 0 34px; }}
    .post-content {{ max-width: 840px; font-size: 18px; }}
    .post-content h2 {{ margin: 44px 0 18px; padding-top: 8px; font-size: 29px; line-height: 1.28; }}
    .post-content h3 {{ margin: 30px 0 14px; font-size: 23px; }}
    .post-content p {{ margin: 0 0 21px; color: #d9e5f2; }}
    .post-content a {{ color: #93c5fd; }}
    .post-content ul {{ margin: 0 0 22px; padding-left: 24px; color: #d9e5f2; }}
    .post-content li {{ margin-bottom: 8px; }}
    .post-content hr {{ border: 0; border-top: 1px solid var(--line); margin: 26px 0; }}
    .post-footer {{ margin-top: 54px; padding-top: 28px; border-top: 1px solid var(--line); }}
    .site-footer {{ border-top: 1px solid var(--line); background: #060b13; color: var(--muted); text-align: center; padding: 24px; }}
    @media (max-width: 720px) {{ .post-container {{ width: min(100% - 24px, 960px); padding-top: 28px; }} .post-content {{ font-size: 16px; }} }}
  </style>
</head>
<body>
  <script src="../../domain-check.js"></script>
  <main class="post-container">
    <a href="../" class="post-back">← 블로그 목록으로</a>
    <header class="post-header">
      <div class="post-meta">
        <span>{today}</span>
        <span>로봇 기술</span>
        <span>Ollama 자동 작성</span>
        <span class="post-views" id="view-count">조회수 로딩중...</span>
      </div>
      <h1>{escaped_title}</h1>
      <p class="post-subtitle">{escaped_excerpt}</p>
    </header>
    <img class="post-hero" src="../assets/latest-humanoid-robots-2026-cover.png" alt="최신 휴머노이드 로봇 모델을 표현한 블로그 대표 이미지">
    <article class="post-content">
      {body_html}
    </article>
    <footer class="post-footer">
      <a href="../" class="post-back">← 블로그 목록으로 돌아가기</a>
    </footer>
  </main>
  <footer class="site-footer">
    <p>&copy; 2026 참소식.com. 모든 권리 보유.</p>
  </footer>
  <script src="../js/view-tracker.js"></script>
  <script>
    document.addEventListener('DOMContentLoaded', function() {{
      if (typeof BlogViewTracker !== 'undefined') {{
        BlogViewTracker.trackPostVisit();
        const viewCountEl = document.getElementById('view-count');
        if (viewCountEl) {{
          const postHref = window.location.pathname.split('/').pop();
          const count = BlogViewTracker.getViewCount('posts/' + postHref);
          viewCountEl.textContent = BlogViewTracker.formatViews(count);
        }}
      }}
    }});
  </script>
</body>
</html>
"""


def extract_post_meta(path: Path, posts_dir: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    title_match = re.search(r"<h1[^>]*>(.*?)</h1>", text, flags=re.I | re.S)
    desc_match = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', text, flags=re.I)
    date_match = re.search(r'<meta\s+property="article:published_time"\s+content="([^"]*)"', text, flags=re.I)
    category = "블로그"
    category_match = re.search(r'<span\s+class="post-category"[^>]*>(.*?)</span>', text, flags=re.I | re.S)
    if category_match:
        category = strip_inline_html(category_match.group(1))
    else:
        meta_match = re.search(r'<div\s+class="post-meta"[^>]*>(.*?)</div>', text, flags=re.I | re.S)
        if meta_match:
            spans = re.findall(r"<span[^>]*>(.*?)</span>", meta_match.group(1), flags=re.I | re.S)
            cleaned = [strip_inline_html(item) for item in spans]
            if len(cleaned) > 1:
                category = cleaned[1]
    title = strip_inline_html(title_match.group(1)) if title_match else path.stem
    excerpt = html.unescape(desc_match.group(1)).strip() if desc_match else ""
    date = date_match.group(1).strip() if date_match else path.stat().st_mtime_ns
    href = path.relative_to(posts_dir.parent).as_posix()
    return {
        "title": title,
        "excerpt": excerpt,
        "date": str(date)[:10],
        "category": category,
        "href": href,
        "modified": str(path.stat().st_mtime_ns),
    }


def update_posts_manifest(bot: dict[str, Any]) -> Path:
    reference = ROOT / bot["site"]["reference_post_path"]
    posts_dir = reference.parent
    log("scanning posts folder for index.json")
    posts = [extract_post_meta(path, posts_dir) for path in posts_dir.rglob("*.html")]
    posts.sort(key=lambda item: item["modified"], reverse=True)
    for item in posts:
        item.pop("modified", None)
    manifest_path = posts_dir / "index.json"
    manifest_path.write_text(json.dumps(posts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"posts manifest updated: {manifest_path}")
    return manifest_path


def get_site_root(bot: dict[str, Any]) -> Path:
    return (ROOT / bot["site"]["main_page_path"]).parent


def ftp_mkdirs(ftp: ftplib.FTP, remote_dir: str) -> None:
    remote_dir = remote_dir.strip("/")
    if not remote_dir:
        return
    current = ""
    for part in remote_dir.split("/"):
        current = f"{current}/{part}" if current else part
        try:
            ftp.mkd(current)
        except ftplib.error_perm as exc:
            if not str(exc).startswith("550"):
                raise


def upload_file_ftp(ftp: ftplib.FTP, local_path: Path, remote_path: str) -> None:
    remote_dir = posixpath.dirname(remote_path)
    ftp_mkdirs(ftp, remote_dir)
    with local_path.open("rb") as handle:
        ftp.storbinary(f"STOR {remote_path}", handle)


def upload_generated_files(bot: dict[str, Any], files: list[Path]) -> None:
    host = os.getenv("BLOG_FTP_HOST", "").strip()
    user = os.getenv("BLOG_FTP_USER", "").strip()
    password = os.getenv("BLOG_FTP_PASSWORD", "")
    remote_root = os.getenv("BLOG_FTP_REMOTE_DIR", "").strip().strip("/")
    if not host or not user or not password:
        log("upload skipped: set BLOG_FTP_HOST, BLOG_FTP_USER, BLOG_FTP_PASSWORD")
        return

    site_root = get_site_root(bot)
    upload_targets: list[Path] = []
    for path in files:
        if path.exists() and path not in upload_targets:
            upload_targets.append(path)

    for path in (site_root / "blog" / "index.html", site_root / "common-site.css"):
        if path.exists() and path not in upload_targets:
            upload_targets.append(path)

    log(f"connecting FTP server: {host}")
    with ftplib.FTP(host, timeout=30) as ftp:
        ftp.login(user, password)
        for local_path in upload_targets:
            rel = local_path.relative_to(site_root).as_posix()
            remote_path = posixpath.join(remote_root, rel) if remote_root else rel
            upload_file_ftp(ftp, local_path, remote_path)
            log(f"uploaded {rel}")


def save_post(bot: dict[str, Any], content: str) -> Path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from add_post_search_links import update_html

    log("converting Ollama markdown to HTML post")
    fallback_title = bot["article"].get("title_hint", "최신 로봇 모델 관찰기")
    title, body_markdown = extract_markdown_title(content, fallback_title)
    plain = strip_inline_html(body_markdown)
    excerpt = plain[:155] + ("..." if len(plain) > 155 else "")
    stamp = dt.datetime.now().strftime("%H%M%S")
    slug = slugify_title(title, stamp)
    body_html = markdown_to_html(body_markdown)
    html_doc = render_post_html(title, body_html, excerpt, slug)

    posts_dir = (ROOT / bot["site"]["reference_post_path"]).parent
    posts_dir.mkdir(parents=True, exist_ok=True)
    out_path = posts_dir / slug
    out_path.write_text(html_doc, encoding="utf-8")
    log(f"html post saved: {out_path}")
    update_html(out_path)
    log("sentence search links applied")
    manifest_path = update_posts_manifest(bot)
    upload_generated_files(bot, [out_path, manifest_path])
    return out_path


def run_once(bot_path: Path, dry_run: bool, no_upload: bool) -> Path:
    log(f"bot run started: {bot_path}")
    bot = load_bot(bot_path)
    weights = collect_weight_context(bot)
    searches = collect_search_context(bot)
    prompt = build_prompt(bot, weights, searches)

    if dry_run:
        log("dry-run mode: Ollama call skipped")
        content = "# DRY RUN PROMPT\n\n```text\n" + prompt + "\n```\n"
        return save_draft(bot, content)

    content = call_ollama(bot, prompt)
    if not content:
        raise RuntimeError("Ollama returned an empty response.")

    if no_upload:
        log("no-upload mode enabled")
        old_host = os.environ.pop("BLOG_FTP_HOST", None)
        try:
            return save_post(bot, content)
        finally:
            if old_host is not None:
                os.environ["BLOG_FTP_HOST"] = old_host

    return save_post(bot, content)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Chamsosik .bot file for robot blog drafting.")
    parser.add_argument("bot_file", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Build the prompt and save it instead of calling Ollama.")
    parser.add_argument("--no-upload", action="store_true", help="Create the post without uploading files.")
    parser.add_argument("--watch", action="store_true", help="Repeat post generation on an interval.")
    parser.add_argument("--interval-minutes", type=float, default=30.0, help="Watch interval in minutes. Default: 30.")
    args = parser.parse_args()

    bot_path = args.bot_file if args.bot_file.is_absolute() else ROOT / args.bot_file
    if args.watch:
        interval = max(args.interval_minutes, 1.0) * 60
        log(f"watch mode started: interval {interval / 60:.1f} minutes")
        while True:
            try:
                out_path = run_once(bot_path, args.dry_run, args.no_upload)
                log(f"run complete: {out_path}")
            except Exception as exc:
                log(f"run failed: {exc}")
            log(f"waiting {interval / 60:.1f} minutes")
            time.sleep(interval)
    else:
        out_path = run_once(bot_path, args.dry_run, args.no_upload)
        log(f"run complete: {out_path}")
        print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
