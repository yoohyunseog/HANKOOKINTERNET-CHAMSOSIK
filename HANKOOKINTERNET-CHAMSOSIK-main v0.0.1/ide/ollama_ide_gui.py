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
from datetime import datetime, timedelta
from threading import Thread
import glob
import re
import html
import subprocess
import webbrowser
import random
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
        
        # 즐겨찾기 명령어
        self.favorites = []
        self.favorites_file = os.path.join(HISTORY_DIR, 'favorites.json')
        
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

    def format_news_answer(self, answer: str) -> str:
        if not answer:
            return answer
        text = answer.replace(' // ', '\n')
        text = re.sub(r'(\s*)(\d+️⃣|\d+\.|\d+\))', lambda m: '\n' + m.group(2), text)
        if text.strip().startswith('-'):
            text = re.sub(r'\s-\s+', '\n- ', text)
        text = re.sub(r'\s+-\s+(?=\*\*)', '\n- ', text)
        return text.strip()

    def extract_news_items(self, answer: str) -> list:
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

    def is_today_news_date(self, date_text: str) -> bool:
        if not date_text:
            return False

        text = date_text.strip().lower()

        if '방금' in text or '초 전' in text or '분 전' in text or '시간 전' in text:
            return True
        if '오늘' in text:
            return True
        if '어제' in text:
            return False

        days_ago = re.search(r'(\d+)\s*일\s*전', text)
        if days_ago:
            return days_ago.group(1) == '0'

        today = datetime.now().date()
        for fmt in ("%Y.%m.%d", "%Y-%m-%d", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(text[:10], fmt).date()
                return dt == today
            except ValueError:
                pass

        m = re.search(r'(\d{1,2})[./-](\d{1,2})', text)
        if m:
            month = int(m.group(1))
            day = int(m.group(2))
            try:
                dt = datetime(today.year, month, day).date()
                return dt == today
            except ValueError:
                return False

        return False

    def filter_today_news_items(self, items: list) -> list:
        if not items:
            return []
        return [item for item in items if self.is_today_news_date(item.get('date', ''))]

    def is_today_news_text(self, text: str) -> bool:
        if not text:
            return False

        cleaned = text.strip().lower()

        if '방금' in cleaned or '초 전' in cleaned or '분 전' in cleaned or '시간 전' in cleaned:
            return True
        if '오늘' in cleaned:
            return True
        if '어제' in cleaned:
            return False

        days_ago = re.search(r'(\d+)\s*일\s*전', cleaned)
        if days_ago:
            return days_ago.group(1) == '0'

        today = datetime.now().date()
        for fmt in ("%Y.%m.%d", "%Y-%m-%d", "%Y/%m/%d"):
            for match in re.finditer(r'\d{4}[./-]\d{1,2}[./-]\d{1,2}', cleaned):
                try:
                    dt = datetime.strptime(match.group(0), fmt).date()
                    return dt == today
                except ValueError:
                    continue

        for match in re.finditer(r'(\d{1,2})[./-](\d{1,2})', cleaned):
            month = int(match.group(1))
            day = int(match.group(2))
            try:
                dt = datetime(today.year, month, day).date()
                return dt == today
            except ValueError:
                continue

        return False

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
            return not self.is_text_stale_by_date(text, category)

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
            ("비트코인", "비트코인"),
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
        
        # 즐겨찾기 명령어 버튼 영역
        favorites_frame = tk.Frame(chat_container, bg="#0f172a")
        favorites_frame.pack(fill=tk.X, padx=20, pady=(0, 5))
        
        tk.Label(
            favorites_frame,
            text="⭐ 즐겨찾기:",
            bg="#0f172a",
            fg="#64748b",
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)
        
        self.favorites_buttons_frame = tk.Frame(favorites_frame, bg="#0f172a")
        self.favorites_buttons_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 즐겨찾기 추가 버튼
        add_fav_btn = tk.Button(
            favorites_frame,
            text="+ 추가",
            bg="#334155",
            fg="#94a3b8",
            font=("Arial", 9),
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self.add_favorite
        )
        add_fav_btn.pack(side=tk.RIGHT, padx=5)
        
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

⭐ 즐겨찾기:
    • 입력 후 [+ 추가] 버튼 클릭하여 저장
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
                self.model_combo.current(0)
                self.current_model = models[0]
                self.display_message("system", f"✅ 모델 로드 완료: {self.current_model}")
            else:
                messagebox.showerror("오류", "사용 가능한 모델이 없습니다.")
        except Exception as e:
            messagebox.showerror("연결 오류", f"Ollama에 연결할 수 없습니다.\n{e}")
    
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
        """즐겨찾기 버튼 업데이트"""
        # 기존 버튼 제거
        for widget in self.favorites_buttons_frame.winfo_children():
            widget.destroy()
        
        # 버튼 생성 (최대 6개)
        for idx, fav in enumerate(self.favorites[:6]):
            btn = tk.Button(
                self.favorites_buttons_frame,
                text=fav[:30] + "..." if len(fav) > 30 else fav,
                bg="#334155",
                fg="#e2e8f0",
                font=("Arial", 9),
                relief=tk.FLAT,
                padx=10,
                pady=3,
                cursor="hand2",
                command=lambda f=fav: self.use_favorite(f)
            )
            btn.pack(side=tk.LEFT, padx=2)
            
            # 우클릭으로 삭제
            btn.bind("<Button-3>", lambda e, f=fav: self.remove_favorite(f))
    
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

    def process_user_message(self, message: str, force_search: bool = False) -> bool:
        """사용자 메시지를 처리하고 응답 생성까지 수행"""
        if not message or self.is_generating:
            return False

        if not self.current_model:
            messagebox.showwarning("경고", "모델을 선택해주세요.")
            return False

        # 사용자 메시지 표시
        self.display_message("user", message)
        self.chat_history.append({"role": "user", "content": message})

        # 반복 명령어 처리
        if self.handle_trend_batch_command(message):
            return True

        if self.handle_repeat_command(message):
            return True

        # 수동 검색 명령어 처리
        if message.startswith('/검색 ') or message.startswith('/네이버 ') or message.startswith('/빙 ') or message.startswith('/뉴스 ') or message.startswith('/유튜브 '):
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

    def parse_extra_keywords(self, raw: str) -> list:
        if not raw:
            return []
        parts = [p.strip() for p in raw.split(',')]
        return [p for p in parts if p]

    def load_trend_keywords_from_file(self) -> list:
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

        lists = data.get('detailed_data', {}).get('lists', [])
        keywords = []
        seen = set()

        for group in lists:
            if not isinstance(group, list):
                continue
            for entry in group:
                if not isinstance(entry, str):
                    continue
                raw = entry.strip()
                if not raw or raw in nav_items:
                    continue
                if '\n' in raw:
                    raw = raw.split('\n', 1)[0].strip()
                keyword = raw
                if not keyword or keyword in seen:
                    continue
                seen.add(keyword)
                keywords.append(keyword)

        if keywords:
            # 키워드를 랜덤하게 섞기
            random.shuffle(keywords)
            line = ', '.join(keywords)
            self.display_message("system", f"✅ 트렌드 키워드 {len(keywords)}개 정리 완료 (랜덤 순서)")
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
                
                final_prompt = f"""다음 검색 결과를 바탕으로 사용자의 질문에 답변하세요.

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
                final_prompt = f"""사용자의 질문에 간단하고 정확하게 답변하세요.

질문: {user_prompt}

지시사항:
- 간결하고 이해하기 쉽게
- 과도한 이모지나 특수문자 제거
- 200자 이내로 작성

답변:"""
            
            log_debug(f"Sending prompt to Ollama...")
            final_response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": self.current_model,
                    "prompt": final_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.6,
                        "num_predict": 2000,
                        "top_k": 40,
                        "top_p": 0.9
                    }
                },
                timeout=180
            )
            final_response.raise_for_status()
            final_json = final_response.json()
            log_debug(f"Response received: {final_json}")
            final_answer = final_json.get('response', '').strip()
            log_debug(f"Final answer: '{final_answer}'")
            final_answer = clean_text_simple(final_answer)

            # 뉴스형 응답 줄바꿈 및 저장
            final_answer = self.format_news_answer(final_answer)
            if self.is_news_query(user_prompt, final_answer):
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
                news_items = self.filter_today_news_items(search_results['news'])
                if not news_items:
                    search_results['news'] = []
                else:
                    search_results['news'] = news_items

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

        prompt = (
            "다음은 검색 결과 페이지에서 추출한 텍스트입니다.\n"
            "검색된 뉴스와 정보를 읽고, 주요 소식들을 간결한 문장으로 정리하세요.\n\n"
            "지시사항:\n"
            "1. 검색 결과에서 실제 뉴스 제목과 내용만 추출하세요\n"
            "2. 각 소식을 1-2개 문장으로 간결하게 요약하세요\n"
            "3. UI 요소(버튼, 메뉴, 검색옵션 등)는 무시하세요\n"
            "4. 형식: '주제 - 내용입니다' 또는 '주제: 내용입니다'\n"
            "5. 최대 5-8개 주요 소식만 선별하세요\n"
            "6. 각 소식 앞에 번호를 붙이지 마세요 (•나 - 사용)\n"
            "7. **반드시 한국어로 요약하세요**\n\n"
            f"검색어: {keyword}\n\n" + "\n\n".join(chunks) +
            "\n\n위 검색 결과에서 주요 소식만 간결한 문장으로 한국어로 정리:"
        )

        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": self.current_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )
            response.raise_for_status()
            data = response.json()
            return data.get('response', '응답을 생성할 수 없습니다.')
        except Exception as e:
            log_debug(f"[요약 오류] {e}")
            return f"요약 중 오류가 발생했습니다: {str(e)[:120]}"

    def generate_category_from_text(self, text: str) -> str:
        """AI가 텍스트 내용을 분석해서 카테고리 생성"""
        try:
            prompt = f"""다음 텍스트를 읽고 가장 적절한 카테고리를 한 단어로 답변하세요.
카테고리 예시:비트코인, 정치, 경제, 사회, 문화, 게임, 드라마, 영화, 애니메이션, 괴물딴지, 스포츠, 기술, 국제, 연예, 사건사고, 건강, 교육

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
            
            # 깔끔하게 정리 (첫 줄만, 특수문자 제거)
            category = category.split('\n')[0].strip()
            category = re.sub(r'[^\w가-힣]', '', category)
            
            return category if category else "일반"
        except Exception as e:
            log_debug(f"[카테고리 생성 오류] {e}")
            return "일반"

    def filter_recent_news_by_ai(self, summary_text: str, category: str = "검색") -> list:
        """AI가 요약을 카테고리에 따라 다르게 필터링
        
        카테고리별 규칙:
        - 정치, 경제: 무조건 오늘자 뉴스만
        - 사회, 문화, 게임, 드라마, 영화, 애니메이션, 스포츠: 오늘자 뉴스 필수
        - 괴물딴지, 기술: 과거 데이터도 상관없음 (내용의 과거 날짜만 제외)
        """
        try:
            today = datetime.now().strftime("%Y년 %m월 %d일")
            
            # 카테고리별 필터링 규칙 결정
            must_be_today = category in ["정치", "경제"]
            prefer_today = category in ["사회", "문화", "게임", "드라마", "영화", "애니메이션", "스포츠"]
            no_date_limit = category in ["괴물딴지", "기술"]
            
            if must_be_today:
                # 정치, 경제: 무조건 오늘자 뉴스만
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
                # 사회, 문화, 게임, 드라마 등: 오늘 뉴스 우선, 최근(1주일) 정보는 가능
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
            
            else:  # no_date_limit - 괴물딴지, 기술
                # 과거 데이터 괜찮음, 하지만 명시된 과거 날짜는 확인
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
            
            # 필터링된 결과를 항목으로 파싱
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
                
                # 의미있는 길이 확인
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
            self.display_message("system", f"🤖 AI가 요약을 분석 중... (카테고리: {category}, 오늘: {today_text})")
            
            # AI가 요약을 분석해서 카테고리에 맞게 필터링
            news_items = self.filter_recent_news_by_ai(summary_text, category)

            if not news_items:
                log_debug("[저장 건너뜀] 오늘 또는 최근 뉴스 항목 없음")
                self.display_message("system", "⏭️ 최근 뉴스가 없어 저장을 건너뜁니다")
                return

            # 각 뉴스 문장마다 웹뷰/브라우저에서 database.html 열기
            log_debug(f"[뉴스 저장] {len(news_items)}개 항목을 웹뷰로 저장 시작")
            self.display_message("system", f"💾 {len(news_items)}개 뉴스 항목 저장 시작...")
            
            for idx, item in enumerate(news_items[:8], 1):  # 최대 8개
                try:
                    if not self.ai_is_recent_text(item, category):
                        log_debug(f"[저장 건너뜀] 오래된 문장: {item[:50]}...")
                        self.display_message("system", f"⏭️ 오래된 문장 건너뜀: {item[:40]}...")
                        continue
                    # AI가 텍스트 내용을 보고 카테고리 자동 생성
                    ai_category = self.generate_category_from_text(item)
                    log_debug(f"[{idx}] AI 생성 카테고리: {ai_category}")
                    
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
                news_results = self.filter_today_news_items(news_results)
                
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
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": self.current_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=120
            )
            response.raise_for_status()
            data = response.json()
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
