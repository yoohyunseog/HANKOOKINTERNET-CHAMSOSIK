#!/usr/bin/env python3
"""
Add sentence-level search links to blog posts.

Each link uses a keyword selected from the sentence as anchor text, while the
actual search query is: post title + sentence.
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path
from urllib.parse import quote_plus


def find_workspace_root() -> Path:
    for path in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]:
        if (path / "web").exists() and (path / "search").exists():
            return path
    return Path(__file__).resolve().parents[6]


ROOT = find_workspace_root()
START = "<!-- sentence-search-links:start -->"
END = "<!-- sentence-search-links:end -->"
INLINE_CLASS = "sentence-search-inline"
SEARCH_BASE = "https://www.google.com/search?q="

STOPWORDS = {
    "그리고", "하지만", "그러나", "또한", "이번", "현재", "기준", "중심", "때문",
    "것이다", "있다", "한다", "했다", "된다", "위해", "대한", "가장", "단순히",
    "that", "with", "from", "this", "these", "those", "into", "about", "their",
}


def remove_existing_block(text: str) -> str:
    pattern = re.escape(START) + r".*?" + re.escape(END)
    return re.sub(pattern, "", text, flags=re.S).rstrip() + "\n"


def remove_existing_inline_links(text: str) -> str:
    pattern = (
        r"<a\b(?=[^>]*\bclass=[\"'][^\"']*\b"
        + re.escape(INLINE_CLASS)
        + r"\b[^\"']*[\"'])[^>]*>(.*?)</a>"
    )
    return re.sub(pattern, r"\1", text, flags=re.I | re.S)


def clean_text(value: str) -> str:
    value = re.sub(r"<script\b[^>]*>.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?。！？다요죠음임됨함])\s+", text)
    sentences = []
    for part in parts:
        sentence = part.strip(" -\t\r\n")
        if len(sentence) < 24:
            continue
        if sentence.startswith(("http://", "https://")):
            continue
        sentences.append(sentence)
    return sentences


def choose_keyword(sentence: str) -> str:
    tokens = re.findall(r"[가-힣A-Za-z][가-힣A-Za-z0-9·&.-]{1,}", sentence)
    ranked = []
    for token in tokens:
        bare = token.strip(".-")
        if len(bare) < 2 or bare.lower() in STOPWORDS or bare in STOPWORDS:
            continue
        has_signal = bool(re.search(r"[A-Z0-9]", bare)) or len(bare) >= 4
        score = (3 if has_signal else 0) + min(len(bare), 14)
        ranked.append((score, bare))
    if not ranked:
        return "검색"
    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[0][1]


def search_url(title: str, sentence: str) -> str:
    return SEARCH_BASE + quote_plus(f"{title} {sentence}")


def unique_sentences(sentences: list[str]) -> list[str]:
    seen = set()
    result = []
    for sentence in sentences:
        key = re.sub(r"\s+", " ", sentence)
        if key in seen:
            continue
        seen.add(key)
        result.append(sentence)
    return result


def extract_html_title(text: str, path: Path) -> str:
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", text, flags=re.I | re.S)
    if h1:
        return clean_text(h1.group(1))
    title = re.search(r"<title[^>]*>(.*?)</title>", text, flags=re.I | re.S)
    if title:
        return clean_text(title.group(1)).split("|", 1)[0].strip()
    return path.stem


def extract_html_sentences(text: str) -> list[str]:
    article = re.search(r"<article\b[^>]*>(.*?)</article>", text, flags=re.I | re.S)
    source = article.group(1) if article else text
    paragraphs = re.findall(r"<p\b[^>]*>(.*?)</p>", source, flags=re.I | re.S)
    sentences = []
    for paragraph in paragraphs:
        cleaned = clean_text(paragraph)
        if not cleaned or "©" in cleaned:
            continue
        sentences.extend(split_sentences(cleaned))
    return unique_sentences(sentences)


def build_html_block(title: str, sentences: list[str]) -> str:
    items = []
    for sentence in sentences:
        keyword = choose_keyword(sentence)
        items.append(
            '        <li>'
            f'<a href="{html.escape(search_url(title, sentence), quote=True)}" '
            'target="_blank" rel="noopener">'
            f"{html.escape(keyword)}</a>"
            f"<span>{html.escape(sentence)}</span>"
            "</li>"
        )
    if not items:
        return ""
    return "\n".join(
        [
            f"      {START}",
            '      <section class="sentence-search-links" aria-labelledby="sentence-search-links-title">',
            '        <h2 id="sentence-search-links-title">문장별 검색 링크</h2>',
            "        <ul>",
            *items,
            "        </ul>",
            "      </section>",
            f"      {END}",
        ]
    )


def link_keyword_in_html_sentence(inner_html: str, title: str, sentence: str) -> str:
    keyword = choose_keyword(sentence)
    if keyword == "검색":
        return inner_html
    href = html.escape(search_url(title, sentence), quote=True)
    anchor = (
        f'<a class="{INLINE_CLASS}" href="{href}" '
        f'target="_blank" rel="noopener">{html.escape(keyword)}</a>'
    )
    pattern = re.compile(r"(?<![A-Za-z0-9가-힣_])" + re.escape(keyword) + r"(?![A-Za-z0-9가-힣_])")

    pieces = re.split(r"(<[^>]+>)", inner_html)
    in_anchor = False
    for index, piece in enumerate(pieces):
        if not piece:
            continue
        if piece.startswith("<"):
            if re.match(r"<a\b", piece, flags=re.I):
                in_anchor = True
            elif re.match(r"</a\s*>", piece, flags=re.I):
                in_anchor = False
            continue
        if in_anchor:
            continue
        replaced, count = pattern.subn(anchor, piece, count=1)
        if count:
            pieces[index] = replaced
            return "".join(pieces)
    return inner_html


def add_inline_links_to_html_paragraph(inner_html: str, title: str) -> str:
    if "<a " in inner_html.lower():
        return inner_html
    plain = clean_text(inner_html)
    if not plain:
        return inner_html
    updated = inner_html
    for sentence in split_sentences(plain):
        updated = link_keyword_in_html_sentence(updated, title, sentence)
    return updated


def add_inline_links_to_html(text: str, title: str) -> str:
    def replace_paragraph(match: re.Match[str]) -> str:
        attrs = match.group(1)
        inner = match.group(2)
        return f"<p{attrs}>{add_inline_links_to_html_paragraph(inner, title)}</p>"

    article = re.search(r"<article\b[^>]*>(.*?)</article>", text, flags=re.I | re.S)
    if not article:
        return text
    article_text = article.group(0)
    linked_article = re.sub(r"<p\b([^>]*)>(.*?)</p>", replace_paragraph, article_text, flags=re.I | re.S)
    return text[: article.start()] + linked_article + text[article.end() :]


def update_html(path: Path) -> bool:
    original = path.read_text(encoding="utf-8", errors="replace")
    base = remove_existing_inline_links(remove_existing_block(original))
    title = extract_html_title(base, path)
    linked = add_inline_links_to_html(base, title)
    block = build_html_block(title, extract_html_sentences(linked))
    if not block or "</article>" not in linked:
        return False
    updated = linked.replace("    </article>", block + "\n    </article>", 1)
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def extract_markdown_title(text: str, path: Path) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
        if stripped and not stripped.startswith(("<!--", "```", "---")):
            return stripped.strip("#* ")
    return path.stem


def extract_markdown_sentences(text: str) -> list[str]:
    base = remove_existing_inline_links(remove_existing_block(text))
    sentences = []
    in_sources = False
    title_consumed = False
    for line in base.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not title_consumed:
            title_consumed = True
            if stripped.startswith("# ") or not stripped.startswith(("<!--", "```", "---")):
                continue
        if stripped.startswith(("<!--", "```", "#", "-", "*", "|")):
            if "참고" in stripped or "URL" in stripped:
                in_sources = True
            continue
        if "참고 URL" in stripped or "참고 자료" in stripped:
            in_sources = True
            continue
        if in_sources:
            continue
        sentences.extend(split_sentences(re.sub(r"[*`]", "", stripped)))
    return unique_sentences(sentences)


def build_markdown_block(title: str, sentences: list[str]) -> str:
    if not sentences:
        return ""
    lines = [START, "## 문장별 검색 링크"]
    for sentence in sentences:
        keyword = choose_keyword(sentence)
        lines.append(f"- [{keyword}]({search_url(title, sentence)}): {sentence}")
    lines.append(END)
    return "\n".join(lines)


def link_keyword_in_markdown_sentence(line: str, title: str, sentence: str) -> str:
    keyword = choose_keyword(sentence)
    if keyword == "검색":
        return line
    href = html.escape(search_url(title, sentence), quote=True)
    anchor = (
        f'<a class="{INLINE_CLASS}" href="{href}" '
        f'target="_blank" rel="noopener">{html.escape(keyword)}</a>'
    )
    pattern = re.compile(r"(?<![A-Za-z0-9가-힣_])" + re.escape(keyword) + r"(?![A-Za-z0-9가-힣_])")
    pieces = re.split(r"(<a\b[^>]*>.*?</a>)", line, flags=re.I)
    for index, piece in enumerate(pieces):
        if not piece or piece.lower().startswith("<a"):
            continue
        replaced, count = pattern.subn(anchor, piece, count=1)
        if count:
            pieces[index] = replaced
            return "".join(pieces)
    return line


def add_inline_links_to_markdown(content: str, title: str) -> str:
    lines = []
    in_sources = False
    in_generated_block = False
    title_consumed = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == START:
            in_generated_block = True
        if in_generated_block:
            lines.append(line)
            if stripped == END:
                in_generated_block = False
            continue
        if not stripped:
            lines.append(line)
            continue
        if not title_consumed:
            title_consumed = True
            lines.append(line)
            continue
        if stripped.startswith(("<!--", "```", "#", "-", "*", "|")):
            if "참고" in stripped or "URL" in stripped:
                in_sources = True
            lines.append(line)
            continue
        if "참고 URL" in stripped or "참고 자료" in stripped:
            in_sources = True
            lines.append(line)
            continue
        if in_sources:
            lines.append(line)
            continue

        updated = line
        plain = re.sub(r"[*`]", "", clean_text(line))
        for sentence in split_sentences(plain):
            updated = link_keyword_in_markdown_sentence(updated, title, sentence)
        lines.append(updated)
    return "\n".join(lines).rstrip() + "\n"


def add_markdown_search_links(content: str, title: str | None = None, path: Path | None = None) -> str:
    fake_path = path or Path("post.md")
    base = remove_existing_inline_links(remove_existing_block(content))
    post_title = title or extract_markdown_title(base, fake_path)
    block = build_markdown_block(post_title, extract_markdown_sentences(base))
    if not block:
        return add_inline_links_to_markdown(base, post_title)
    linked = add_inline_links_to_markdown(base, post_title)
    return linked.rstrip() + "\n\n" + block + "\n"


def update_markdown(path: Path) -> bool:
    original = path.read_text(encoding="utf-8", errors="replace")
    updated = add_markdown_search_links(original, path=path)
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Add sentence search links to posts.")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    changed = 0
    for input_path in args.paths:
        path = input_path if input_path.is_absolute() else ROOT / input_path
        if path.is_dir():
            files = list(path.glob("*.html")) + list(path.glob("*.md"))
        else:
            files = [path]
        for file_path in files:
            if file_path.suffix.lower() == ".html":
                changed += int(update_html(file_path))
            elif file_path.suffix.lower() in {".md", ".markdown"}:
                changed += int(update_markdown(file_path))
    print(f"updated {changed} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
