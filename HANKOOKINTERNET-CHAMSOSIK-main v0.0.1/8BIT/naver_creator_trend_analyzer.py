"""
네이버 크리에이터 어드바이저 트렌드 분석기
- 설정순 보기 데이터 자동 수집
- 예약 실행 및 데이터 저장
"""

import time
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import schedule
import pandas as pd

class NaverCreatorTrendAnalyzer:
    def __init__(self, user_id, password):
        """
        초기화
        Args:
            user_id: 네이버 로그인 ID
            password: 네이버 로그인 비밀번호
        """
        self.user_id = user_id
        self.password = password
        self.driver = None
        self.logged_in = False
        self.data_dir = "data/naver_creator_trends"
        
        # 데이터 저장 디렉토리 생성
        os.makedirs(self.data_dir, exist_ok=True)
        
    def setup_driver(self, headless=True):
        """Chrome 드라이버 설정"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')  # 백그라운드 실행
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 20)

    def is_driver_alive(self):
        try:
            return self.driver is not None and self.driver.title is not None
        except Exception:
            return False
        
    def login(self):
        """네이버 로그인 (수동)"""
        try:
            print("로그인 시작...")
            self.driver.get('https://nid.naver.com/nidlogin.login')
            time.sleep(2)
            
            print("\n📱 로그인 페이지가 열렸습니다.")
            print("➡️  다음 작업을 수행하세요:")
            print("   1. 아이디와 비밀번호를 입력하세요")
            print("   2. 로그인 버튼을 클릭하세요")
            print("   3. 로그인 완료 후 Enter를 누르세요\n")
            
            input("💬 로그인을 완료하셨으면 Enter를 누르세요...")
            
            print("\n✅ 로그인 완료")
            self.logged_in = True
            return True
            
        except Exception as e:
            print(f"❌ 로그인 실패: {e}")
            return False
    
    def navigate_to_trends(self, blog_id):
        """트렌드 페이지로 이동"""
        try:
            url = f'https://creator-advisor.naver.com/naver_blog/{blog_id}/trends'
            self.driver.get(url)
            print("⏳ 트렌드 페이지 로딩 중... (10초 대기)")
            time.sleep(10)
            print(f"✅ 트렌드 페이지 이동 완료: {url}")
            return True
        except Exception as e:
            print(f"❌ 페이지 이동 실패: {e}")
            return False
    
    def click_setting_view(self):
        """설정순 보기 클릭 (선택사항)"""
        try:
            # 다양한 선택자 시도
            selectors = [
                "//button[contains(text(), '설정순')]",
                "//button[contains(text(), '설정')]",
                "//a[contains(text(), '설정순')]",
                "//span[contains(text(), '설정순')]",
                "[data-view='setting']",
                ".setting-view",
                "#setting-view"
            ]
            
            for selector in selectors:
                try:
                    if selector.startswith('//'):
                        btn = self.driver.find_element(By.XPATH, selector)
                    else:
                        btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    btn.click()
                    time.sleep(2)
                    print(f"✅ 설정순 보기 클릭 완료 (선택자: {selector[:30]}...)")
                    return True
                except:
                    continue
            
            print("⚠️ 설정순 보기 버튼을 찾지 못했습니다. 기본 페이지 데이터를 수집합니다.")
            return False
            
        except Exception as e:
            print(f"⚠️ 설정순 보기 클릭 시도 중 오류: {e}")
            print("   기본 페이지 데이터를 수집합니다.")
            return False
    
    def scroll_tabs_left(self):
        """탭 네비게이션을 좌측으로 스크롤"""
        try:
            # 탭 컨테이너 찾기
            tab_containers = [
                "[class*='tab']",
                "[class*='scroll']",
                "[role='tablist']",
                ".horizontal-scroll",
                "[class*='carousel']"
            ]
            
            for selector in tab_containers:
                try:
                    container = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # 좌측 네비게이션 버튼 찾기
                    left_buttons = [
                        "[class*='prev']",
                        "[class*='left']",
                        "button[aria-label*='이전']",
                        "button[aria-label*='left']"
                    ]
                    
                    for button_selector in left_buttons:
                        try:
                            left_btn = container.find_element(By.CSS_SELECTOR, button_selector)
                            # 좌측으로 여러 번 클릭
                            for i in range(5):
                                try:
                                    left_btn.click()
                                    time.sleep(0.5)
                                    print(f"⬅️ 탭 좌측 이동 {i+1}회")
                                except:
                                    break
                            return True
                        except:
                            continue
                    
                    # 버튼이 없으면 JavaScript로 스크롤
                    try:
                        self.driver.execute_script(
                            "arguments[0].scrollLeft -= 300;",
                            container
                        )
                        print("⬅️ 탭 좌측 스크롤 완료")
                        time.sleep(1)
                        return True
                    except:
                        continue
                        
                except:
                    continue
            
            print("⚠️ 좌측 이동 버튼/스크롤을 찾지 못했습니다.")
            return False
            
        except Exception as e:
            print(f"❌ 탭 좌측 이동 실패: {e}")
            return False
    
    def extract_trend_data(self):
        """트렌드 탭 데이터 추출 (강화된 버전)"""
        try:
            trend_data = []
            
            # 더 많은 선택자 패턴 시도
            selectors = [
                ".trend-tab-item",
                ".tab-content-item",
                "[class*='trend']",
                "[class*='Trend']",
                "[class*='card']",
                "[class*='item']",
                "article",
                ".article",
                "[role='article']",
                "[class*='content']"
            ]
            
            all_elements = []
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    all_elements.extend(elements)
                except:
                    continue
            
            # 중복 제거
            unique_elements = list(set(all_elements))
            print(f"📊 {len(unique_elements)}개의 요소 발견")
            
            for idx, elem in enumerate(unique_elements[:50]):  # 최대 50개
                try:
                    text = elem.text.strip()
                    if not text or len(text) < 10:  # 너무 짧은 텍스트 제외
                        continue
                    
                    tab_info = {
                        'index': idx + 1,
                        'timestamp': datetime.now().isoformat(),
                        'title': '',
                        'keywords': [],
                        'metrics': {},
                        'raw_text': text,
                        'element_tag': elem.tag_name,
                        'element_class': elem.get_attribute('class')
                    }
                    
                    # 제목 추출 (여러 패턴)
                    for title_selector in ["h1", "h2", "h3", "h4", ".title", "[class*='title']", "strong"]:
                        try:
                            title_elem = elem.find_element(By.CSS_SELECTOR, title_selector)
                            if title_elem.text.strip():
                                tab_info['title'] = title_elem.text.strip()
                                break
                        except:
                            continue
                    
                    # 키워드 추출
                    for kw_selector in [".keyword", ".tag", "[class*='keyword']", "[class*='tag']", "span"]:
                        try:
                            keyword_elems = elem.find_elements(By.CSS_SELECTOR, kw_selector)
                            keywords = [k.text.strip() for k in keyword_elems if k.text.strip() and len(k.text.strip()) < 50]
                            if keywords:
                                tab_info['keywords'].extend(keywords)
                        except:
                            continue
                    
                    # 중복 제거
                    tab_info['keywords'] = list(set(tab_info['keywords']))[:10]  # 최대 10개
                    
                    # 링크 추출
                    try:
                        links = elem.find_elements(By.TAG_NAME, "a")
                        tab_info['links'] = [link.get_attribute('href') for link in links if link.get_attribute('href')][:5]
                    except:
                        tab_info['links'] = []
                    
                    trend_data.append(tab_info)
                        
                except Exception as e:
                    continue
            
            print(f"✅ {len(trend_data)}개의 트렌드 데이터 추출 완료")
            return trend_data
            
        except Exception as e:
            print(f"❌ 데이터 추출 실패: {e}")
            return []
    
    def extract_detailed_data(self):
        """상세 데이터 추출 (테이블, 리스트 등)"""
        try:
            detailed_data = {
                'timestamp': datetime.now().isoformat(),
                'tables': [],
                'lists': [],
                'charts': []
            }
            
            # 테이블 데이터 추출
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            for table in tables:
                try:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    table_data = []
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if not cells:
                            cells = row.find_elements(By.TAG_NAME, "th")
                        row_data = [cell.text.strip() for cell in cells]
                        if any(row_data):
                            table_data.append(row_data)
                    if table_data:
                        detailed_data['tables'].append(table_data)
                except:
                    pass
            
            # 리스트 데이터 추출
            lists = self.driver.find_elements(By.CSS_SELECTOR, "ul, ol")
            for lst in lists[:10]:  # 처음 10개만
                try:
                    items = lst.find_elements(By.TAG_NAME, "li")
                    list_data = [item.text.strip() for item in items if item.text.strip()]
                    if list_data:
                        detailed_data['lists'].append(list_data)
                except:
                    pass
            
            return detailed_data
            
        except Exception as e:
            print(f"❌ 상세 데이터 추출 실패: {e}")
            return {}
    
    def save_data(self, data, filename_prefix="trend_data"):
        """데이터 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON 저장
            json_filename = f"{self.data_dir}/{filename_prefix}_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ JSON 저장: {json_filename}")
            
            # CSV 저장 (트렌드 데이터만)
            if 'trend_data' in data and data['trend_data']:
                csv_filename = f"{self.data_dir}/{filename_prefix}_{timestamp}.csv"
                df = pd.DataFrame(data['trend_data'])
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"✅ CSV 저장: {csv_filename}")
            
            # 최신 데이터도 별도 저장 (항상 덮어쓰기)
            latest_json = f"{self.data_dir}/latest_{filename_prefix}.json"
            with open(latest_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return json_filename
            
        except Exception as e:
            print(f"❌ 데이터 저장 실패: {e}")
            return None
    
    def analyze_and_collect(self, blog_id='dbghwns2', headless=True, keep_browser_open=False, pause_on_finish=False):
        """전체 분석 프로세스 실행"""
        try:
            print(f"\n{'='*50}")
            print(f"📊 트렌드 데이터 수집 시작: {datetime.now()}")
            print(f"{'='*50}\n")
            
            # 드라이버 설정
            if not self.is_driver_alive():
                self.setup_driver(headless=headless)
                self.logged_in = False
            
            # 로그인
            if not self.logged_in:
                if not self.login():
                    return False
            
            # 트렌드 페이지 이동
            if not self.navigate_to_trends(blog_id):
                return False
            
            # 설정순 보기 클릭 (선택사항)
            self.click_setting_view()
            
            # 페이지 완전히 로드될 때까지 대기
            print("⏳ 페이지 데이터 로딩 중... (5초 대기)")
            time.sleep(5)
            
            # 탭을 좌측으로 이동해서 모든 탭 데이터 확인
            print("\n🔄 탭 좌측 이동 시작...")
            self.scroll_tabs_left()
            time.sleep(2)
            
            # 스크린샷 저장 (디버깅용)
            screenshot_path = f"{self.data_dir}/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            self.driver.save_screenshot(screenshot_path)
            print(f"📸 스크린샷 저장: {screenshot_path}")
            
            # 데이터 추출
            trend_data = self.extract_trend_data()
            detailed_data = self.extract_detailed_data()
            
            # 통합 데이터
            result = {
                'collection_time': datetime.now().isoformat(),
                'blog_id': blog_id,
                'trend_data': trend_data,
                'detailed_data': detailed_data,
                'total_items': len(trend_data)
            }
            
            # 데이터 저장
            self.save_data(result)
            
            print(f"\n✅ 분석 완료: {len(trend_data)}개 항목 수집")
            if pause_on_finish:
                print("\n✅ 브라우저는 유지됩니다. 종료하려면 Enter를 누르세요...")
                input()
            else:
                print("\n✅ 브라우저는 유지됩니다.")
            return True
            
        except Exception as e:
            print(f"❌ 분석 실패: {e}")
            import traceback
            traceback.print_exc()
            if pause_on_finish:
                print("\n⚠️  오류 확인을 위해 브라우저를 유지합니다. 종료하려면 Enter를 누르세요...")
                input()
            else:
                print("\n⚠️  오류 확인을 위해 브라우저를 유지합니다.")
            return False
            
        finally:
            if self.driver and not keep_browser_open:
                print("🔒 브라우저 종료 중...")
                self.driver.quit()
                print("✅ 브라우저 종료 완료")
            elif self.driver:
                print("✅ 브라우저 유지 중 (자동 종료 없음)")
    
    def schedule_analysis(self, blog_id='dbghwns2', interval_minutes=60, start_time=None, end_time=None, headless=True):
        """예약 실행 설정 (시간 설정 지원)"""
        print(f"\n⏰ 예약 실행 스케줄링 시작")
        print(f"기본 설정:")
        print(f"  - 블로그 ID: {blog_id}")
        print(f"  - 실행 간격: {interval_minutes}분마다")
        
        if start_time:
            print(f"  - 시작 시간: {start_time}")
        if end_time:
            print(f"  - 종료 시간: {end_time}")
        
        print(f"  - 모드: {'빠른' if headless else '메모리'} 내단기단기")
        print(f"  - 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 즉시 한 번 실행
        self.analyze_and_collect(blog_id, headless=headless, keep_browser_open=True, pause_on_finish=False)
        
        # 예약 설정
        if start_time or end_time:
            # 시간 기반 스케줄링
            self._schedule_by_time(blog_id, interval_minutes, start_time, end_time, headless)
        else:
            # 분 기반 스케줄링
            self._schedule_by_interval(blog_id, interval_minutes, headless)
    
    def _schedule_by_interval(self, blog_id, interval_minutes, headless):
        """분 기반 스케줄링"""
        schedule.every(interval_minutes).minutes.do(
            lambda: self.analyze_and_collect(blog_id, headless=headless, keep_browser_open=True, pause_on_finish=False)
        )
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️ 예약 실행 중지")
    
    def _schedule_by_time(self, blog_id, interval_minutes, start_time, end_time, headless):
        """시간 기반 스케줄링
        
        예: start_time='09:00', end_time='18:00'
        주어진 시간 내에만 실행
        """
        def run_if_in_time_range():
            from datetime import datetime as dt
            now = dt.now().strftime('%H:%M')
            
            # 시간 범위 체크
            if start_time and end_time:
                if start_time <= now <= end_time:
                    self.analyze_and_collect(blog_id, headless=headless, keep_browser_open=True, pause_on_finish=False)
                else:
                    print(f"[{now}] 다음 시간({start_time}-{end_time}) 내에 예비 스케줄링")
            elif start_time:
                if now >= start_time:
                    self.analyze_and_collect(blog_id, headless=headless, keep_browser_open=True, pause_on_finish=False)
            elif end_time:
                if now <= end_time:
                    self.analyze_and_collect(blog_id, headless=headless, keep_browser_open=True, pause_on_finish=False)
        
        schedule.every(interval_minutes).minutes.do(run_if_in_time_range)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⏹️ 예약 실행 중지")


def main():
    """메인 함수"""
    print("""
    ╔══════════════════════════════════════════════════╗
    ║  네이버 크리에이터 어드바이저 트렌드 분석기      ║
    ║  Naver Creator Trend Analyzer                    ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    # 설정 파일에서 읽기 또는 직접 입력
    config_file = "config/naver_creator_config.json"
    headless = True  # 기본값
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        user_id = config.get('naver_id')
        password = config.get('naver_password')
        blog_id = config.get('blog_id', 'dbghwns2')
        headless = config.get('chrome_driver', {}).get('headless', True)
    else:
        print("⚠️ 설정 파일이 없습니다. 직접 입력해주세요.\n")
        user_id = input("네이버 ID: ").strip()
        password = input("비밀번호: ").strip()
        blog_id = input("블로그 ID (기본값: dbghwns2): ").strip() or 'dbghwns2'
    
    if not user_id or not password:
        print("❌ ID와 비밀번호를 입력해주세요.")
        return
    
    # 분석기 생성
    analyzer = NaverCreatorTrendAnalyzer(user_id, password)
    
    # 실행 모드 선택
    print("\n실행 모드를 선택하세요:")
    print("1. 로그인하기")
    print("2. 즉시 실행 (1회)")
    print("3. 예약 실행 (반복)")
    
    mode = input("선택 (1, 2 or 3): ").strip()
    
    if mode == '1':
        # 로그인만 하기 (브라우저 표시)
        print("\n🔐 로그인을 진행합니다...")
        analyzer.setup_driver(headless=False)
        if analyzer.login():
            print("\n✅ 로그인 성공!")
            print("📍 네이버 페이지가 열려있습니다.")
            print("   필요한 작업을 완료한 후 브라우저를 종료하세요.")
            print("\n💡 팁: 브라우저 개발자 도구(F12)를 열어서 페이지 구조를 확인할 수 있습니다.")
            input("\n브라우저를 닫지 않습니다. 종료하려면 Enter를 누르세요...")
        else:
            print("\n❌ 로그인 실패")
            input("\nEnter를 누르세요...")
    elif mode == '2':
        # 즉시 실행 (브라우저 표시)
        print("\n🚀 데이터 수집을 시작합니다...")
        analyzer.analyze_and_collect(blog_id, headless=False, keep_browser_open=True, pause_on_finish=True)
    elif mode == '3':
        # 예약 실행
        print("\n⏰ 예약 실행 설정")
        
        interval = input("실행 간격(분) [기본값: 60]: ").strip()
        interval = int(interval) if interval.isdigit() else 60
        
        start_time = input("시작 시간 [HH:MM, 비워두면 제한 없음]: ").strip()
        end_time = input("종료 시간 [HH:MM, 비워두면 제한 없음]: ").strip()
        
        start_time = start_time if start_time else None
        end_time = end_time if end_time else None
        
        analyzer.schedule_analysis(blog_id, interval, start_time, end_time, headless=False)
    else:
        print("❌ 잘못된 선택입니다.")


if __name__ == "__main__":
    main()
