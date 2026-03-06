#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웹사이트의 순수 텍스트 내용만 추출하는 도구
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import sys

def extract_text_from_url(url, wait_time=15):
    """웹사이트에서 순수 텍스트만 추출"""
    
    # Chrome 설정
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    print(f'🌐 {url} 페이지 로딩 중...')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get(url)
        print(f'⏳ JavaScript 로딩 대기 중 ({wait_time}초)...')
        time.sleep(wait_time)
        
        # 스크롤로 lazy loaded 콘텐츠 로드
        print('📜 페이지 스크롤 중...')
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight/2);')
        time.sleep(2)
        driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
        time.sleep(2)
        driver.execute_script('window.scrollTo(0, 0);')
        time.sleep(1)
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # 스크립트, 스타일, noscript 태그 제거
        for tag in soup(['script', 'style', 'noscript', 'meta', 'link']):
            tag.decompose()
        
        # 텍스트 추출
        text = soup.get_text(separator='\n', strip=True)
        
        # 빈 줄 제거 및 정리
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        print('\n' + '='*70)
        print(f'📄 {url} - 페이지 텍스트 내용')
        print('='*70 + '\n')
        
        # 모든 줄 출력
        for i, line in enumerate(lines, 1):
            print(f'{i:3d}. {line}')
        
        print('\n' + '='*70)
        print(f'✅ 총 {len(lines)}줄 추출 완료')
        print('='*70)
        
        return lines
        
    except Exception as e:
        print(f'❌ 오류 발생: {e}')
        return None
    finally:
        try:
            driver.quit()
        except:
            pass


if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://xn--9l4b4xi9r.com'
    wait_time = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    lines = extract_text_from_url(url, wait_time)
    
    # 파일로 저장
    if output_file and lines:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for i, line in enumerate(lines, 1):
                    f.write(f'{i:3d}. {line}\n')
            print(f'\n💾 결과를 파일로 저장했습니다: {output_file}')
        except Exception as e:
            print(f'⚠️ 파일 저장 실패: {e}')
