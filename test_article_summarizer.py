"""
기사 요약 AI 테스트 스크립트
"""

import sys
import os

# 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '8BIT'))

from article_summarizer import ArticleSummarizer


def test_basic():
    """기본 테스트 (AI 없이)"""
    print("\n" + "="*50)
    print("테스트 1: 기본 요약 (AI 없이)")
    print("="*50)
    
    summarizer = ArticleSummarizer(use_ollama=False)
    
    # 테스트 URL들
    test_urls = [
        "https://news.naver.com",
        "https://news.daum.net"
    ]
    
    result = summarizer.summarize_latest_articles(max_articles_per_site=1)
    
    print(f"\n결과: {result['total_articles']}개 기사 처리됨")
    
    return result


def test_with_ai():
    """AI 요약 테스트"""
    print("\n" + "="*50)
    print("테스트 2: AI 요약 포함")
    print("="*50)
    
    summarizer = ArticleSummarizer(use_ollama=True)
    
    result = summarizer.summarize_latest_articles(max_articles_per_site=2)
    
    print(f"\n결과: {result['total_articles']}개 기사 처리됨")
    print(f"AI 요약: {result['statistics']['ai_summarized']}개")
    
    return result


def test_custom_urls():
    """커스텀 URL 테스트"""
    print("\n" + "="*50)
    print("테스트 3: 커스텀 URL")
    print("="*50)
    
    summarizer = ArticleSummarizer(use_ollama=False)
    
    # 샘플 뉴스 URL (실제 URL로 변경 필요)
    urls = [
        "https://www.yna.co.kr",
        "https://news.kbs.co.kr"
    ]
    
    result = summarizer.summarize_custom_urls(urls)
    
    print(f"\n결과: {result['total_articles']}개 기사 처리됨")
    
    return result


def main():
    print("\n" + "="*60)
    print("🧪 기사 요약 AI 테스트")
    print("="*60)
    
    print("\n테스트 옵션:")
    print("1. 기본 테스트 (AI 없이, 빠름)")
    print("2. AI 요약 테스트 (Ollama 필요)")
    print("3. 커스텀 URL 테스트")
    print("4. 전체 테스트")
    
    choice = input("\n선택하세요 (1-4): ").strip()
    
    if choice == "1":
        test_basic()
    elif choice == "2":
        test_with_ai()
    elif choice == "3":
        test_custom_urls()
    elif choice == "4":
        test_basic()
        test_with_ai()
        test_custom_urls()
    else:
        print("잘못된 선택입니다.")
    
    print("\n✅ 테스트 완료!")


if __name__ == "__main__":
    main()