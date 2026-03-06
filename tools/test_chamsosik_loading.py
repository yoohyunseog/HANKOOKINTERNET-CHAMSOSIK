#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
참소식.com 데이터 로딩 테스트
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time

def test_chamsosik():
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    print('🌐 참소식.com 로딩 테스트 시작...')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get('https://xn--9l4b4xi9r.com')
        print('⏳ 10초 대기...')
        time.sleep(10)
        
        # "로딩 중..." 텍스트 확인
        loading_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '로딩') or contains(text(), '데이터 로딩')]")
        print(f'\n"로딩 중..." 요소: {len(loading_elements)}개')
        for elem in loading_elements:
            print(f'  - {elem.text}')
        
        # 페이지 텍스트 일부 출력
        body_text = driver.find_element(By.TAG_NAME, 'body').text
        lines = [line.strip() for line in body_text.split('\n') if line.strip()]
        
        print(f'\n📄 페이지 텍스트 (처음 30줄):')
        for i, line in enumerate(lines[:30], 1):
            print(f'{i:2d}. {line}')
        
        print(f'\n총 {len(lines)}줄')
        
        # 30초 더 대기 후 다시 확인
        print('\n⏳ 30초 더 대기...')
        time.sleep(30)
        
        loading_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '로딩') or contains(text(), '데이터 로딩')]")
        print(f'\n30초 후 "로딩 중..." 요소: {len(loading_elements)}개')
        
        body_text = driver.find_element(By.TAG_NAME, 'body').text
        lines = [line.strip() for line in body_text.split('\n') if line.strip()]
        print(f'30초 후 총 텍스트 줄 수: {len(lines)}줄')
        
        # 링크 확인
        links = driver.find_elements(By.TAG_NAME, 'a')
        print(f'\n🔗 링크 수: {len(links)}개')
        
    finally:
        driver.quit()

if __name__ == '__main__':
    test_chamsosik()
