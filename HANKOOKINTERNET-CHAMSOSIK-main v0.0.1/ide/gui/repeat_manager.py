"""
반복 실행 및 일괄 처리 관리
"""

import os
import json
import random
import re
from .config import TREND_DATA_FILE, NAV_ITEMS
from .utils import log_debug


class RepeatManager:
    """반복 실행 관리"""
    
    def __init__(self):
        self.repeat_active = False
        self.repeat_remaining = 0
        self.repeat_interval = 2.0
        self.repeat_message = ""
        self.repeat_force_search = False
    
    def is_active(self) -> bool:
        """반복 실행 활성화 여부"""
        return self.repeat_active
    
    def start(self, message: str, count: int, interval: float, force_search: bool = False):
        """반복 실행 시작"""
        self.repeat_active = True
        self.repeat_remaining = count
        self.repeat_interval = interval
        self.repeat_message = message
        self.repeat_force_search = force_search
    
    def stop(self):
        """반복 실행 중단"""
        if self.repeat_active:
            self.repeat_active = False
            self.repeat_remaining = 0
    
    def get_next(self) -> dict:
        """다음 반복 작업 가져오기"""
        if not self.repeat_active:
            return None
        
        if self.repeat_remaining == 0:
            return None
        
        if self.repeat_remaining > 0:
            self.repeat_remaining -= 1
        
        return {
            'message': self.repeat_message,
            'force_search': self.repeat_force_search,
            'interval': self.repeat_interval
        }


class BatchManager:
    """일괄 처리 관리"""
    
    def __init__(self):
        self.batch_active = False
        self.batch_items = []
        self.batch_index = 0
        self.batch_interval = 2.0
        self.batch_search_mode = False
        self.batch_infinite = False
        self.batch_open_background = False
    
    def is_active(self) -> bool:
        """일괄 처리 활성화 여부"""
        return self.batch_active
    
    def start(self, items: list, interval: float, search_mode: bool = False, infinite_loop: bool = False, background: bool = False):
        """일괄 처리 시작"""
        self.batch_active = True
        self.batch_items = items
        self.batch_index = 0
        self.batch_interval = interval
        self.batch_search_mode = search_mode
        self.batch_infinite = infinite_loop
        self.batch_open_background = background
    
    def stop(self):
        """일괄 처리 중단"""
        if self.batch_active:
            self.batch_active = False
            self.batch_items = []
            self.batch_index = 0
    
    def get_next(self) -> dict:
        """다음 일괄 작업 가져오기"""
        if not self.batch_active:
            return None
        
        if self.batch_index >= len(self.batch_items):
            if self.batch_infinite:
                self.batch_index = 0
                return {
                    'restart': True,
                    'interval': self.batch_interval
                }
            else:
                return {'complete': True}
        
        keyword = self.batch_items[self.batch_index]
        self.batch_index += 1
        
        return {
            'keyword': keyword,
            'search_mode': self.batch_search_mode,
            'interval': self.batch_interval,
            'background': self.batch_open_background
        }
    
    def load_trend_keywords(self) -> list:
        """트렌드 키워드 로드"""
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        file_path = os.path.join(root_dir, TREND_DATA_FILE)
        
        if not os.path.exists(file_path):
            log_debug(f"파일을 찾을 수 없습니다: {file_path}")
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            log_debug(f"트렌드 파일 읽기 오류: {e}")
            return []

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
                if not raw or raw in NAV_ITEMS:
                    continue
                if '\n' in raw:
                    raw = raw.split('\n', 1)[0].strip()
                keyword = raw
                if not keyword or keyword in seen:
                    continue
                seen.add(keyword)
                keywords.append(keyword)

        if keywords:
            # 랜덤하게 섞기
            random.shuffle(keywords)
            log_debug(f"✅ 트렌드 키워드 {len(keywords)}개 정리 완료 (랜덤 순서)")

        return keywords
    
    @staticmethod
    def parse_extra_keywords(raw: str) -> list:
        """추가 키워드 파싱"""
        if not raw:
            return []
        parts = [p.strip() for p in raw.split(',')]
        return [p for p in parts if p]
    
    @staticmethod
    def parse_trend_batch_command(message: str) -> dict:
        """트렌드 일괄 명령어 파싱"""
        # 트렌드반복
        match = re.match(r'^/(?:트렌드반복|trend-batch)(?:\s+(\d+(?:\.\d+)?))?(?:\s+(--infinite|-무한))?(?:\s+(--bg|--background))?\s*$', message)
        if match:
            interval = float(match.group(1)) if match.group(1) else 2.0
            infinite_mode = bool(match.group(2)) if match.lastindex >= 2 else False
            background_mode = bool(match.group(3)) if match.lastindex >= 3 else False
            
            return {
                'type': 'trend',
                'interval': interval,
                'infinite': infinite_mode,
                'background': background_mode,
                'search_mode': False
            }
        
        # 트렌드검색반복
        match = re.match(r'^/(?:트렌드검색반복|trend-batch-search)(?:\s+(\d+(?:\.\d+)?))?(?:\s+(--infinite|-무한))?(?:\s+(--bg|--background))?(?:\s*\[(.+)\])?\s*$', message)
        if not match:
            return None
        
        interval = float(match.group(1)) if match.group(1) else 2.0
        infinite_mode = bool(match.group(2)) if match.lastindex >= 2 else False
        background_mode = bool(match.group(3)) if match.lastindex >= 3 else False
        extra_keywords_raw = match.group(4) if match.lastindex >= 4 else None
        
        return {
            'type': 'trend_search',
            'interval': interval,
            'infinite': infinite_mode,
            'background': background_mode,
            'extra_keywords': extra_keywords_raw,
            'search_mode': True
        }
