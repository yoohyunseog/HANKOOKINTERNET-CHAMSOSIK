"""
설정 및 상수 정의
"""

import os
from datetime import datetime

# API URLs
OLLAMA_URL = "http://localhost:11434"
NB_API_URL = os.getenv("NB_API_URL", "http://localhost:3000")
DATABASE_BASE_URL = os.getenv("DATABASE_BASE_URL", "https://xn--9l4b4xi9r.com")

# Feature Flags
AUTO_UPLOAD_DATA = os.getenv("AUTO_UPLOAD_DATA", "1") == "1"
AJAX_SAVE_ENABLED = os.getenv("AJAX_SAVE_ENABLED", "1") == "1"
SAVE_LOCAL_SUMMARY = os.getenv("SAVE_LOCAL_SUMMARY", "0") == "1"

# Directories
HISTORY_DIR = "data/ollama_chat"
LOG_FILE = os.path.join(HISTORY_DIR, "debug.log")
ROTATION_FILE = os.path.join(HISTORY_DIR, "model_rotation.json")
FAVORITES_FILE = os.path.join(HISTORY_DIR, "favorites.json")
TREND_DATA_FILE = "data/naver_creator_trends/latest_trend_data.json"

# 디렉토리 생성
os.makedirs(HISTORY_DIR, exist_ok=True)

# UI 색상
COLORS = {
    'bg_dark': '#0f172a',
    'bg_medium': '#1e293b',
    'bg_light': '#334155',
    'text_primary': '#e2e8f0',
    'text_secondary': '#94a3b8',
    'text_tertiary': '#64748b',
    'accent': '#22c55e',
    'accent_blue': '#3b82f6',
    'accent_cyan': '#38bdf8',
    'black': '#000'
}

# 카테고리 목록
CATEGORIES = [
    ("전체", "all"),
    ("정치", "정치"),
    ("경제", "경제"),
    ("사회", "사회"),
    ("문화", "문화"),
    ("게임", "게임"),
    ("드라마", "드라마"),
    ("영화", "영화"),
    ("애니메이션", "애니메이션"),
    ("괴물딴지", "괴물딴지"),
    ("스포츠", "스포츠"),
    ("기술", "기술"),
    ("국제", "국제"),
    ("연예", "연예"),
    ("사건사고", "사건사고"),
    ("건강", "건강"),
    ("교육", "교육"),
    ("비트코인", "비트코인"),
]

# 검색 키워드
SEARCH_KEYWORDS = [
    '오늘', '어제', '내일', '요즘', '최근', '현재', '지금', '뉴스', '트렌드', '인기',
    '유행', '핫', '뜨는', '뜨고', '화제', '이슈', '속도', '빠른', '새로운', '신',
    '다가오는', '다음', '예정', '개최', '개최됨', '오픈', '론칭', '출시', '공개',
    '실시간', '라이브', '생중계', '방송', '영상', '동영상', '유튜브', '유튜버',
    '조회수', '조회', '인기도', '랭킹', '순위', '베스트', '톱10', '추천',
    '검색', '정보', '소식', '기사', '보도', '보고', '발표', '성명', '의견',
    '리뷰', '평가', '평판', '후기', '후기글', '댓글', '반응', '반응글', '논란',
    '찬성', '반대', '비판', '비판글', '지적', '지탄', '분노', '논쟁'
]

# 네비게이션 제외 항목
NAV_ITEMS = {
    '참소식 블로그', '홈', '통합 데이터', '유입분석', '리워드', '트렌드', '비즈니스',
    '검색 유입 트렌드', '메인 유입 트렌드', '주제별 비교', '주제별 트렌드',
    '주제별 인기유입검색어', '성별,연령별 인기유입검색어', '유입순 보기', '설정순 보기'
}

# 기본 즐겨찾기
DEFAULT_FAVORITES = [
    "/트렌드검색반복 60",
    "/반복 1 0 오늘 주요 뉴스",
    "오늘 주요 뉴스",
    "/뉴스",
    "/도움말"
]

# 환영 메시지
WELCOME_MESSAGE = """안녕하세요! AI 어시스턴트입니다 👋

🤖 자동 검색 기능:
  • 질문만 하면 AI가 필요시 자동으로 검색합니다!
  • 예: "요즘 트렌드가 뭐야?"
  • 예: "오늘 주요 뉴스"
  • 예: "파이썬 강좌 추천해줘"

🔍 수동 검색 (NEW):
  • /검색 키워드 - 네이버 + Bing + 뉴스 통합 검색 (🆕)
  • /네이버 키워드 - 네이버 웹 검색  
  • /빙 키워드 - Bing 웹 검색 (🆕)
  • /뉴스 키워드 - 뉴스 검색 (🆕)
  • /유튜브 키워드 - 유튜브 검색

🔁 반복 실행:
    • /반복 횟수 [간격초] 질문 - 질문 반복 실행
    • /반복중지 - 반복 실행 중단

🧾 트렌드 일괄 실행:
    • /트렌드반복 [간격초] - 최신 트렌드 키워드 순서대로 실행
    • /트렌드반복 [간격초] --infinite - 트렌드 반복 (무한 반복)
    • /트렌드검색반복 [간격초] [키워드,키워드] - 최신 트렌드 키워드를 /검색으로 순서 실행
    • /트렌드검색반복 [간격초] --infinite [키워드,키워드] - 검색 반복 (무한 반복)
    • /트렌드검색반복 [간격초] --bg [키워드,키워드] - 페이지를 백그라운드로 열기

⭐ 즐겨찾기:
    • 입력 후 [+ 추가] 버튼 클릭하여 저장
    • 버튼 클릭으로 빠른 입력
    • 우클릭으로 삭제

💬 일반 AI 채팅도 가능합니다!"""
