# 검색 모듈

네이버, Bing, YouTube, 뉴스 RSS 등 다양한 검색 기능을 제공하는 Python 모듈입니다.

## 📁 구조

```
search/
├── __init__.py          # 모듈 초기화 및 export
├── naver_search.py      # 네이버 검색 기능
├── bing_search.py       # Bing 검색 기능 (새로 추가)
├── youtube_search.py    # 유튜브 검색 기능
├── news_rss.py          # 뉴스 RSS 피드 기능
└── README.md            # 이 파일
```

## 🚀 사용법

### 1. 네이버 검색

```python
from search import search_naver, get_naver_results

# 검색 URL 생성
url = search_naver("파이썬", search_type='blog')
# https://search.naver.com/search.naver?where=blog&query=%ED%8C%8C%EC%9D%B4%EC%8D%AC

# 검색 결과 가져오기
results = get_naver_results("파이썬", search_type='blog', limit=5)
# [{'title': '...', 'description': '...', 'url': '...', 'date': '...'}, ...]
```

#### 지원하는 검색 유형
- `blog`: 블로그 (기본값)
- `news`: 뉴스
- `web`: 통합 검색
- `image`: 이미지
- `video`: 동영상

### 2. Bing 검색 (🆕 새로 추가)

```python
from search import search_bing, get_bing_results, format_bing_results

# 검색 URL 생성
url = search_bing("파이썬", search_type='web')
# https://www.bing.com/search?q=%ED%8C%8C%EC%9D%B4%EC%8D%AC

# 검색 결과 가져오기
results = get_bing_results("파이썬", search_type='web', limit=5)
# [{'title': '...', 'description': '...', 'url': '...', 'source': 'Bing'}, ...]

# 결과 포맷팅
formatted = format_bing_results(results)
print(formatted)
```

#### 지원하는 검색 유형
- `web`: 웹 검색 (기본값)
- `news`: 뉴스
- `image`: 이미지
- `video`: 동영상

### 3. 유튜브 검색

```python
from search import search_youtube, get_youtube_results

# 검색 URL 생성
url = search_youtube("Python tutorial")
# https://www.youtube.com/results?search_query=Python+tutorial

# 검색 결과 가져오기
results = get_youtube_results("Python tutorial", limit=5)
# [{'title': '...', 'url': '...', 'channel': '...', 'description': '...'}, ...]
```

### 4. 뉴스 RSS 검색

```python
from search import get_naver_news_rss, get_news_by_category

# 키워드로 뉴스 검색
news = get_naver_news_rss("인공지능", limit=5)

# 카테고리별 뉴스
news = get_news_by_category("정치", limit=5)
```

### 5. 🆕 다중 검색 (모든 소스에서 동시 검색)

```python
from search import multi_search, format_multi_search_results

# 여러 검색 엔진에서 동시에 검색
results = multi_search(
    keyword="주요 뉴스",
    sources=['naver', 'bing', 'news'],  # 원하는 소스만 선택
    limit=5
)

# 결과 포맷팅
formatted = format_multi_search_results(results)
print(formatted)
```

#### 지원하는 소스
- `naver`: 네이버 웹 검색
- `bing`: Bing 웹 검색
- `news`: 뉴스 RSS
- `youtube`: YouTube 검색

**기본값**: `['naver', 'bing', 'news']`

### 6. GUI에서 사용 (Ollama IDE)

검색 명령어를 입력하면 자동으로 검색이 실행됩니다:

```
/검색 키워드          # 네이버 + Bing + 뉴스 통합 검색 (기본)
/네이버 키워드        # 네이버 웹 검색
/유튜브 키워드        # 유튜브 검색
/빙 키워드            # Bing 웹 검색
/뉴스 키워드          # 뉴스 검색
```

예시:
```
/검색 주요 뉴스
/검색 파이썬 배우기
/네이버 맛집 추천
/빙 최신 기술 동향
/유튜브 기타 강좌
/뉴스 인공지능
```

## 📦 필요한 라이브러리

```bash
pip install requests beautifulsoup4 lxml
```

## ⚠️ 주의사항

1. **네이버 검색**: 
   - HTML 구조 변경 시 크롤링이 작동하지 않을 수 있습니다
   - 과도한 요청은 차단될 수 있습니다
   - 검색 유형(blog, news, web)에 따라 HTML 구조가 다릅니다

2. **Bing 검색** (🆕):
   - 국제 검색 지원으로 다양한 콘텐츠 수집 가능
   - 네이버보다 안정적인 HTML 구조
   - 실시간 뉴스 검색 지원

3. **유튜브 검색**:
   - 유튜브는 동적 로딩을 사용하므로 제한적입니다
   - 더 정확한 결과를 위해서는 YouTube Data API 사용을 권장합니다
   - 현재는 검색 URL만 생성하고 기본 정보 제공

4. **뉴스 RSS**:
   - RSS 피드 구조에 의존합니다
   - 신문사에서 피드를 제공하지 않으면 검색 불가

5. **Rate Limiting**: 
   - 검색 요청 간 적절한 딜레이 권장
   - 대량 크롤링 시 IP 차단 가능
   - 다중 검색 시 소스당 1초 이상 간격 권장

## 🔧 커스터마이징

### User-Agent 변경

```python
# naver_search.py의 headers 수정
headers = {
    'User-Agent': '원하는 User-Agent 문자열'
}
```

### 검색 결과 개수 조절

```python
# limit 파라미터 조정
results = get_naver_results("키워드", limit=10)  # 10개까지
```

### 검색 유형별 파싱 추가

`naver_search.py`의 `get_naver_results()` 함수에서 검색 유형별 파싱 로직을 추가할 수 있습니다.

## 📊 반환 형식

### 네이버 검색 결과
```python
{
    'title': '제목',
    'description': '설명',
    'url': 'https://...',
    'date': '날짜'
}
```

### Bing 검색 결과 (🆕)
```python
{
    'title': '제목',
    'description': '설명',
    'url': 'https://...',
    'date': '날짜',
    'source': 'Bing'
}
```

### 유튜브 검색 결과
```python
{
    'title': '제목',
    'url': 'https://...',
    'channel': '채널명',
    'description': '설명'
}
```

### 뉴스 RSS 결과
```python
{
    'title': '제목',
    'description': '본문 요약',
    'url': 'https://...',
    'date': '발행일',
    'source': '매체명'
}
```

### 다중 검색 결과
```python
{
    'naver': [{'title': '...', 'url': '...', ...}, ...],
    'bing': [{'title': '...', 'url': '...', ...}, ...],
    'news': [{'title': '...', 'url': '...', ...}, ...],
    'youtube': [{'title': '...', 'url': '...', ...}, ...]
}
```

## 🐛 문제 해결

### 검색 결과가 없을 때
- 네이버/유튜브의 HTML 구조가 변경되었을 수 있습니다
- 브라우저 개발자 도구로 현재 구조를 확인하세요

### 인코딩 오류
- `encoding='utf-8'` 명시적으로 지정
- BeautifulSoup 파서 변경: `html.parser` → `lxml`

### 연결 오류
- 인터넷 연결 확인
- timeout 값 조정: `requests.get(url, timeout=20)`

## 📝 라이센스

이 모듈은 교육 및 개인 프로젝트 용도로 사용됩니다.
상업적 크롤링은 각 플랫폼의 이용약관을 확인하세요.
