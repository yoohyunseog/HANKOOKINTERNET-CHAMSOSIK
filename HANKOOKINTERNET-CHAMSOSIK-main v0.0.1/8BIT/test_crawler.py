"""
크롤러 빠른 테스트
간단한 URL 몇 개로 모든 기능을 테스트합니다.
"""

from advanced_crawler import AdvancedWebCrawler

def main():
    # 테스트할 URL (한국 사이트 위주)
    test_urls = [
        # 기술
        'https://www.python.org',
        
        # 뉴스
        'https://www.yonhapnews.co.kr',
        
        # 블로그 (naver는 로그인 필요할 수 있음)
        # 'https://blog.naver.com',
    ]
    
    print("=" * 60)
    print("🧪 크롤러 테스트")
    print("=" * 60)
    print(f"\n테스트 URL 개수: {len(test_urls)}개")
    print("브라우저 모드: 표시 (디버깅용)")
    print("\n시작하려면 Enter를 누르세요...")
    input()
    
    crawler = AdvancedWebCrawler(headless=False)
    
    try:
        # 크롤링 실행
        results = crawler.crawl_multiple(test_urls, delay=3)
        
        # 결과 출력
        crawler.print_summary()
        
        # JSON 저장
        crawler.save_to_json('data/test_crawled_data.json')
        
        print("\n" + "="*60)
        print("✅ 테스트 완료!")
        print("="*60)
        print("\n다음 단계:")
        print("1. data/test_crawled_data.json 파일 확인")
        print("2. advanced_crawler.py에서 urls 수정")
        print("3. python 8BIT/advanced_crawler.py 실행")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {str(e)}")
        print("\n문제 해결:")
        print("1. Chrome 브라우저가 설치되어 있는지 확인")
        print("2. pip install -r 8BIT/requirements_crawler.txt 실행")
        
    finally:
        crawler.close()


if __name__ == '__main__':
    main()
