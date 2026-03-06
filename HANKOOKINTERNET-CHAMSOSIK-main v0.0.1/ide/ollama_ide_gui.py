"""
Ollama IDE - GUI 버전 (Tkinter)
GPT 같은 채팅 인터페이스 + 대화 히스토리 + 검색 기능
"""

import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import requests
import json
import os
import sys
import time
import random
from datetime import datetime, timedelta
from threading import Thread
import glob
import re
import html
import subprocess
import webbrowser
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 로깅 설정
LOG_FILE = "data/ollama_chat/debug.log"

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

# 웹뷰 라이브러리 임포트
try:
    from tkinterweb import HtmlFrame
    WEBVIEW_AVAILABLE = True
    log_debug("[시스템] tkinterweb 사용 가능 - 웹뷰 모드로 실행")
except ImportError:
    WEBVIEW_AVAILABLE = False
    log_debug("[시스템] tkinterweb 미설치 - 브라우저 모드로 실행")

# 검색 모듈 import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from search import (
    search_naver, get_naver_results, search_youtube, get_youtube_results,
    get_naver_news_rss, get_news_by_category, format_news_summary, fetch_page_content, get_latest_naver_news,
    search_bing, get_bing_results, format_bing_results,
    get_naver_results_smart, get_bing_results_smart,
    get_naver_news_smart, get_naver_news_by_category, get_naver_news_search_selenium,  # Selenium 뉴스
    multi_search, format_multi_search_results
)
from search.naver_search import format_search_results
from search.youtube_search import format_youtube_results

OLLAMA_URL = "http://localhost:11434"
NB_API_URL = os.getenv("NB_API_URL", "http://localhost:3000")
AUTO_UPLOAD_DATA = os.getenv("AUTO_UPLOAD_DATA", "1") == "1"
DATABASE_BASE_URL = os.getenv("DATABASE_BASE_URL", "https://xn--9l4b4xi9r.com")
AJAX_SAVE_ENABLED = os.getenv("AJAX_SAVE_ENABLED", "1") == "1"
SAVE_LOCAL_SUMMARY = os.getenv("SAVE_LOCAL_SUMMARY", "0") == "1"
HISTORY_DIR = "data/ollama_chat"
ROTATION_FILE = os.path.join(HISTORY_DIR, "model_rotation.json")
os.makedirs(HISTORY_DIR, exist_ok=True)


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


class OllamaIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama IDE - GPT 같은 채팅")
        self.root.geometry("1200x700")
        self.root.configure(bg="#0f172a")
        
        self.current_model = None
        self.chat_history = []
        self.is_generating = False
        self.current_chat_file = None
        self.chat_files = []
        self.detail_logs = {}
        self.detail_tag_map = {}
        self.detail_tag_count = 0
        self.repeat_active = False
        self.repeat_remaining = 0
        self.repeat_interval = 2.0
        self.repeat_message = ""
        self.repeat_force_search = False
        self.batch_active = False
        self.batch_items = []
        self.batch_index = 0
        self.batch_interval = 2.0
        self.batch_search_mode = False
        self.batch_infinite = False
        self.batch_open_background = False
        self.model_rotation = None
        
        # 보고서 분석: AI가 이미 검색한 키워드 기억 (중복 방지)
        self.searched_keywords = []  # 이전에 생성된 질문들 저장
        
        # 즐겨찾기 명령어
        self.favorites = []
        self.favorites_file = os.path.join(HISTORY_DIR, 'favorites.json')
        
        # AI 행동 지침 로드
        self.ai_guidelines = self.load_ai_guidelines()
        
        self.setup_ui()
        self.load_models()
        self.load_history_list()
        self.load_favorites()

    def is_news_query(self, question: str, answer: str) -> bool:
        if not question:
            return False
        keywords = ['뉴스', '주요 뉴스', '오늘 뉴스']
        if any(k in question for k in keywords):
            return True
        return bool(re.search(r'\d+️⃣|\d+\.|^\s*-\s+', answer or '', re.MULTILINE))

    def notify_system(self, message: str):
        try:
            if hasattr(self, 'root'):
                self.root.after(0, self.display_message, "system", message)
            else:
                log_debug(message)
        except Exception:
            log_debug(message)

    def notify_system_detail(self, message: str, detail_key: str):
        try:
            if hasattr(self, 'root'):
                self.root.after(0, self.display_system_detail, message, detail_key)
            else:
                log_debug(message)
        except Exception:
            log_debug(message)

    def clear_detail_logs(self):
        self.detail_logs = {
            'calc': [],
            'paths': [],
            'upload': []
        }

    def add_detail_log(self, key: str, line: str):
        if key not in self.detail_logs:
            self.detail_logs[key] = []
        self.detail_logs[key].append(line)

    def show_detail_log(self, key: str):
        lines = self.detail_logs.get(key, [])
        if not lines:
            messagebox.showinfo("상세 로그", "기록된 상세 로그가 없습니다.")
            return
        messagebox.showinfo("상세 로그", "\n".join(lines))

    def extract_date_from_text(self, text: str):
        if not text:
            return None
        today = datetime.now().date()
        patterns = [
            r'(\d{4})[./-](\d{1,2})[./-](\d{1,2})',
            r'(\d{4})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일',
            r'(\d{1,2})[./-](\d{1,2})'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if not match:
                continue
            parts = [int(p) for p in match.groups()]
            try:
                if len(parts) == 3:
                    year, month, day = parts
                else:
                    year = today.year
                    month, day = parts
                return datetime(year, month, day).date()
            except ValueError:
                continue
        return None

    def is_text_stale_by_date(self, text: str, category: str = "검색") -> bool:
        if not text:
            return True

        cleaned = text.strip().lower()
        if "작년" in cleaned or "지난해" in cleaned:
            return True

        today = datetime.now().date()
        must_be_today = category in ["정치", "경제"]
        prefer_today = category in ["사회", "문화", "게임", "드라마", "영화", "애니메이션", "스포츠"]

        dt = self.extract_date_from_text(cleaned)
        if not dt:
            return False
        if dt.year < today.year:
            return True
        if must_be_today and dt != today:
            return True
        if prefer_today and dt < (today - timedelta(days=7)):
            return True
        return False

    def ai_is_recent_text(self, text: str, category: str = "검색") -> bool:
        if self.is_text_stale_by_date(text, category):
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
            data = self._ollama_generate(prompt, timeout=12)
            verdict = (data.get('response') or '').strip().upper()
            return verdict.startswith("YES")
        except Exception as e:
            log_debug(f"[신선도 판단 오류] {e}")
            return not self.is_text_stale_by_date(text, category)

    def _validate_item_relevance(self, item: str, summary_text: str, keyword: str = "") -> bool:
        """Ollama AI가 저장할 item이 원본 summary_text와 관련성이 있는지 판단"""
        try:
            if not summary_text or not item:
                return False
            
            # AI에게 관련성 판단 요청
            today = datetime.now().strftime("%Y년 %m월 %d일")
            validation_prompt = f"""다음 필터링된 뉴스 항목이 검색 결과와 관련성이 있는지 판단하세요.

📋 검색 원본 (처음 찾은 내용):
{summary_text[:500]}

🔍 검색어:
{keyword if keyword else '(없음)'}

📝 필터링된 항목 (저장 후보):
{item}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
판단 기준:
1. 필터링된 항목이 원본 검색 결과에서 나온 내용인가?
2. 검색어와의 연관성이 있는가?
3. 논리적으로 이해가 되는가?

응답: YES 또는 NO 중 하나만 반환
- YES: 저장해도 됨
- NO: 저장하지 말 것"""
            
            log_debug(f"[관련성 AI 검증] 시작: {item[:40]}...")
            data = self._ollama_generate(validation_prompt, timeout=15)
            verdict = (data.get('response') or '').strip().upper()
            
            is_valid = verdict.startswith("YES")
            status = "✅ 통과" if is_valid else "❌ 거절"
            log_debug(f"[관련성 AI 검증] {status}: AI 판단 = '{verdict}'")
            
            return is_valid
            
        except Exception as e:
            log_debug(f"[관련성 AI 검증 오류] {e} → 저장 진행")
            return True  # 오류 발생 시 저장 진행

    def save_news_result(self, question: str, answer: str):
        try:
            self.clear_detail_logs()
            self.notify_system("💾 뉴스 저장 중...")
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            nb_max_dir = os.path.join(root_dir, 'data', 'nb_max')
            nb_min_dir = os.path.join(root_dir, 'data', 'nb_min')
            os.makedirs(nb_max_dir, exist_ok=True)
            os.makedirs(nb_min_dir, exist_ok=True)

            items = self.extract_news_items(answer)
            if AJAX_SAVE_ENABLED:
                self.notify_system_detail("🧮 AJAX 저장 호출 중...", "calc")
                calculations = self.trigger_ajax_save(items)
            else:
                self.notify_system_detail("🧮 N/B 계산 및 저장 중...", "calc")
                calculations = self.save_news_nb_calculations(items)

            data = {
                'success': True,
                'count': len(calculations),
                'results': calculations
            }

            if SAVE_LOCAL_SUMMARY:
                for target_dir in (nb_max_dir, nb_min_dir):
                    target_path = os.path.join(target_dir, 'result.json')
                    with open(target_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
            if not AJAX_SAVE_ENABLED:
                self.notify_system_detail("📁 경로 저장 중...", "paths")
                self.save_news_results_by_path(calculations, nb_max_dir, nb_min_dir)

            self.notify_system("✅ 뉴스 저장 완료")
            self.upload_data_only(root_dir)
        except Exception as e:
            log_debug(f"[저장 오류] 뉴스 저장 실패: {e}")

    def trigger_ajax_save(self, items: list) -> list:
        results = []
        if not items:
            return results

        for item in items:
            try:
                url = f"{DATABASE_BASE_URL}/database.html?nb={requests.utils.quote(item)}&end=5s"
                # 브라우저 열지 않고 백그라운드에서 HTTP 요청
                response = requests.get(url, timeout=10)
                self.add_detail_log('calc', f"GET: {url} (Status: {response.status_code})")
                results.append({
                    'input': item,
                    'url': url,
                    'triggered': True,
                    'status_code': response.status_code
                })
            except Exception as e:
                self.add_detail_log('calc', f"실패: {item} - {e}")
                results.append({
                    'input': item,
                    'url': None,
                    'triggered': False,
                    'error': str(e)
                })

        return results

    def number_to_path(self, value: float) -> str:
        value_str = repr(value).replace('-', '_')
        parts = []
        for ch in value_str:
            if ch == '.':
                parts.append('.')
            elif ch.isdigit() or ch == '_':
                parts.append(ch)
        return os.path.join(*parts) if parts else '0'

    def save_news_results_by_path(self, calculations: list, nb_max_dir: str, nb_min_dir: str):
        if not calculations:
            return

        for calc in calculations:
            try:
                calc_id = calc.get('id') or calc.get('calculation_id')
                if not calc_id:
                    continue

                results = calc.get('results') or []
                if not results:
                    continue

                nb_max = results[0].get('nb_max')
                nb_min = results[0].get('nb_min')
                if nb_max is None or nb_min is None:
                    continue

                max_path = self.number_to_path(nb_max)
                min_path = self.number_to_path(nb_min)

                self.add_detail_log('paths', f"nb_max: {max_path}")
                self.add_detail_log('paths', f"nb_min: {min_path}")


                max_dir = os.path.join(nb_max_dir, max_path)
                min_dir = os.path.join(nb_min_dir, min_path)
                os.makedirs(max_dir, exist_ok=True)
                os.makedirs(min_dir, exist_ok=True)

                payload = json.dumps(calc, ensure_ascii=False, indent=2)
                max_file = os.path.join(max_dir, "results.json")
                min_file = os.path.join(min_dir, "results.json")

                with open(max_file, 'w', encoding='utf-8') as f:
                    f.write(payload)
                with open(min_file, 'w', encoding='utf-8') as f:
                    f.write(payload)
            except Exception as e:
                log_debug(f"[저장 오류] 경로 저장 실패: {e}")

    def save_news_nb_calculations(self, items: list, category: str = "news") -> list:
        results = []
        if not items:
            return results

        for item in items:
            try:
                unicode_array = [ord(ch) for ch in item]

                self.add_detail_log('calc', f"요청: {item}")

                # 1) Search existing
                search_response = requests.post(
                    f"{NB_API_URL}/api/search",
                    json={"text": item, "unicode": unicode_array},
                    timeout=20
                )
                search_response.raise_for_status()
                search_data = search_response.json()

                if search_data.get('success') and search_data.get('results'):
                    self.add_detail_log('calc', "기존 결과 사용")
                    results.append(search_data['results'][0])
                    continue

                # 2) Calculate & save
                calc_response = requests.post(
                    f"{NB_API_URL}/api/calculate",
                    json={"input": item, "bit": 999, "category": category},
                    timeout=20
                )
                calc_response.raise_for_status()
                data = calc_response.json()

                entry = {
                    'id': data.get('id') or data.get('calculation_id'),
                    'calculation_id': data.get('calculation_id'),
                    'timestamp': data.get('timestamp'),
                    'type': data.get('type', 'text'),
                    'input': data.get('input', item),
                    'unicode': data.get('unicode') or unicode_array,
                    'bit': data.get('bit', 999),
                    'view_count': data.get('view_count', 0),
                    'results': data.get('results') or [],
                    'saved': data.get('saved', False)
                }

                if not entry['results']:
                    entry['results'] = [{
                        'nb_max': data.get('nb_max'),
                        'nb_min': data.get('nb_min'),
                        'difference': None
                    }]

                results.append(entry)
                self.add_detail_log('calc', f"새 계산 저장: {entry.get('id')}")
            except Exception as e:
                log_debug(f"[저장 오류] N/B 계산 실패: {e}")
                self.add_detail_log('calc', f"실패: {item}")
                results.append({
                    'id': None,
                    'calculation_id': None,
                    'timestamp': None,
                    'type': 'text',
                    'input': item,
                    'unicode': None,
                    'bit': None,
                    'view_count': 0,
                    'results': [],
                    'saved': False
                })

        return results

    def upload_data_only(self, root_dir: str):
        if not AUTO_UPLOAD_DATA:
            self.notify_system("⏭️ 데이터 업로드 생략됨")
            return

        script_path = os.path.join(root_dir, 'sync_data_only.bat')
        if not os.path.exists(script_path):
            self.notify_system("⚠️ 데이터 업로드 스크립트 없음")
            return

        self.notify_system_detail("📤 데이터 업로드 시작...", "upload")
        try:
            result = subprocess.run(
                ['cmd', '/c', script_path],
                capture_output=True,
                text=True,
                check=False
            )
            if result.stdout:
                self.add_detail_log('upload', result.stdout.strip())
            if result.stderr:
                self.add_detail_log('upload', result.stderr.strip())
            if result.returncode == 0:
                self.notify_system("✅ 데이터 업로드 완료")
            else:
                self.notify_system("❌ 데이터 업로드 실패")
                if result.stderr:
                    log_debug(result.stderr.strip())
        except Exception as e:
            self.notify_system("❌ 데이터 업로드 오류")
            log_debug(f"[업로드 오류] {e}")
    
    def setup_ui(self):
        """UI 구성"""
        # 스크롤바 스타일 설정
        style = ttk.Style()
        style.theme_use('clam')
        
        # 세로 스크롤바 스타일
        style.configure("Vertical.TScrollbar",
                       background="#334155",
                       darkcolor="#1e293b",
                       lightcolor="#475569",
                       troughcolor="#1e293b",
                       bordercolor="#1e293b",
                       arrowcolor="#94a3b8")
        
        style.map("Vertical.TScrollbar",
                 background=[('active', '#475569'), ('!active', '#334155')])
        
        # 메인 컨테이너
        main_container = tk.Frame(self.root, bg="#0f172a")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 왼쪽 사이드바 (대화 히스토리)
        sidebar = tk.Frame(main_container, bg="#1e293b", width=280)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # 사이드바 헤더
        sidebar_header = tk.Frame(sidebar, bg="#334155", height=50)
        sidebar_header.pack(fill=tk.X)
        sidebar_header.pack_propagate(False)
        
        tk.Label(
            sidebar_header,
            text="💬 대화 기록",
            bg="#334155",
            fg="#22c55e",
            font=("Arial", 12, "bold")
        ).pack(pady=15)
        
        # 대화 목록
        history_frame = tk.Frame(sidebar, bg="#1e293b")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.history_listbox = tk.Listbox(
            history_frame,
            bg="#1e293b",
            fg="#e2e8f0",
            font=("Arial", 9),
            relief=tk.FLAT,
            selectbackground="#334155",
            selectforeground="#22c55e",
            activestyle="none",
            highlightthickness=0,
            borderwidth=0
        )
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.history_listbox.bind("<<ListboxSelect>>", self.on_history_select)
        
        scrollbar = ttk.Scrollbar(
            history_frame,
            command=self.history_listbox.yview,
            style="Vertical.TScrollbar"
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_listbox.config(yscrollcommand=scrollbar.set)
        
        # 오른쪽 채팅 영역
        chat_container = tk.Frame(main_container, bg="#0f172a")
        chat_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 상단 바
        top_frame = tk.Frame(chat_container, bg="#1e293b")
        top_frame.pack(fill=tk.X, padx=0, pady=0)
        
        # 제목이 있는 상단 첫 번째 줄
        title_frame = tk.Frame(top_frame, bg="#1e293b", height=50)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="🤖 Ollama IDE", 
            bg="#1e293b", 
            fg="#22c55e",
            font=("Arial", 16, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # 모델 선택 (제목과 같은 줄)
        model_frame = tk.Frame(title_frame, bg="#1e293b")
        model_frame.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # 카테고리 선택 프레임 (두 번째 줄)
        category_frame = tk.Frame(top_frame, bg="#1e293b", height=45)
        category_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        category_frame.pack_propagate(False)
        
        tk.Label(
            category_frame,
            text="카테고리:",
            bg="#1e293b",
            fg="#94a3b8",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.category_var = tk.StringVar(value="all")
        categories = [
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
        ]
        
        for label, value in categories:
            btn_color = "#22c55e" if value == "all" else "#334155"
            btn_fg = "#000" if value == "all" else "#e2e8f0"
            tk.Radiobutton(
                category_frame,
                text=label,
                variable=self.category_var,
                value=value,
                bg="#1e293b",
                fg=btn_fg,
                selectcolor="#22c55e",
                font=("Arial", 9),
                relief=tk.FLAT,
                cursor="hand2",
                padx=8,
                pady=4,
                bd=0
            ).pack(side=tk.LEFT, padx=2)
        
        tk.Label(
            model_frame, 
            text="모델:", 
            bg="#1e293b", 
            fg="#e2e8f0",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.model_var,
            state="readonly",
            width=20,
            font=("Arial", 10)
        )
        self.model_combo.pack(side=tk.LEFT, padx=5)
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_change)
        
        # 새 대화 버튼
        new_chat_btn = tk.Button(
            model_frame,
            text="+ 새 대화",
            bg="#22c55e",
            fg="#000",
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.new_chat
        )
        new_chat_btn.pack(side=tk.LEFT, padx=10)
        
        # 채팅 영역
        chat_frame = tk.Frame(chat_container, bg="#0f172a")
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 채팅 디스플레이 (Text + 커스텀 스크롤바)
        self.chat_display = tk.Text(
            chat_frame,
            bg="#1e293b",
            fg="#e2e8f0",
            font=("Arial", 11),
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=15,
            pady=15,
            insertbackground="#22c55e",
            borderwidth=0,
            highlightthickness=0
        )
        self.chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 커스텀 스크롤바
        chat_scrollbar = ttk.Scrollbar(
            chat_frame,
            command=self.chat_display.yview,
            style="Vertical.TScrollbar"
        )
        chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_display.config(yscrollcommand=chat_scrollbar.set)
        self.chat_display.config(state=tk.DISABLED)
        
        # 태그 설정
        self.chat_display.tag_config("user", foreground="#3b82f6", font=("Arial", 11, "bold"))
        self.chat_display.tag_config("assistant", foreground="#22c55e", font=("Arial", 11, "bold"))
        self.chat_display.tag_config("user_msg", foreground="#e2e8f0")
        self.chat_display.tag_config("assistant_msg", foreground="#e2e8f0")
        self.chat_display.tag_config("system", foreground="#64748b", font=("Arial", 10, "italic"))
        self.chat_display.tag_config("system_detail", foreground="#38bdf8", font=("Arial", 10, "underline"))
        
        # 즐겨찾기 명령어 버튼 영역 (스크롤 + 저장 버튼)
        favorites_frame = tk.Frame(chat_container, bg="#1e293b", height=80)
        favorites_frame.pack(fill=tk.X, padx=20, pady=(10, 5))
        favorites_frame.pack_propagate(False)  # 높이 고정
        
        # 위쪽: 레이블 영역
        label_frame = tk.Frame(favorites_frame, bg="#1e293b")
        label_frame.pack(fill=tk.X, padx=5, pady=(5, 2))
        
        tk.Label(
            label_frame,
            text="⭐ 즐겨찾기 명령어",
            bg="#1e293b",
            fg="#22c55e",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        # 아래쪽: Canvas + 저장 버튼 영역
        button_area = tk.Frame(favorites_frame, bg="#1e293b")
        button_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=(2, 5))
        
        # 즐겨찾기 추가 버튼 (좌측 끝)
        add_fav_btn = tk.Button(
            button_area,
            text="➕ 저장",
            bg="#22c55e",
            fg="#000",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.add_favorite
        )
        add_fav_btn.pack(side=tk.LEFT, padx=(0, 5), pady=5)
        
        # Canvas 기반 스크롤 가능 버튼 영역
        self.favorites_canvas = tk.Canvas(
            button_area,
            bg="#1e293b",
            highlightthickness=0,
            height=50
        )
        favorites_scrollbar = tk.Scrollbar(
            button_area,
            orient=tk.HORIZONTAL,
            command=self.favorites_canvas.xview
        )
        self.favorites_canvas.config(xscrollcommand=favorites_scrollbar.set)
        
        self.favorites_buttons_frame = tk.Frame(self.favorites_canvas, bg="#1e293b")
        self.favorites_canvas.create_window((0, 0), window=self.favorites_buttons_frame, anchor="nw")
        
        self.favorites_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        favorites_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 마우스 휠 스크롤 바인딩
        self.favorites_canvas.bind("<MouseWheel>", self._on_favorites_mousewheel)
        self.favorites_canvas.bind("<Button-4>", self._on_favorites_mousewheel)  # Linux scroll up
        self.favorites_canvas.bind("<Button-5>", self._on_favorites_mousewheel)  # Linux scroll down
        
        # 좌우 마우스 클릭 스크롤
        self.favorites_canvas.bind("<Button-1>", self._on_favorites_click)  # 좌클릭
        self.favorites_canvas.bind("<Button-3>", self._on_favorites_click)  # 우클릭
        
        # 입력 영역
        input_frame = tk.Frame(chat_container, bg="#0f172a")
        input_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # 입력 박스
        self.input_text = tk.Text(
            input_frame,
            bg="#1e293b",
            fg="#e2e8f0",
            font=("Arial", 11),
            height=3,
            relief=tk.FLAT,
            padx=10,
            pady=10,
            insertbackground="#22c55e"
        )
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        self.input_text.bind("<Return>", self.on_enter_key)
        self.input_text.bind("<Shift-Return>", lambda e: None)
        
        # 전송 버튼
        self.send_btn = tk.Button(
            input_frame,
            text="전송",
            bg="#22c55e",
            fg="#000",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            width=10,
            cursor="hand2",
            command=self.send_message
        )
        self.send_btn.pack(side=tk.RIGHT)
        
        # 초기 메시지
        welcome_msg = """안녕하세요! AI 어시스턴트입니다 👋

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

📊 보고서 일괄 검색 (NEW 🆕):
    • /보고서검색반복 [간격초] - YouTube 보고서 키워드를 /검색으로 순서 실행
    • /보고서검색반복 [간격초] --infinite - 보고서 검색 반복 (무한 반복)
    • /보고서검색반복 [간격초] --bg - 페이지를 백그라운드로 열기

⭐ 즐겨찾기:
    • 입력 후 [➕ 현재 입력 저장] 버튼 클릭하여 저장
    • 버튼 클릭으로 빠른 입력
    • 우클릭으로 삭제

💬 일반 AI 채팅도 가능합니다!"""
        
        self.display_message("system", welcome_msg)
    
    def load_history_list(self):
        """대화 히스토리 목록 로드"""
        self.history_listbox.delete(0, tk.END)
        
        # 모든 대화 파일 찾기
        chat_files = sorted(
            glob.glob(os.path.join(HISTORY_DIR, "chat_*.json")),
            key=os.path.getmtime,
            reverse=True
        )
        
        for filepath in chat_files[:50]:  # 최근 50개만
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 파일명에서 날짜 추출
                filename = os.path.basename(filepath)
                date_str = filename.replace("chat_", "").replace(".json", "")
                
                # 날짜 포맷팅
                try:
                    dt = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                    date_display = dt.strftime("%m/%d %H:%M")
                except:
                    date_display = date_str[:10]
                
                # 첫 메시지 요약
                messages = data.get('messages', [])
                first_msg = ""
                for msg in messages:
                    if msg.get('role') == 'user':
                        content = msg.get('content', '')
                        first_msg = content[:30] + "..." if len(content) > 30 else content
                        break
                
                if not first_msg:
                    first_msg = "빈 대화"
                
                # 메시지 수
                msg_count = len(messages)
                model = data.get('model', 'N/A')
                
                # 표시 텍스트
                display_text = f"📅 {date_display}\n💬 {first_msg}\n📊 {msg_count}개 | {model[:15]}"
                
                self.history_listbox.insert(tk.END, display_text)
                # 파일 경로를 숨겨진 데이터로 저장
                self.history_listbox.itemconfig(tk.END, {'fg': '#e2e8f0'})
                
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
        
        # 파일 경로 매핑 저장
        self.chat_files = chat_files[:50]
    
    def on_history_select(self, event):
        """대화 선택 시"""
        selection = self.history_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < len(self.chat_files):
            self.load_chat_from_file(self.chat_files[index])
    
    def load_chat_from_file(self, filepath):
        """파일에서 대화 불러오기"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 현재 대화 초기화
            self.chat_history = data.get('messages', [])
            self.current_model = data.get('model', self.current_model)
            self.current_chat_file = filepath
            
            # 모델 선택 업데이트
            if self.current_model in self.model_combo['values']:
                self.model_var.set(self.current_model)
            
            # 채팅 화면 업데이트
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state=tk.DISABLED)
            
            # 메시지 표시
            for msg in self.chat_history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                self.display_message(role, content)
            
            self.display_message("system", f"💾 대화 불러옴: {os.path.basename(filepath)}")
            
        except Exception as e:
            messagebox.showerror("오류", f"대화를 불러올 수 없습니다.\n{e}")
    
    def load_models(self):
        """모델 로드"""
        try:
            response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            models = [m['name'] for m in data.get('models', [])]
            
            if models:
                self.model_combo['values'] = models
                self.model_rotation = self._load_model_rotation(models, preferred_model=models[0])
                current = self._get_rotation_model() or models[0]
                self.model_combo.current(models.index(current) if current in models else 0)
                self._set_current_model(current)
                self.display_message("system", f"✅ 모델 로드 완료: {self.current_model}")
            else:
                messagebox.showerror("오류", "사용 가능한 모델이 없습니다.")
        except Exception as e:
            messagebox.showerror("연결 오류", f"Ollama에 연결할 수 없습니다.\n{e}")

    def _load_model_rotation(self, models, preferred_model=None):
        state = {"models": models, "index": 0}
        if os.path.exists(ROTATION_FILE):
            try:
                with open(ROTATION_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                saved_models = saved.get("models", [])
                saved_index = int(saved.get("index", 0))
                if saved_models == models and 0 <= saved_index < len(models):
                    state = {"models": models, "index": saved_index}
            except Exception:
                pass

        if preferred_model in models:
            state["index"] = models.index(preferred_model)

        self._save_model_rotation(state)
        return state

    def _save_model_rotation(self, state=None):
        target = state if state is not None else self.model_rotation
        if not target:
            return
        try:
            with open(ROTATION_FILE, 'w', encoding='utf-8') as f:
                json.dump(target, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _get_rotation_model(self):
        if not self.model_rotation or not self.model_rotation.get("models"):
            return self.current_model
        models = self.model_rotation["models"]
        index = int(self.model_rotation.get("index", 0))
        if index >= len(models):
            index = 0
        return models[index]

    def _set_current_model(self, model, notify=False):
        if not model:
            return
        self.current_model = model
        if hasattr(self, 'model_var'):
            self.model_var.set(model)
        if self.model_rotation and model in self.model_rotation.get("models", []):
            self.model_rotation["index"] = self.model_rotation["models"].index(model)
            self._save_model_rotation()
        if notify:
            self.display_message("system", f"🔁 모델 전환: {model}")

    def _advance_model_rotation(self):
        if not self.model_rotation or not self.model_rotation.get("models"):
            return None
        models = self.model_rotation["models"]
        self.model_rotation["index"] = (int(self.model_rotation.get("index", 0)) + 1) % len(models)
        self._save_model_rotation()
        return models[self.model_rotation["index"]]

    def _ollama_generate(self, prompt, timeout=120, options=None):
        models = []
        if self.model_rotation and self.model_rotation.get("models"):
            models = self.model_rotation["models"]
        if not models:
            models = [self.current_model] if self.current_model else []

        if not models:
            raise RuntimeError("사용 가능한 모델이 없습니다.")

        base_delay = 1.5
        try:
            start_index = models.index(self.current_model)
        except ValueError:
            start_index = int(self.model_rotation.get("index", 0)) if self.model_rotation else 0

        last_error = None

        for attempt in range(len(models)):
            model = models[start_index]
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            if options:
                payload["options"] = options

            try:
                response = requests.post(
                    f"{OLLAMA_URL}/api/generate",
                    json=payload,
                    timeout=timeout
                )
                if response.status_code in (429, 500, 502, 503, 504):
                    raise requests.HTTPError(
                        f"{response.status_code} {response.reason}",
                        response=response
                    )
                response.raise_for_status()
                data = response.json()
                if model != self.current_model:
                    self._set_current_model(model, notify=True)
                else:
                    self._set_current_model(model)
                return data
            except requests.HTTPError as e:
                status = e.response.status_code if e.response else None
                if status in (429, 500, 502, 503, 504):
                    last_error = str(e)
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                    log_debug(f"[Ollama 전환] 상태 {status}, {delay:.1f}s 대기")
                    time.sleep(delay)
                    next_model = self._advance_model_rotation()
                    if next_model:
                        log_debug(f"[Ollama 전환] {model} -> {next_model}")
                        start_index = models.index(next_model)
                        continue
                raise

        raise RuntimeError(last_error or "모든 모델에서 429가 발생했습니다.")
    
    def load_ai_guidelines(self):
        """AI 행동 지침 로드"""
        try:
            guideline_path = os.path.join(os.path.dirname(__file__), "AI_GUIDELINES.md")
            if os.path.exists(guideline_path):
                with open(guideline_path, 'r', encoding='utf-8') as f:
                    guidelines = f.read()
                    log_debug("[시스템] AI_GUIDELINES.md 로드 완료")
                    return guidelines
        except Exception as e:
            log_debug(f"[경고] AI 지침 로드 실패: {e}")
        return None
    
    def get_system_prompt(self):
        """시스템 프롬프트 생성 (AI 지침 포함)"""
        now = datetime.now()
        today = now.strftime("%Y년 %m월 %d일")
        current_time = now.strftime("%H:%M")
        current_month = now.month
        current_day = now.day
        
        system_prompt = f"""당신은 한국인을 위한 지능형 AI 어시스턴트입니다.

**현재 시각: {today} {current_time}**
**현재 날짜: {current_month}월 {current_day}일**

## ⚠️ 반드시 준수해야 할 핵심 규칙

### 1. 뉴스/정보 필터링 (가장 중요!)
✓ 반드시 포함:
  - 오늘 또는 최근(7일 이내)의 새로운 발표, 업데이트, 사건
  - 구체적인 수치나 실적이 포함된 최신 정보
  - 날짜가 명시된 최신 뉴스
  - 진행 중이거나 앞으로 진행될 이벤트
    - **하나의 종합적인 문장으로 통합**

✗ 반드시 제외 (저장 금지):
  - 일반적인 설명이나 소개 ("~는 ~입니다", "~에서 찾을 수 있습니다")
  - 블로그/갤러리/커뮤니티 링크나 포스팅 소개
  - 시스템 요구사항, 회원가입 안내 등 기본 정보
  - 단순한 사실 나열 (뉴스성 없는 내용)  
  - "Tistory에 있음", "DC Inside에서 찾을 수 있음" 같은 링크 정보
  - 과거 날짜 (작년, 지난해, 2025년, 2024년 등)
  - **이미 종료된 이벤트 (예: 설날이 지났으면 설날 이벤트, 크리스마스가 지났으면 크리스마스 이벤트 제외)**
    → 현재 날짜({current_month}월 {current_day}일) 기준으로 판단
  - **여러 항목으로 나열된 내용 (하나의 종합 문장만 허용)**

### 2. 카테고리별 타임라인 규칙
- **정치, 경제:** 무조건 오늘({today}) 뉴스만
- **사회, 문화, 게임, 드라마, 영화, 애니메이션, 스포츠:** 최근 1주일 내 뉴스
- **괴물딴지, 미스테리:** 과거 데이터 허용 (단, 매우 오래된 것 제외)
- **기술:** 과거 데이터 허용

### 3. 응답 언어 규칙
✓ **반드시 한글로만 응답** - 모든 요약, 필터링, 분석은 한글로 작성
✓ 카테고리 생성도 한글 단어로만 (예: 정치, 게임, 문화)

### 4. 정보 정확성
- 확실하지 않은 정보는 "제 정보가 제한적입니다"라고 명시
- 최신 정보가 필요한 경우 검색 결과 우선
- 출처를 명확히 표시

### 5. 절대 금지 사항
✗ 북한 선전 매체(조선중앙통신, 조선신보 등) 절대 인용 금지
✗ 북한 정치 성향 기사, 북한 지도자 발언/정치 선언/체제 홍보성 내용 금지
  (단, 도발 상황은 국방부/통일부 공식 발표 기반으로만 제공)
✗ 인종, 종교, 성별 차별 표현 금지
✗ 혐오 및 극단주의 선전 금지
✗ 개인정보 공개 절대 금지
✗ 불법 활동 상세 방법 제시 금지
✗ 과도한 이모지 (최대 1-2개만 사용)

### 6. 신뢰 가능한 출처만 인용
✓ 국방부, 통일부 공식 발표
✓ BBC, AFP, AP, Reuters 등 국제 통신사
✓ 연합뉴스, 한겨레, 조선일보 등 국내 주류 언론
✓ 공식 정부/기업 발표

✗ 개인 블로그의 주관적 의견
✗ 광고성 콘텐츠
✗ 미확인 출처
✗ 날짜 없는 정보

### 7. 응답 형식
- 간결하게 200자 이내로 작성 (뉴스 제외)
- 과도한 특수문자 제거
- 명확하고 직접적인 표현 사용
- 필요시 출처와 날짜 명시

이 규칙들은 **모든 응답에서 반드시 지켜야 합니다.**"""
        
        return system_prompt

    def is_disallowed_nk_political_content(self, text: str) -> bool:
        if not text:
            return False

        has_nk = ('북한' in text) or ('김정은' in text) or ('조선' in text)
        if not has_nk:
            return False

        urgent_markers = (
            '미사일', '핵', '핵실험', '도발', '발사', '군사', '포격', '경보', '위협', '긴급'
        )
        if any(marker in text for marker in urgent_markers):
            return False

        political_markers = (
            '선언', '담화', '연설', '정책', '국방력', '자력갱생', '체제', '지도자', '위원장'
        )
        return any(marker in text for marker in political_markers) or has_nk
    
    def load_favorites(self):
        """즐겨찾기 로드"""
        try:
            if os.path.exists(self.favorites_file):
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    self.favorites = json.load(f)
            else:
                # 기본 즐겨찾기
                self.favorites = [
                    "/트렌드검색반복 60",
                    "/반복 1 0 오늘 주요 뉴스",
                    "오늘 주요 뉴스",
                    "/뉴스",
                    "/도움말"
                ]
                self.save_favorites()
            
            self.update_favorites_buttons()
        except Exception as e:
            log_debug(f"[즐겨찾기 로드 오류] {e}")
            self.favorites = []
    
    def save_favorites(self):
        """즐겨찾기 저장"""
        try:
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_debug(f"[즐겨찾기 저장 오류] {e}")
    
    def update_favorites_buttons(self):
        """즐겨찾기 버튼 업데이트 (스크롤 지원)"""
        # 기존 버튼 제거
        for widget in self.favorites_buttons_frame.winfo_children():
            widget.destroy()
        
        if not self.favorites:
            tk.Label(
                self.favorites_buttons_frame,
                text="[⭐ 입력 후 저장 버튼을 클릭해서 즐겨찾기 추가]",
                bg="#1e293b",
                fg="#64748b",
                font=("Arial", 9, "italic")
            ).pack(side=tk.LEFT, padx=5)
        else:
            # 버튼 생성 (모든 즐겨찾기)
            for idx, fav in enumerate(self.favorites):
                # 명령어 여부에 따른 색상 분기
                if fav.startswith('/'):
                    btn_bg = "#3b82f6"  # 파란색 (명령어)
                    btn_fg = "#fff"
                else:
                    btn_bg = "#06b6d4"  # 청록색 (일반 텍스트)
                    btn_fg = "#000"
                
                btn = tk.Button(
                    self.favorites_buttons_frame,
                    text=fav[:25] + "..." if len(fav) > 25 else fav,
                    bg=btn_bg,
                    fg=btn_fg,
                    font=("Arial", 9, "bold"),
                    relief=tk.FLAT,
                    padx=10,
                    pady=4,
                    cursor="hand2",
                    command=lambda f=fav: self.use_favorite(f),
                    activebackground="#0ea5e9" if btn_bg == "#3b82f6" else "#14b8a6",
                    activeforeground="#fff"
                )
                btn.pack(side=tk.LEFT, padx=3, pady=2)
                
                # 우클릭으로 삭제 (Tooltip)
                btn.bind("<Button-3>", lambda e, f=fav: self.remove_favorite(f))
                btn.bind("<Enter>", lambda e, f=fav: self.show_favorite_tooltip(e, f))
        
        # Canvas 스크롤 영역 업데이트
        self.favorites_buttons_frame.update_idletasks()
        self.favorites_canvas.config(scrollregion=self.favorites_canvas.bbox("all"))
    
    def show_favorite_tooltip(self, event, text):
        """즐겨찾기 버튼 호버시 전체 텍스트 표시"""
        if len(text) > 25:
            event.widget.config(text=f"{text}")
    
    def use_favorite(self, text):
        """즐겨찾기 사용"""
        self.input_text.delete(1.0, tk.END)
        self.input_text.insert(1.0, text)
        self.input_text.focus()

    
    def add_favorite(self):
        """즐겨찾기 추가"""
        current_text = self.input_text.get(1.0, tk.END).strip()
        
        if not current_text:
            messagebox.showwarning("입력 필요", "입력창에 저장할 명령어를 입력하세요.")
            return
        
        if current_text in self.favorites:
            messagebox.showinfo("알림", "이미 즐겨찾기에 있습니다.")
            return
        
        self.favorites.insert(0, current_text)
        if len(self.favorites) > 10:
            self.favorites = self.favorites[:10]
        
        self.save_favorites()
        self.update_favorites_buttons()
        self.display_message("system", f"⭐ 즐겨찾기 추가: {current_text[:50]}")
    
    def remove_favorite(self, text):
        """즐겨찾기 제거"""
        if messagebox.askyesno("삭제 확인", f"'{text[:50]}'을(를) 즐겨찾기에서 제거하시겠습니까?"):
            if text in self.favorites:
                self.favorites.remove(text)
                self.save_favorites()
                self.update_favorites_buttons()
                self.display_message("system", f"❌ 즐겨찾기 제거: {text[:50]}")
    
    def _on_favorites_mousewheel(self, event):
        """즐겨찾기 Canvas 마우스 휠 스크롤"""
        if event.num == 5 or event.delta < 0:
            self.favorites_canvas.xview_scroll(3, "units")
        else:
            self.favorites_canvas.xview_scroll(-3, "units")
    
    def _on_favorites_click(self, event):
        """즐겨찾기 Canvas 좌우 마우스 클릭 스크롤"""
        if event.num == 1:  # 좌클릭 = 좌로 스크롤
            self.favorites_canvas.xview_scroll(-5, "units")
        elif event.num == 3:  # 우클릭 = 우로 스크롤
            self.favorites_canvas.xview_scroll(5, "units")
    
    def on_model_change(self, event):
        """모델 변경"""
        self.current_model = self.model_var.get()
        self.display_message("system", f"모델 변경: {self.current_model}")
    
    def new_chat(self):
        """새 대화 시작"""
        if self.chat_history:
            if messagebox.askyesno("확인", "현재 대화를 저장하시겠습니까?"):
                self.save_chat()
        
        self.chat_history = []
        self.current_chat_file = None
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.display_message("system", "새 대화를 시작합니다. 👋")
    
    def display_message(self, role, content):
        """메시지 표시"""
        self.chat_display.config(state=tk.NORMAL)
        
        if role == "user":
            self.chat_display.insert(tk.END, "\n👤 You:\n", "user")
            self.chat_display.insert(tk.END, f"{content}\n", "user_msg")
        elif role == "assistant":
            self.chat_display.insert(tk.END, "\n🤖 AI:\n", "assistant")
            self.chat_display.insert(tk.END, f"{content}\n", "assistant_msg")
        elif role == "system":
            self.chat_display.insert(tk.END, f"\n{content}\n", "system")
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def display_system_detail(self, message: str, detail_key: str):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"\n{message} ", "system")

        tag_name = f"system_detail_{self.detail_tag_count}"
        self.detail_tag_count += 1
        self.detail_tag_map[tag_name] = detail_key

        self.chat_display.insert(tk.END, "[자세히]", ("system_detail", tag_name))
        self.chat_display.insert(tk.END, "\n")

        def handler(event, tag=tag_name):
            key = self.detail_tag_map.get(tag)
            if key:
                self.show_detail_log(key)

        self.chat_display.tag_bind(tag_name, "<Button-1>", handler)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def on_enter_key(self, event):
        """Enter 키 처리"""
        if not event.state & 0x1:  # Shift가 눌리지 않은 경우
            self.send_message()
            return "break"
    
    def send_message(self):
        """메시지 전송"""
        message = self.input_text.get(1.0, tk.END).strip()
        if not message or self.is_generating:
            return
        
        if not self.current_model:
            messagebox.showwarning("경고", "모델을 선택해주세요.")
            return
        
        # 입력 초기화
        self.input_text.delete(1.0, tk.END)
        
        self.process_user_message(message)

    @staticmethod
    def normalize_user_message(message: str) -> str:
        """사용자 입력 정규화 (보이지 않는 문자/슬래시 변형 보정)"""
        if not isinstance(message, str):
            return ""

        normalized = message.replace('\ufeff', '').replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
        normalized = normalized.replace('／', '/').replace('⁄', '/').replace('∕', '/')
        normalized = normalized.strip()
        return normalized

    def process_user_message(self, message: str, force_search: bool = False) -> bool:
        """사용자 메시지를 처리하고 응답 생성까지 수행"""
        message = self.normalize_user_message(message)
        if not message or self.is_generating:
            return False

        if not self.current_model:
            messagebox.showwarning("경고", "모델을 선택해주세요.")
            return False

        # 사용자 메시지 표시
        self.display_message("user", message)
        self.chat_history.append({"role": "user", "content": message})

        # 보고서 검색 명령어 처리 (트렌드보다 먼저 검사)
        log_debug(f"[Command Check] Processing: {repr(message)}")
        log_debug(f"[Command Check] Starts with '/보고서검색반복': {message.startswith('/보고서검색반복')}")
        if self.handle_report_batch_command(message):
            log_debug(f"[Command Check] ✅ Report batch command matched")
            return True
        log_debug(f"[Command Check] Report batch command not matched")

        # 반복 명령어 처리
        log_debug(f"[Command Check] About to check trend batch...")
        if self.handle_trend_batch_command(message):
            log_debug(f"[Command Check] ✅ Trend batch command matched")
            return True
        log_debug(f"[Command Check] Trend batch command not matched")

        log_debug(f"[Command Check] About to check repeat command...")
        if self.handle_repeat_command(message):
            log_debug(f"[Command Check] ✅ Repeat command matched")
            return True
        log_debug(f"[Command Check] Repeat command not matched")

        # 수동 검색 명령어 처리
        log_debug(f"[Command Check] About to check manual search command...")
        if message.startswith('/검색 ') or message.startswith('/네이버 ') or message.startswith('/빙 ') or message.startswith('/뉴스 ') or message.startswith('/유튜브 '):
            log_debug(f"[Command Check] ✅ Manual search command matched")
            self.handle_search_command(message)
            return True

        # 버튼 비활성화
        self.is_generating = True
        self.send_btn.config(state=tk.DISABLED, text="🤖 생성 중...")

        # AI 응답 생성 (자동 검색 포함)
        Thread(target=self.generate_response_with_auto_search, args=(message, force_search), daemon=True).start()
        return True

    def handle_repeat_command(self, message: str) -> bool:
        """반복 실행 명령 처리"""
        if message in ('/반복중지', '/중지', '/stop'):
            self.stop_repeat()
            self.stop_batch()
            return True

        match = re.match(r'^/(?:반복|repeat)\s+(\d+)(?:\s+(\d+(?:\.\d+)?))?\s+(.+)$', message)
        if not match:
            return False

        count = int(match.group(1))
        interval = float(match.group(2)) if match.group(2) else 2.0
        prompt = match.group(3).strip()

        if count < 0:
            self.display_message("system", "반복 횟수는 0 이상이어야 합니다.")
            return True
        if count > 50:
            self.display_message("system", "반복 횟수는 최대 50회까지 가능합니다.")
            return True
        if interval < 0:
            self.display_message("system", "간격은 0 이상이어야 합니다.")
            return True
        if 0 < interval < 0.5:
            self.display_message("system", "간격은 0.5초 이상이거나 0이어야 합니다.")
            return True
        if not prompt:
            self.display_message("system", "반복할 질문을 입력해주세요.")
            return True

        if count == 0:
            count = -1

        self.start_repeat(prompt, count, interval, force_search=(interval == 0))
        return True

    def handle_trend_batch_command(self, message: str) -> bool:
        """트렌드 키워드 일괄 실행 명령 처리"""
        match = re.match(r'^/(?:트렌드반복|trend-batch)(?:\s+(\d+(?:\.\d+)?))?(?:\s+(--infinite|-무한))?(?:\s+(--bg|--background))?\s*$', message)
        if not match:
            match = re.match(r'^/(?:트렌드검색반복|trend-batch-search)(?:\s+(\d+(?:\.\d+)?))?(?:\s+(--infinite|-무한))?(?:\s+(--bg|--background))?(?:\s*\[(.+)\])?\s*$', message)
            if not match:
                return False

        interval = float(match.group(1)) if match.group(1) else 2.0
        if interval < 0.5:
            self.display_message("system", "간격은 0.5초 이상이어야 합니다.")
            return True

        # 무한 반복 옵션 확인
        infinite_mode = bool(match.group(2)) if match.lastindex >= 2 else False
        background_mode = bool(match.group(3)) if match.lastindex >= 3 else False
        # 키워드 추출 (트렌드검색반복의 경우 그룹 3)
        extra_raw = None
        if '/트렌드검색반복' in message or '/trend-batch-search' in message:
            extra_raw = match.group(4) if match.lastindex >= 4 else None
        else:
            extra_raw = match.group(2) if match.lastindex >= 2 and not match.group(2) else None

        keywords = self.load_trend_keywords_from_file()
        if not keywords:
            self.display_message("system", "트렌드 키워드를 찾을 수 없습니다.")
            return True

        extra_keywords = self.parse_extra_keywords(extra_raw)
        if extra_keywords:
            keywords.extend(extra_keywords)

        self.stop_repeat()
        self.stop_batch()
        self.batch_open_background = background_mode
        search_mode = message.startswith('/트렌드검색반복') or message.startswith('/trend-batch-search')
        self.start_batch(keywords, interval, search_mode, infinite_loop=infinite_mode)
        return True

    def handle_report_batch_command(self, message: str) -> bool:
        """보고서 키워드 일괄 실행 명령 처리"""
        # 명령어 전체 매칭
        if not (message.startswith('/보고서검색반복') or message.startswith('/report-batch-search')):
            log_debug(f"[Report Command] Not a report command: {repr(message[:50])}")
            return False
        
        log_debug(f"[Report Command] ✅ Report command detected: {repr(message)}")
        # 기본값 설정
        interval = 2.0
        infinite_mode = False
        background_mode = False
        
        # 나머지 부분 파싱
        rest = None
        if message.startswith('/보고서검색반복'):
            rest = message[len('/보고서검색반복'):].strip()
        else:
            rest = message[len('/report-batch-search'):].strip()
        
        # 파라미터 추출
        if rest:
            parts = rest.split()
            for idx, part in enumerate(parts):
                if part in ('--infinite', '-무한'):
                    infinite_mode = True
                elif part in ('--bg', '--background'):
                    background_mode = True
                elif part and part[0].isdigit():
                    try:
                        interval = float(part)
                        if interval < 0.5 and interval != 0:
                            self.display_message("system", "간격은 0.5초 이상이거나 0이어야 합니다.")
                            return True
                    except ValueError:
                        pass

        # Step 1: 보고서 로드 메시지
        self.display_message("system", "📄 [Step 1/4] 최신 YouTube 보고서 로드 중...")
        self.display_message("system", "   • reports 폴더에서 가장 최신 보고서 파일 자동 선택")
        
        # Step 2: Ollama AI가 보고서를 분석해서 질문형 문장 1개 생성
        self.display_message("system", "🤖 [Step 2/4] Ollama AI가 보고서 분석 중...")
        self.display_message("system", f"   • 모델: {self.current_model}")
        self.display_message("system", "   • 보고서 내용을 모델에 전달하여 핵심 이슈 분석 중...")
        self.display_message("system", f"   • 이미 검색한 질문: {len(self.searched_keywords)}개")
        question = self.generate_question_from_report(self.current_model)
        
        if not question:
            self.display_message("system", "❌ 보고서 분석 실패. 기본 검색 질문을 사용합니다.")
            # 오늘 날짜를 반영한 기본 질문
            today_str = datetime.now().strftime("%Y년 %m월 %d일")
            question = f"오늘({today_str}) 주요 뉴스는 무엇인가?"
            log_debug(f"[보고서 분석] 기본 질문 사용: {question}")
        
        # ✅ 생성된 질문을 검색 이력에 추가 (중복 방지용)
        if question not in self.searched_keywords:
            self.searched_keywords.append(question)
            
            # 30개 초과 시 초기화
            if len(self.searched_keywords) > 30:
                log_debug(f"[보고서 분석] 검색 이력 초기화: {len(self.searched_keywords)}개 → 리셋")
                self.display_message("system", f"📊 검색 이력 초기화: {len(self.searched_keywords)}개 질문 이후 리셋됨")
                self.searched_keywords = [question]  # 현재 질문만 유지
        
        self.display_message("system", f"✅ [Step 2/4] 검색 질문 생성 완료 (총 {len(self.searched_keywords)}개):")
        self.display_message("system", f"   💬 {question}")

        # Step 3: 배치 모드 준비
        self.display_message("system", f"⚙️ [Step 3/4] 배치 검색 준비 중...")
        self.display_message("system", "   • 기존 반복/배치 작업 중단")
        
        self.stop_repeat()
        self.stop_batch()
        self.batch_open_background = background_mode
        
        self.display_message("system", f"   • 검색 간격: {interval}초")
        self.display_message("system", f"   • 무한반복: {'활성화' if infinite_mode else '비활성화'}")
        if background_mode:
            self.display_message("system", "   • 백그라운드 모드: ON")
        self.display_message("system", "   ✅ 배치 준비 완료")
        
        # Step 4: 배치 검색 시작 (질문형 문장 1개로 검색)
        self.display_message("system", f"🔍 [Step 4/4] 배치 검색 시작!")
        self.display_message("system", f"   • 생성된 검색어로 /검색 명령 자동 반복 실행")
        self.display_message("system", f"   • 지정한 간격으로 계속 검색 중...")
        # 보고서 검색은 항상 검색 모드 사용 (/반복 1 0 형태)
        self.start_batch([question], interval, search_mode=True, infinite_loop=infinite_mode)
        return True

    def generate_question_from_report(self, model: str, retry_count: int = 0) -> str:
        """최신 YouTube 보고서를 분석해서 질문형 문장 1개 생성 (재시도 지원)"""
        import requests
        
        # 경로 수정: ide/ollama_ide_gui.py -> .. -> HANKOOKINTERNET-CHAMSOSIK-main v0.0.1 -> .. -> 사이트 root
        current_dir = os.path.dirname(os.path.abspath(__file__))  # ide/
        parent_dir = os.path.dirname(current_dir)  # HANKOOKINTERNET-CHAMSOSIK-main v0.0.1/
        root_dir = os.path.dirname(parent_dir)  # 사이트 root/
        reports_dir = os.path.join(root_dir, 'youtube', 'reports')
        
        log_debug(f"[보고서 분석] 보고서 경로 조회: {reports_dir} (시도 {retry_count + 1})")
        
        # 가장 최신 날짜 폴더 찾기
        if not os.path.exists(reports_dir):
            log_debug(f"[보고서 분석] 보고서 폴더 없음: {reports_dir}")
            return None
        
        date_folders = sorted([d for d in os.listdir(reports_dir) if os.path.isdir(os.path.join(reports_dir, d))], reverse=True)
        if not date_folders:
            log_debug(f"[보고서 분석] 날짜 폴더 없음: {reports_dir}")
            return None
        
        latest_date_dir = os.path.join(reports_dir, date_folders[0])
        log_debug(f"[보고서 분석] 최신 보고서 폴더: {latest_date_dir}")
        
        # 최신 JSON 보고서 찾기 (최대 5개까지 시도)
        json_files = sorted(glob.glob(os.path.join(latest_date_dir, 'report_*.json')), reverse=True)
        if not json_files:
            log_debug(f"[보고서 분석] JSON 파일 없음: {latest_date_dir}")
            return None
        
        # 재시도 시 다른 보고서 파일 선택
        file_index = min(retry_count, len(json_files) - 1)
        selected_file = json_files[file_index]
        
        log_debug(f"[보고서 분석] 보고서 파일 로드 [{file_index + 1}/{len(json_files)}]: {selected_file}")
        
        try:
            with open(selected_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
        except Exception as e:
            log_debug(f"[보고서 분석] JSON 파일 로드 실패: {e}")
            # 재시도 (최대 3번)
            if retry_count < 3 and len(json_files) > file_index + 1:
                log_debug(f"[보고서 분석] 다음 보고서 파일로 재시도...")
                return self.generate_question_from_report(model, retry_count + 1)
            return None
        
        # 보고서 메타데이터 추출
        report_timestamp = report_data.get("timestamp", "")
        report_model = report_data.get("model", "")
        
        # 보고서 내용 정리 (상위 30개 키워드까지 보고, 이미 검색한 것 제외)
        today = datetime.now().strftime("%Y년 %m월 %d일")
        report_summary = f"📊 YouTube 트렌드 보고서 분석\n"
        report_summary += f"• 보고서 생성: {report_timestamp}\n"
        report_summary += f"• 분석 날짜: {today}\n"
        report_summary += f"• 사용 모델: {report_model}\n\n"
        report_summary += "=== 상위 트렌드 키워드 (최대 30개) ===\n\n"
        
        if isinstance(report_data, dict) and "keywords" in report_data:
            keywords_list = report_data.get("keywords", [])
            if not keywords_list:
                log_debug(f"[보고서 분석] 키워드 리스트가 비어있음")
                return None
            
            # 30개까지만 보되, 이미 검색한 키워드는 제외
            available_keywords = []
            for idx, kw_data in enumerate(keywords_list[:30]):  # 상위 30개만 검토
                if not isinstance(kw_data, dict):
                    continue
                keyword = kw_data.get("keyword", "")
                # 이전에 검색한 키워드는 제외
                if keyword and keyword not in self.searched_keywords:
                    available_keywords.append(kw_data)
                    if len(available_keywords) >= 30:  # 30개 모았으면 중단
                        break
            
            for idx, kw_data in enumerate(available_keywords[:30], 1):  # 최대 30개 표시
                if not isinstance(kw_data, dict):
                    continue
                    
                keyword = kw_data.get("keyword", "")
                views = kw_data.get("views", [])
                video_count = kw_data.get("video_count", 0)
                videos = kw_data.get("videos", [])
                
                # 조회수 통계
                total_views = sum(views) if views else 0
                avg_views = int(total_views / len(views)) if views else 0
                
                report_summary += f"{idx}. 키워드: {keyword} (영상 {video_count}개, 평균 조회 {avg_views:,})\n"
                
                # 상위 2개 영상 요약
                for vid_idx, video in enumerate(videos[:2], 1):
                    if not isinstance(video, dict):
                        continue
                    title = video.get("title", "")[:50]
                    subtitle = video.get("subtitle_summary", "")[:100]
                    report_summary += f"   영상: {title}\n"
                    if subtitle and subtitle not in ("자막 없음", "요약 생성 오류", ""):
                        report_summary += f"   요약: {subtitle}\n"
                
                report_summary += "\n"
        else:
            log_debug(f"[보고서 분석] 보고서 구조 오류 - keywords 필드 없음")
            return None
        
        # 현재 날짜 정보
        today = datetime.now().strftime("%Y년 %m월 %d일")
        
        # 이미 검색한 키워드 정보를 프롬프트에 포함
        already_searched = ""
        if self.searched_keywords:
            already_searched = f"""
=== ⚠️ 이미 검색한 질문들 (중복 피하기) ===
"""
            for i, kw in enumerate(self.searched_keywords[-10:], 1):  # 최근 10개만 표시
                already_searched += f"{i}. {kw}\n"
            already_searched += "\n👉 위 질문들과 다른 새로운 주제의 질문을 만들어주세요!\n"
        
        # Ollama AI에게 질문형 문장 생성 요청 (최신 정보 강조)
        prompt = f"""오늘은 {today}입니다. 다음 YouTube 보고서를 분석하여 가장 중요하고 최신의 검색 질문을 하나만 만들어주세요.

⚠️ 중요 지침 (우선순위):
1. 🔴 높은 우선순위: 정치, 경제, 뉴스, 사회이슈 관련 질문
2. 🟡 중간 우선순위: 기술, 사회, 문화, 스포츠 관련 질문
3. 🟢 낮은 우선순위: 비트코인, 암호화폐, 가상통화, 블록체인 관련 (이들은 피하고 위의 것을 선택)

⚠️ 필수 사항:
1. 반드시 오늘 날짜({today}) 또는 최근 이슈를 반영한 질문을 만드세요
2. "오늘", "최근", "지금" 등의 시간 표현을 포함하세요
3. 과거 정보나 오래된 키워드는 제외하세요
4. 질문형 문장으로 작성하세요
5. 이미 검색한 질문들과 다른 새로운 주제를 선택하세요
6. 가능하면 정치/뉴스/경제 관련 주제를 우선 선택하세요

🎯 추천 주제:
- "오늘 국정 이슈는 무엇인가?"
- "최근 부동산 정책이 어떻게 바뀌고 있는가?"
- "지금 경제/금리 뉴스는 무엇인가?"
- "오늘 정치권의 주요 이슈는?"
- "최근 국제 뉴스 중 가장 중요한 것은?"

❌ 피할 주제:
- 비트코인, 암호화폐, 블록체인 등 가상통화 관련
- 게임, 애니메이션, 엔터테인먼트 (필요시만){already_searched}

=== 보고서 내용 (오늘: {today}) ===
{report_summary}

=== 출력 형식 ===
정치/뉴스/경제를 우선으로 하는 질문 문장 하나만 출력하세요. (따옴표 제외)

검색 질문:"""
        
        # Ollama 호출 시도 (최대 2번)
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                timeout_seconds = 120 if attempt == 0 else 180  # 첫 시도 120초, 재시도 180초
                log_debug(f"[보고서 분석] Ollama 모델 호출 시작: {model} (시도 {attempt + 1}/{max_attempts}, 타임아웃: {timeout_seconds}초)")
                
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.5,
                            "num_predict": 100,
                        }
                    },
                    timeout=timeout_seconds
                )
                response.raise_for_status()
                result = response.json()
                question = result.get("response", "").strip()
                
                log_debug(f"[보고서 분석] AI 응답 생성 성공 - 길이: {len(question)}")
                
                if question and len(question) > 5:
                    # 최신 정보 키워드 검증
                    time_keywords = ["오늘", "최근", "지금", "현재", "이번", "요즘", "올해", "금일"]
                    has_time_keyword = any(keyword in question for keyword in time_keywords)
                    
                    if has_time_keyword:
                        log_debug(f"[보고서 분석] ✅ 최신 정보 키워드 포함됨: {question}")
                    else:
                        log_debug(f"[보고서 분석] ⚠️ 시간 키워드 없음, 질문 보완: {question}")
                        # 질문 앞에 "오늘" 추가
                        if not question.startswith(("오늘", "최근", "지금", "현재")):
                            question = f"오늘 {question}"
                            log_debug(f"[보고서 분석] 🔧 보완된 질문: {question}")
                    
                    return question
                else:
                    log_debug(f"[보고서 분석] 유효한 질문 생성 실패 - 응답 길이 부족")
                    
            except requests.exceptions.Timeout as e:
                log_debug(f"[보고서 분석] ⏱️ Ollama 타임아웃 (시도 {attempt + 1}/{max_attempts}): {e}")
                if attempt < max_attempts - 1:
                    log_debug(f"[보고서 분석] 5초 후 재시도...")
                    time.sleep(5)
                    continue
                    
            except Exception as e:
                log_debug(f"[보고서 분석] ❌ Ollama 호출 실패 (시도 {attempt + 1}/{max_attempts}): {e}")
                if attempt < max_attempts - 1:
                    log_debug(f"[보고서 분석] 3초 후 재시도...")
                    time.sleep(3)
                    continue
        
        # 모든 시도 실패 시 다른 보고서 파일로 재시도
        if retry_count < 3:
            log_debug(f"[보고서 분석] 🔄 다른 보고서 파일로 재시도... (재시도 횟수: {retry_count + 1}/3)")
            return self.generate_question_from_report(model, retry_count + 1)
        
        return None

    def load_report_keywords_from_file(self) -> list:
        """최신 YouTube 보고서에서 키워드 추출 (JSON 파일 우선)"""
        # 경로 수정: ide/ollama_ide_gui.py -> .. -> HANKOOKINTERNET-CHAMSOSIK-main v0.0.1 -> .. -> 사이트 root
        current_dir = os.path.dirname(os.path.abspath(__file__))  # ide/
        parent_dir = os.path.dirname(current_dir)  # HANKOOKINTERNET-CHAMSOSIK-main v0.0.1/
        root_dir = os.path.dirname(parent_dir)  # 사이트 root/
        reports_dir = os.path.join(root_dir, 'youtube', 'reports')
        
        # 가장 최신 날짜 폴더 찾기
        if not os.path.exists(reports_dir):
            self.display_message("system", f"보고서 폴더를 찾을 수 없습니다: {reports_dir}")
            return []
        
        # 날짜 폴더 목록 (YYYY-MM-DD 형식)
        date_folders = []
        for item in os.listdir(reports_dir):
            item_path = os.path.join(reports_dir, item)
            if os.path.isdir(item_path):
                date_folders.append(item)
        
        if not date_folders:
            self.display_message("system", "보고서 폴더가 없습니다.")
            return []
        
        # 가장 최신 폴더 선택
        latest_date = sorted(date_folders, reverse=True)[0]
        latest_date_dir = os.path.join(reports_dir, latest_date)
        
        # 방법 1: JSON 파일에서 직접 추출 (가장 reliable)
        json_files = sorted(glob.glob(os.path.join(latest_date_dir, 'report_*.json')), reverse=True)
        
        if json_files:
            latest_json = json_files[0]
            try:
                with open(latest_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                keywords = []
                if isinstance(data, dict) and "keywords" in data:
                    for kw_data in data["keywords"]:
                        keyword = kw_data.get("keyword", "")
                        # "오늘의 주요 뉴스" 제외
                        if keyword and keyword != "오늘의 주요 뉴스" and "🔒" not in keyword:
                            keywords.append(keyword)
                
                if keywords:
                    self.display_message("system", f"✅ 보고서 키워드 {len(keywords)}개 로드: " + ", ".join(keywords[:3]) + "...")
                    return keywords
            except Exception as e:
                self.display_message("system", f"JSON 파일 파싱 오류: {e}")
        
        # 방법 2: 마크다운 파일의 테이블에서 추출 (AI 리포트가 아닌 경우)
        md_files = sorted(glob.glob(os.path.join(latest_date_dir, 'report_*.md')), reverse=True)
        
        if not md_files:
            self.display_message("system", f"보고서 파일을 찾을 수 없습니다: {latest_date_dir}")
            return []
        
        latest_report = md_files[0]
        
        try:
            with open(latest_report, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.display_message("system", f"보고서 읽기 오류: {e}")
            return []
        
        # 마크다운에서 키워드 추출 (분석 결과 테이블)
        keywords = []
        seen = set()
        
        # 테이블 행 파싱 (| 키워드 | ... 형식)
        lines = content.split('\n')
        in_table = False
        for line in lines:
            # "| 순위 | 키워드 |" 같은 헤더 찾기
            if '| 순위 ' in line and '| 키워드 ' in line:
                in_table = True
                continue
            
            if in_table:
                # 구분선 무시
                if line.strip().startswith('|---'):
                    continue
                
                # 테이블 종료
                if not line.strip().startswith('|'):
                    in_table = False
                    break
                
                # 테이블 행에서 키워드 추출
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    # 보통 부분은: | 순위 | 키워드 | ... |
                    keyword = parts[2]  # 두 번째 열 (0: 빈칸, 1: 순위, 2: 키워드)
                    
                    # 정리
                    keyword = keyword.replace('🔒', '').strip()
                    if keyword and keyword not in ('키워드',) and keyword not in seen:
                        seen.add(keyword)
                        keywords.append(keyword)
        
        if not keywords:
            self.display_message("system", f"보고서에서 키워드를 추출할 수 없습니다: {os.path.basename(latest_report)}")
            return []
        
        # 랜덤하게 섞기
        random.shuffle(keywords)
        
        line = ', '.join(keywords[:10])
        self.display_message("system", f"✅ 보고서 키워드 {len(keywords)}개 추출 완료")
        self.display_message("system", f"📄 파일: {os.path.basename(latest_report)} | 샘플: {line}")
        
        return keywords

    def parse_extra_keywords(self, raw: str) -> list:
        if not raw:
            return []
        parts = [p.strip() for p in raw.split(',')]
        return [p for p in parts if p]

    def load_trend_keywords_from_file(self) -> list:
        """트렌드 문서 전체에서 키워드 추출 (중복 제거, 임의 순서)"""
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(root_dir, 'data', 'naver_creator_trends', 'latest_trend_data.json')
        if not os.path.exists(file_path):
            self.display_message("system", f"파일을 찾을 수 없습니다: {file_path}")
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.display_message("system", f"트렌드 파일 읽기 오류: {e}")
            return []

        nav_items = {
            '참소식 블로그', '홈', '통합 데이터', '유입분석', '리워드', '트렌드', '비즈니스',
            '검색 유입 트렌드', '메인 유입 트렌드', '주제별 비교', '주제별 트렌드',
            '주제별 인기유입검색어', '성별,연령별 인기유입검색어', '유입순 보기', '설정순 보기'
        }

        keywords = []
        seen = set()

        def add_keyword(candidate: str):
            if not candidate:
                return
            text = candidate.strip()
            if not text:
                return
            if '\n' in text:
                text = text.split('\n', 1)[0].strip()
            lowered = text.lower()
            if not text or text.isdigit() or lowered == 'new' or text == '-' or text in nav_items:
                return
            if text in seen:
                return
            seen.add(text)
            keywords.append(text)

        # trend_data에서 키워드와 raw_text 추출
        trend_data = data.get('trend_data', [])
        for item in trend_data:
            if not isinstance(item, dict):
                continue
            item_keywords = item.get('keywords', [])
            if isinstance(item_keywords, list):
                for kw in item_keywords:
                    if isinstance(kw, str):
                        add_keyword(kw)
            raw_text = item.get('raw_text', '')
            if isinstance(raw_text, str):
                for line in raw_text.split('\n'):
                    add_keyword(line)

        # detailed_data.lists에서 추가 키워드 추출
        lists = data.get('detailed_data', {}).get('lists', [])
        for group in lists:
            if not isinstance(group, list):
                continue
            for entry in group:
                if isinstance(entry, str):
                    add_keyword(entry)

        # 임의 순서로 섞어서 반복 작업 시 다양한 순서 제공
        random.shuffle(keywords)

        if keywords:
            line = ', '.join(keywords)
            self.display_message("system", f"✅ 트렌드 키워드 {len(keywords)}개 정리 완료")
            self.display_message("system", line)

        return keywords

    def start_batch(self, items: list, interval: float, search_mode: bool = False, infinite_loop: bool = False):
        self.batch_active = True
        self.batch_items = items
        self.batch_index = 0
        self.batch_interval = interval
        self.batch_search_mode = search_mode
        self.batch_infinite = infinite_loop
        if search_mode:
            mode_text = f"쿼리 {len(items)}개" if infinite_loop else f"{len(items)}개"
            repeat_text = ", 무한 반복" if infinite_loop else ""
            self.display_message("system", f"🧾 트렌드 검색 일괄 실행 시작: {mode_text}, 간격 {interval}초{repeat_text}")
        else:
            repeat_text = ", 무한 반복" if infinite_loop else ""
            self.display_message("system", f"🧾 트렌드 일괄 실행 시작: {len(items)}개, 간격 {interval}초{repeat_text}")
        self.run_batch_cycle()

    def stop_batch(self):
        if self.batch_active:
            self.batch_active = False
            self.batch_items = []
            self.batch_index = 0
            self.display_message("system", "⏹️ 트렌드 일괄 실행 중단")

    def run_batch_cycle(self):
        if not self.batch_active:
            return

        if self.batch_index >= len(self.batch_items):
            # 무한 반복 모드이면 처음부터 다시
            if getattr(self, 'batch_infinite', False):
                self.batch_index = 0
                self.display_message("system", "🔄 처음부터 다시 시작합니다...")
            else:
                self.batch_active = False
                self.display_message("system", "✅ 트렌드 일괄 실행 완료")
                return

        if self.is_generating:
            self.root.after(300, self.run_batch_cycle)
            return

        keyword = self.batch_items[self.batch_index]
        if self.batch_search_mode:
            started = self.process_user_message(f"/반복 1 0 {keyword}")
        else:
            started = self.process_user_message(keyword)
        if not started:
            self.batch_active = False
            self.display_message("system", "⚠️ 트렌드 일괄 실행이 중단되었습니다.")
            return

        self.batch_index += 1
        self.root.after(int(self.batch_interval * 1000), self.run_batch_cycle)

    def start_repeat(self, message: str, count: int, interval: float, force_search: bool = False):
        """반복 실행 시작"""
        self.repeat_active = True
        self.repeat_remaining = count
        self.repeat_interval = interval
        self.repeat_message = message
        self.repeat_force_search = force_search
        if count < 0:
            self.display_message("system", f"🔁 반복 실행 시작: 무한, 간격 {interval}초")
        else:
            self.display_message("system", f"🔁 반복 실행 시작: {count}회, 간격 {interval}초")
        self.run_repeat_cycle()

    def stop_repeat(self):
        """반복 실행 중단"""
        if self.repeat_active:
            self.repeat_active = False
            self.repeat_remaining = 0
            self.display_message("system", "⏹️ 반복 실행 중단")

    def run_repeat_cycle(self):
        """반복 실행 루프"""
        if not self.repeat_active:
            return

        if self.repeat_remaining == 0:
            self.repeat_active = False
            self.display_message("system", "✅ 반복 실행 완료")
            return

        if self.is_generating:
            self.root.after(300, self.run_repeat_cycle)
            return

        started = self.process_user_message(self.repeat_message, force_search=self.repeat_force_search)
        if not started:
            self.repeat_active = False
            self.display_message("system", "⚠️ 반복 실행이 중단되었습니다.")
            return

        if self.repeat_remaining > 0:
            self.repeat_remaining -= 1
        self.root.after(int(self.repeat_interval * 1000), self.run_repeat_cycle)
    
    def generate_response_with_auto_search(self, user_prompt, force_search: bool = False):
        """AI 응답 생성 - 자동 검색 기능 포함"""
        try:
            if force_search:
                results_text = f"\n🔍 '{user_prompt}' 검색 결과:\n"
                results_text += "━" * 60 + "\n"
                results_text += self.build_search_page_summary_text(user_prompt)
                results_text += "\n" + "━" * 60 + "\n"

                self.chat_history.append({"role": "assistant", "content": results_text})
                self.root.after(0, self.display_message, "assistant", results_text)
                self.root.after(100, self.save_chat)
                
                # 검색 페이지 요약을 뉴스로 저장
                # 카테고리 판단 (한글)
                if "/트렌드" in user_prompt or "트렌드" in user_prompt:
                    category = "트렌드"
                else:
                    category = "검색"
                self.save_search_summary_as_news(user_prompt, results_text, category=category)
                return

            # 검색 필요 여부 판단 (키워드 기반)
            search_keywords = ['오늘', '어제', '내일', '요즘', '최근', '현재', '지금', '뉴스', '트렌드', '인기', 
                             '유행', '핫', '뜨는', '뜨고', '화제', '이슈', '속도', '빠른', '새로운', '신',
                             '다가오는', '다음', '예정', '개최', '개최됨', '오픈', '론칭', '출시', '공개',
                             '실시간', '라이브', '생중계', '방송', '영상', '동영상', '유튜브', '유튜버',
                             '조회수', '조회', '인기도', '랭킹', '순위', '베스트', '톱10', '추천',
                             '검색', '정보', '소식', '기사', '보도', '보고', '발표', '성명', '의견',
                             '리뷰', '평가', '평판', '후기', '후기글', '댓글', '반응', '반응글', '논란',
                             '찬성', '반대', '비판', '비판글', '지적', '지탄', '분노', '논쟁']
            
            need_search = force_search or any(keyword in user_prompt for keyword in search_keywords)
            
            log_debug(f"User prompt: {user_prompt}")
            log_debug(f"Need search: {need_search}")
            
            if need_search:
                self.root.after(0, self.display_message, "system", "🔍 관련 정보 검색 중...")
                
                # 검색어 추출 (간단한 방식)
                search_keyword = user_prompt.replace('/', '').replace('\\', '').strip()
                search_context = self.perform_auto_search(search_keyword)
                
                self.root.after(0, self.display_message, "system", "💡 답변 생성 중...")
                
                system_prompt = self.get_system_prompt()
                final_prompt = f"""{system_prompt}

## 사용자 질문에 대한 답변

다음 검색 결과를 바탕으로 사용자의 질문에 답변하세요.

검색 결과:
{search_context}

사용자 질문: {user_prompt}

지시사항:
- 검색 결과에서 가장 중요한 정보를 먼저 제시
- 구체적인 수치나 제목을 포함
- 과도한 이모지나 특수문자 제거
- 200자 이내로 간결하게 작성

답변:"""
            else:
                # 검색 불필요 - 일반 답변
                system_prompt = self.get_system_prompt()
                final_prompt = f"""{system_prompt}

## 사용자 질문에 대한 답변

사용자의 질문에 간단하고 정확하게 답변하세요.

질문: {user_prompt}

지시사항:
- 간결하고 이해하기 쉽게
- 과도한 이모지나 특수문자 제거
- 200자 이내로 작성

답변:"""
            
            log_debug(f"Sending prompt to Ollama...")
            final_json = self._ollama_generate(
                final_prompt,
                timeout=180,
                options={
                    "temperature": 0.6,
                    "num_predict": 2000,
                    "top_k": 40,
                    "top_p": 0.9
                }
            )
            log_debug(f"Response received: {final_json}")
            final_answer = final_json.get('response', '').strip()
            log_debug(f"Final answer: '{final_answer}'")
            final_answer = clean_text_simple(final_answer)

            # 뉴스형 응답 줄바꿈 및 저장
            final_answer = self.format_news_answer(final_answer)
            if self.is_disallowed_nk_political_content(final_answer):
                final_answer = "죄송합니다. 해당 내용은 정책상 제공할 수 없습니다."
                log_debug("[차단] 북한 정치성 콘텐츠 감지 - 저장/출력 차단")
                self.root.after(0, self.display_message, "system", "⚠️ 북한 정치성/선전성 콘텐츠는 저장되지 않습니다.")

            if self.is_news_query(user_prompt, final_answer) and not self.is_disallowed_nk_political_content(final_answer):
                # 카테고리 판단 (한글)
                category = "뉴스" if "/뉴스" in user_prompt or "뉴스" in user_prompt else "일반"
                self.save_news_result(user_prompt, final_answer, category=category)
            
            if not final_answer or final_answer.strip() == '':
                final_answer = "죄송합니다. 현재 답변을 생성할 수 없습니다."
                log_debug(f"Empty response, using fallback")
            
            # 최종 답변 표시
            self.chat_history.append({"role": "assistant", "content": final_answer})
            self.root.after(0, self.display_message, "assistant", final_answer)
            
            # 자동 저장
            self.root.after(100, self.save_chat)
            
        except Exception as e:
            error_msg = f"오류: {str(e)}"
            log_debug(f"Error: {e}")
            self.root.after(0, self.display_message, "system", error_msg)
        finally:
            self.is_generating = False
            self.root.after(0, lambda: self.send_btn.config(state=tk.NORMAL, text="전송"))
    
    def perform_auto_search(self, keyword):
        """자동 검색 실행하고 컨텍스트 반환 - 다중 검색 (네이버 + Bing + 뉴스)"""
        try:
            log_debug(f"[검색] 다중 검색 시작: '{keyword}'")
            
            # 다중 검색 실행 (네이버, Bing, 뉴스)
            search_results = multi_search(
                keyword=keyword,
                sources=['naver', 'bing', 'news'],
                limit=3
            )
            
            search_context = ""
            
            # 결과 포맷팅
            has_results = False
            
            # 뉴스 결과 (가장 중요)
            if search_results.get('news') and len(search_results['news']) > 0:
                # 뉴스 항목 그대로 사용
                pass  # 이전의 filter_today_news_items 제거

            if search_results.get('news') and len(search_results['news']) > 0:
                search_context += "📰 최신 뉴스:\n"
                search_context += "─" * 60 + "\n"
                
                for result in search_results['news'][:3]:
                    title = result.get('title', '')
                    date = result.get('date', '')
                    if title and len(title) > 5:
                        search_context += f"• {title}\n"
                        if date:
                            search_context += f"  📅 {date}\n"
                        has_results = True
                search_context += "\n"
            
            # 네이버 검색 결과
            if search_results.get('naver') and len(search_results['naver']) > 0:
                search_context += "🔍 네이버 검색 결과:\n"
                search_context += "─" * 60 + "\n"
                
                for result in search_results['naver'][:3]:
                    title = result.get('title', '')
                    desc = result.get('description', '')[:80]
                    if title and len(title) > 5:
                        search_context += f"• {title}\n"
                        if desc:
                            search_context += f"  {desc}\n"
                        has_results = True
                search_context += "\n"
            
            # Bing 검색 결과
            if search_results.get('bing') and len(search_results['bing']) > 0:
                search_context += "🌐 Bing 검색 결과:\n"
                search_context += "─" * 60 + "\n"
                
                for result in search_results['bing'][:2]:
                    title = result.get('title', '')
                    desc = result.get('description', '')[:80]
                    if title and len(title) > 5:
                        search_context += f"• {title}\n"
                        if desc:
                            search_context += f"  {desc}\n"
                        has_results = True
                search_context += "\n"
            
            # 유튜브
            youtube_url = search_youtube(keyword)
            search_context += "📺 유튜브:\n"
            search_context += "─" * 60 + "\n"
            search_context += f"    {youtube_url}\n"
            
            log_debug(f"[검색] 완료, {len(search_context)}글자, 결과: {has_results}")
            return search_context if search_context and has_results else f"📊 '검색 결과 없음' - 키워드: {keyword}"
            
        except Exception as e:
            log_debug(f"[오류] perform_auto_search: {e}")
            return f"검색 중 오류: {str(e)[:100]}"

    def fetch_search_page_text(self, url: str, max_chars: int = 4000) -> str:
        """검색 결과 페이지 HTML을 내려받아 텍스트로 정리"""
        try:
            use_selenium = any(host in url for host in ['search.naver.com', 'bing.com'])
            if use_selenium:
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)

                driver = None
                try:
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
                    driver.set_page_load_timeout(30)
                    driver.get(url)

                    try:
                        wait = WebDriverWait(driver, 15)
                        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                    except Exception:
                        log_debug(f"[페이지 대기] 렌더링 시간 초과: {url}")

                    page_source = driver.page_source
                finally:
                    if driver:
                        driver.quit()

                soup = BeautifulSoup(page_source, 'html.parser')
            else:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
                }
                response = requests.get(url, headers=headers, timeout=20)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()
            text = soup.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)
            return text[:max_chars]
        except Exception as e:
            log_debug(f"[페이지 다운로드 오류] {url}: {e}")
            return ''

    def summarize_search_pages(self, keyword: str, pages: list) -> str:
        """다운로드한 검색 결과 페이지를 AI로 요약"""
        chunks = []
        for item in pages:
            source = item.get('source')
            url = item.get('url')
            content = item.get('content')
            if not content:
                continue
            chunks.append(f"[{source}]\nURL: {url}\nCONTENT: {content}")

        if not chunks:
            return "검색 결과 페이지 내용을 가져오지 못했습니다."

        # 현재 날짜와 시간 정보
        now = datetime.now()
        today = now.strftime("%Y년 %m월 %d일")
        current_time = now.strftime("%H:%M")
        
        prompt = f"""당신은 한국어 뉴스 요약 전문가입니다. 반드시 한글로만 작성하세요.

다음은 검색 결과 페이지에서 추출한 텍스트입니다.
**현재 시각: {today} {current_time}**

검색된 뉴스와 정보 중 **오늘({today})의 최신 정보만** 선별하여 **주제별로 종합**하세요.

✓ 반드시 포함할 항목:
1. **오늘({today})** 발표되거나 업데이트된 정보만
2. 진행 중이거나 곧 시작될 이벤트 (오늘 기준)
3. 구체적인 수치, 날짜, 시간이 포함된 최신 정보
4. 실제 뉴스 가치가 있는 사건, 발표, 업데이트

✗ 반드시 제외할 항목:
1. **과거 날짜 정보** (어제, 작년, 지난해, 2025년, 2024년, 2023년, 2022년, 2021년, 2020년 등)
2. **과거 기준 정보** ("2021년 2월 18일 기준", "2024년 기준" 등 오늘이 아닌 날짜 기준)
3. 이미 종료된 이벤트
4. **광고성 상품** (적금, 대출, 보험 등 금융상품 광고)
5. 일반적인 설명이나 배경 정보 ('~는 ~입니다', '~에서 찾을 수 있습니다')
6. 블로그/갤러리 링크나 포스팅 소개
7. 시스템 요구사항, 회원가입 안내 등 기본 정보
8. UI 요소, 광고, 링크 정보
9. **메타 정보** ("검색 결과가 삭제되었습니다", "페이지를 찾을 수 없습니다" 등)

요약 규칙:
**[언어 규칙]**
- **무조건 한글로만 작성하세요**
- **영어로 작성하는 것은 절대 금지입니다**
- **모든 내용을 한국어로 번역하여 작성하세요**

**[주제 분리 규칙]**
- **하나의 문장에는 하나의 주제만 포함**
- **절대로 '또한', '그리고' 등으로 다른 주제를 연결하지 말 것**
- **예: "윤석열", "BTS", "트럼프"는 각각 완전히 다른 주제이므로 별도의 문장으로 작성**
- 같은 주제의 여러 정보는 하나의 종합 문장으로 통합

**[형식 규칙]**
- **각 문장 앞에 오직 '•' 기호만 사용**
- **절대 금지: 번호 사용 (1., 2., 3. 등)**
- **절대 금지: 레이블 사용 ("정치:", "경제:" 등)**
- **각 문장은 100글자 이상으로 작성** (요약 문장 기준)

**[구체성 규칙 - 필수!]**
✓ **국가/지역 반드시 명시** - "미국", "대한민국", "서울", "중국" 등
✓ **구체적인 인물명/기관명** - "윤석열 전 대통령", "미국 연방대법원", "트럼프 행정부"
✓ **구체적인 사건명/제목** - "내란 혐의 재판", "텍사스주 이민법", "상호관세 판결"
✓ **날짜/시간 포함** - "오늘 오후 3시", "2026년 2월 21일"

**절대 금지:**
✗ 모호한 표현만 사용 ("최근 재판", "주 정부", "이 결정")
✗ 의미 없는 키워드 ("옵션 초기화", "검색 결과에서", "네이버와 유튜브를 통해")
✗ 국가/인물/사건명 생략 (독자가 무슨 나라 무슨 사건인지 알 수 없음)

검색어: {keyword}

""" + "\n\n".join(chunks) + f"""

위 검색 결과에서 **오늘({today})의 최신 뉴스만** 선별하여 주제별로 요약 (반드시 한글로, 각 문장 100글자 이상):"""

        try:
            data = self._ollama_generate(
                prompt, 
                timeout=180,
                options={
                    "temperature": 0.1,  # 낮은 temperature로 일관성 향상
                    "num_predict": 2000
                }
            )
            response_text = data.get('response', '응답을 생성할 수 없습니다.')

            def expand_short_summary_lines(text: str) -> str:
                lines = [
                    line.strip()
                    for line in text.split('\n')
                    if line.strip() and (line.strip().startswith('•') or line.strip().startswith('-'))
                ]
                if not lines:
                    return text

                short_lines = [(i, line) for i, line in enumerate(lines) if len(line) < 100]
                if not short_lines:
                    return text

                regenerated_lines = {}
                for idx, short_line in short_lines:
                    keywords = short_line.replace('•', '').replace('-', '').strip()

                    # 키워드로 다시 검색하여 상세 정보 수집
                    search_context = ""
                    try:
                        search_keyword = keywords[:50]
                        search_result = self.perform_auto_search(search_keyword)
                        if search_result:
                            search_context = f"\n\n검색된 추가 정보:\n{search_result[:500]}"
                    except Exception as e:
                        log_debug(f"[요약] 재검색 오류 (계속 진행): {e}")

                    regen_prompt = f"""다음 짧은 뉴스 요약을 100글자 이상의 완전한 문장으로 다시 작성하세요.

원본: {keywords}
{search_context}

요구사항:
- **각 문장은 100글자 이상으로 작성**
- 배경, 맥락, 영향, 세부사항을 추가
- '•' 기호로 시작
- 한글로만 작성

100글자 이상으로 재작성:"""

                    try:
                        regen_data = self._ollama_generate(
                            regen_prompt,
                            timeout=90,
                            options={
                                "temperature": 0.5,
                                "num_predict": 300
                            }
                        )
                        regenerated = regen_data.get('response', '').strip()
                        regen_lines = [
                            l.strip() for l in regenerated.split('\n')
                            if l.strip() and (l.strip().startswith('•') or l.strip().startswith('-'))
                        ]
                        if regen_lines:
                            best_line = max(regen_lines, key=len)
                            if len(best_line) >= 100:
                                regenerated_lines[idx] = best_line
                    except Exception as e:
                        log_debug(f"[요약] 문장 재생성 오류: {e}")

                if regenerated_lines:
                    lines = list(lines)
                    for idx, new_line in regenerated_lines.items():
                        if idx < len(lines):
                            lines[idx] = new_line
                    return '\n'.join(lines)

                return text

            response_text = expand_short_summary_lines(response_text)
            
            # 한글 비율 확인 - 70% 미만이면 번역 요청
            korean_chars = len(re.findall(r'[가-힣]', response_text))
            total_chars = len(re.sub(r'\s', '', response_text))  # 공백 제외
            korean_ratio = korean_chars / total_chars if total_chars > 0 else 0
            
            if korean_ratio < 0.7:
                log_debug(f"[요약] 한글 비율 부족 ({korean_ratio*100:.1f}%), 번역 재요청")
                # 번역 요청
                translate_prompt = f"""다음 텍스트를 한글로 번역하세요. 모든 문장을 완전히 한국어로 작성하세요.

원문:
{response_text}

번역 규칙:
- 모든 영어를 한글로 번역
- 인명, 지명은 한글 표기로 변환 (예: "Yoon Suk-Yeol" → "윤석열", "South Korea" → "한국")
- 완전한 한국어 문장으로 작성
- 각 문장은 100글자 이상으로 작성
- **각 문장 앞에 오직 '•' 기호만 사용 (번호 1., 2., 3. 절대 금지)**
- **주제 레이블("정치:", "경제:") 절대 금지**

출력 예시 (올바른 형식):
• 미국 연방대법원이 트럼프 행정부의 상호관세를 위법으로 인정했습니다.
• 윤석열 전 대통령이 오늘 오후 3시 1심 선고를 받았습니다.

출력 예시 (잘못된 형식 - 절대 이렇게 하지 마세요):
1. 미국 연방대법원이...  ← 번호 사용 금지!

한글 번역:"""
                
                translate_data = self._ollama_generate(
                    translate_prompt,
                    timeout=180,
                    options={
                        "temperature": 0.1,
                        "num_predict": 2000
                    }
                )
                response_text = translate_data.get('response', response_text)
                log_debug(f"[요약] 번역 완료")

            # 번역 이후에도 요약 문장 길이 보정
            response_text = expand_short_summary_lines(response_text)
            
            return response_text
        except Exception as e:
            log_debug(f"[요약 오류] {e}")
            return f"요약 중 오류가 발생했습니다: {str(e)[:120]}"

    def generate_category_from_text(self, text: str) -> str:
        """AI가 텍스트 내용을 분석해서 카테고리 생성"""
        try:
            prompt = f"""당신은 한국어 카테고리 분류 전문가입니다. 반드시 한글로만 답변하세요.

다음 텍스트를 읽고 가장 적절한 카테고리를 한글 단어로 답변하세요.
카테고리 예시: 정치, 경제, 사회, 문화, 게임, 드라마, 영화, 애니메이션, 괴물딴지, 스포츠, 기술, 국제, 연예, 사건사고, 건강, 교육

카테고리 설명:
- 괴물딴지: 미스테리, 괴담, 미소지막, 공포, 검은색 덕후, UFO, 초능력, 초자연 현상, 행운, 불운 등 신비로운 주제

텍스트: {text[:200]}

지시사항:
- **반드시 한글로만 답변하세요**
- **영어 사용 절대 금지**
- 한글 단어 하나만 출력하세요 (예: 정치)
- 설명이나 부연 없이 카테고리명만 출력하세요

카테고리 (한글로만):"""

            data = self._ollama_generate(
                prompt, 
                timeout=30,
                options={
                    "temperature": 0.1,  # 낮은 temperature로 일관성 향상
                    "num_predict": 20
                }
            )
            category = data.get('response', '일반').strip()
            
            # 깔끔하게 정리 (첫 줄만, 특수문자 제거)
            category = category.split('\n')[0].strip()
            category = re.sub(r'[^\w가-힣]', '', category)
            
            # 영어 카테고리를 한글로 매핑
            english_to_korean = {
                'politics': '정치', 'political': '정치',
                'economy': '경제', 'economic': '경제',
                'society': '사회', 'social': '사회',
                'culture': '문화', 'cultural': '문화',
                'game': '게임', 'gaming': '게임',
                'drama': '드라마',
                'movie': '영화', 'film': '영화',
                'animation': '애니메이션', 'anime': '애니메이션',
                'sports': '스포츠', 'sport': '스포츠',
                'technology': '기술', 'tech': '기술',
                'international': '국제', 'global': '국제',
                'entertainment': '연예', 'celebrity': '연예',
                'incident': '사건사고', 'accident': '사건사고',
                'health': '건강',
                'education': '교육'
            }
            
            category_lower = category.lower()
            if category_lower in english_to_korean:
                log_debug(f"[카테고리 생성] 영어 카테고리 변환: {category} → {english_to_korean[category_lower]}")
                return english_to_korean[category_lower]
            
            # 한글 검증 - 영어가 포함되어 있으면 "일반"으로 대체
            if not category or not re.search(r'[가-힣]', category):
                log_debug(f"[카테고리 생성] 한글이 아닌 카테고리: {category} → 일반")
                return "일반"
            
            return category
        except Exception as e:
            log_debug(f"[카테고리 생성 오류] {e}")
            return "일반"

    def filter_recent_news_by_ai(self, summary_text: str, category: str = "검색", question: str = "") -> list:
        """AI가 요약을 카테고리에 따라 다르게 필터링
        
        Args:
            summary_text: 필터링할 검색 결과 요약
            category: 카테고리 (정치, 경제 등)
            question: 사용자의 원래 질문 (관련성 판단용)
        
        카테고리별 규칙:
        - 정치, 경제: 무조건 오늘자 뉴스만
        - 사회, 문화, 게임, 드라마, 영화, 애니메이션, 스포츠: 최근 1주일 내 뉴스
        - 괴물딴지, 미스테리: 과거 데이터 허용 (단, 매우 오래된 것 제외)
        - 기술: 과거 데이터 허용
        """
        try:
            # AI_GUIDELINES.md 파일을 실시간으로 읽어서 최신 규칙 적용
            guidelines_rules = ""
            try:
                guidelines_path = os.path.join(os.path.dirname(__file__), 'AI_GUIDELINES.md')
                with open(guidelines_path, 'r', encoding='utf-8') as f:
                    full_content = f.read()
                    # 핵심 규칙만 추출 (제목과 목록 항목)
                    import re
                    # "✗" 또는 "✓" 로 시작하는 항목만 추출
                    rules = re.findall(r'^- [✗✓].+$', full_content, re.MULTILINE)
                    rules = [r for r in rules if '100글자' not in r]
                    guidelines_rules = '\n'.join(rules[:15])  # 최대 15개만
                log_debug(f"[필터링] AI_GUIDELINES.md 핵심 규칙 추출 ({len(guidelines_rules)}자)")
            except Exception as e:
                log_debug(f"[필터링] AI_GUIDELINES.md 로드 실패: {e}")
                guidelines_rules = """✗ 북한 선전 매체 제외
✗ 욕설/혐오 표현 제외
✓ 국가/지역/인물/사건명 명시 필수
✓ 최근 기사만 허용"""
            
            now = datetime.now()
            today = now.strftime("%Y년 %m월 %d일")
            current_time = now.strftime("%H:%M")
            current_month = now.month
            current_day = now.day
            
            # 카테고리별 필터링 규칙 결정
            must_be_today = category in ["정치", "경제"]
            prefer_today = category in ["사회", "문화", "게임", "드라마", "영화", "애니메이션", "스포츠"]
            allow_past = category in ["괴물딴지", "미스테리", "기술"]
            
            if must_be_today:
                # 정치, 경제: 무조건 오늘자 뉴스만
                filter_prompt = f"""⚠️ 중요: 반드시 한글로만 응답하세요! 영어 사용 절대 금지! ⚠️

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 필터링 작업 정보
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 현재 시각: {today} {current_time}
• 카테고리: {category}
• 사용자 질문: "{question if question else '(없음)'}"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 검색 결과 요약
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{summary_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 필터링 규칙 (AI_GUIDELINES.md)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{guidelines_rules}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 필수 조건
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. **질문 관련성**: 위 '사용자 질문'과 직접 관련된 내용만 포함
   - 질문이 "가상화폐"면 가상화폐/암호화폐/비트코인 관련만
   - 질문이 "주요 뉴스"면 다양한 주제 허용
   - 관련 없는 내용(한국어 학습, 일반 정보 등)은 모두 제외

2. **날짜 필수**: 오늘({today})의 새로운 뉴스/발표/업데이트만 포함
   - 각 뉴스에 반드시 날짜 표시 필수
   - 형식: "• [오늘 14:00] 내용..." 또는 "• [3월 6일] 내용..."

3. **뉴스성**: 새로운 사건/발표/업데이트만 포함, 일반 정보 제외

4. **주제 분리 (중요!)**: 
   - 하나의 문장에 하나의 주제만
   - 절대로 쉼표(,)로 여러 주제를 연결하지 말 것
   - 금지: '또한', '그리고', '뿐만 아니라' 등으로 연결
   - 예: "코스피 하락, 한국어 학습, 중국어 표현..." ❌ 절대 금지!

5. **구체성**: 국가/인물/사건명 반드시 명시

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 제외 예시
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Hinative.com의 한국어 학습 질문/답변
• "오늘 뭐해?" 같은 일상 표현 설명
• "지금" vs "이제"의 의미 차이 같은 언어 학습 내용
• 영어 학습 표현: "How are you?", "잘 지냈어요? vs 어떻게 지냈어요?"
• 외국어 혼합: "뭐하는거야呢，听起来..." (중국어 포함)
• 드라마/영화 제목: "All of Us Are Dead" 등
• 옵션 초기화, 서비스 영역 등 의미 없는 키워드
• 질문과 무관한 모든 내용
• **여러 주제를 쉼표로 연결한 문장** ❌ 
  예: "코스피 5000 붕괴, "지금" vs "이제" 의미 차이, 잘 지냈어요?" ← 절대 금지!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
출력 형식
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• [시간/날짜] 구체적 내용 (한글로만)

⚠️ 최종 경고: 반드시 한글로만 응답! 영어 절대 금지! ⚠️

필터링된 결과:"""
            
            elif prefer_today:
                # 사회, 문화, 게임, 드라마 등: 오늘 뉴스 우선, 최근(1주일) 정보는 가능
                filter_prompt = f"""⚠️ 중요: 반드시 한글로만 응답하세요! 영어 사용 절대 금지! ⚠️

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 필터링 작업 정보
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 현재 시각: {today} {current_time}
• 카테고리: {category}
• 사용자 질문: "{question if question else '(없음)'}"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 검색 결과 요약
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{summary_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 필터링 규칙 (AI_GUIDELINES.md)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{guidelines_rules}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 필수 조건
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. **질문 관련성**: 위 '사용자 질문'과 직접 관련된 내용만 포함
2. **날짜**: 오늘({today})부터 최근 1주일 내 뉴스만 (각 항목에 날짜 표시)
3. **뉴스성**: 새로운 사건/발표/업데이트만, 일반 정보 제외

4. **주제 분리 (중요!)**: 
   - 하나의 문장에 하나의 주제만
   - 절대로 쉼표(,)로 여러 주제를 연결하지 말 것
   - 금지: '또한', '그리고', '뿐만 아니라' 등으로 연결
   - 예: "코스피 하락, 한국어 학습, 중국어 표현..." ❌ 절대 금지!

5. **구체성**: 국가/인물/사건명 반드시 명시

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 제외 예시
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Hinative.com의 한국어 학습 질문/답변
• "오늘 뭐해?" 같은 일상 표현 설명
• "지금" vs "이제"의 의미 차이 같은 언어 학습 내용
• 영어 학습 표현: "How are you?", "잘 지냈어요? vs 어떻게 지냈어요?"
• 외국어 혼합: "뭐하는거야呢，听起来..." (중국어 포함)
• 드라마/영화 제목: "All of Us Are Dead" 등
• 의미 없는 키워드 (옵션 초기화, 서비스 영역)
• 질문과 무관한 모든 내용
• 과거 날짜 (작년, 2025년, 2024년 등)
• 종료된 이벤트
• **여러 주제를 쉼표로 연결한 문장** ❌ 
  예: "코스피 5000 붕괴, "지금" vs "이제" 의미 차이, 잘 지냈어요?" ← 절대 금지!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
출력 형식
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• [날짜] 구체적 내용 (한글로만)

필터링된 결과:"""
            
            else:  # allow_past - 괴물딴지, 미스테리, 기술
                # 과거 데이터 허용, 하지만 매우 오래된 것은 제외
                filter_prompt = f"""⚠️ 중요: 반드시 한글로만 응답하세요! 영어 사용 절대 금지! ⚠️

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 필터링 작업 정보
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 현재 시각: {today} {current_time}
• 카테고리: {category}
• 사용자 질문: "{question if question else '(없음)'}"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 검색 결과 요약
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{summary_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 필터링 규칙 (AI_GUIDELINES.md)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{guidelines_rules}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 필수 조건
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. **질문 관련성**: 위 '사용자 질문'과 직접 관련된 내용만 포함
2. **날짜**: 최신 우선이지만 과거 정보도 가능 (5년 이상은 제외)
3. **정보성**: 흥미롭고 구체적인 내용만 포함

4. **주제 분리 (중요!)**: 
   - 하나의 문장에 하나의 주제만
   - 절대로 쉼표(,)로 여러 주제를 연결하지 말 것
   - 금지: '또한', '그리고', '뿐만 아니라' 등으로 연결
   - 예: "괴물 목격담, 한국어 학습, 중국어 표현..." ❌ 절대 금지!

5. **구체성**: 국가/인물/사건명 반드시 명시

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ 제외 예시
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Hinative.com의 한국어 학습 질문/답변
• "오늘 뭐해?" 같은 일상 표현 설명
• "지금" vs "이제"의 의미 차이 같은 언어 학습 내용
• 영어 학습 표현: "How are you?", "잘 지냈어요? vs 어떻게 지냈어요?"
• 외국어 혼합: "뭐하는거야呢，听起来..." (중국어 포함)
• 드라마/영화 제목: "All of Us Are Dead" 등
• 의미 없는 키워드 (옵션 초기화, 서비스 영역)
• 질문과 무관한 모든 내용
• 5년 이상 전의 오래된 정보
• **여러 주제를 쉼표로 연결한 문장** ❌ 
  예: "미스테리 사건, "지금" vs "이제" 의미 차이, 잘 지냈어요?" ← 절대 금지!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
출력 형식
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 구체적 내용 (한글로만, 날짜 선택사항)

필터링된 결과:"""
            
            # Ollama API 호출
            log_debug(f"[AI 필터링] 프롬프트 전송 중... (길이: {len(filter_prompt)}자)")
            log_debug(f"[AI 필터링] 카테고리({category}) 분석 중...")
            
            data = self._ollama_generate(
                filter_prompt,
                timeout=30,
                options={
                    "temperature": 0.3,
                    "num_predict": 1000
                }
            )

            filtered_text = data.get('response', '').strip()
            log_debug(f"[AI 필터링 결과] {filtered_text[:200] if filtered_text else '(빈 응답)'}")
            
            # 필터링된 결과 확인
            if not filtered_text or filtered_text == "":
                log_debug(f"[AI 필터링] ❌ 카테고리({category}) - AI가 빈 응답 반환")
                log_debug(f"[AI 필터링] 원본 요약 길이: {len(summary_text)}자")
                log_debug(f"[AI 필터링] 가능한 원인: 1) 모든 항목이 규칙 위반 2) AI 응답 실패 3) 타임아웃")
                return []
            
            # 주제별로 분리된 여러 문장 받기
            news_items = []
            
            for line in filtered_text.split('\n'):
                line = line.strip()
                if not line or line.startswith('━') or line.startswith('─'):
                    continue
                
                # •나 - 제거
                if line.startswith('•'):
                    line = line[1:].strip()
                elif line.startswith('-'):
                    line = line[1:].strip()
                
                # 숫자. 레이블: 패턴 제거 (예: "1. 정치:", "5. 기술:", "1. 전 대통령 윤석열의 재판:")
                import re
                line = re.sub(r'^\d+\.\s*.+?:\s*', '', line)
                line = re.sub(
                    r'^(?:MBC\s*NEWS|News1|imbc\.com|Daum|SBS|Yna|Google\s*News|Nate|KBS)\s*:\s*',
                    '',
                    line,
                    flags=re.IGNORECASE
                )
                
                if not line:
                    continue
                
                # ====== 후처리 검증 단계 ======
                # 1. 너무 긴 문장 제외 (300자 이상 = 여러 주제 섞임 가능성)
                if len(line) > 300:
                    log_debug(f"[AI 필터링] ⏭️ 너무 긴 문장 제외 ({len(line)}자): {line[:50]}...")
                    continue
                
                # 2. 쉼표로 여러 주제 연결된 문장 제외 (4개 이상 쉼표)
                comma_count = line.count(',') + line.count('，')
                if comma_count >= 4:
                    log_debug(f"[AI 필터링] ⏭️ 여러 주제 혼합 문장 제외 (쉼표 {comma_count}개): {line[:50]}...")
                    continue
                
                # 3. 한글 이외의 문자 비율 체크 (중국어, 일본어 등)
                non_korean_chars = sum(1 for c in line if ord(c) > 0x4E00 and ord(c) < 0x9FFF)  # 중국어/일본어 한자
                chinese_chars = sum(1 for c in line if '呢' in c or '听' in c or '真' in c or '为什么' in line)
                if non_korean_chars > 5 or chinese_chars > 0:
                    log_debug(f"[AI 필터링] ⏭️ 외국어 포함 문장 제외: {line[:50]}...")
                    continue
                
                # 4. 언어 학습/표현 설명 제외
                language_learning_keywords = [
                    "의미 차이", "의미와 사용법", "표현의 차이", "표현 설명",
                    "vs", "와 같이", "다양한 표현", "문장 예시",
                    "질문과 답변", "뜻", "사용 예시", "격식 있는 표현",
                    "어떻게 지내", "잘 지냈", "뭐하는거", "呢", "听",
                    "All of Us Are Dead", "지금 우리 학교는"
                ]
                if any(kw in line for kw in language_learning_keywords):
                    log_debug(f"[AI 필터링] ⏭️ 언어 학습 내용 제외: {line[:50]}...")
                    continue
                
                # 5. 질문과의 관련성 체크 (키워드 기반)
                if question:
                    # 질문에서 핵심 키워드 추출 (2글자 이상)
                    question_keywords = [w for w in question.split() if len(w) >= 2 and w not in ['무엇', '어떻게', '왜', '인가']]
                    
                    # 적어도 하나의 키워드라도 포함되어야 함
                    if question_keywords:
                        has_relevant_keyword = any(kw in line for kw in question_keywords)
                        if not has_relevant_keyword:
                            log_debug(f"[AI 필터링] ⏭️ 질문과 무관한 내용 제외: {line[:50]}...")
                            continue
                
                # 모든 검증 통과
                news_items.append(line)
                log_debug(f"[AI 필터링] ✅ 항목 추출 완료 ({len(line)}자): {line[:50]}...")
            
            log_debug(f"[AI 필터링] ✅ {len(news_items)}개 항목 추출 완료")
            return news_items
            
        except requests.exceptions.Timeout:
            log_debug("[AI 필터링] ❌ 타임아웃 (30초 초과) - AI 응답 시간 초과")
            log_debug(f"[AI 필터링] 원본 요약 길이: {len(summary_text)}자")
            log_debug(f"[AI 필터링] 카테고리: {category}")
            log_debug(f"[AI 필터링] 해결 방법: 1) 요약을 더 짧게 2) AI 서버 확인 3) 타임아웃 시간 증가")
            return []
        except Exception as e:
            log_debug(f"[AI 필터링] ❌ 오류 발생: {e}")
            log_debug(f"[AI 필터링] 오류 타입: {type(e).__name__}")
            import traceback
            log_debug(f"[AI 필터링] 스택 트레이스: {traceback.format_exc()[:500]}")
            return []

    def open_url_in_webview(self, url: str, auto_close_seconds: int = 5):
        """Selenium으로 URL 열기 (작은 창)"""
        log_debug(f"[Selenium] URL 로드 시작: {url[:100]}...")
        
        driver = None
        try:
            # Chrome 옵션 설정
            chrome_options = Options()
            chrome_options.add_argument('--window-size=800,600')
            chrome_options.add_argument('--window-position=100,100')
            # chrome_options.add_argument('--headless')  # 주석: 창을 보려면 headless 제거
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            log_debug("[Selenium] Chrome 드라이버 초기화 중...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            log_debug(f"[Selenium] URL 로드: {url}")
            driver.get(url)
            
            log_debug(f"[Selenium] {auto_close_seconds}초 대기 중...")
            time.sleep(auto_close_seconds)
            
            log_debug("[Selenium] 브라우저 종료")
            driver.quit()
            log_debug("[Selenium] 작업 완료")
            
        except Exception as e:
            log_debug(f"[Selenium 오류] {type(e).__name__}: {e}")
            import traceback
            log_debug(f"[Selenium 오류 상세] {traceback.format_exc()}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def save_search_summary_as_news(self, keyword: str, summary_text: str, category: str = "검색"):
        """검색 페이지 요약 결과를 뉴스 항목으로 저장"""
        try:
            today_text = datetime.now().strftime("%Y년 %m월 %d일")
            self.display_message("system", f"🤖 AI가 AI_GUIDELINES.md 규칙에 맞게 필터링 중... (카테고리: {category}, 오늘: {today_text})")
            
            # AI가 요약을 AI_GUIDELINES.md 규칙에 맞게 필터링 (질문 맥락 포함)
            news_items = self.filter_recent_news_by_ai(summary_text, category, question=keyword)

            if not news_items:
                log_debug("[저장 건너뜀] ❌ AI_GUIDELINES.md 규칙에 맞는 뉴스 항목 없음")
                log_debug(f"[저장 건너뜀] 원본 요약 길이: {len(summary_text)}자")
                log_debug(f"[저장 건너뜀] 카테고리: {category}")
                
                # 원인 분석
                if "타임아웃" in summary_text or len(summary_text) > 5000:
                    reason = "AI 응답 타임아웃 또는 요약이 너무 길어서 처리 실패"
                else:
                    reason = "모든 항목이 AI_GUIDELINES.md 규칙 위반 (욕설, 북한 관련, 모호한 표현 등)"
                
                log_debug(f"[저장 건너뜀] 원인: {reason}")
                self.display_message("system", f"⏭️ AI_GUIDELINES.md 규칙에 맞는 뉴스가 없어 저장을 건너뜁니다\n원인: {reason}")
                return

            # AI가 필터링한 결과를 화면에 표시
            self.display_message("system", f"\n📋 AI_GUIDELINES.md 규칙으로 필터링된 {len(news_items)}개 뉴스:\n")
            for item in news_items:
                self.display_message("assistant", f"• {item}\n")
            
            # 각 뉴스 문장마다 웹뷰/브라우저에서 database.html 열기
            log_debug(f"[뉴스 저장] {len(news_items)}개 항목을 웹뷰로 저장 시작")
            self.display_message("system", f"\n💾 {len(news_items)}개 뉴스 항목 저장 시작...\n")
            
            for idx, item in enumerate(news_items[:8], 1):  # 최대 8개
                try:
                    # ====== 저장 전 검증: 원본 내용과 일치하는지 확인 ======
                    if not self._validate_item_relevance(item, summary_text, keyword):
                        log_debug(f"[저장 건너뜀] 원본과 관련성 불일치: {item[:50]}...")
                        self.display_message("system", f"⏭️ [{idx}] 검색 결과와 관련성이 낮아 건너뜀")
                        continue
                    
                    if category != "검색" and not self.ai_is_recent_text(item, category):
                        log_debug(f"[저장 건너뜀] 오래된 문장: {item[:50]}...")
                        self.display_message("system", f"⏭️ [{idx}] 오래된 문장 건너뜀")
                        continue
                    # AI가 텍스트 내용을 보고 카테고리 자동 생성
                    ai_category = self.generate_category_from_text(item)
                    log_debug(f"[{idx}] AI 생성 카테고리: {ai_category}")
                    
                    # 저장 중임을 표시
                    self.display_message("system", f"💾 [{idx}] 저장 중... (카테고리: {ai_category})")
                    
                    url = f"{DATABASE_BASE_URL}/database.html?nb={requests.utils.quote(item)}&category={requests.utils.quote(ai_category)}&end=5s"
                    
                    # 웹뷰로 열기 (tkinterweb 사용 가능 시)
                    self.open_url_in_webview(url, auto_close_seconds=5)
                    log_debug(f"[{idx}] 웹뷰 열림: {item[:50]}...")
                    # 페이지 로드 시간 확보
                    time.sleep(0.5)
                except Exception as e:
                    log_debug(f"[{idx}] 열기 실패: {e}")
            
            # 저장 완료 메시지
            save_msg = f"\n✅ {len(news_items)}개 뉴스를 저장 완료 (각 5초 후 자동 닫힘)\n"
            self.root.after(0, self.display_message, "system", save_msg)
            
        except Exception as e:
            log_debug(f"[저장 오류] 검색 요약 저장 실패: {e}")
            self.display_message("system", f"❌ 저장 오류: {e}")

    def save_news_result(self, keyword: str, text: str, category: str = "검색"):
        """단일 뉴스 항목을 N/B 계산 및 저장"""
        try:
            if not self.ai_is_recent_text(text, category) and '오늘' not in keyword:
                log_debug("[저장 건너뜀] 오래된 문장")
                return

            # AI가 텍스트 내용을 보고 카테고리 자동 생성
            ai_category = self.generate_category_from_text(text)
            log_debug(f"[AI 카테고리] {ai_category}")
            
            # N/B 계산
            calculations = self.save_news_nb_calculations([text], category=ai_category)
            if not calculations:
                log_debug("[저장 실패] N/B 계산 결과 없음")
                return

            calc = calculations[0]
            results = calc.get('results', [])
            if not results:
                log_debug("[저장 실패] N/B 결과 없음")
                return

            nb_max = results[0].get('nb_max', 0)
            nb_min = results[0].get('nb_min', 0)
            timestamp = calc.get('timestamp', '')

            # 저장 결과 메시지 표시
            result_msg = f"\n💾 저장 완료:\n#{keyword}\n{text[:100]}\n[{timestamp}] MAX: {nb_max} MIN: {nb_min}\n"
            self.root.after(0, self.display_message, "system", result_msg)
            
            log_debug(f"[저장 성공] {keyword} - MAX: {nb_max} MIN: {nb_min}")
        except Exception as e:
            log_debug(f"[저장 오류] save_news_result 실패: {e}")

    def build_search_page_summary_text(self, keyword: str) -> str:
        pages = [
            {
                'source': 'Naver Web',
                'url': search_naver(keyword, 'web')
            },
            {
                'source': 'Naver News',
                'url': search_naver(keyword, 'news')
            },
            {
                'source': 'Bing Web',
                'url': search_bing(keyword, 'web')
            }
        ]

        for page in pages:
            page['content'] = self.fetch_search_page_text(page['url'])

        summary = self.summarize_search_pages(keyword, pages)

        today = datetime.now().strftime("%Y년 %m월 %d일")
        results_text = f"\n📄 검색 페이지 요약 [{today}]\n" + "─" * 60 + "\n"
        results_text += summary.strip() + "\n"
        results_text += "\n🔗 참고 URL\n" + "─" * 60 + "\n"
        for page in pages:
            results_text += f"• {page['source']}: {page['url']}\n"

        return results_text
    
    def handle_search_command(self, command):
        """검색 명령어 처리"""
        self.is_generating = True
        self.send_btn.config(state=tk.DISABLED, text="검색 중...")
        
        # 백그라운드에서 검색 실행
        Thread(target=self.execute_search, args=(command,), daemon=True).start()
    
    def execute_search(self, command):
        """검색 실행 - 다양한 검색 엔진 지원"""
        try:
            # 명령어 파싱
            if command.startswith('/네이버 '):
                keyword = command.replace('/네이버 ', '', 1).strip()
                search_type = 'naver'
            elif command.startswith('/빙 '):
                keyword = command.replace('/빙 ', '', 1).strip()
                search_type = 'bing'
            elif command.startswith('/뉴스 '):
                keyword = command.replace('/뉴스 ', '', 1).strip()
                search_type = 'news'
            elif command.startswith('/유튜브 '):
                keyword = command.replace('/유튜브 ', '', 1).strip()
                search_type = 'youtube'
            else:  # /검색 (다중 검색)
                keyword = command.replace('/검색 ', '', 1).strip()
                search_type = 'multi'
            
            if not keyword:
                self.root.after(0, self.display_message, "system", "❌ 검색어를 입력해주세요.")
                return
            
            results_text = f"\n🔍 '{keyword}' 검색 결과:\n"
            results_text += "━" * 60 + "\n"
            
            # 다중 검색 (네이버 + Bing + 뉴스)
            if search_type == 'multi':
                self.root.after(0, self.display_message, "system", "🔍 검색 페이지 다운로드 중 (네이버, Bing, 뉴스)...")
                results_text += self.build_search_page_summary_text(keyword)
            
            # 개별 검색 - 네이버
            elif search_type == 'naver':
                self.root.after(0, self.display_message, "system", "📰 네이버 뉴스 검색 중...")
                news_results = get_naver_results(keyword, 'news', limit=5)
                
                if news_results:
                    results_text += "\n📰 네이버 뉴스\n" + "─" * 60 + "\n"
                    results_text += format_search_results(news_results)
                else:
                    results_text += "\n📝 검색 결과 없음\n"
            
            # 개별 검색 - Bing (Selenium 드라이버 사용)\n            elif search_type == 'bing':\n                self.root.after(0, self.display_message, "system", "🌐 Bing 검색 중 (Chrome 드라이버 사용)...\")\n                bing_results = get_bing_results_smart(keyword, 'web', limit=5, use_selenium=True)\n                \n                if bing_results:\n                    results_text += "\n🌐 Bing 검색 결과\n" + "─" * 60 + "\n"\n                    results_text += format_bing_results(bing_results)\n                else:\n                    results_text += "\n⚠️ 검색 결과 없음\n"
            
            # 개별 검색 - 뉴스 (Selenium 기반)
            elif search_type == 'news':
                self.root.after(0, self.display_message, "system", "📰 뉴스 검색 중 (Selenium 크롤링)...")
                news_results = get_naver_news_smart(keyword, limit=5, use_selenium=True)
                # 뉴스 결과 그대로 사용 (필터링은 이후 AI 단계에서 처리)
                
                if news_results:
                    results_text += "\n📰 뉴스 검색 결과\n" + "─" * 60 + "\n"
                    for i, result in enumerate(news_results, 1):
                        results_text += f"\n{i}. {result.get('title', 'N/A')}\n"
                        if result.get('date'):
                            results_text += f"   📅 {result['date']}\n"
                        if result.get('description'):
                            results_text += f"   📝 {result['description'][:100]}\n"
                        if result.get('url'):
                            results_text += f"   🔗 {result['url'][:80]}\n"
                else:
                    results_text += "\n⚠️ 오늘 뉴스 없음\n"
            
            # 개별 검색 - 유튜브
            elif search_type == 'youtube':
                self.root.after(0, self.display_message, "system", "📺 유튜브 검색 중...")
                youtube_results = get_youtube_results(keyword, limit=3)
                
                if youtube_results:
                    results_text += "\n📺 유튜브 검색\n" + "─" * 60 + "\n"
                    results_text += format_youtube_results(youtube_results)
            
            results_text += "\n" + "━" * 60 + "\n"
            
            # 결과 표시
            self.chat_history.append({"role": "assistant", "content": results_text})
            self.root.after(0, self.display_message, "assistant", results_text)
            
            # 자동 저장
            self.root.after(100, self.save_chat)
            
        except Exception as e:
            error_msg = f"❌ 검색 오류: {e}"
            log_debug(f"[오류] execute_search: {e}")
            self.root.after(0, self.display_message, "system", error_msg)
        finally:
            self.is_generating = False
            self.root.after(0, lambda: self.send_btn.config(state=tk.NORMAL, text="전송"))
    
    def generate_response(self, prompt):
        """AI 응답 생성"""
        try:
            data = self._ollama_generate(prompt, timeout=120)
            reply = data.get('response', '응답을 생성할 수 없습니다.')
            
            self.chat_history.append({"role": "assistant", "content": reply})
            self.root.after(0, self.display_message, "assistant", reply)
            
            # 자동 저장
            self.root.after(100, self.save_chat)
            
        except Exception as e:
            error_msg = f"오류가 발생했습니다: {e}"
            self.root.after(0, self.display_message, "system", error_msg)
        finally:
            self.is_generating = False
            self.root.after(0, lambda: self.send_btn.config(state=tk.NORMAL, text="전송"))
    
    def save_chat(self):
        """대화 저장"""
        if not self.chat_history:
            return
        
        # 기존 파일이 있으면 덮어쓰기, 없으면 새로 생성
        if self.current_chat_file:
            filename = self.current_chat_file
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(HISTORY_DIR, f"chat_{timestamp}.json")
        
        data = {
            "model": self.current_model,
            "timestamp": datetime.now().isoformat(),
            "messages": self.chat_history
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        self.current_chat_file = filename
        self.display_message("system", f"💾 대화 저장: {os.path.basename(filename)}")
        
        # 히스토리 목록 새로고침
        self.load_history_list()
    
    def on_closing(self):
        """창 닫기"""
        if self.chat_history:
            if messagebox.askyesno("종료", "대화를 저장하시겠습니까?"):
                self.save_chat()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = OllamaIDE(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
