# 📰 최신 기사 요약 AI

다양한 뉴스 사이트에서 최신 기사를 크롤링하고 AI로 요약하는 시스템입니다.

## 🚀 주요 기능

- **다양한 뉴스 사이트 지원**: 네이버 뉴스, 다음 뉴스, 연합뉴스, KBS 뉴스 등
- **AI 요약**: Ollama를 사용한 고품질 요약
- **키워드 추출**: 자동 키워드 추출
- **JSON 저장**: 결과를 JSON 파일로 저장

## 📦 설치

```bash
# 필요한 패키지 설치
pip install requests beautifulsoup4 selenium

# Ollama 설치 (AI 요약 사용 시)
# https://ollama.ai 에서 다운로드
```

## 🔧 사용법

### 1. 기본 실행

```bash
# 배치 파일 실행
run_article_summarizer.bat

# 또는 직접 실행
python 8BIT/article_summarizer.py
```

### 2. 옵션 사용

```bash
# 사이트당 5개 기사
python 8BIT/article_summarizer.py --max 5

# AI 요약 없이 (빠른 실행)
python 8BIT/article_summarizer.py --no-ai

# 특정 모델 사용
python 8BIT/article_summarizer.py --model gemma4:31b-cloud

# 특정 URL만 처리
python 8BIT/article_summarizer.py --urls https://news.naver.com/... https://...
```

### 3. Python 코드에서 사용

```python
from article_summarizer import ArticleSummarizer

# 초기화
summarizer = ArticleSummarizer(
    use_ollama=True,  # AI 요약 사용
    ollama_model="gemma4:31b-cloud"  # 모델 지정
)

# 최신 기사 요약
result = summarizer.summarize_latest_articles(max_articles_per_site=3)

# 특정 URL 요약
result = summarizer.summarize_custom_urls([
    "https://news.naver.com/...",
    "https://news.daum.net/..."
])

# 결과 확인
for article in result['articles']:
    print(f"제목: {article['title']}")
    print(f"키워드: {article['keywords']}")
    print(f"AI 요약: {article['ai_summary']}")
```

## 📁 출력 파일

결과는 `data/article_summaries/` 폴더에 저장됩니다:

```
data/article_summaries/
├── article_summaries_20260604_120000.json  # 타임스탬프 파일
├── article_summaries_20260604_130000.json
└── latest_article_summaries.json             # 항상 최신 파일
```

## 📋 JSON 출력 형식

```json
{
  "summary_time": "2026-06-04T12:00:00",
  "total_articles": 10,
  "articles": [
    {
      "url": "https://news.naver.com/...",
      "title": "기사 제목",
      "description": "메타 설명",
      "keywords": ["키워드1", "키워드2", "키워드3"],
      "basic_summary": "규칙 기반 요약",
      "ai_summary": "AI 생성 요약",
      "content_length": 2500,
      "crawled_at": "2026-06-04T12:00:00",
      "source": "news.naver.com"
    }
  ],
  "statistics": {
    "sites_processed": 4,
    "total_keywords": 70,
    "ai_summarized": 10
  }
}
```

## ⚙️ 설정

### 뉴스 사이트 추가/수정

`article_summarizer.py` 파일의 `self.news_sites` 리스트를 수정:

```python
self.news_sites = [
    {
        "name": "새로운 뉴스 사이트",
        "url": "https://example-news.com",
        "type": "portal",
        "enabled": True
    },
    # ...
]
```

### Ollama 설정

환경 변수로 설정 가능:

```bash
# Windows
set OLLAMA_BASE_URL=http://localhost:11434
set OLLAMA_MODEL=gemma4:31b-cloud

# Linux/Mac
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=gemma4:31b-cloud
```

## 🧪 테스트

```bash
python test_article_summarizer.py
```

## 📝 참고사항

- AI 요약을 사용하려면 Ollama가 실행 중이어야 합니다
- 크롤링 간격은 1초로 설정되어 있습니다 (서버 부하 방지)
- 일부 사이트는 크롤링이 차단될 수 있습니다
- Selenium을 사용한 동적 크롤링도 지원됩니다

## 🔗 관련 파일

- `article_summarizer.py` - 메인 모듈
- `text_summarizer.py` - 텍스트 요약기
- `keyword_extractor.py` - 키워드 추출기
- `run_article_summarizer.bat` - 실행 배치 파일
- `test_article_summarizer.py` - 테스트 스크립트