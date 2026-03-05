"""
날짜 처리 및 뉴스 관리
"""

import os
import json
import requests
import subprocess
from datetime import datetime, timedelta
import re

from .config import (
    NB_API_URL, DATABASE_BASE_URL, AUTO_UPLOAD_DATA,
    AJAX_SAVE_ENABLED, SAVE_LOCAL_SUMMARY
)
from .utils import log_debug


class DateHelper:
    """날짜 관련 헬퍼 함수"""
    
    @staticmethod
    def is_today_news_date(date_text: str) -> bool:
        """오늘 뉴스 날짜인지 확인"""
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
    
    @staticmethod
    def is_today_news_text(text: str) -> bool:
        """텍스트가 오늘 뉴스인지 확인"""
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
    
    @staticmethod
    def extract_date_from_text(text: str):
        """텍스트에서 날짜 추출"""
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
    
    @staticmethod
    def is_text_stale_by_date(text: str, category: str = "검색") -> bool:
        """텍스트가 오래된 정보인지 판단"""
        if not text:
            return True

        cleaned = text.strip().lower()
        if "작년" in cleaned or "지난해" in cleaned:
            return True

        today = datetime.now().date()
        must_be_today = category in ["정치", "경제"]
        prefer_today = category in ["사회", "문화", "게임", "드라마", "영화", "애니메이션", "스포츠"]

        dt = DateHelper.extract_date_from_text(cleaned)
        if not dt:
            return False
        if dt.year < today.year:
            return True
        if must_be_today and dt != today:
            return True
        if prefer_today and dt < (today - timedelta(days=7)):
            return True
        return False


class NewsManager:
    """뉴스 저장 및 관리"""
    
    def __init__(self, notify_callback=None):
        self.notify_callback = notify_callback
        self.detail_logs = {}
        self.clear_detail_logs()
    
    def notify(self, message: str):
        """시스템 메시지 전송"""
        if self.notify_callback:
            self.notify_callback("system", message)
        else:
            log_debug(message)
    
    def clear_detail_logs(self):
        """상세 로그 초기화"""
        self.detail_logs = {
            'calc': [],
            'paths': [],
            'upload': []
        }
    
    def add_detail_log(self, key: str, line: str):
        """상세 로그 추가"""
        if key not in self.detail_logs:
            self.detail_logs[key] = []
        self.detail_logs[key].append(line)
    
    def filter_today_news_items(self, items: list) -> list:
        """오늘 뉴스만 필터링"""
        if not items:
            return []
        return [item for item in items if DateHelper.is_today_news_date(item.get('date', ''))]
    
    def trigger_ajax_save(self, items: list) -> list:
        """AJAX 방식으로 저장 트리거"""
        results = []
        if not items:
            return results

        for item in items:
            try:
                url = f"{DATABASE_BASE_URL}/database.html?nb={requests.utils.quote(item)}&end=5s"
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
    
    def save_news_nb_calculations(self, items: list, category: str = "news") -> list:
        """N/B 계산 및 저장"""
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
    
    def number_to_path(self, value: float) -> str:
        """숫자를 경로로 변환"""
        value_str = repr(value).replace('-', '_')
        parts = []
        for ch in value_str:
            if ch == '.':
                parts.append('.')
            elif ch.isdigit() or ch == '_':
                parts.append(ch)
        return os.path.join(*parts) if parts else '0'
    
    def save_news_results_by_path(self, calculations: list, nb_max_dir: str, nb_min_dir: str):
        """경로별로 뉴스 결과 저장"""
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
    
    def upload_data_only(self, root_dir: str):
        """데이터 업로드"""
        if not AUTO_UPLOAD_DATA:
            self.notify("⏭️ 데이터 업로드 생략됨")
            return

        script_path = os.path.join(root_dir, 'sync_data_only.bat')
        if not os.path.exists(script_path):
            self.notify("⚠️ 데이터 업로드 스크립트 없음")
            return

        self.notify("📤 데이터 업로드 시작...")
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
                self.notify("✅ 데이터 업로드 완료")
            else:
                self.notify("❌ 데이터 업로드 실패")
                if result.stderr:
                    log_debug(result.stderr.strip())
        except Exception as e:
            self.notify("❌ 데이터 업로드 오류")
            log_debug(f"[업로드 오류] {e}")
