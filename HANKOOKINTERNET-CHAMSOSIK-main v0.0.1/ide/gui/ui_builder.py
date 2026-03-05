"""
UI 빌더 - tkinter UI 구성
"""

import tkinter as tk
from tkinter import ttk
from .config import COLORS, CATEGORIES, WELCOME_MESSAGE


class UIBuilder:
    """UI 생성 및 관리"""
    
    @staticmethod
    def create_main_ui(root, callbacks):
        """메인 UI 생성
        
        Args:
            root: Tkinter root window
            callbacks: 콜백 함수 딕셔너리
                - on_history_select: 대화 선택
                - on_model_change: 모델 변경
                - new_chat: 새 대화
                - on_enter_key: Enter 키
                - send_message: 메시지 전송
                - add_favorite: 즐겨찾기 추가
                - use_favorite: 즐겨찾기 사용
                - remove_favorite: 즐겨찾기 제거
        
        Returns:
            dict: UI 위젯 딕셔너리
        """
        widgets = {}
        
        # 스크롤바 스타일 설정
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("Vertical.TScrollbar",
                       background=COLORS['bg_light'],
                       darkcolor=COLORS['bg_medium'],
                       lightcolor='#475569',
                       troughcolor=COLORS['bg_medium'],
                       bordercolor=COLORS['bg_medium'],
                       arrowcolor=COLORS['text_secondary'])
        
        style.map("Vertical.TScrollbar",
                 background=[('active', '#475569'), ('!active', COLORS['bg_light'])])
        
        # 메인 컨테이너
        main_container = tk.Frame(root, bg=COLORS['bg_dark'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 왼쪽 사이드바 (대화 히스토리)
        sidebar = UIBuilder._create_sidebar(main_container, callbacks)
        widgets['history_listbox'] = sidebar['history_listbox']
        
        # 오른쪽 채팅 영역
        chat_widgets = UIBuilder._create_chat_area(main_container, callbacks)
        widgets.update(chat_widgets)
        
        return widgets
    
    @staticmethod
    def _create_sidebar(parent, callbacks):
        """사이드바 생성"""
        sidebar = tk.Frame(parent, bg=COLORS['bg_medium'], width=280)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # 헤더
        header = tk.Frame(sidebar, bg=COLORS['bg_light'], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="💬 대화 기록",
            bg=COLORS['bg_light'],
            fg=COLORS['accent'],
            font=("Arial", 12, "bold")
        ).pack(pady=15)
        
        # 대화 목록
        history_frame = tk.Frame(sidebar, bg=COLORS['bg_medium'])
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        history_listbox = tk.Listbox(
            history_frame,
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            font=("Arial", 9),
            relief=tk.FLAT,
            selectbackground=COLORS['bg_light'],
            selectforeground=COLORS['accent'],
            activestyle="none",
            highlightthickness=0,
            borderwidth=0
        )
        history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_listbox.bind("<<ListboxSelect>>", callbacks['on_history_select'])
        
        scrollbar = ttk.Scrollbar(
            history_frame,
            command=history_listbox.yview,
            style="Vertical.TScrollbar"
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        history_listbox.config(yscrollcommand=scrollbar.set)
        
        return {'history_listbox': history_listbox}
    
    @staticmethod
    def _create_chat_area(parent, callbacks):
        """채팅 영역 생성"""
        widgets = {}
        
        chat_container = tk.Frame(parent, bg=COLORS['bg_dark'])
        chat_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 상단 바
        top_widgets = UIBuilder._create_top_bar(chat_container, callbacks)
        widgets.update(top_widgets)
        
        # 채팅 디스플레이
        chat_widgets = UIBuilder._create_chat_display(chat_container)
        widgets.update(chat_widgets)
        
        # 즐겨찾기 버튼
        fav_widgets = UIBuilder._create_favorites_area(chat_container, callbacks)
        widgets.update(fav_widgets)
        
        # 입력 영역
        input_widgets = UIBuilder._create_input_area(chat_container, callbacks)
        widgets.update(input_widgets)
        
        return widgets
    
    @staticmethod
    def _create_top_bar(parent, callbacks):
        """상단 바 생성"""
        widgets = {}
        
        top_frame = tk.Frame(parent, bg=COLORS['bg_medium'])
        top_frame.pack(fill=tk.X, padx=0, pady=0)
        
        # 제목 줄
        title_frame = tk.Frame(top_frame, bg=COLORS['bg_medium'], height=50)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(
            title_frame,
            text="🤖 Ollama IDE",
            bg=COLORS['bg_medium'],
            fg=COLORS['accent'],
            font=("Arial", 16, "bold")
        ).pack(side=tk.LEFT, padx=20, pady=10)
        
        # 모델 선택
        model_frame = tk.Frame(title_frame, bg=COLORS['bg_medium'])
        model_frame.pack(side=tk.RIGHT, padx=20, pady=10)
        
        tk.Label(
            model_frame,
            text="모델:",
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        model_var = tk.StringVar()
        model_combo = ttk.Combobox(
            model_frame,
            textvariable=model_var,
            state="readonly",
            width=20,
            font=("Arial", 10)
        )
        model_combo.pack(side=tk.LEFT, padx=5)
        model_combo.bind("<<ComboboxSelected>>", callbacks['on_model_change'])
        
        widgets['model_var'] = model_var
        widgets['model_combo'] = model_combo
        
        # 새 대화 버튼
        new_chat_btn = tk.Button(
            model_frame,
            text="+ 새 대화",
            bg=COLORS['accent'],
            fg=COLORS['black'],
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=5,
            cursor="hand2",
            command=callbacks['new_chat']
        )
        new_chat_btn.pack(side=tk.LEFT, padx=10)
        
        # 카테고리 선택
        category_frame = tk.Frame(top_frame, bg=COLORS['bg_medium'], height=45)
        category_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        category_frame.pack_propagate(False)
        
        tk.Label(
            category_frame,
            text="카테고리:",
            bg=COLORS['bg_medium'],
            fg=COLORS['text_secondary'],
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        category_var = tk.StringVar(value="all")
        for label, value in CATEGORIES:
            tk.Radiobutton(
                category_frame,
                text=label,
                variable=category_var,
                value=value,
                bg=COLORS['bg_medium'],
                fg=COLORS['text_primary'],
                selectcolor=COLORS['accent'],
                font=("Arial", 9),
                relief=tk.FLAT,
                cursor="hand2",
                padx=8,
                pady=4,
                bd=0
            ).pack(side=tk.LEFT, padx=2)
        
        widgets['category_var'] = category_var
        
        return widgets
    
    @staticmethod
    def _create_chat_display(parent):
        """채팅 디스플레이 생성"""
        widgets = {}
        
        chat_frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        chat_display = tk.Text(
            chat_frame,
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            font=("Arial", 11),
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=15,
            pady=15,
            insertbackground=COLORS['accent'],
            borderwidth=0,
            highlightthickness=0
        )
        chat_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(
            chat_frame,
            command=chat_display.yview,
            style="Vertical.TScrollbar"
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        chat_display.config(yscrollcommand=scrollbar.set)
        chat_display.config(state=tk.DISABLED)
        
        # 태그 설정
        chat_display.tag_config("user", foreground=COLORS['accent_blue'], font=("Arial", 11, "bold"))
        chat_display.tag_config("assistant", foreground=COLORS['accent'], font=("Arial", 11, "bold"))
        chat_display.tag_config("user_msg", foreground=COLORS['text_primary'])
        chat_display.tag_config("assistant_msg", foreground=COLORS['text_primary'])
        chat_display.tag_config("system", foreground=COLORS['text_tertiary'], font=("Arial", 10, "italic"))
        chat_display.tag_config("system_detail", foreground=COLORS['accent_cyan'], font=("Arial", 10, "underline"))
        
        widgets['chat_display'] = chat_display
        
        # 초기 메시지
        chat_display.config(state=tk.NORMAL)
        chat_display.insert(tk.END, f"\n{WELCOME_MESSAGE}\n", "system")
        chat_display.config(state=tk.DISABLED)
        
        return widgets
    
    @staticmethod
    def _create_favorites_area(parent, callbacks):
        """즐겨찾기 영역 생성"""
        widgets = {}
        
        favorites_frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        favorites_frame.pack(fill=tk.X, padx=20, pady=(0, 5))
        
        tk.Label(
            favorites_frame,
            text="⭐ 즐겨찾기:",
            bg=COLORS['bg_dark'],
            fg=COLORS['text_tertiary'],
            font=("Arial", 9)
        ).pack(side=tk.LEFT, padx=5)
        
        favorites_buttons_frame = tk.Frame(favorites_frame, bg=COLORS['bg_dark'])
        favorites_buttons_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        widgets['favorites_buttons_frame'] = favorites_buttons_frame
        
        # 추가 버튼
        add_fav_btn = tk.Button(
            favorites_frame,
            text="+ 추가",
            bg=COLORS['bg_light'],
            fg=COLORS['text_secondary'],
            font=("Arial", 9),
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor="hand2",
            command=callbacks['add_favorite']
        )
        add_fav_btn.pack(side=tk.RIGHT, padx=5)
        
        return widgets
    
    @staticmethod
    def _create_input_area(parent, callbacks):
        """입력 영역 생성"""
        widgets = {}
        
        input_frame = tk.Frame(parent, bg=COLORS['bg_dark'])
        input_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        input_text = tk.Text(
            input_frame,
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary'],
            font=("Arial", 11),
            height=3,
            relief=tk.FLAT,
            padx=10,
            pady=10,
            insertbackground=COLORS['accent']
        )
        input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        input_text.bind("<Return>", callbacks['on_enter_key'])
        input_text.bind("<Shift-Return>", lambda e: None)
        
        widgets['input_text'] = input_text
        
        send_btn = tk.Button(
            input_frame,
            text="전송",
            bg=COLORS['accent'],
            fg=COLORS['black'],
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            width=10,
            cursor="hand2",
            command=callbacks['send_message']
        )
        send_btn.pack(side=tk.RIGHT)
        
        widgets['send_btn'] = send_btn
        
        return widgets
