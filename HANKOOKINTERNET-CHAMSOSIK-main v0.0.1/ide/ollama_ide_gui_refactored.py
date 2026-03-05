"""
Ollama IDE - GUI 버전 (리팩토링됨)
모듈화된 구조로 유지보수성 향상
"""

import tkinter as tk
from tkinter import messagebox
import requests
import json
import os
import glob
import re
import time
from datetime import datetime
from threading import Thread
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# GUI 모듈 import
from gui.config import (
    OLLAMA_URL, HISTORY_DIR, FAVORITES_FILE, DEFAULT_FAVORITES
)
from gui.utils import (
    log_debug, clean_text_simple, format_news_answer,
    extract_news_items, is_news_query
)
from gui.news_manager import NewsManager, DateHelper
from gui.search_handler import SearchHandler
from gui.ai_handler import AIHandler
from gui.repeat_manager import RepeatManager, BatchManager
from gui.ui_builder import UIBuilder


class OllamaIDE:
    """Ollama IDE 메인 클래스"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama IDE - GPT 같은 채팅")
        self.root.geometry("1200x700")
        self.root.configure(bg="#0f172a")
        
        # 상태 변수
        self.current_model = None
        self.chat_history = []
        self.is_generating = False
        self.current_chat_file = None
        self.chat_files = []
        self.favorites = []
        
        # 상세 로그 관리
        self.detail_logs = {}
        self.detail_tag_map = {}
        self.detail_tag_count = 0
        
        # 매니저 초기화
        self.news_manager = NewsManager(notify_callback=self.display_message)
        self.ai_handler = AIHandler()
        self.search_handler = SearchHandler(ai_handler=self.ai_handler)
        self.repeat_manager = RepeatManager()
        self.batch_manager = BatchManager()
        
        # UI 구성
        self.setup_ui()
        
        # 초기화
        self.load_models()
        self.load_history_list()
        self.load_favorites()
    
    def setup_ui(self):
        """UI 설정"""
        callbacks = {
            'on_history_select': self.on_history_select,
            'on_model_change': self.on_model_change,
            'new_chat': self.new_chat,
            'on_enter_key': self.on_enter_key,
            'send_message': self.send_message,
            'add_favorite': self.add_favorite,
            'use_favorite': self.use_favorite,
            'remove_favorite': self.remove_favorite
        }
        
        widgets = UIBuilder.create_main_ui(self.root, callbacks)
        
        # 위젯 참조 저장
        self.history_listbox = widgets['history_listbox']
        self.model_var = widgets['model_var']
        self.model_combo = widgets['model_combo']
        self.category_var = widgets['category_var']
        self.chat_display = widgets['chat_display']
        self.favorites_buttons_frame = widgets['favorites_buttons_frame']
        self.input_text = widgets['input_text']
        self.send_btn = widgets['send_btn']
    
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
                self.ai_handler.set_model(self.current_model)
                self.display_message("system", f"✅ 모델 로드 완료: {self.current_model}")
            else:
                messagebox.showerror("오류", "사용 가능한 모델이 없습니다.")
        except Exception as e:
            messagebox.showerror("연결 오류", f"Ollama에 연결할 수 없습니다.\n{e}")
    
    def load_history_list(self):
        """대화 히스토리 목록 로드"""
        self.history_listbox.delete(0, tk.END)
        
        chat_files = sorted(
            glob.glob(os.path.join(HISTORY_DIR, "chat_*.json")),
            key=os.path.getmtime,
            reverse=True
        )
        
        for filepath in chat_files[:50]:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                filename = os.path.basename(filepath)
                date_str = filename.replace("chat_", "").replace(".json", "")
                
                try:
                    dt = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                    date_display = dt.strftime("%m/%d %H:%M")
                except:
                    date_display = date_str[:10]
                
                messages = data.get('messages', [])
                first_msg = ""
                for msg in messages:
                    if msg.get('role') == 'user':
                        content = msg.get('content', '')
                        first_msg = content[:30] + "..." if len(content) > 30 else content
                        break
                
                if not first_msg:
                    first_msg = "빈 대화"
                
                msg_count = len(messages)
                model = data.get('model', 'N/A')
                
                display_text = f"📅 {date_display}\n💬 {first_msg}\n📊 {msg_count}개 | {model[:15]}"
                self.history_listbox.insert(tk.END, display_text)
                
            except Exception as e:
                log_debug(f"Error loading {filepath}: {e}")
        
        self.chat_files = chat_files[:50]
    
    def on_history_select(self, event):
        """대화 선택"""
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
            
            self.chat_history = data.get('messages', [])
            self.current_model = data.get('model', self.current_model)
            self.current_chat_file = filepath
            
            if self.current_model in self.model_combo['values']:
                self.model_var.set(self.current_model)
                self.ai_handler.set_model(self.current_model)
            
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.config(state=tk.DISABLED)
            
            for msg in self.chat_history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                self.display_message(role, content)
            
            self.display_message("system", f"💾 대화 불러옴: {os.path.basename(filepath)}")
            
        except Exception as e:
            messagebox.showerror("오류", f"대화를 불러올 수 없습니다.\n{e}")
    
    def on_model_change(self, event):
        """모델 변경"""
        self.current_model = self.model_var.get()
        self.ai_handler.set_model(self.current_model)
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
        """상세 로그 링크가 있는 시스템 메시지 표시"""
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
    
    def show_detail_log(self, key: str):
        """상세 로그 표시"""
        lines = self.news_manager.detail_logs.get(key, [])
        if not lines:
            messagebox.showinfo("상세 로그", "기록된 상세 로그가 없습니다.")
            return
        messagebox.showinfo("상세 로그", "\n".join(lines))
    
    def load_favorites(self):
        """즐겨찾기 로드"""
        try:
            if os.path.exists(FAVORITES_FILE):
                with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
                    self.favorites = json.load(f)
            else:
                self.favorites = DEFAULT_FAVORITES.copy()
                self.save_favorites()
            
            self.update_favorites_buttons()
        except Exception as e:
            log_debug(f"[즐겨찾기 로드 오류] {e}")
            self.favorites = []
    
    def save_favorites(self):
        """즐겨찾기 저장"""
        try:
            with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_debug(f"[즐겨찾기 저장 오류] {e}")
    
    def update_favorites_buttons(self):
        """즐겨찾기 버튼 업데이트"""
        for widget in self.favorites_buttons_frame.winfo_children():
            widget.destroy()
        
        for fav in self.favorites[:6]:
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
    
    def on_enter_key(self, event):
        """Enter 키 처리"""
        if not event.state & 0x1:
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
        
        self.input_text.delete(1.0, tk.END)
        self.process_user_message(message)
    
    def process_user_message(self, message: str, force_search: bool = False) -> bool:
        """사용자 메시지 처리"""
        if not message or self.is_generating:
            return False

        if not self.current_model:
            messagebox.showwarning("경고", "모델을 선택해주세요.")
            return False

        # 사용자 메시지 표시
        self.display_message("user", message)
        self.chat_history.append({"role": "user", "content": message})

        # 반복/배치 명령어 처리
        if self.handle_repeat_command(message):
            return True

        if self.handle_trend_batch_command(message):
            return True

        # 수동 검색 명령어
        if message.startswith(('/검색', '/네이버', '/빙', '/뉴스', '/유튜브')):
            self.handle_search_command(message)
            return True

        # AI 응답 생성 (자동 검색 포함)
        self.is_generating = True
        self.send_btn.config(state=tk.DISABLED, text="🤖 생성 중...")
        Thread(target=self.generate_response_with_auto_search, args=(message, force_search), daemon=True).start()
        return True
    
    def handle_repeat_command(self, message: str) -> bool:
        """반복 실행 명령 처리"""
        if message in ('/반복중지', '/중지', '/stop'):
            self.repeat_manager.stop()
            self.batch_manager.stop()
            self.display_message("system", "⏹️ 반복 실행 중단")
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

        self.repeat_manager.start(prompt, count, interval, force_search=(interval == 0))
        
        if count < 0:
            self.display_message("system", f"🔁 반복 실행 시작: 무한, 간격 {interval}초")
        else:
            self.display_message("system", f"🔁 반복 실행 시작: {count}회, 간격 {interval}초")
        
        self.run_repeat_cycle()
        return True
    
    def run_repeat_cycle(self):
        """반복 실행 루프"""
        if not self.repeat_manager.is_active():
            return

        next_task = self.repeat_manager.get_next()
        if not next_task:
            self.repeat_manager.stop()
            self.display_message("system", "✅ 반복 실행 완료")
            return

        if self.is_generating:
            self.root.after(300, self.run_repeat_cycle)
            return

        started = self.process_user_message(
            next_task['message'],
            force_search=next_task['force_search']
        )
        
        if not started:
            self.repeat_manager.stop()
            self.display_message("system", "⚠️ 반복 실행이 중단되었습니다.")
            return

        self.root.after(int(next_task['interval'] * 1000), self.run_repeat_cycle)
    
    def handle_trend_batch_command(self, message: str) -> bool:
        """트렌드 일괄 명령 처리"""
        parsed = BatchManager.parse_trend_batch_command(message)
        if not parsed:
            return False

        interval = parsed['interval']
        if interval < 0.5:
            self.display_message("system", "간격은 0.5초 이상이어야 합니다.")
            return True

        # 키워드 로드
        keywords = self.batch_manager.load_trend_keywords()
        if not keywords:
            self.display_message("system", "트렌드 키워드를 찾을 수 없습니다.")
            return True

        # 추가 키워드
        if parsed.get('extra_keywords'):
            extra = BatchManager.parse_extra_keywords(parsed['extra_keywords'])
            if extra:
                keywords.extend(extra)

        # 키워드 출력
        line = ', '.join(keywords)
        self.display_message("system", line)

        # 배치 시작
        self.repeat_manager.stop()
        self.batch_manager.stop()
        self.batch_manager.start(
            keywords,
            interval,
            search_mode=parsed.get('search_mode', False),
            infinite_loop=parsed.get('infinite', False),
            background=parsed.get('background', False)
        )

        mode_text = "검색 " if parsed.get('search_mode') else ""
        repeat_text = ", 무한 반복" if parsed.get('infinite') else""
        self.display_message("system", f"🧾 트렌드 {mode_text}일괄 실행 시작: {len(keywords)}개, 간격 {interval}초{repeat_text}")
        
        self.run_batch_cycle()
        return True
    
    def run_batch_cycle(self):
        """배치 실행 루프"""
        if not self.batch_manager.is_active():
            return

        next_task = self.batch_manager.get_next()
        if not next_task:
            self.batch_manager.stop()
            self.display_message("system", "✅ 트렌드 일괄 실행 완료")
            return

        if next_task.get('complete'):
            self.batch_manager.stop()
            self.display_message("system", "✅ 트렌드 일괄 실행 완료")
            return

        if next_task.get('restart'):
            self.display_message("system", "🔄 처음부터 다시 시작합니다...")
            self.root.after(int(next_task['interval'] * 1000), self.run_batch_cycle)
            return

        if self.is_generating:
            self.root.after(300, self.run_batch_cycle)
            return

        keyword = next_task['keyword']
        if next_task.get('search_mode'):
            started = self.process_user_message(f"/반복 1 0 {keyword}")
        else:
            started = self.process_user_message(keyword)

        if not started:
            self.batch_manager.stop()
            self.display_message("system", "⚠️ 트렌드 일괄 실행이 중단되었습니다.")
            return

        self.root.after(int(next_task['interval'] * 1000), self.run_batch_cycle)
    
    def handle_search_command(self, command):
        """검색 명령어 처리"""
        self.is_generating = True
        self.send_btn.config(state=tk.DISABLED, text="검색 중...")
        Thread(target=self.execute_search, args=(command,), daemon=True).start()
    
    def execute_search(self, command):
        """검색 실행"""
        try:
            # /검색 명령어는 특별 처리
            if command.startswith('/검색'):
                keyword = command.replace('/검색 ', '', 1).strip()
                if not keyword:
                    self.root.after(0, self.display_message, "system", "❌ 검색어를 입력해주세요.")
                    return
                
                self.root.after(0, self.display_message, "system", "🔍 검색 페이지 다운로드 중...")
                results_text = f"\n🔍 '{keyword}' 검색 결과:\n"
                results_text += "━" * 60 + "\n"
                results_text += self.search_handler.build_search_page_summary_text(keyword, self.current_model)
                results_text += "\n" + "━" * 60 + "\n"
                
                self.chat_history.append({"role": "assistant", "content": results_text})
                self.root.after(0, self.display_message, "assistant", results_text)
                self.root.after(100, self.save_chat)
                
                # 검색 결과 저장
                category = self.category_var.get()
                self.save_search_summary_as_news(keyword, results_text, category=category)
                return
            
            # 기타 검색 명령어
            filter_callback = self.news_manager.filter_today_news_items if command.startswith('/뉴스') else None
            results_text = self.search_handler.execute_manual_search(command, filter_callback)
            
            if not results_text:
                return
            
            self.chat_history.append({"role": "assistant", "content": results_text})
            self.root.after(0, self.display_message, "assistant", results_text)
            self.root.after(100, self.save_chat)
            
        except Exception as e:
            error_msg = f"❌ 검색 오류: {e}"
            log_debug(f"[오류] execute_search: {e}")
            self.root.after(0, self.display_message, "system", error_msg)
        finally:
            self.is_generating = False
            self.root.after(0, lambda: self.send_btn.config(state=tk.NORMAL, text="전송"))
    
    def generate_response_with_auto_search(self, user_prompt, force_search: bool = False):
        """AI 응답 생성 - 자동 검색 기능 포함"""
        try:
            if force_search:
                results_text = f"\n🔍 '{user_prompt}' 검색 결과:\n"
                results_text += "━" * 60 + "\n"
                results_text += self.search_handler.build_search_page_summary_text(user_prompt, self.current_model)
                results_text += "\n" + "━" * 60 + "\n"

                self.chat_history.append({"role": "assistant", "content": results_text})
                self.root.after(0, self.display_message, "assistant", results_text)
                self.root.after(100, self.save_chat)
                
                category = self.category_var.get()
                self.save_search_summary_as_news(user_prompt, results_text, category=category)
                return

            # 검색 필요 여부 판단
            need_search = force_search or self.search_handler.is_search_needed(user_prompt)
            
            log_debug(f"Need search: {need_search}")
            
            if need_search:
                self.root.after(0, self.display_message, "system", "🔍 관련 정보 검색 중...")
                search_keyword = user_prompt.replace('/', '').replace('\\', '').strip()
                search_context = self.search_handler.perform_auto_search(search_keyword)
                
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
                final_prompt = f"""사용자의 질문에 간단하고 정확하게 답변하세요.

질문: {user_prompt}

지시사항:
- 간결하고 이해하기 쉽게
- 과도한 이모지나 특수문자 제거
- 200자 이내로 작성

답변:"""
            
            log_debug("Sending prompt to Ollama...")
            final_answer = self.ai_handler.generate_simple(final_prompt, self.current_model)
            
            if not final_answer or final_answer.strip() == '':
                final_answer = "죄송합니다. 현재 답변을 생성할 수 없습니다."
            
            # 뉴스형 응답 처리
            final_answer = format_news_answer(final_answer)
            if is_news_query(user_prompt, final_answer):
                category = self.category_var.get()
                self.save_news_result(user_prompt, final_answer, category=category)
            
            # 최종 답변 표시
            self.chat_history.append({"role": "assistant", "content": final_answer})
            self.root.after(0, self.display_message, "assistant", final_answer)
            self.root.after(100, self.save_chat)
            
        except Exception as e:
            error_msg = f"오류: {str(e)}"
            log_debug(f"Error: {e}")
            self.root.after(0, self.display_message, "system", error_msg)
        finally:
            self.is_generating = False
            self.root.after(0, lambda: self.send_btn.config(state=tk.NORMAL, text="전송"))
    
    def save_search_summary_as_news(self, keyword: str, summary_text: str, category: str = "검색"):
        """검색 페이지 요약 결과를 뉴스로 저장"""
        try:
            today_text = datetime.now().strftime("%Y년 %m월 %d일")
            self.display_message("system", f"🤖 AI가 요약을 분석 중... (카테고리: {category}, 오늘: {today_text})")
            
            # AI 필터링
            news_items = self.ai_handler.filter_recent_news_by_ai(summary_text, category)

            if not news_items:
                log_debug("[저장 건너뜀] 최근 뉴스 항목 없음")
                self.display_message("system", "⏭️ 최근 뉴스가 없어 저장을 건너뜁니다")
                return

            self.display_message("system", f"💾 {len(news_items)}개 뉴스 항목 저장 시작...")
            
            for idx, item in enumerate(news_items[:8], 1):
                try:
                    if not self.ai_handler.is_recent_text_by_ai(item, category):
                        log_debug(f"[저장 건너뜀] 오래된 문장: {item[:50]}")
                        self.display_message("system", f"⏭️ 오래된 문장 건너뜀: {item[:40]}...")
                        continue
                    
                    ai_category = self.ai_handler.generate_category_from_text(item)
                    log_debug(f"[{idx}] AI 카테고리: {ai_category}")
                    
                    url = f"https://xn--9l4b4xi9r.com/database.html?nb={requests.utils.quote(item)}&category={requests.utils.quote(ai_category)}&end=5s"
                    
                    self.open_url_in_webview(url, auto_close_seconds=5)
                    log_debug(f"[{idx}] 웹뷰 열림: {item[:50]}")
                    time.sleep(0.5)
                except Exception as e:
                    log_debug(f"[{idx}] 열기 실패: {e}")
            
            save_msg = f"\n✅ {len(news_items)}개 뉴스를 저장 완료 (각 5초 후 자동 닫힘)\n"
            self.root.after(0, self.display_message, "system", save_msg)
            
        except Exception as e:
            log_debug(f"[저장 오류] {e}")
            self.display_message("system", f"❌ 저장 오류: {e}")
    
    def save_news_result(self, keyword: str, text: str, category: str = "검색"):
        """뉴스 결과 저장"""
        try:
            if not self.ai_handler.is_recent_text_by_ai(text, category) and '오늘' not in keyword:
                log_debug("[저장 건너뜀] 오래된 문장")
                return

            ai_category = self.ai_handler.generate_category_from_text(text)
            log_debug(f"[AI 카테고리] {ai_category}")
            
            # N/B 계산
            news_items = extract_news_items(text)
            calculations = self.news_manager.save_news_nb_calculations(news_items, category=ai_category)
            
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

            result_msg = f"\n💾 저장 완료:\n#{keyword}\n{text[:100]}\n[{timestamp}] MAX: {nb_max} MIN: {nb_min}\n"
            self.root.after(0, self.display_message, "system", result_msg)
            
            log_debug(f"[저장 성공] {keyword} - MAX: {nb_max} MIN: {nb_min}")
        except Exception as e:
            log_debug(f"[저장 오류] {e}")
    
    def open_url_in_webview(self, url: str, auto_close_seconds: int = 5):
        """Selenium으로 URL 열기"""
        log_debug(f"[Selenium] URL 로드: {url[:100]}")
        
        driver = None
        try:
            options = Options()
            options.add_argument('--window-size=800,600')
            options.add_argument('--window-position=100,100')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            log_debug("[Selenium] Chrome 드라이버 초기화")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            driver.get(url)
            time.sleep(auto_close_seconds)
            driver.quit()
            log_debug("[Selenium] 완료")
            
        except Exception as e:
            log_debug(f"[Selenium 오류] {e}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def save_chat(self):
        """대화 저장"""
        if not self.chat_history:
            return
        
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
        self.load_history_list()
    
    def on_closing(self):
        """창 닫기"""
        if self.chat_history:
            if messagebox.askyesno("종료", "대화를 저장하시겠습니까?"):
                self.save_chat()
        self.root.destroy()


def main():
    """메인 함수"""
    root = tk.Tk()
    app = OllamaIDE(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
