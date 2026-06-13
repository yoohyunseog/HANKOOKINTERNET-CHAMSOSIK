# 📚 Vatican Blog 포스터 작성 가이드

이 문서는 참소식.com Vatican Blog 섹션에 포스터(블로그 포스트)를 작성하고 디자인하는 방법을 설명합니다.

---

## 📁 디렉토리 구조

```
blog/
├── README.md                    # 이 가이드 파일
├── assets/                      # 이미지 및 미디어 자산
│   ├── images/                  # 포스터 이미지
│   └── thumbnails/              # 썸네일 이미지
└── [포스터-슬러그]/              # 각 포스터 디렉토리
    ├── index.html               # 포스터 소개/목차 페이지
    ├── 01-intro.html            # 챕터 1
    ├── 02-chapter.html          # 챕터 2
    └── ...
```

---

## 🎨 디자인 시스템

### 색상 팔레트 (CSS 변수)

```css
:root {
  --wine: #6f1018;        /* 와인색 - 주요 강조색 */
  --wine-dark: #4b090f;   /* 진한 와인색 - 헤더 배경 */
  --gold: #c98b26;        /* 금색 - 포인트 강조 */
  --ink: #241c19;         /* 잉크색 - 본문 텍스트 */
  --muted: #6e625c;       /* 흐릿한 색 - 부가 텍스트 */
  --line: #eadfce;        /* 테두리 색 */
  --paper: #fffdf9;       /* 종이 배경 */
  --cream: #fbf4e8;       /* 크림색 배경 */
  --shadow: 0 14px 32px rgba(76, 38, 25, .13);
}
```

### 타이포그래피

- **제목 (h1)**: Georgia, "Nanum Myeongjo", serif
- **본문**: "Noto Sans KR", "Malgun Gothic", Arial, sans-serif
- **브랜드**: Georgia, serif

---

## 📝 포스터 작성 단계

### 1단계: 포스터 디렉토리 생성

새 포스터를 위한 디렉토리를 생성합니다:

```
blog/[포스터-슬러그]/
```

예시: `blog/mar-mari-emmanuel/`

### 2단계: index.html (소개 페이지) 작성

소개 페이지는 포스터 시리즈의 진입점입니다. 다음 요소를 포함합니다:

```html
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="[포스터 설명]">
  <meta name="keywords" content="[키워드1, 키워드2, ...]">
  <meta name="author" content="참소식.com">
  <meta property="og:type" content="article">
  <meta property="og:title" content="[포스터 제목]">
  <meta property="og:description" content="[포스터 요약]">
  <link rel="icon" href="/favicon.svg" type="image/svg+xml">
  <title>[포스터 제목] | 참소식.com</title>
  <style>
    /* CSS 스타일 */
  </style>
</head>
<body>
  <!-- 헤더 -->
  <header class="topbar">
    <nav class="nav">
      <a class="brand" href="../index.html">
        <span class="brand-mark">✚</span>
        <span>참소식.com</span>
      </a>
    </nav>
  </header>

  <!-- 메인 콘텐츠 -->
  <main class="page">
    <!-- 히어로 섹션 -->
    <section class="hero">
      <h1>[포스터 제목]</h1>
      <p class="lead>[포스터 요약]</p>
    </section>

    <!-- 챕터 목록 -->
    <section class="chapters">
      <!-- 챕터 카드들 -->
    </section>
  </main>

  <footer>
    참소식.com · 말씀과 기도, 그리고 깨어 있는 믿음을 위한 기록
  </footer>
</body>
</html>
```

### 3단계: 챕터 페이지 작성

각 챕터는 다음 구조를 따릅니다:

```html
<!doctype html>
<html lang="ko">
<head>
  <!-- 메타 태그 -->
  <title>[챕터 제목] | [포스터 제목] | 참소식.com</title>
  <style>
    /* 기본 스타일 + 추가 스타일 */
  </style>
</head>
<body>
  <header class="topbar">
    <!-- 네비게이션 -->
  </header>

  <main class="page">
    <section class="hero">
      <p class="eyebrow">Chapter [N] of [TOTAL]</p>
      <h1>[챕터 제목]</h1>
      <p class="lead">[챕터 요약]</p>
      <div class="meta">
        <span>[날짜]</span>
        <span>[카테고리]</span>
        <span>[저자]</span>
      </div>
    </section>

    <div class="content">
      <article>
        <!-- 비디오 프레임 (선택사항) -->
        <h2>🎬 설교 영상</h2>
        <div class="video-frame">
          <iframe src="https://www.youtube.com/embed/[VIDEO_ID]"></iframe>
        </div>

        <!-- 본문 -->
        <h2>📖 [챕터 제목]</h2>
        <div class="story-text">
          <p>[본문 내용]</p>
        </div>

        <!-- 성경 인용 (선택사항) -->
        <div class="bible-quote">
          "[성경 구절]"
          <span class="reference">— [성경 참조]</span>
        </div>

        <!-- 노트 (선택사항) -->
        <div class="note">
          [강조할 내용]
        </div>

        <!-- 챕터 네비게이션 -->
        <div class="chapter-nav">
          <a href="[이전 챕터]">← 이전: [제목]</a>
          <a href="[다음 챕터]">다음: [제목] →</a>
        </div>

        <div class="nav-buttons">
          <a class="nav-btn" href="[이전]">← 이전 장</a>
          <a class="nav-btn primary" href="[다음]">다음 장 →</a>
        </div>
      </article>

      <aside>
        <h2 class="side-title">📖 전체 포스팅</h2>
        <div class="chapter-links">
          <a href="01-intro.html" class="chapter-link-item">
            <span class="chapter-num">1</span>
            <span class="chapter-text">서두</span>
          </a>
          <!-- 추가 챕터 링크 -->
        </div>

        <h2 class="side-title">포스팅 정보</h2>
        <ul class="side-list">
          <li>분류: [카테고리]</li>
          <li>장: [N]장 / [TOTAL]장</li>
          <li>주제: [주제1], [주제2], ...</li>
        </ul>
      </aside>
    </div>
  </main>

  <footer>
    참소식.com · 말씀과 기도, 그리고 깨어 있는 믿음을 위한 기록
  </footer>
</body>
</html>
```

---

## 🎯 필수 CSS 클래스

### 레이아웃

| 클래스 | 용도 |
|--------|------|
| `.topbar` | 상단 네비게이션 바 |
| `.page` | 메인 콘텐츠 컨테이너 |
| `.hero` | 히어로 섹션 |
| `.content` | article + aside 그리드 |
| `article` | 본문 영역 |
| `aside` | 사이드바 |

### 콘텐츠

| 클래스 | 용도 |
|--------|------|
| `.story-text` | 소설 형식 본문 |
| `.bible-quote` | 성경 인용문 |
| `.note` | 강조 노트 |
| `.video-frame` | YouTube 임베드 컨테이너 |
| `.final-message` | 마지막 메시지 (결론용) |

### 네비게이션

| 클래스 | 용도 |
|--------|------|
| `.chapter-links` | 챕터 링크 컨테이너 |
| `.chapter-link-item` | 개별 챕터 링크 |
| `.chapter-nav` | 이전/다음 네비게이션 |
| `.nav-buttons` | 하단 버튼 그룹 |
| `.nav-btn` | 네비게이션 버튼 |

### 텍스트

| 클래스 | 용도 |
|--------|------|
| `.search-word` | Google 검색 링크가 있는 키워드 |
| `.eyebrow` | 챕터 번호 표시 |
| `.lead` | 리드 문장 |
| `.meta` | 메타 정보 태그 |

---

## 📺 YouTube 영상 임베드

```html
<div class="video-frame">
  <iframe
    src="https://www.youtube.com/embed/[VIDEO_ID]"
    title="[영상 제목]"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
    referrerpolicy="strict-origin-when-cross-origin"
    allowfullscreen>
  </iframe>
</div>
```

---

## 🔍 검색 링크 추가

중요 키워드에 Google 검색 링크를 추가합니다:

```html
<a href="https://www.google.com/search?q=[검색어]"
   class="search-word"
   target="_blank"
   rel="noopener">[키워드]</a>
```

---

## 📱 반응형 디자인

모든 페이지는 반응형으로 설계되어 있습니다:

```css
@media (max-width: 820px) {
  .content { grid-template-columns: 1fr; }
  aside { position: static; }
  .nav { align-items: flex-start; flex-direction: column; padding: 12px 0; }
  .brand { font-size: 22px; }
}
```

---

## ✅ 체크리스트

새 포스터 작성 시 확인사항:

- [ ] 디렉토리 생성 (`blog/[포스터-슬러그]/`)
- [ ] index.html (소개 페이지) 작성
- [ ] 각 챕터 HTML 파일 작성
- [ ] 메타 태그 (title, description, keywords) 설정
- [ ] Open Graph 태그 설정
- [ ] 챕터 간 네비게이션 링크 확인
- [ ] 사이드바 챕터 목록 확인
- [ ] YouTube 영상 임베드 (필요시)
- [ ] 검색 링크 추가 (필요시)
- [ ] 반응형 디자인 테스트
- [ ] favicon 링크 확인 (`/favicon.svg`)

---

## 📂 예시: Mar Mari Emmanuel 포스터

```
blog/mar-mari-emmanuel/
├── index.html           # 소개 페이지
├── 01-intro.html        # 서두
├── 02-word-beginning.html  # 말씀의 시작
├── 03-fire-water.html   # 계시록의 불과 물
├── 04-to-youth.html     # 청년들에게
└── 05-conclusion.html   # 결론
```

---

## 🔗 vatican/index.html에 포스터 링크 추가

새 포스터를 작성한 후, `vatican/index.html`에 링크를 추가합니다:

```html
<a href="blog/[포스터-슬러그]/index.html" class="card">
  <h3>[포스터 제목]</h3>
  <p>[포스터 요약]</p>
  <span class="card-meta">[날짜] · [카테고리]</span>
</a>
```

---

## 📝 작성 팁

1. **일관성 유지**: 모든 챕터 페이지는 동일한 CSS 스타일을 사용합니다.
2. **네비게이션**: 각 챕터의 사이드바에서 현재 챕터에 `.active` 클래스를 추가합니다.
3. **첫 글자 강조**: `.story-text p:first-of-type::first-letter`로 첫 글자가 강조됩니다.
4. **성경 인용**: `.bible-quote` 클래스로 성경 구절을 강조합니다.
5. **노트 박스**: 중요한 메시지는 `.note` 클래스로 강조합니다.

---

*이 가이드는 참소식.com Vatican Blog의 포스터 작성 표준을 따릅니다.*