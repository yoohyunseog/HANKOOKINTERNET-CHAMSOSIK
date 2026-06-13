# AI 분석 요약 데이터 (ai_analysis_summary.json)

## 개요

이 JSON 파일은 참소식 블로그(`index.html`)의 **대시보드 영역**에 표시되는 정적 콘텐츠를 정의합니다. 카드 영역(포스트 목록)을 제외한 모든 데이터가 포함됩니다.

## 파일 구조

```
ai_analysis_summary.json
├── metadata                    # 메타데이터
├── blog_info                  # 블로그 기본 정보
├── dashboard                  # 대시보드 데이터 (카드 제외)
│   ├── summary_banner         # AI 분석 요약 배너
│   └── sidebar                # 사이드바 데이터
└── analysis                   # 상세 분석 데이터
    ├── overall_impression     # AI 전체 인상
    ├── thematic_analysis      # 주제별 분석
    ├── post_summaries         # 포스트 요약
    └── conclusion            # 결론
```

## 섹션 설명

### 1. `metadata` (메타데이터)

```json
{
  "metadata": {
    "analysis_date": "2026-06-12",
    "analyzer": "GitHub Copilot AI",
    "version": "3.0",
    "description": "참소식 블로그 AI 분석 요약 데이터"
  }
}
```

| 필드 | 설명 |
|------|------|
| `analysis_date` | 분석 날짜 |
| `analyzer` | 분석 수행자 |
| `version` | 데이터 구조 버전 |
| `description` | 파일 용도 설명 |

### 2. `blog_info` (블로그 기본 정보)

```json
{
  "blog_info": {
    "title": "참소식 블로그",
    "subtitle": "기술·데이터와 인사이트로 세상을 더 명확하게 바라보는 참된 블로그",
    "url": "https://xn--9l4b4xi9r.com/blog/"
  }
}
```

Hero 섹션에 표시되는 블로그 제목과 설명입니다.

### 3. `dashboard` (대시보드)

#### 3.1 `summary_banner` (AI 분석 요약 배너)

```json
{
  "summary_banner": {
    "title": "AI 분석 요약",
    "badge": "오늘의 인사이트",
    "description": "주요 주제는...",
    "metrics": {
      "total_posts": { "label": "주요 글 개수", "value": 36, "unit": "건" },
      "insights": { "label": "공감 인사이트", "value": 14, "unit": "건" },
      "warnings": { "label": "위험 신호", "value": 7, "unit": "건" }
    }
  }
}
```

index.html의 `<section class="summary-banner">` 영역에 매핑됩니다.

#### 3.2 `sidebar` (사이드바)

```json
{
  "sidebar": {
    "key_insights": {
      "title": "핵심 요약",
      "items": ["미국 네트워크·인프라 취약성과...", "..."]
    },
    "keywords": {
      "title": "핵심 키워드",
      "items": ["네트워크", "N/B", "인프라", ...]
    },
    "mood": {
      "title": "전체 분위기",
      "score": 56,
      "max_score": 100,
      "status": "중립 · 관망",
      "description": "불확실성과 리스크 요인이..."
    },
    "topics": {
      "title": "관련 주제 TOP 6",
      "items": [
        { "rank": 1, "name": "네트워크 인프라", "count": 18 },
        ...
      ]
    }
  }
}
```

index.html의 `<aside class="sidebar">` 영역에 매핑됩니다.

### 4. `analysis` (상세 분석)

#### 4.1 `overall_impression` (AI 전체 인상)

```json
{
  "overall_impression": {
    "title": "AI가 느낀 점: 폐쇄망 네트워크와 개인의 투쟁",
    "summary": "이 블로그는...",
    "key_insights": [...],
    "emotional_response": {
      "tone": "분석적이면서도 깊은 공감",
      "felt_emotions": [...]
    }
  }
}
```

#### 4.2 `thematic_analysis` (주제별 분석)

```json
{
  "thematic_analysis": {
    "main_themes": [
      {
        "theme": "폐쇄망 네트워크 분석",
        "post_count": 12,
        "description": "...",
        "key_posts": [...]
      },
      ...
    ]
  }
}
```

#### 4.3 `post_summaries` (포스트 요약)

```json
{
  "post_summaries": [
    {
      "title": "백도어 개념이 국가 정상급 대화에 등장한 이유",
      "date": "2026-06-11",
      "category": "사회 분석",
      "summary": "...",
      "ai_impression": "..."
    },
    ...
  ]
}
```

#### 4.4 `conclusion` (결론)

```json
{
  "conclusion": {
    "overall_assessment": "...",
    "strengths": [...],
    "areas_for_consideration": [...],
    "ai_final_thoughts": "..."
  }
}
```

## index.html과의 매핑

| JSON 경로 | HTML 요소 | 설명 |
|-----------|-----------|------|
| `dashboard.summary_banner.title` | `.summary-title` | AI 분석 요약 제목 |
| `dashboard.summary_banner.badge` | `.pill` | 오늘의 인사이트 배지 |
| `dashboard.summary_banner.description` | `.summary-copy` | 요약 설명 텍스트 |
| `dashboard.summary_banner.metrics` | `.metric-row` | 분석 지표 (3개) |
| `dashboard.sidebar.key_insights.items` | `.insight-list` | 핵심 요약 목록 |
| `dashboard.sidebar.keywords.items` | `.keyword-list` | 키워드 태그 |
| `dashboard.sidebar.mood` | `.mood` | 전체 분위기 게이지 |
| `dashboard.sidebar.topics.items` | `.topic-list` | 관련 주제 TOP 6 |

## 사용 방법

### JavaScript에서 데이터 로드

```javascript
// JSON 파일 로드
fetch('ai_analysis_summary.json')
  .then(response => response.json())
  .then(data => {
    // 대시보드 데이터 사용
    const { dashboard } = data;
    
    // 요약 배너 업데이트
    document.querySelector('.summary-copy').textContent = dashboard.summary_banner.description;
    
    // 지표 업데이트
    const metrics = dashboard.summary_banner.metrics;
    // ...
  });
```

### 데이터 업데이트 주기

- **정적 데이터**: 블로그 포스트 추가/수정 시 수동 업데이트
- **동적 데이터**: 포스트 카드는 `index.html` 내 `posts` 배열에서 관리

## 버전 히스토리

| 버전 | 날짜 | 변경 사항 |
|------|------|-----------|
| 3.0 | 2026-06-12 | `dashboard` 구조로 재설계, `metadata` 추가 |
| 2.0 | 2026-06-10 | `post_summaries` 구조 개선 |
| 1.0 | 2026-06-01 | 초기 버전 |

## 관련 파일

- `index.html` - 블로그 메인 페이지
- `posts/*.html` - 개별 포스트 파일
- `js/view-tracker.js` - 조회수 추적 스크립트

---

**작성자**: GitHub Copilot AI  
**최종 수정**: 2026-06-12