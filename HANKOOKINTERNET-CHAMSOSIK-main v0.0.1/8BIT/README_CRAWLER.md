# 🤖 웹 데이터 크롤러 사용 가이드

완전한 웹 데이터 수집 시스템: 크롤링 + 장르분류 + 요약 + 키워드추출

## 📦 설치

### 1. 가상환경 활성화
```powershell
# Windows PowerShell
.\.venv\Scripts\activate
```

### 2. 패키지 설치
```powershell
pip install -r 8BIT/requirements_crawler.txt
```

### 3. Chrome WebDriver 설치
Chrome 브라우저가 설치되어 있어야 합니다.
Selenium이 자동으로 ChromeDriver를 다운로드합니다.

## 🚀 빠른 시작

### 통합 크롤러 (추천)
```python
from advanced_crawler import AdvancedWebCrawler

# 크롤링할 URL 리스트
urls = [
    'https://www.python.org',
    'https://github.com/trending',
    'https://news.naver.com',
]

# 크롤러 실행
crawler = AdvancedWebCrawler(headless=False)

try:
    # 크롤링 + 분석
    crawler.crawl_multiple(urls, delay=2)
    
    # 결과 출력
    crawler.print_summary()
    
    # JSON 저장
    crawler.save_to_json()
    
finally:
    crawler.close()
```

### 실행 명령어
```powershell
# 통합 크롤러 실행
python 8BIT/advanced_crawler.py

# 개별 모듈 테스트
python 8BIT/genre_classifier.py
python 8BIT/text_summarizer.py
python 8BIT/keyword_extractor.py
```

## 📊 수집되는 데이터

### 기본 정보
- `id`: 고유 ID (crawl_20240101123456_1)
- `url`: 페이지 URL
- `domain`: 도메인 (example.com)
- `title`: 페이지 제목
- `crawled_at`: 수집 시간 (ISO 8601)

### 분석 결과
- `genre`: 장르 (기술/뉴스/블로그/쇼핑/영상)
- `summary`: 1줄 요약 (최대 100자)
- `keywords`: 키워드 리스트 (최대 7개)

### 상세 데이터
- `meta_description`: 메타 설명
- `paragraphs_count`: 단락 개수
- `content_length`: 본문 길이

## 🎯 장르 분류

5가지 카테고리로 자동 분류:

| 장르 | 예시 도메인 | 키워드 |
|------|------------|--------|
| **기술** | github.com, stackoverflow.com | 개발, AI, 프로그래밍 |
| **뉴스** | news.naver.com, chosun.com | 속보, 정치, 경제 |
| **블로그** | blog.naver.com, tistory.com | 일상, 후기, 여행 |
| **쇼핑** | coupang.com, gmarket.co.kr | 가격, 할인, 상품 |
| **영상** | youtube.com, vimeo.com | 동영상, 구독, 재생 |

## 📝 개별 모듈 사용법

### 1. 장르 분류기
```python
from genre_classifier import GenreClassifier

classifier = GenreClassifier()
genre = classifier.classify(
    url='https://github.com/python',
    title='Python 공식 저장소',
    content='파이썬 프로그래밍 언어...'
)
print(f"장르: {genre}")  # 출력: 장르: 기술
```

### 2. 텍스트 요약기
```python
from text_summarizer import TextSummarizer

summarizer = TextSummarizer()
summary = summarizer.summarize(
    text='긴 본문 텍스트...',
    title='페이지 제목',
    max_length=100
)
print(f"요약: {summary}")
```

### 3. 키워드 추출기
```python
from keyword_extractor import KeywordExtractor

extractor = KeywordExtractor()
keywords = extractor.extract_keywords(
    text='본문 텍스트...',
    title='페이지 제목',
    max_keywords=7
)
print(f"키워드: {', '.join(keywords)}")
```

## 💾 출력 형식 (JSON)

```json
{
  "total_count": 3,
  "crawled_at": "2024-01-01T12:34:56",
  "stats": {
    "total_pages": 3,
    "total_keywords": 18,
    "avg_keywords_per_page": 6.0,
    "genre_distribution": {
      "기술": 2,
      "뉴스": 1
    }
  },
  "data": [
    {
      "id": "crawl_20240101123456_1",
      "url": "https://example.com",
      "domain": "example.com",
      "title": "페이지 제목",
      "genre": "기술",
      "summary": "OpenAI가 최신 AI 모델을 공개했으며...",
      "keywords": ["AI", "OpenAI", "모델", "기술"],
      "crawled_at": "2024-01-01T12:34:56"
    }
  ]
}
```

## 🔧 고급 설정

### 헤드리스 모드
```python
# 브라우저 숨김 (서버 환경)
crawler = AdvancedWebCrawler(headless=True)

# 브라우저 표시 (개발/디버깅)
crawler = AdvancedWebCrawler(headless=False)
```

### 크롤링 속도 조절
```python
# delay: 페이지 간 대기 시간 (초)
crawler.crawl_multiple(urls, delay=2)  # 2초 대기
crawler.crawl_multiple(urls, delay=5)  # 5초 대기
```

### 요약 길이 조절
```python
summary = summarizer.summarize(text, title, max_length=50)   # 짧게
summary = summarizer.summarize(text, title, max_length=100)  # 기본
summary = summarizer.summarize(text, title, max_length=200)  # 길게
```

### 키워드 개수 조절
```python
keywords = extractor.extract_keywords(text, title, max_keywords=3)   # 3개
keywords = extractor.extract_keywords(text, title, max_keywords=7)   # 7개 (기본)
keywords = extractor.extract_keywords(text, title, max_keywords=10)  # 10개
```

## 📂 프로젝트 구조

```
8BIT/
├── advanced_crawler.py       # 통합 크롤러 (메인)
├── web_crawler.py             # 기본 크롤러
├── genre_classifier.py        # 장르 분류
├── text_summarizer.py         # 텍스트 요약
├── keyword_extractor.py       # 키워드 추출
├── requirements_crawler.txt   # 패키지 목록
└── README_CRAWLER.md          # 이 파일
```

## ✅ 완료된 기능

1. ✅ 데이터 수집 (web_crawler.py)
2. ✅ 장르 분류 (genre_classifier.py) - 5가지 카테고리
3. ✅ 1줄 요약 생성 (text_summarizer.py)
4. ✅ 검색어 추출 (keyword_extractor.py)
5. ✅ 통합 크롤러 (advanced_crawler.py)

## 🚧 향후 계획

- [ ] Express API 연동 (실시간 크롤링 요청)
- [ ] 배치 처리 스케줄러
- [ ] 중복 URL 필터링
- [ ] 데이터베이스 저장 (MySQL/PostgreSQL)
- [ ] 웹 UI 대시보드

## 🐛 문제 해결

### ChromeDriver 오류
```
selenium.common.exceptions.WebDriverException
```
**해결방법**: Chrome 브라우저를 최신 버전으로 업데이트

### 한글 인코딩 오류
```
UnicodeEncodeError
```
**해결방법**: Python 파일을 UTF-8로 저장

### 메모리 부족
**해결방법**: 크롤링 개수를 줄이거나 delay를 늘림

## 📞 문의

문제가 발생하면 이슈를 남겨주세요.
