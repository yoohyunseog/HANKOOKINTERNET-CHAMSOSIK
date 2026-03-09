#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import html
import os
import re
from pathlib import Path


def extract_labels(mmd_text: str):
    labels = re.findall(r"\[(.*?)\]", mmd_text, flags=re.DOTALL)
    cleaned = []
    seen = set()
    for raw in labels:
        text = html.unescape(raw)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(text)
    return cleaned


def build_meta(labels):
    if len(labels) >= 2:
        headline = f"{labels[0]} → {labels[1]}"
    elif labels:
        headline = labels[0]
    else:
        headline = "실시간 이슈 흐름"

    title = f"참소식.com | {headline}"
    if len(title) > 70:
        title = "참소식.com | 실시간 이슈 맵 · 뉴스 트렌드 분석"

    summary_terms = labels[:4] if labels else ["실시간 이슈", "뉴스 트렌드"]
    summary = " · ".join(summary_terms)

    description = (
        f"참소식.com 실시간 이슈 맵: {summary} 흐름을 한눈에 확인하고, "
        f"지정학 리스크·글로벌 경제 영향을 빠르게 파악하세요."
    )

    keyword_base = [
        "참소식",
        "실시간 이슈",
        "뉴스 트렌드",
        "이슈 맵",
        "지정학 리스크",
        "글로벌 경제",
    ]

    keywords = []
    seen = set()
    for term in keyword_base + labels[:10]:
        t = term.strip()
        if not t:
            continue
        k = t.lower()
        if k in seen:
            continue
        seen.add(k)
        keywords.append(t)

    keyword_text = ", ".join(keywords)

    return {
        "title": title,
        "description": description,
        "keywords": keyword_text,
        "og:title": title,
        "og:description": description,
        "twitter:title": title,
        "twitter:description": description,
        "og:image:alt": "참소식.com 실시간 이슈 맵 미리보기",
    }


def replace_meta_content(html_text: str, name: str, value: str, is_property=False):
    attr = "property" if is_property else "name"
    pattern = re.compile(
        rf'(<meta\s+[^>]*{attr}=["\']{re.escape(name)}["\'][^>]*content=["\'])([^"\']*)(["\'][^>]*>)',
        flags=re.IGNORECASE,
    )
    if pattern.search(html_text):
        return pattern.sub(rf"\g<1>{value}\g<3>", html_text, count=1)

    insert = f'  <meta {attr}="{name}" content="{value}">\n'
    return html_text.replace("</head>", insert + "</head>", 1)


def replace_title(html_text: str, title: str):
    pattern = re.compile(r"<title>.*?</title>", flags=re.IGNORECASE | re.DOTALL)
    if pattern.search(html_text):
        return pattern.sub(f"<title>{title}</title>", html_text, count=1)
    return html_text.replace("</head>", f"  <title>{title}</title>\n</head>", 1)


def update_index_html(index_path: Path, meta: dict):
    html_text = index_path.read_text(encoding="utf-8")

    html_text = replace_title(html_text, meta["title"])
    html_text = replace_meta_content(html_text, "description", meta["description"], is_property=False)
    html_text = replace_meta_content(html_text, "keywords", meta["keywords"], is_property=False)

    html_text = replace_meta_content(html_text, "og:title", meta["og:title"], is_property=True)
    html_text = replace_meta_content(html_text, "og:description", meta["og:description"], is_property=True)
    html_text = replace_meta_content(html_text, "og:image:alt", meta["og:image:alt"], is_property=True)

    html_text = replace_meta_content(html_text, "twitter:title", meta["twitter:title"], is_property=False)
    html_text = replace_meta_content(html_text, "twitter:description", meta["twitter:description"], is_property=False)

    index_path.write_text(html_text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="website_diagram.mmd 기반 index.html 메타 태그 자동 업데이트")
    parser.add_argument(
        "--mmd",
        default="web/public/한국인터넷.한국/참소식.com/website_diagram.mmd",
        help="입력 Mermaid 파일 경로",
    )
    parser.add_argument(
        "--html",
        default="web/public/한국인터넷.한국/참소식.com/index.html",
        help="업데이트할 index.html 경로",
    )
    args = parser.parse_args()

    mmd_path = Path(args.mmd)
    html_path = Path(args.html)

    if not mmd_path.exists():
        raise FileNotFoundError(f"MMD 파일을 찾을 수 없습니다: {mmd_path}")
    if not html_path.exists():
        raise FileNotFoundError(f"HTML 파일을 찾을 수 없습니다: {html_path}")

    mmd_text = mmd_path.read_text(encoding="utf-8")
    labels = extract_labels(mmd_text)
    meta = build_meta(labels)

    update_index_html(html_path, meta)

    print("✅ 메타 태그 업데이트 완료")
    print(f"- MMD: {mmd_path}")
    print(f"- HTML: {html_path}")
    print(f"- Title: {meta['title']}")


if __name__ == "__main__":
    main()
