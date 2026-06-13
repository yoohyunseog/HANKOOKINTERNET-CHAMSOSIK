#!/usr/bin/env python3
"""
Restore corrupted HTML posts from markdown files.
"""
import re
import html
from pathlib import Path

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


def extract_markdown_title(content: str, fallback: str) -> tuple[str, str]:
    lines = content.strip().splitlines()
    for index, line in enumerate(lines[:12]):
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            # Remove markdown links from title
            title = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', title)
            return title or fallback, "\n".join(lines[index + 1:]).strip()
        bold_match = re.fullmatch(r"\*\*(.+?)\*\*", stripped)
        if bold_match:
            title = bold_match.group(1).strip()
            return title or fallback, "\n".join(lines[index + 1:]).strip()
    return fallback, content.strip()


def strip_inline_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[*_`>#-]+", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def render_post_html(title: str, body_html: str, excerpt: str, slug: str) -> str:
    import datetime as dt
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
	<script src="./js/ahrefs-analytics.js"></script>
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
</body>
</html>
"""


def main():
    import datetime as dt
    
    # Define paths
    posts_dir = Path(__file__).resolve().parent.parent / "posts"
    generated_dir = Path(__file__).resolve().parent.parent / "generated_posts"
    
    # Find markdown files
    md_files = sorted(generated_dir.glob("latest_robot_post_*.md"), reverse=True)
    
    if not md_files:
        print("No markdown files found!")
        return
    
    # Use the two most recent files
    md_files_to_restore = md_files[:2]
    
    for md_path in md_files_to_restore:
        print(f"Processing: {md_path.name}")
        
        # Read markdown content
        content = md_path.read_text(encoding="utf-8")
        
        # Extract title and body
        title, body = extract_markdown_title(content, md_path.stem)
        
        # Create excerpt from first paragraph
        first_para_match = re.search(r'^(?:\*\*[^*]+\*\*\n\n)?(.+?)(?:\n\n|$)', body, re.S)
        excerpt = strip_inline_html(first_para_match.group(1)[:200] if first_para_match else title)
        
        # Convert markdown to HTML
        body_html = markdown_to_html(body)
        
        # Generate slug
        stamp = md_path.stem.split("_")[-1]
        date_prefix = dt.datetime.now().strftime("%Y-%m-%d")
        
        # Create slug from title
        title_words = re.findall(r"[A-Za-z0-9가-힣]+", title)
        if title_words:
            slug_words = "-".join(title_words[:6]).lower()
            slug = f"{date_prefix}-{slug_words}-{stamp}.html"
        else:
            slug = f"{date_prefix}-latest-robot-post-{stamp}.html"
        
        # Render HTML
        html_content = render_post_html(title, body_html, excerpt, slug)
        
        # Write to posts directory
        output_path = posts_dir / slug
        output_path.write_text(html_content, encoding="utf-8")
        print(f"Created: {output_path}")


if __name__ == "__main__":
    main()