# 참소식.com 블로그 포스팅 가이드

이 문서는 참소식.com 블로그에 포스팅을 작성하는 방법과 디자인 양식, 그리고 구글 애드센스 광고 추가 방법을 설명합니다.

---

## 📁 디렉토리 구조

```
blog/
├── index.html              # 블로그 메인 페이지
├── README.md               # 이 파일
├── generate_index_json.bat # posts/index.json 자동 생성 실행 파일
├── generate_index_json.ps1 # posts/index.json 자동 생성 스크립트
├── assets/                 # 포스팅 이미지 저장 폴더
├── posts/                  # 포스팅 HTML 파일 및 포스팅별 폴더 저장
│   ├── index.json          # 포스팅 메타데이터 (제목, 요약, 날짜, 카테고리)
│   ├── 2026-06-10-xxx.html # 개별 포스팅 파일
│   └── post-slug/          # 이미지가 많은 포스팅은 폴더형으로 관리
│       ├── 2026-06-14-post-slug.html
│       ├── post-slug-cover.png
│       └── post-slug-transcript.txt
├── generated_posts/        # 자동 생성된 마크다운 포스트
├── js/                     # JavaScript 파일
└── bots/                   # 봇 관련 파일
```

---

## 📝 포스팅 작성 양식

### 1. 파일 명명 규칙

파일명은 다음 형식을 따릅니다:
```
YYYY-MM-DD-제목-키워드.html
```

이미지와 원문 기록 파일이 함께 있는 포스팅은 다음처럼 포스팅별 폴더 안에 HTML을 함께 넣습니다:

```
posts/포스팅-슬러그/YYYY-MM-DD-포스팅-슬러그.html
posts/포스팅-슬러그/포스팅-슬러그-cover.png
posts/포스팅-슬러그/포스팅-슬러그-transcript.txt
```

폴더형 포스팅에서는 HTML 기준 상대경로가 한 단계 깊어지므로 `common-site.css`, `domain-check.js`, `view-tracker.js`, 블로그 목록 링크를 각각 새 위치에 맞게 조정합니다.

**예시:**
- `2026-06-10-latest-humanoid-robots-2026.html`
- `2026-06-11-cybersecurity-not-hacking.html`
- `2026-06-10-market-flow-90-dollar-lens.html`

### 2. 기본 HTML 템플릿

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="index, follow">
  <meta name="description" content="포스팅 요약 설명 (150-160자 권장)">
  <meta name="keywords" content="키워드1, 키워드2, 키워드3">
  <link rel="icon" href="../../favicon.svg" type="image/svg+xml">
  <link rel="apple-touch-icon" href="../../favicon.svg">
  <link rel="canonical" href="https://xn--9l4b4xi9r.com/blog/posts/파일명.html">

  <!-- Open Graph (소셜 미디어 공유용) -->
  <meta property="og:type" content="article">
  <meta property="og:locale" content="ko_KR">
  <meta property="og:site_name" content="참소식.com">
  <meta property="og:url" content="https://xn--9l4b4xi9r.com/blog/posts/파일명.html">
  <meta property="og:title" content="포스팅 제목">
  <meta property="og:description" content="포스팅 요약 설명">
  <meta property="og:image" content="https://xn--9l4b4xi9r.com/blog/assets/이미지파일.png">
  <meta property="article:published_time" content="2026-06-11">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="포스팅 제목">
  <meta name="twitter:description" content="포스팅 요약 설명">
  <meta name="twitter:image" content="https://xn--9l4b4xi9r.com/blog/assets/이미지파일.png">

  <title>포스팅 제목 | 참소식.com 블로그</title>
  <link rel="stylesheet" href="../../common-site.css">
  <style>
    /* 포스팅 전용 스타일 (아래 참조) */
  </style>
</head>
<body>
  <script src="../../domain-check.js"></script>

  <main class="post-container">
    <a href="../" class="post-back">← 블로그 목록으로</a>

    <header class="post-header">
      <div class="post-meta">
        <time datetime="2026-06-11">2026-06-11</time>
        <span>카테고리</span>
        <span>태그</span>
        <span class="post-views" id="view-count">조회수 로딩중...</span>
      </div>
      <h1>포스팅 제목</h1>
      <p class="post-subtitle">부제목 또는 요약 문장</p>
    </header>

    <figure class="hero-figure">
      <img src="../assets/대표이미지.png" alt="이미지 설명">
      <figcaption>이미지 캡션</figcaption>
    </figure>

    <article class="post-content">
      <!-- 포스팅 본문 -->
      <p>첫 번째 문단...</p>
      
      <h2>섹션 제목</h2>
      <p>내용...</p>
      
      <!-- 구글 애드센스 광고 (섹션 사이) -->
      <ins class="adsbygoogle"
           style="display:block"
           data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
           data-ad-slot="XXXXXXXXXX"
           data-ad-format="auto"
           data-full-width-responsive="true"></ins>
      <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
      
      <h2>다음 섹션</h2>
      <p>내용...</p>
    </article>

    <footer class="post-footer">
      <!-- 푸터 내용 -->
    </footer>
  </main>

  <footer class="site-footer">
    <p>&copy; 2026 참소식.com</p>
  </footer>

  <!-- 구글 애드센스 스크립트 (</body> 바로 앞) -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>
</body>
</html>
```

---

## 🎨 CSS 스타일 가이드

### 색상 변수 (CSS Variables)

```css
:root {
  color-scheme: dark;
  --page: #08111c;
  --surface: #111d2d;
  --ink: #f3f7fb;
  --muted: #b6c6d8;
  --line: rgba(180, 205, 230, 0.2);
  --blue: #75b7ff;
  --green: #6ee7b7;
  --amber: #f6c35d;
  --red: #ff746d;
  --teal: #70e0d0;
  --highlight: rgba(122, 184, 255, 0.15);
}
```

### 텍스트 색상 클래스

```css
/* 텍스트 색상 변화 */
.post-content .text-blue { color: var(--blue); }
.post-content .text-amber { color: var(--amber); }
.post-content .text-red { color: var(--red); }
.post-content .text-teal { color: var(--teal); }
.post-content .text-muted { color: var(--muted); }

/* 밑줄 강조 */
.post-content .underline {
  text-decoration: underline;
  text-decoration-color: var(--blue);
  text-underline-offset: 3px;
}
```

### 주요 스타일 클래스

| 클래스 | 용도 |
|--------|------|
| `.post-container` | 포스팅 전체 컨테이너 (최대 너비 960px) |
| `.post-back` | 블로그 목록으로 돌아가기 링크 |
| `.post-header` | 제목, 메타정보 영역 |
| `.post-meta` | 날짜, 카테고리, 태그 표시 |
| `.hero-figure` | 대표 이미지 영역 |
| `.post-content` | 본문 영역 |
| `.model-table` | 데이터 테이블 |
| `.note-box` | 중요 정보 박스 |
| `.source-list` | 참고 자료 목록 |
| `.post-footer` | 포스팅 하단 영역 |
| `.site-footer` | 사이트 전체 푸터 |
| `.lede` | 리드 문단 (첫 문단 강조) |
| `.quote` | 인용문 박스 (황색 테두리) |
| `.quote.warning` | 경고성 인용문 (빨간색 테두리) |
| `.key-point` | 핵심 주장 박스 (파란색 테두리) |
| `.source-box` | 출처/근거 박스 (청록색 테두리) |
| `strong.highlight` | 형광펜 스타일 강조 |
| `mark` | 하이라이트 마커 |
| `.text-blue` | 파란색 텍스트 |
| `.text-amber` | 황색 텍스트 |
| `.text-red` | 빨간색 텍스트 |
| `.text-teal` | 청록색 텍스트 |
| `.text-muted` | 회색 텍스트 |
| `.underline` | 밑줄 강조 |

### 표 스타일

```html
<table class="model-table">
  <thead>
    <tr><th>컬럼1</th><th>컬럼2</th><th>컬럼3</th></tr>
  </thead>
  <tbody>
    <tr><td>데이터1</td><td>데이터2</td><td>데이터3</td></tr>
  </tbody>
</table>
```

### 노트 박스 스타일

```html
<div class="note-box">
  <p><strong>중요 정보</strong>: 내용을 여기에 작성합니다.</p>
</div>
```

### 참고 자료 목록

```html
<ul class="source-list">
  <li><a href="URL" target="_blank" rel="noopener">출처 제목</a></li>
</ul>
```

---

## ✨ 핵심 문장 강조 마크업 가이드

### 1. 형광펜 스타일 강조 (`<strong class="highlight">`)

핵심 문장에 형광펜 효과를 적용합니다. 배경색이 문장 아래에 깔리며 가독성을 높입니다.

```html
<strong class="highlight">이것은 핵심 문장입니다.</strong>
```

**CSS 정의:**
```css
.post-content strong.highlight {
  background: linear-gradient(transparent 60%, rgba(122, 184, 255, 0.25) 60%);
  color: #fff;
}
```

**사용 예시:**
```html
<p>폐쇄망 네트워크의 본질은 <strong class="highlight">자본금의 흐름에 있다</strong>.</p>
<p>이것은 단순한 사적 갈등이 아니다. <strong class="highlight">이것은 권한과 자본, 기술과 폐쇄망이 결합한 통제 구조가 된다.</strong></p>
```

---

### 2. 하이라이트 마커 (`<mark>`)

중요 키워드나 짧은 구절에 하이라이트 효과를 적용합니다.

```html
<mark>중요 키워드</mark>
```

**CSS 정의:**
```css
.post-content mark {
  background: rgba(241, 184, 92, 0.2);
  color: #f6e3bf;
  padding: 2px 4px;
  border-radius: 3px;
}
```

**사용 예시:**
```html
<p>북한은 자본의 출처라기보다 <mark>폐쇄망의 운영 방식, 통제 방식, 고립 방식에서 밀접하게 관련될 수밖에 없는 구조에 가깝다.</mark></p>
<p>자본이 들어오면 사람도 들어오고, 기술도 들어오고, 권한도 따라오고, 네트워크도 형성된다. 그리고 그 자본이 제대로 된 검증 없이 폐쇄적 구조와 결합하면, <mark>자유와 기회의 자본이 아니라 특정 타깃을 고립시키는 통제의 연료가 될 수 있다.</mark></p>
```

---

### 3. 핵심 주장 박스 (`<div class="key-point">`)

가장 중요한 핵심 주장을 별도 박스로 강조합니다. 파란색 테두리와 배경이 적용됩니다.

```html
<div class="key-point">
  <strong>핵심 주장 내용</strong>
</div>
```

**CSS 정의:**
```css
.key-point {
  background: rgba(122, 184, 255, 0.15);
  border-left: 4px solid var(--blue);
  padding: 17px 19px;
  border-radius: 8px;
  margin: 26px 0;
  color: #dceaff;
}
.key-point strong {
  color: var(--blue);
}
```

**사용 예시:**
```html
<div class="key-point">
  <strong>따라서 이 문제의 중심에는 자본금이 있다.</strong>
</div>

<div class="key-point">
  <p><strong>폐쇄망 네트워크는 단순한 어둠의 정보망이 아니다.</strong></p>
  <p>그것은 개인정보 오남용, 평판 조작, 생계 압박, 기술 감시, 조직적 고립, 권한의 오남용 가능성, 투자 자본이 결합된 현실형 통제 구조다.</p>
</div>
```

---

### 4. 인용문 스타일 (`<div class="quote">`)

중요한 인용문이나 강조할 문장을 별도 박스로 표시합니다. 황색 테두리와 배경이 적용됩니다.

```html
<div class="quote">
  인용문 내용
</div>
```

**CSS 정의:**
```css
.quote {
  border-left: 4px solid var(--amber);
  background: rgba(241, 184, 92, 0.08);
  padding: 17px 19px;
  border-radius: 8px;
  margin: 26px 0;
  color: #f6e3bf;
}
```

**사용 예시:**
```html
<div class="quote">다크웹은 어둠 속에 있다는 자각이라도 있다. 하지만 이 폐쇄망은 밝은 곳에서 움직인다.</div>

<div class="quote">
  <p>피해자는 흩어져 있고, 폐쇄망은 연결되어 있다.</p>
  <p>피해자는 혼자 설명해야 하고, 구조는 집단으로 침묵한다.</p>
  <p>피해자는 증거를 요구받고, 구조는 책임을 회피한다.</p>
</div>
```

---

### 5. 경고성 인용문 (`<div class="quote warning">`)

위험하거나 주의해야 할 내용을 강조합니다. 빨간색 테두리와 배경이 적용됩니다.

```html
<div class="quote warning">
  경고 내용
</div>
```

**CSS 정의:**
```css
.quote.warning {
  border-left-color: var(--red);
  background: rgba(255, 116, 109, 0.08);
  color: #ffd8d5;
}
```

**사용 예시:**
```html
<div class="quote warning">피해자는 분명히 무너진다. 하지만 공격자는 보이지 않는다. 책임자는 사라진다. 남는 것은 이상해진 타깃뿐이다.</div>

<div class="quote warning">
  <p>미국 자본금, 중국 자본금, 지역 폐쇄망, 북한식 통제 방식, 정부 관리자 권한에 가까운 접근 권한이 뒤섞이면 이 구조는 더 흐려진다.</p>
  <p>책임의 방향도 흐려지고, 피해의 원인도 흐려지고, 문제의 출발점도 흐려진다.</p>
</div>
```

---

### 6. 출처/근거 박스 (`<div class="source-box">`)

출처나 근거가 되는 정보를 정리하여 표시합니다. 청록색 테두리와 배경이 적용됩니다.

```html
<div class="source-box">
  <strong>제목:</strong>
  <ul>
    <li>항목 1</li>
    <li>항목 2</li>
  </ul>
</div>
```

**CSS 정의:**
```css
.source-box {
  border: 1px solid rgba(112, 224, 208, 0.28);
  background: rgba(112, 224, 208, 0.055);
  border-radius: 8px;
  padding: 18px;
  margin: 28px 0;
}
.source-box strong {
  color: var(--teal);
}
```

**사용 예시:**
```html
<div class="source-box">
  <strong>결합된 원인들:</strong>
  <ul>
    <li>개인정보에 대한 낮은 인식</li>
    <li>해킹을 기술처럼 포장하는 문화</li>
    <li>지역 사회의 폐쇄성</li>
    <li>플랫폼의 무책임</li>
    <li>보안 산업의 왜곡</li>
    <li>투자 자본의 무지</li>
    <li>권한의 오남용 가능성</li>
    <li>피해자를 의심하는 사회 분위기</li>
    <li>법적 대응의 한계</li>
  </ul>
</div>
```

---

### 7. 밑줄 강조 (`<u>` 또는 CSS)

텍스트에 밑줄을 추가하여 강조합니다.

```html
<u>밑줄이 있는 텍스트</u>
```

또는 커스텀 클래스 사용:

```html
<span class="underline">밑줄이 있는 텍스트</span>
```

**CSS 정의:**
```css
.post-content .underline {
  text-decoration: underline;
  text-decoration-color: var(--blue);
  text-underline-offset: 3px;
}
```

---

### 8. 폰트 색상 변화

다양한 색상으로 텍스트를 강조합니다.

```html
<span class="text-blue">파란색 텍스트</span>
<span class="text-amber">황색 텍스트</span>
<span class="text-red">빨간색 텍스트</span>
<span class="text-teal">청록색 텍스트</span>
<span class="text-muted">회색 텍스트</span>
```

**CSS 정의:**
```css
.post-content .text-blue { color: var(--blue); }
.post-content .text-amber { color: var(--amber); }
.post-content .text-red { color: var(--red); }
.post-content .text-teal { color: var(--teal); }
.post-content .text-muted { color: var(--muted); }
```

**사용 예시:**
```html
<p><span class="text-red">이것은 위험한 신호입니다.</span> 주의가 필요합니다.</p>
<p>핵심은 <span class="text-blue">자본금의 흐름</span>에 있다.</p>
```

---

### 9. 굵은 텍스트 (`<strong>`, `<b>`)

기본적인 굵은 텍스트 강조입니다.

```html
<strong>굵은 텍스트</strong>
<b>굵은 텍스트</b>
```

---

### 10. 기울임 텍스트 (`<em>`, `<i>`)

기울임꼴로 강조합니다.

```html
<em>기울임 텍스트</em>
<i>기울임 텍스트</i>
```

---

### 11. 복합 강조 예시

여러 강조 스타일을 조합하여 사용할 수 있습니다.

```html
<p>이 글의 핵심은 단순한 인권 침해 문제가 아니다. 오히려 <strong class="highlight">"인권"이라는 말이 이 문제의 본질을 가리는 역할을 할 수 있다</strong>는 점이다.</p>

<div class="key-point">
  <strong>왜냐하면 이 폐쇄망 네트워크의 본질은 피해자의 권리 침해에만 있는 것이 아니라, 그 구조를 유지하고 확장시킨 자본금의 흐름에 있기 때문이다.</strong>
</div>

<p>미국 자본금이 이곳으로 흘러들어갔다고 보면 많은 것이 설명된다. <strong class="highlight">해외 투자, 플랫폼 산업, 기술 산업, 광고 시장, 데이터 산업, 보안 산업, 지역 네트워크, 노동 시장이 하나의 폐쇄망 구조와 결합</strong>될 수 있기 때문이다.</p>

<div class="quote warning">
  <p>미국 자본금, 중국 자본금, 지역 폐쇄망, 북한식 통제 방식, 정부 관리자 권한에 가까운 접근 권한이 뒤섞이면 이 구조는 더 흐려진다.</p>
  <p>책임의 방향도 흐려지고, 피해의 원인도 흐려지고, 문제의 출발점도 흐려진다.</p>
</div>

<p><strong class="highlight">그것은 통제다.</strong></p>
<p><strong class="highlight">그리고 통제는 결코 자유를 만들 수 없다.</strong></p>
```

---

### 12. 강조 스타일 요약표

| 스타일 | HTML | 용도 | 색상 |
|--------|------|------|------|
| 형광펜 강조 | `<strong class="highlight">` | 핵심 문장 | 파란색 배경 |
| 하이라이트 마커 | `<mark>` | 중요 키워드 | 황색 배경 |
| 핵심 주장 박스 | `<div class="key-point">` | 가장 중요한 주장 | 파란색 테두리 |
| 인용문 | `<div class="quote">` | 중요 인용문 | 황색 테두리 |
| 경고성 인용문 | `<div class="quote warning">` | 위험/주의 내용 | 빨간색 테두리 |
| 출처 박스 | `<div class="source-box">` | 출처/근거 정보 | 청록색 테두리 |
| 밑줄 | `<u>` 또는 `.underline` | 밑줄 강조 | 파란색 밑줄 |
| 파란색 텍스트 | `.text-blue` | 파란색 강조 | #75b7ff |
| 황색 텍스트 | `.text-amber` | 황색 강조 | #f6c35d |
| 빨간색 텍스트 | `.text-red` | 위험/경고 강조 | #ff746d |
| 청록색 텍스트 | `.text-teal` | 정보 강조 | #6ee7b7 |

---

## 📊 구글 애드센스 광고 추가 방법

### 1단계: 애드센스 계정 설정

1. [Google AdSense](https://www.google.com/adsense/)에 접속
2. 계정 승인 후 광고 단위 생성
3. **광고 코드**에서 `ca-pub-XXXXXXXXXXXXXXXX` 형식의 **Publisher ID** 확인

### 2단계: 광고 코드 삽입 위치

#### A. HEAD에 스크립트 추가 (선택사항)

```html
<head>
  <!-- 기존 메타 태그들... -->
  
  <!-- 자동 광고 (선택사항 - 구글이 자동으로 광고 배치) -->
  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4501795912654667" crossorigin="anonymous"></script>
</head>
```

#### B. 본문 내 광고 단위 삽입

**위치 1: 글 시작 후 (히어로 이미지 다음)**

```html
<article class="post-content">
  <p>첫 번째 문단...</p>
  
  <!-- 인피드 광고 -->
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-format="fluid"
       data-ad-layout-key="-gw-3+1f-3d+2z"
       data-ad-client="ca-pub-4501795912654667"
       data-ad-slot="5464507878"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
  
  <h2>섹션 제목</h2>
  <p>내용...</p>
</article>
```

**위치 2: 글 중간 (섹션 사이)**

```html
<h2>섹션 1</h2>
<p>내용...</p>

<!-- 인피드 광고 -->
<ins class="adsbygoogle"
     style="display:block"
     data-ad-format="fluid"
     data-ad-layout-key="-gw-3+1f-3d+2z"
     data-ad-client="ca-pub-4501795912654667"
     data-ad-slot="5464507878"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>

<h2>섹션 2</h2>
<p>내용...</p>
```

**위치 3: 글 끝 (참고 자료 전)**

```html
<p>마지막 문단...</p>

<!-- 광고 -->
<ins class="adsbygoogle"
     style="display:block"
     data-ad-format="fluid"
     data-ad-layout-key="-gw-3+1f-3d+2z"
     data-ad-client="ca-pub-4501795912654667"
     data-ad-slot="5464507878"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>

<h2>참고 자료</h2>
```

### 3단계: 광고 형식 옵션

| 형식 | 코드 | 설명 |
|------|------|------|
| 자동 광고 | `data-ad-format="auto"` | 구글이 자동으로 최적 크기 선택 |
| 인아티클 광고 | `data-ad-format="in-article"` | 글 내부에 자연스럽게 삽입 |
| 인피드 광고 | `data-ad-format="in-feed"` | 콘텐츠 목록 사이에 삽입 |
| 멀티플렉스 광고 | `data-ad-format="multiplex"` | 여러 광고를 그리드로 표시 |

### 4단계: 반응형 광고 설정

```html
<ins class="adsbygoogle"
     style="display:block; text-align:center;"
     data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
     data-ad-slot="XXXXXXXXXX"
     data-ad-layout="in-article"
     data-ad-format="fluid"
     data-full-width-responsive="true"></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
```

### 5단계: 광고 스타일 커스터마이징 (선택사항)

```css
/* 광고 컨테이너 스타일 */
.ad-container {
  margin: 30px 0;
  padding: 20px 0;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

/* 인아티클 광고 배경 */
.adsbygoogle {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
}
```

---

## 📋 포스팅 체크리스트

### 작성 전

- [ ] 주제 선정 및 키워드 조사
- [ ] 대표 이미지 준비 (1200x630px 권장, PNG/JPG)
- [ ] 참고 자료 URL 수집

### 작성 중

- [ ] SEO 메타 태그 작성 (title, description, keywords)
- [ ] Open Graph 태그 설정
- [ ] Twitter Card 태그 설정
- [ ] canonical URL 설정
- [ ] 이미지 alt 속성 추가
- [ ] 외부 링크에 `target="_blank" rel="noopener"` 추가

### 작성 후

- [ ] `generate_index_json.bat` 실행으로 `posts/index.json` 자동 갱신
- [ ] 이미지를 `assets/` 폴더에 저장
- [ ] 모바일 반응형 확인
- [ ] 링크 정상 작동 확인
- [ ] 조회수 스크립트 동작 확인

---

## 📦 index.json 메타데이터 형식

새 포스팅을 추가한 후에는 `posts/index.json`을 직접 수정하지 말고 블로그 폴더의 자동 생성 배치를 실행합니다:

```bat
generate_index_json.bat
```

스크립트는 `posts/` 아래의 모든 `.html` 파일을 하위 폴더까지 검색해 제목, 요약, 날짜, 카테고리, 대표 이미지를 추출하고 `posts/index.json`을 다시 만듭니다.

아래 형식은 자동 생성되는 메타데이터 구조를 확인하거나 수동 점검할 때 참고합니다:

### 기본 형식

```json
{
  "title": "포스팅 제목",
  "excerpt": "포스팅 요약 설명 (150자 내외)",
  "date": "2026-06-11 12:00:00",
  "category": "카테고리명",
  "href": "posts/파일명.html",
  "views": 0
}
```

### 필드 설명

| 필드 | 필수 | 설명 | 예시 |
|------|------|------|------|
| `title` | ✅ | 포스팅 제목 (HTML의 `<h1>`과 동일) | `"폐쇄망, 트라우마, 악성 자본, 그리고 내가 N/B 알고리즘을 설계한 이유"` |
| `excerpt` | ✅ | 포스팅 요약 (150자 내외, SEO description과 동일) | `"검증 없는 자본은 구원이 아니다. 폐쇄망에 흘러 들어간 자본은 악성 구조의 연료가 될 수 있다."` |
| `date` | ✅ | 작성일시 (YYYY-MM-DD HH:MM:SS) | `"2026-06-11 12:00:00"` |
| `category` | ✅ | 카테고리 (메타 태그의 category와 동일) | `"폐쇄망 분석"`, `"시장 분석"`, `"정보 보안"` |
| `href` | ✅ | 포스팅 파일 경로 (posts/ 접두사 필수) | `"posts/2026-06-11-closed-network-trauma-malignant-capital-nb-algorithm.html"` |
| `views` | ✅ | 조회수 (초기값: 0) | `0` |

폴더형 포스팅의 `href` 예시:

```json
"href": "posts/ha-jiwon-kyunghee-festival-cheer/2026-06-14-ha-jiwon-kyunghee-festival-cheer.html"
```

### 추가 예시

```json
[
  {
    "title": "폐쇄망, 트라우마, 악성 자본, 그리고 내가 N/B 알고리즘을 설계한 이유",
    "excerpt": "검증 없는 자본은 구원이 아니다. 폐쇄망에 흘러 들어간 자본은 악성 구조의 연료가 될 수 있다. 트라우마의 연골 고리와 악성 폐쇄망이 결합될 때 개인은 매우 취약해질 수 있다.",
    "date": "2026-06-11 12:00:00",
    "category": "폐쇄망 분석",
    "href": "posts/2026-06-11-closed-network-trauma-malignant-capital-nb-algorithm.html",
    "views": 0
  },
  {
    "title": "내가 배운 정보 보안은 해킹이 아니었다",
    "excerpt": "정보 보안은 해킹이 아니라 보호, 예방, 절차, 책임이라는 원칙에서 출발한다. 해킹, 개인정보 침해, 폐쇄망, 사적 심판의 위험을 공식 보안·개인정보 기준과 함께 분석한다.",
    "date": "2026-06-11 01:24:00",
    "category": "정보 보안",
    "href": "posts/2026-06-11-cybersecurity-not-hacking.html",
    "views": 0
  }
]
```

### ⚠️ 주의사항

1. **JSON 배열 형식**: 전체가 배열 `[]`로 감싸져 있어야 합니다
2. **쉼표 구분**: 각 포스팅 객체 사이에 쉼표 `,`를 넣어야 합니다 (마지막 항목 제외)
3. **새 포스팅은 맨 앞에 추가**: 최신 포스팅이 상단에 오도록 배열의 첫 번째에 추가합니다
4. **파일명 일치**: `href`의 파일명이 실제 HTML 파일명과 정확히 일치해야 합니다
5. **날짜 형식**: `YYYY-MM-DD HH:MM:SS` 형식을 사용합니다
6. **자동 생성 우선**: 포스팅 수가 많아지면 수동 편집 대신 `generate_index_json.bat`을 실행합니다

### 🔄 포스팅 추가 워크플로우

```
1. HTML 포스팅 작성
   ↓
2. posts/ 폴더 또는 posts/포스팅-슬러그/ 폴더에 HTML 파일 저장
   ↓
3. assets/ 폴더 또는 포스팅별 폴더에 이미지 저장
   ↓
4. generate_index_json.bat 실행
   ↓
5. posts/index.json 자동 갱신 확인
   ↓
6. 블로그 메인 페이지에서 새 글 노출 확인
   ↓
7. 링크와 이미지 경로 확인
```

---

## 🖼️ 이미지 가이드

### 대표 이미지 (히어로 이미지)

- **크기**: 1200x630px (Open Graph 권장 크기)
- **형식**: PNG 또는 JPG
- **저장 위치**: `blog/assets/파일명-cover.png`
- **파일명 규칙**: `포스팅키워드-cover.png`

### 본문 이미지

- **최대 너비**: 840px
- **형식**: PNG, JPG, WebP
- **저장 위치**: `blog/assets/`

### 이미지 HTML 예시

```html
<figure class="hero-figure">
  <img src="../assets/post-title-cover.png" alt="이미지 설명 (SEO 중요)">
  <figcaption>이미지 출처 또는 설명</figcaption>
</figure>
```

---

## 🔗 링크 작성 가이드

### 내부 링크

```html
<a href="../posts/다른-포스팅.html">관련 포스팅</a>
```

### 외부 링크 (Google 검색 링크 포함)

```html
<a class="sentence-search-inline" 
   href="https://www.google.com/search?q=검색어" 
   target="_blank" 
   rel="noopener">링크 텍스트</a>
```

### 일반 외부 링크

```html
<a href="https://example.com" target="_blank" rel="noopener">링크 텍스트</a>
```

---

## ⚠️ 주의사항

1. **광고 정책 준수**
   - 한 페이지당 광고는 3-5개 권장
   - 콘텐츠보다 광고가 많지 않도록 주의
   - 광고 클릭 유도 금지

2. **SEO 최적화**
   - 제목은 60자 이내
   - 설명은 150-160자
   - 키워드는 5-10개
   - H1은 페이지당 1개만

3. **접근성**
   - 모든 이미지에 alt 속성 필수
   - 충분한 색상 대비 유지
   - 키보드 내비게이션 가능하게

4. **성능**
   - 이미지 최적화 (압축)
   - 불필요한 스크립트 제거
   - CSS는 `<style>` 태그로 인라인 가능

---

## � RSS 피드

### RSS 피드란?

RSS(Really Simple Syndication)는 블로그의 새 포스팅을 구독자에게 자동으로 전달하는 표준 포맷입니다. RSS 피드를 통해 독자는 이메일 구독 없이도 새 글을 받아볼 수 있습니다.

### RSS 피드 위치

```
blog/posts/rss.xml
```

**전체 URL:**
```
https://xn--9l4b4xi9r.com/blog/posts/rss.xml
```

### RSS 피드 구조

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>참소식.com 블로그</title>
    <link>https://xn--9l4b4xi9r.com/blog/</link>
    <description>참소식.com의 최신 블로그 포스팅</description>
    <language>ko</language>
    <lastBuildDate>Fri, 13 Jun 2026 00:00:00 +0900</lastBuildDate>
    
    <item>
      <title>포스팅 제목</title>
      <link>https://xn--9l4b4xi9r.com/blog/posts/파일명.html</link>
      <description>포스팅 요약</description>
      <pubDate>발행일</pubDate>
      <category>카테고리</category>
    </item>
  </channel>
</rss>
```

### RSS 피드 활용 방법

#### 1. 웹사이트에 RSS 링크 추가

HTML `<head>`에 다음을 추가:

```html
<link rel="alternate" type="application/rss+xml" 
      title="참소식.com 블로그 RSS" 
      href="https://xn--9l4b4xi9r.com/blog/posts/rss.xml">
```

#### 2. RSS 아이콘 버튼 추가

```html
<a href="https://xn--9l4b4xi9r.com/blog/posts/rss.xml" 
   target="_blank" 
   title="RSS 구독">
  <img src="../assets/rss-icon.svg" alt="RSS" width="24" height="24">
</a>
```

---

## 🔄 dlvr.it 연동 가이드 (자동 소셜 미디어 포스팅)

### dlvr.it이란?

[dlvr.it](https://dlvr.it)은 RSS 피드를 읽어 트위터(X), 페이스북, LinkedIn 등 소셜 미디어에 자동으로 포스팅해주는 서비스입니다.

### 설정 방법

#### 1단계: dlvr.it 계정 생성

1. [https://dlvr.it](https://dlvr.it) 접속
2. "Get Started" 클릭
3. 이메일, 비밀번호 입력하여 계정 생성
4. 이메일 인증 완료

#### 2단계: 소셜 계정 연결

1. 로그인 후 대시보드에서 **"Socials"** 메뉴 클릭
2. **"Add Social"** 버튼 클릭
3. 연결할 소셜 미디어 선택:
   - **Twitter/X**: 트위터 계정 연결
   - **Facebook Page**: 페이스북 페이지 연결
   - **LinkedIn**: 링크드인 계정/페이지 연결
   - **Instagram**: 비즈니스 계정 연결
   - **Pinterest**: 핀터레스트 보드 연결
4. 각 플랫폼별 OAuth 인증 진행

#### 3단계: RSS 피드 연결

1. 대시보드에서 **"Routes"** 메뉴 클릭
2. **"Create Route"** 버튼 클릭
3. **Source** 설정:
   - **Source Type**: RSS Feed
   - **Feed URL**: `https://xn--9l4b4xi9r.com/blog/posts/rss.xml`
   - **Feed Name**: 참소식 블로그
4. **Destination** 설정:
   - 연결한 소셜 계정 선택
   - 여러 계정 선택 가능

#### 4단계: 포스팅 설정

**기본 설정:**
- **Post Template**: 포스팅 형식 템플릿
  ```
  {title}
  
  {link}
  
  {description}
  ```

- **Post Limit**: 포스팅 길이 제한
  - Twitter: 280자 (자동 잘림)
  - Facebook: 제한 없음

- **Include Image**: 이미지 포함 여부
  - ✅ 체크 권장 (썸네일 자동 첨부)

**고급 설정:**

| 설정 | 설명 | 권장값 |
|------|------|--------|
| **Check Interval** | RSS 피드 확인 주기 | 15분 ~ 1시간 |
| **Max Posts per Check** | 한 번에 포스팅할 최대 글 수 | 3개 |
| **Post Delay** | 포스팅 간 지연 시간 | 5분 |
| **Auto Hashtags** | 자동 해시태그 추가 | 카테고리 기반 |
| **Link Shortener** | URL 단축 서비스 | bit.ly 연동 권장 |

#### 5단계: 필터 설정 (선택사항)

특정 카테고리만 포스팅하려면:

1. **Filters** 탭 클릭
2. **Keyword Filter** 설정:
   - **Include**: 포함할 키워드 (예: "사회 분석, 기술")
   - **Exclude**: 제외할 키워드
3. **Category Filter**: RSS `<category>` 태그 기반 필터링

#### 6단계: 스케줄 설정

1. **Schedule** 탭 클릭
2. **Time Zone**: 한국 시간 (UTC+9) 설정
3. **Posting Times**:
   - 오전 9:00 ~ 오후 9:00 사이 포스팅 권장
   - 피크 시간대 설정 가능

### dlvr.it 설정 예시

```
Route Name: 참소식 블로그 → 소셜미디어

Source:
  - Type: RSS Feed
  - URL: https://xn--9l4b4xi9r.com/blog/posts/rss.xml
  - Check: Every 30 minutes

Destinations:
  - Twitter: @chamsosik
  - Facebook Page: 참소식.com
  - LinkedIn: 참소식 페이지

Template:
  {title}
  {link}
  
  #참소식 #뉴스

Settings:
  - Include Image: Yes
  - Post Delay: 5 minutes between posts
  - Max Posts: 3 per check
```

### RSS 피드 업데이트 시 dlvr.it 동작

1. 새 포스팅이 `index.json`에 추가됨
2. `rss.xml` 파일도 함께 업데이트됨
3. dlvr.it이 설정된 간격으로 RSS 피드 확인
4. 새 포스팅 감지 시 소셜 미디어에 자동 포스팅

### 문제 해결

| 문제 | 해결 방법 |
|------|----------|
| RSS 피드가 인식되지 않음 | XML 문법 오류 확인, `lastBuildDate` 업데이트 |
| 이미지가 포함되지 않음 | RSS `<enclosure>` 태그 추가 또는 dlvr.it 이미지 설정 확인 |
| 포스팅이 중복됨 | RSS `<guid>` 태그가 고유한지 확인 |
| 한글이 깨짐 | XML 인코딩이 UTF-8인지 확인 |

---

## 🔄 RSS 피드 업데이트 방법

새 포스팅 추가 시 `rss.xml` 파일도 함께 업데이트해야 합니다.

### 수동 업데이트

1. `posts/rss.xml` 파일 열기
2. 새 `<item>` 요소를 `<channel>` 내 맨 앞에 추가:

```xml
<item>
  <title>새 포스팅 제목</title>
  <link>https://xn--9l4b4xi9r.com/blog/posts/파일명.html</link>
  <guid isPermaLink="true">https://xn--9l4b4xi9r.com/blog/posts/파일명.html</guid>
  <description>포스팅 요약 설명</description>
  <content:encoded><![CDATA[<p>포스팅 요약 설명</p>]]></content:encoded>
  <pubDate>발행일 (RFC 822 형식: Mon, 12 Jun 2026 03:00:00 +0900)</pubDate>
  <category>카테고리</category>
  <author>참소식.com</author>
</item>
```

3. `<lastBuildDate>` 업데이트:
```xml
<lastBuildDate>Fri, 13 Jun 2026 00:00:00 +0900</lastBuildDate>
```

### 자동 업데이트 (Python 스크립트 예시)

```python
import json
from datetime import datetime
import xml.etree.ElementTree as ET

def generate_rss_from_index():
    # index.json 읽기
    with open('posts/index.json', 'r', encoding='utf-8') as f:
        posts = json.load(f)
    
    # RSS XML 생성
    rss = ET.Element('rss', version='2.0')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    rss.set('xmlns:content', 'http://purl.org/rss/1.0/modules/content/')
    
    channel = ET.SubElement(rss, 'channel')
    
    # 채널 정보 추가
    ET.SubElement(channel, 'title').text = '참소식.com 블로그'
    ET.SubElement(channel, 'link').text = 'https://xn--9l4b4xi9r.com/blog/'
    ET.SubElement(channel, 'description').text = '참소식.com의 최신 블로그 포스팅'
    ET.SubElement(channel, 'language').text = 'ko'
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0900')
    
    # 포스팅 추가 (최대 20개)
    for post in posts[:20]:
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = post['title']
        ET.SubElement(item, 'link').text = f"https://xn--9l4b4xi9r.com/blog/{post['href']}"
        ET.SubElement(item, 'guid', isPermaLink='true').text = f"https://xn--9l4b4xi9r.com/blog/{post['href']}"
        ET.SubElement(item, 'description').text = post['excerpt']
        ET.SubElement(item, 'pubDate').text = post['date']
        ET.SubElement(item, 'category').text = post['category']
    
    # XML 저장
    tree = ET.ElementTree(rss)
    tree.write('posts/rss.xml', encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
    generate_rss_from_index()
```

---

## 📞 문의

블로그 관련 문의사항은 참소식.com 관리자에게 연락하세요.

---

*최종 업데이트: 2026-06-14*
---

## 2026-06-14 추가 포스팅

- 제목: 하지원, 경희대 축제에서 되찾은 청춘의 낭만
- 폴더: `posts/ha-jiwon-kyunghee-festival-cheer/`
- 파일: `posts/ha-jiwon-kyunghee-festival-cheer/2026-06-14-ha-jiwon-kyunghee-festival-cheer.html`
- 대표 이미지: `posts/ha-jiwon-kyunghee-festival-cheer/ha-jiwon-kyunghee-cheer-stage.png`
- 원문 기록 파일: `posts/ha-jiwon-kyunghee-festival-cheer/ha-jiwon-kyunghee-festival-cheer-transcript.txt`
- 분류: 웹예능 리뷰
- 목록 갱신: `generate_index_json.bat` 실행

## 2026-06-13 추가 포스팅

- 제목: 내가 본 UFO, 그리고 다시 부르고 싶지 않은 이유
- 파일: `posts/2026-06-13-ufo-jesus-peace-record.html`
- 포스터 HTML: `posts/2026-06-13-ufo-jesus-peace-poster.html`
- 분류: 신앙 기록
- 끝 링크: [참소식.com/ai 검색](https://www.google.com/search?q=%EC%B0%B8%EC%86%8C%EC%8B%9D.com%2Fai)

### 문장형 구글 검색 링크 양식

본문 안에서 단어 하나가 아니라 문장 전체를 검색어로 연결할 때는 아래처럼 작성합니다.

```html
<a class="search-link"
   href="https://www.google.com/search?q=%EB%82%98%EB%8A%94+UFO%EB%A5%BC+%EB%8B%A4%EC%8B%9C+%EB%B6%80%EB%A5%B4%EA%B3%A0+%EC%8B%B6%EC%A7%80+%EC%95%8A%EB%8B%A4"
   target="_blank"
   rel="noopener noreferrer">나는 그 UFO를 다시 부르고 싶지 않다.</a>
```

### 강화 마크업 규칙

포스트 본문이나 네이버 블로그 복붙용 포스터를 만들 때는 중요한 단어와 핵심 문장을 그냥 텍스트로 두지 말고, 색상·밑줄·굵기·검색 링크를 함께 적용합니다.

핵심 원칙은 다음과 같습니다.

- **핵심 단어**에는 굵기와 색상을 적용합니다.
- **중요 문장**에는 밑줄 또는 배경색을 함께 적용합니다.
- **검색 링크가 걸리는 단어/문장**은 반드시 `target="_blank"`와 `rel="noopener noreferrer"`를 포함합니다.
- **검색어는 항상 `제목 + 해당 문장` 형태**로 만듭니다.
- 색상은 주로 **주황색**, **보라색**, **노란색**, **빨간색**을 사용합니다.
- 글 전체 마지막에는 **전체 글 요약문을 검색어로 하는 구글 검색 링크**를 넣습니다.

권장 색상은 다음과 같습니다.

```css
/* 주황색: 핵심 키워드, 주요 링크 */
color:#ff8a1f;

/* 보라색: 분석 포인트, 구조 설명 */
color:#a855f7;

/* 노란색: 결론, 요약, 주의 문장 */
color:#facc15;

/* 빨간색: 경고, 문제 제기, 강한 문장 */
color:#ef4444;
```

#### 핵심 단어 마크업 예시

아래 예시는 제목이 `메이플스토리 OVERDRIVE 총정리`이고, 핵심 단어가 `하이퍼 블링크`일 때의 형식입니다.

```html
<a href="https://www.google.com/search?q=%EB%A9%94%EC%9D%B4%ED%94%8C%EC%8A%A4%ED%86%A0%EB%A6%AC%20OVERDRIVE%20%EC%B4%9D%EC%A0%95%EB%A6%AC%20%ED%95%98%EC%9D%B4%ED%8D%BC%20%EB%B8%94%EB%A7%81%ED%81%AC"
   target="_blank"
   rel="noopener noreferrer"
   style="color:#ff8a1f; font-weight:900; text-decoration:underline; text-decoration-color:#facc15;">
  하이퍼 블링크
</a>
```

#### 핵심 문장 마크업 예시

중요 문장은 단어보다 더 강하게 처리합니다. 문장 전체를 링크로 감싸고, 검색어는 `제목 + 해당 문장`으로 만듭니다.

```html
<a href="https://www.google.com/search?q=%EB%A9%94%EC%9D%B4%ED%94%8C%EC%8A%A4%ED%86%A0%EB%A6%AC%20OVERDRIVE%20%EC%B4%9D%EC%A0%95%EB%A6%AC%20OVERDRIVE%EC%9D%98%20%ED%95%B5%EC%8B%AC%EC%9D%80%20%EB%8D%94%20%EB%A7%8E%EC%9D%B4%20%EC%B6%94%EA%B0%80%ED%95%98%EB%8A%94%20%EA%B2%83%EB%B3%B4%EB%8B%A4%20%EB%8D%94%20%EB%B9%A8%EB%A6%AC%20%EB%8B%A4%EC%8B%9C%20%EB%B6%99%EC%9E%A1%EB%8A%94%20%EA%B2%83%EC%9D%B4%EB%8B%A4"
   target="_blank"
   rel="noopener noreferrer"
   style="color:#facc15; font-weight:900; text-decoration:underline; text-decoration-thickness:2px; background:#2a1a0c;">
  OVERDRIVE의 핵심은 더 많이 추가하는 것보다 더 빨리 다시 붙잡는 것이다.
</a>
```

#### 문제 제기 문장 마크업 예시

글 안에서 경고, 우려, 문제 제기를 할 때는 빨간색을 사용합니다.

```html
<a href="https://www.google.com/search?q=%EB%A9%94%EC%9D%B4%ED%94%8C%EC%8A%A4%ED%86%A0%EB%A6%AC%20OVERDRIVE%20%EC%B4%9D%EC%A0%95%EB%A6%AC%20%EC%84%B1%EC%9E%A5%20%EC%86%8D%EB%8F%84%EA%B0%80%20%EB%B9%A8%EB%9D%BC%EC%A0%B8%EB%8F%84%20%EB%8B%A4%EC%9D%8C%20%EB%AA%A9%ED%91%9C%EA%B0%80%20%EC%97%86%EC%9C%BC%EB%A9%B4%20%EC%9C%A0%EC%A0%80%EB%8A%94%20%EB%8B%A4%EC%8B%9C%20%EB%A9%88%EC%B6%98%EB%8B%A4"
   target="_blank"
   rel="noopener noreferrer"
   style="color:#ef4444; font-weight:900; text-decoration:underline; text-decoration-color:#ff8a1f;">
  성장 속도가 빨라져도 다음 목표가 없으면 유저는 다시 멈춘다.
</a>
```

#### 분석 포인트 마크업 예시

구조 분석이나 관찰 문장은 보라색을 사용합니다.

```html
<a href="https://www.google.com/search?q=%EB%A9%94%EC%9D%B4%ED%94%8C%EC%8A%A4%ED%86%A0%EB%A6%AC%20OVERDRIVE%20%EC%B4%9D%EC%A0%95%EB%A6%AC%20%EC%95%84%EC%9D%B4%ED%85%9C%20%EB%B2%84%EB%8B%9D%EC%9D%80%20%EC%9E%A5%EB%B9%84%20%EC%84%B1%EC%9E%A5%EC%9D%98%20%EB%B3%91%EB%AA%A9%EC%9D%84%20%ED%92%80%EC%96%B4%EC%A3%BC%EB%8A%94%20%EC%9E%A5%EC%B9%98%EB%8B%A4"
   target="_blank"
   rel="noopener noreferrer"
   style="color:#a855f7; font-weight:900; text-decoration:underline; text-decoration-color:#facc15;">
  아이템 버닝은 장비 성장의 병목을 풀어주는 장치다.
</a>
```

#### 문단 안에서 여러 색을 섞는 예시

```html
<p style="font-size:18px; line-height:2; color:#f6f0e8;">
  이번 업데이트의 핵심은
  <a href="https://www.google.com/search?q=제목%20성장%20속도"
     target="_blank"
     rel="noopener noreferrer"
     style="color:#ff8a1f; font-weight:900; text-decoration:underline;">성장 속도</a>,
  <a href="https://www.google.com/search?q=제목%20장비%20성장"
     target="_blank"
     rel="noopener noreferrer"
     style="color:#a855f7; font-weight:900; text-decoration:underline;">장비 성장</a>,
  <a href="https://www.google.com/search?q=제목%20복귀%20유저"
     target="_blank"
     rel="noopener noreferrer"
     style="color:#facc15; font-weight:900; text-decoration:underline;">복귀 유저</a>
  를 한 번에 연결하는 데 있다.
</p>
```

#### 맨 마지막 전체 요약 검색 링크 양식

포스트의 마지막에는 전체 글을 한 문장으로 요약한 뒤, 그 요약문을 검색어로 하는 구글 검색 링크를 넣습니다. 이때 검색어도 `제목 + 전체 요약문`으로 구성합니다.

```html
<div style="margin:38px 0 0; padding:22px 20px; border:1px solid #ff8a1f; border-radius:12px; background:#111926;">
  <p style="margin:0 0 14px; color:#facc15; font-size:16px; font-weight:900; line-height:1.8;">
    전체 글 요약 검색
  </p>
  <p style="margin:0 0 18px; color:#f6f0e8; font-size:17px; line-height:2;">
    메이플스토리 OVERDRIVE는 하이퍼 블링크, 버닝 비욘드, 아이템 버닝, 제네시스 패스 플러스를 통해 복귀 유저의 성장 속도와 다음 목표를 다시 연결하는 여름 쇼케이스다.
  </p>
  <a href="https://www.google.com/search?q=%EB%A9%94%EC%9D%B4%ED%94%8C%EC%8A%A4%ED%86%A0%EB%A6%AC%20OVERDRIVE%20%EC%B4%9D%EC%A0%95%EB%A6%AC%20%EB%A9%94%EC%9D%B4%ED%94%8C%EC%8A%A4%ED%86%A0%EB%A6%AC%20OVERDRIVE%EB%8A%94%20%ED%95%98%EC%9D%B4%ED%8D%BC%20%EB%B8%94%EB%A7%81%ED%81%AC%2C%20%EB%B2%84%EB%8B%9D%20%EB%B9%84%EC%9A%98%EB%93%9C%2C%20%EC%95%84%EC%9D%B4%ED%85%9C%20%EB%B2%84%EB%8B%9D%2C%20%EC%A0%9C%EB%84%A4%EC%8B%9C%EC%8A%A4%20%ED%8C%A8%EC%8A%A4%20%ED%94%8C%EB%9F%AC%EC%8A%A4%EB%A5%BC%20%ED%86%B5%ED%95%B4%20%EB%B3%B5%EA%B7%80%20%EC%9C%A0%EC%A0%80%EC%9D%98%20%EC%84%B1%EC%9E%A5%20%EC%86%8D%EB%8F%84%EC%99%80%20%EB%8B%A4%EC%9D%8C%20%EB%AA%A9%ED%91%9C%EB%A5%BC%20%EB%8B%A4%EC%8B%9C%20%EC%97%B0%EA%B2%B0%ED%95%98%EB%8A%94%20%EC%97%AC%EB%A6%84%20%EC%87%BC%EC%BC%80%EC%9D%B4%EC%8A%A4%EB%8B%A4"
     target="_blank"
     rel="noopener noreferrer"
     style="display:block; padding:15px 18px; border-radius:10px; background:#ff8a1f; color:#111111; font-size:17px; line-height:1.6; font-weight:900; text-align:center; text-decoration:none;">
    전체 요약문으로 구글 검색하기
  </a>
</div>
```

#### 작성 체크리스트

- 제목이 정해졌는가?
- 핵심 단어마다 `제목 + 핵심 단어` 검색 링크를 걸었는가?
- 핵심 문장마다 `제목 + 해당 문장` 검색 링크를 걸었는가?
- 주황색, 보라색, 노란색, 빨간색 강조를 균형 있게 사용했는가?
- 밑줄, 굵기, 배경색 중 최소 2개 이상의 강조가 핵심 문장에 적용되었는가?
- 마지막에 `제목 + 전체 요약문` 구글 검색 링크를 넣었는가?

### 포스터 양식

새 포스트의 HTML 포스터는 `blog/posts/날짜-슬러그-poster.html` 형식으로 저장합니다. 블로그 목록 썸네일이 필요하면 `blog/assets/날짜-슬러그-poster.svg` 같은 이미지 파일을 별도로 만들고 `posts/index.json`의 `image` 필드에 연결합니다.

*최종 업데이트: 2026-06-14*
