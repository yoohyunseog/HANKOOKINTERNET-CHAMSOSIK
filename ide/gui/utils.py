"""
유틸리티 함수 모음
"""

import os
import re
import html
from datetime import datetime
from .config import LOG_FILE


def log_debug(msg):
    """디버그 로그를 파일과 콘솔에 출력"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_msg + "\n")
    except:
        pass


def clean_text_simple(text: str) -> str:
    """텍스트에서 특수문자와 HTML 태그 제거"""
    if not text:
        return text
    
    # HTML 엔티티 디코딩
    text = html.unescape(text)
    
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    
    # CDATA 제거
    text = text.replace('<![CDATA[', '').replace(']]>', '')
    
    # 여러 공백을 한 칸으로
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def format_news_answer(answer: str) -> str:
    """뉴스 답변 포맷팅"""
    if not answer:
        return answer
    text = answer.replace(' // ', '\n')
    text = re.sub(r'(\s*)(\d+️⃣|\d+\.|\d+\))', lambda m: '\n' + m.group(2), text)
    if text.strip().startswith('-'):
        text = re.sub(r'\s-\s+', '\n- ', text)
    text = re.sub(r'\s+-\s+(?=\*\*)', '\n- ', text)
    return text.strip()


def extract_news_items(answer: str) -> list:
    """뉴스 답변에서 항목 추출"""
    items = []
    for line in answer.splitlines():
        match = re.match(r'^\s*(\d+️⃣|\d+\.|\d+\))\s*(.+)', line)
        if match:
            items.append(match.group(2).strip())
            continue
        if re.match(r'^\s*-\s+\S+', line):
            items.append(line.lstrip('-').strip())
            continue
        if re.match(r'^\s*\*\*.+\*\*\s*:', line):
            cleaned = re.sub(r'\*\*', '', line).strip()
            items.append(cleaned)
    return items


def is_news_query(question: str, answer: str) -> bool:
    """뉴스 질문인지 판단"""
    if not question:
        return False
    keywords = ['뉴스', '주요 뉴스', '오늘 뉴스']
    if any(k in question for k in keywords):
        return True
    return bool(re.search(r'\d+️⃣|\d+\.|^\s*-\s+', answer or '', re.MULTILINE))


def number_to_path(value: float) -> str:
    """숫자를 경로로 변환"""
    value_str = repr(value).replace('-', '_')
    parts = []
    for ch in value_str:
        if ch == '.':
            parts.append('.')
        elif ch.isdigit() or ch == '_':
            parts.append(ch)
    return os.path.join(*parts) if parts else '0'
