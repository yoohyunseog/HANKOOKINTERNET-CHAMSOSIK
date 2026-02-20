# 참소식.com RSS 피드 가이드

## 개요
참소식.com에서 제공하는 RSS 피드를 **dlvr.it**에 등록하여 자동으로 최신 데이터를 공유할 수 있습니다.

## 사용 가능한 RSS 피드

### 1. 최신글 피드 (최근 순)
```
https://xn--9l4b4xi9r.com/feed.xml
```
- **설명**: 최근에 추가된 N/B 계산 결과를 시간순으로 제공
- **업데이트**: 실시간
- **항목 수**: 기본 30개 (limit 파라미터로 조정 가능)
- **용도**: 최신 정보 추적

**사용 예:**
```
https://xn--9l4b4xi9r.com/feed.xml?limit=50  # 50개 항목 반환
```

### 2. 인기글 피드 (조회수 순)
```
https://xn--9l4b4xi9r.com/feed-popular.xml
```
- **설명**: 조회수가 가장 많은 N/B 계산 결과를 제공
- **업데이트**: 실시간
- **항목 수**: 기본 30개 (limit 파라미터로 조정 가능)
- **용도**: 인기있는 콘텐츠 추적

**사용 예:**
```
https://xn--9l4b4xi9r.com/feed-popular.xml?limit=100  # 100개 항목 반환
```

### 3. Sitemap (SEO)
```
https://xn--9l4b4xi9r.com/sitemap.xml
```
- **설명**: 사이트의 구조를 검색 엔진에 알림
- **용도**: 검색 엔진 최적화

## dlvr.it 등록 방법

### 1단계: dlvr.it 접속
1. https://dlvr.it/ 접속
2. 새 계정 생성 또는 로그인

### 2단계: RSS 피드 추가
1. Dashboard에서 "New Feed" 클릭
2. RSS 피드 URL 복사:
   ```
   https://xn--9l4b4xi9r.com/feed.xml
   ```
   또는
   ```
   https://xn--9l4b4xi9r.com/feed-popular.xml
   ```

### 3단계: 배포 채널 설정
dlvr.it을 통해 다음 채널로 자동 배포 가능:
- **Twitter** (X)
- **Facebook**
- **LinkedIn**
- **Slack**
- **Discord**
- **Telegram**
- **기타 웹훅**

### 4단계: 스케줄 조정
- **갱신 빈도**: 기본 12시간 (필요시 조정)
- **포스팅 시간**: 원하는 시간 설정

## RSS 피드 항목 정보

각 항목(Item)에는 다음 정보가 포함됩니다:

```xml
<item>
    <title>키워드 또는 데이터</title>
    <description>
        카테고리: 드라마
        MAX: 45 | MIN: 23
        유형: 텍스트
        조회수: 1250
    </description>
    <link>https://xn--9l4b4xi9r.com#timestamp</link>
    <category>드라마</category>
    <pubDate>발행 날짜</pubDate>
    <guid>고유 식별자</guid>
</item>
```

### 포함되는 카테고리
- 정치, 경제, 사회, 문화, 게임, 드라마, 영화, 애니메이션, 괴물딴지
- 스포츠, 기술, 국제, 연예, 사건사고, 건강, 교육, 일반

## 활용 예시

### 예1: Twitter/X에 자동 포스팅
```
✨ 인기글 피드를 dlvr.it으로 설정
→ 조회수 많은 콘텐츠가 자동으로 트윗됨
```

### 예2: Slack 알림
```
RSS 피드를 Slack 채널과 연동
→ 새로운 데이터가 추가되면 자동으로 팀에 알림
```

### 예3: 웹훅
```
Custom webhook 이용
→ 자신의 서비스에 데이터 자동 전달
```

## HTTP 파라미터

### limit 파라미터
구글의 최신 몇 개 항목만 반환할지 지정

```
GET /feed.xml?limit=50    # 50개 항목
GET /feed.xml?limit=100   # 100개 항목
```

- **기본값**: 30
- **최소값**: 1
- **최대값**: 1000 이상

## 유의사항

1. **URL 도메인**: 
   - 한국 도메인: `https://xn--9l4b4xi9r.com/`
   - 한글: 참소식.com → 퓨니코드: xn--9l4b4xi9r.com

2. **업데이트 주기**:
   - 최신글 피드: 신규 항목이 추가될 때마다 즉시 반영
   - 인기글 피드: 조회수 변동 시 실시간 갱신

3. **캐싱**:
   - RSS 리더기의 캐시 정책에 따라 반영 시간이 다를 수 있음
   - dlvr.it은 기본 12시간 주기로 확인

4. **문자 인코딩**:
   - 모든 피드는 UTF-8 인코딩
   - 한글/특수문자 완벽 지원

## 피드 검증

온라인 RSS 검증 도구를 이용하여 피드가 정상작동하는지 확인:
- https://www.feedvalidator.org/
- https://validator.w3.org/feed/

## 기술 문제

### 피드가 안 보일 때
1. URL이 정확한지 확인
2. 도메인이 `xn--9l4b4xi9r.com`인지 확인
3. 네트워크 연결 상태 확인
4. 브라우저 캐시 삭제

### 항목이 안 나타날 때
1. `limit` 파라미터 확인
2. RSS 리더의 갱신 설정 시간 확인
3. dlvr.it 대시보드에서 수동 갱신 시도

## 추가 정보

- **웹사이트**: https://xn--9l4b4xi9r.com/
- **API 문서**: `/api/recent`, `/api/most-viewed`
- **RSS 2.0 표준**: https://www.rssboard.org/rss-specification

---

**최종 수정**: 2026년 2월 20일
