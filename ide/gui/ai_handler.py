"""
AI 응답 생성 및 처리
"""

import requests
import re
from datetime import datetime

from .config import OLLAMA_URL, DATABASE_BASE_URL
from .utils import log_debug, clean_text_simple
from .news_manager import DateHelper


class AIHandler:
    """AI 응답 생성 관리"""
    
    def __init__(self, model: str = None):
        self.current_model = model
    
    def set_model(self, model: str):
        """모델 설정"""
        self.current_model = model
    
    def generate_simple(self, prompt: str, model: str = None, temperature: float = 0.6, timeout: int = 120) -> str:
        """간단한 AI 응답 생성"""
        try:
            use_model = model or self.current_model
            if not use_model:
                return "모델이 설정되지 않았습니다."
            
            log_debug(f"Sending prompt to Ollama (model: {use_model})...")
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": use_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": 2000,
                        "top_k": 40,
                        "top_p": 0.9
                    }
                },
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()
            log_debug(f"Response received")
            
            answer = data.get('response', '').strip()
            return clean_text_simple(answer) if answer else "응답을 생성할 수 없습니다."
            
        except Exception as e:
            log_debug(f"[AI 오류] {e}")
            return f"응답 생성 중 오류: {str(e)[:100]}"
    
    def generate_category_from_text(self, text: str) -> str:
        """텍스트 내용으로 카테고리 생성"""
        try:
            prompt = f"""다음 텍스트를 읽고 가장 적절한 카테고리를 한 단어로 답변하세요.
카테고리 예시: 비트코인, 정치, 경제, 사회, 문화, 게임, 드라마, 영화, 애니메이션, 괴물딴지, 스포츠, 기술, 국제, 연예, 사건사고, 건강, 교육

카테고리 설명:
- 괴물딴지: 미스테리, 괴담, 미소지막, 공포, 검은색 덕후, UFO, 초능력, 초자연 현상, 행운, 불운 등 신비로운 주제

텍스트: {text[:200]}

지시사항:
- 한 단어로만 답변하세요 (예: 정치)
- 설명이나 부연 없이 카테고리명만 출력하세요

카테고리:"""

            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": self.current_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            category = data.get('response', '일반').strip()
            
            # 깔끔하게 정리
            category = category.split('\n')[0].strip()
            category = re.sub(r'[^\w가-힣]', '', category)
            
            return category if category else "일반"
        except Exception as e:
            log_debug(f"[카테고리 생성 오류] {e}")
            return "일반"
    
    def filter_recent_news_by_ai(self, summary_text: str, category: str = "검색") -> list:
        """AI로 최신 뉴스 필터링"""
        try:
            today = datetime.now().strftime("%Y년 %m월 %d일")
            
            # 카테고리별 필터링 규칙
            must_be_today = category in ["정치", "경제"]
            prefer_today = category in ["사회", "문화", "게임", "드라마", "영화", "애니메이션", "스포츠"]
            no_date_limit = category in ["괴물딴지", "기술"]
            
            if must_be_today:
                filter_prompt = f"""다음은 검색 결과 요약입니다. 

카테고리: {category}
오늘 날짜: {today}

**필수 조건: 오늘({today})의 뉴스/정보만 포함하세요.**

**제외할 항목:**
1. 오늘이 아닌 다른 날짜
2. 과거 날짜 (작년, 지난달 등)
3. 미래 날짜

요약:
{summary_text}

지시사항:
1. 각 항목이 정확히 오늘({today})의 정보인지 확인
2. 오늘이 아닌 모든 항목 제외
3. 원래 형식대로 "• [내용]" 형태로 반환
4. 조건에 맞는 항목이 없으면 빈 결과 반환

필터링된 결과:"""
            
            elif prefer_today:
                filter_prompt = f"""다음은 검색 결과 요약입니다.

카테고리: {category}
오늘 날짜: {today}

**선호 조건: 오늘({today})부터 최근 1주일 내의 뉴스/정보만 포함하세요.**

**제외할 항목:**
1. 명백한 과거 날짜 (작년, 지난해, 2025년, 2024년 등)
2. 미래 날짜

요약:
{summary_text}

지시사항:
1. 각 항목의 날짜를 확인
2. 지난해/작년 같은 과거 명시 정보는 제외
3. 최근 1주일 내의 항목 우선
4. 원래 형식대로 "• [내용]" 형태로 반환
5. 조건에 맞는 항목이 없으면 빈 결과 반환

필터링된 결과:"""
            
            else:  # no_date_limit
                filter_prompt = f"""다음은 검색 결과 요약입니다.

카테고리: {category}

**조건: 현재/최신 정보 우선이지만 과거 정보도 포함 가능**

**제외할 항목:**
1. 명확한 과거 출시/발표 날짜가 과도하게 오래된 경우만 고려
   (예: 5년 이상 전, 매우 오래된 정보)
2. 미래 날짜는 제외

요약:
{summary_text}

지시사항:
1. 대부분의 항목을 포함 (정보성 있는 모든 항목)
2. 너무 오래된 정보(5년 이상 전)만 제외
3. 원래 형식대로 "• [내용]" 형태로 반환
4. 조건에 맞는 항목이 없으면 빈 결과 반환

필터링된 결과:"""
            
            log_debug(f"[AI 필터링] 카테고리({category}) 분석 중...")
            
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": self.current_model,
                    "prompt": filter_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 1000
                    }
                },
                timeout=30
            )
            
            if response.status_code != 200:
                log_debug(f"[AI 필터링 실패] Status: {response.status_code}")
                return []
            
            filtered_text = response.json().get('response', '').strip()
            log_debug(f"[AI 필터링 결과] {filtered_text[:100]}")
            
            if not filtered_text or filtered_text == "":
                log_debug(f"[AI 필터링] 카테고리({category}) 조건에 맞는 항목 없음")
                return []
            
            # 각 라인을 항목으로 추출
            news_items = []
            for line in filtered_text.split('\n'):
                line = line.strip()
                if not line or line.startswith('━') or line.startswith('─'):
                    continue
                if line.startswith('•'):
                    line = line[1:].strip()
                elif line.startswith('-'):
                    line = line[1:].strip()
                
                if len(line) > 20:
                    news_items.append(line)
            
            log_debug(f"[AI 필터링] {len(news_items)}개 항목 추출")
            return news_items
            
        except requests.exceptions.Timeout:
            log_debug("[AI 필터링] 타임아웃")
            return []
        except Exception as e:
            log_debug(f"[AI 필터링 오류] {e}")
            return []
    
    def is_recent_text_by_ai(self, text: str, category: str = "검색") -> bool:
        """AI로 텍스트 신선도 판단"""
        if DateHelper.is_text_stale_by_date(text, category):
            return False

        try:
            today = datetime.now().strftime("%Y년 %m월 %d일")
            prompt = f"""다음 문장이 최신 정보인지 판단하세요.

오늘 날짜: {today}
카테고리: {category}

규칙:
- 정치/경제는 오늘({today}) 정보만 최신
- 사회/문화/게임/드라마/영화/애니메이션/스포츠는 최근 7일 이내면 최신
- 그 외는 명백한 과거 연도/날짜가 있으면 오래됨

문장:
{text}

출력 형식: YES 또는 NO 중 하나만 반환
"""
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": self.current_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=12
            )
            response.raise_for_status()
            data = response.json()
            verdict = (data.get('response') or '').strip().upper()
            return verdict.startswith("YES")
        except Exception as e:
            log_debug(f"[신선도 판단 오류] {e}")
            return not DateHelper.is_text_stale_by_date(text, category)
