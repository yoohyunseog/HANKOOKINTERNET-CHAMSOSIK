# 참소식.com - N/B 데이터베이스 시스템

한국인터넷.한국 도메인의 참소식.com 웹사이트 - N/B 계산 및 데이터베이스 시스템

## 🌟 주요 기능

### 1. N/B 계산 시스템
- 텍스트 Unicode 기반 MAX/MIN 계산
- 숫자 배열 계산
- BIT 999 기반 정밀 계산
- 계층형 디렉토리 구조 저장

### 2. 카테고리 시스템
- AI 자동 카테고리 생성 (Ollama)
- 13개 카테고리: 정치, 경제, 사회, 문화, 스포츠, 기술, 국제, 연예, 사건사고, 건강, 교육, 일반
- 카테고리별 필터링 및 정렬

### 3. 데이터베이스
- 파일 기반 JSON 데이터베이스
- 계층형 디렉토리 구조: `data/nb_max/5/9/6/8/result_{id}.json`
- 조회수 추적 및 인기도 집계
- 최근 100개, 조회수 TOP 100 제공

### 4. 검색 및 분석
- 텍스트/Unicode 기반 검색
- Naver 크리에이터 트렌드 분석
- 자동 뉴스 수집 및 요약
- 키워드 클릭 추적

### 5. UI/UX
- Masonry 레이아웃 (반응형 3단 레이아웃)
- 카테고리 필터 버튼
- Bootstrap 5 기반 모던 디자인
- 모바일 최적화

## 📂 프로젝트 구조

```
├── web/                          # Node.js 웹 서버
│   ├── server.js                 # Express 서버
│   ├── storage.js                # 파일 기반 데이터베이스
│   ├── calculate.js              # N/B 계산 로직
│   └── public/
│       └── 한국인터넷.한국/
│           └── 참소식.com/
│               ├── index.html    # 메인 페이지 (Masonry + 카테고리)
│               └── database.html # 검색/계산 페이지
│
├── ide/                          # Python AI 도구
│   ├── ollama_ide_gui.py         # Ollama AI 채팅 GUI
│   └── ollama_chat.py            # AI 채팅 기능
│
├── 8BIT/                         # Python 분석 도구
│   ├── naver_creator_trend_analyzer.py  # 트렌드 분석
│   ├── advanced_crawler.py       # 웹 크롤러
│   └── trend_ai_local.py         # 로컬 AI 분석
│
├── data/                         # 데이터 저장소
│   ├── nb_max/                   # MAX 결과
│   ├── nb_min/                   # MIN 결과
│   ├── index.json                # 인덱스
│   └── naver_creator_trends/     # 트렌드 데이터
│
└── config/                       # 설정 파일
    └── naver_creator_config.json
```

## 🚀 시작하기

### 1. Git 저장소 초기 설정 (최초 1회)
```bash
git_init_setup.bat
```

### 2. Node.js 서버 실행
```bash
cd web
node server.js
```

### 3. 브라우저 접속
- http://localhost:3000/index.html
- http://localhost:3000/database.html

## 📤 GitHub 업로드

### 자동 업로드
```bash
upload_to_github.bat
```

### 수동 업로드
```bash
git add .
git commit -m "Update: 변경사항 설명"
git push origin main
```

## 🛠 기술 스택

### Backend
- **Node.js** + Express
- 파일 기반 JSON 데이터베이스
- RESTful API

### Frontend
- **HTML5** + **CSS3** + **JavaScript**
- **Bootstrap 5**
- CSS Columns (Masonry 레이아웃)
- Vanilla JavaScript

### AI/ML
- **Ollama** (gpt-oss:120b-cloud)
- 자동 카테고리 생성
- 뉴스 요약 및 분석

### Python Tools
- **Selenium** (동적 페이지 렌더링)
- **BeautifulSoup** (HTML 파싱)
- **Requests** (HTTP 클라이언트)
- **Tkinter** (GUI)

## 📊 API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/calculate` | N/B 계산 및 저장 (category 포함) |
| POST | `/api/search` | 텍스트/Unicode 검색 |
| GET | `/api/recent?limit=100` | 최근 계산 결과 |
| GET | `/api/most-viewed?limit=100` | 조회수 많은 순 |
| GET | `/api/stats` | 통계 정보 |
| GET | `/api/calculation/:id` | 단일 조회 |
| GET | `/api/track-keyword` | 키워드 클릭 추적 |

## 🎨 카테고리 시스템

AI가 텍스트 내용을 분석하여 자동으로 카테고리를 생성합니다:

- 정치 / 경제 / 사회 / 문화
- 스포츠 / 기술 / 국제 / 연예
- 사건사고 / 건강 / 교육 / 일반

## 📝 데이터 저장 형식

```json
{
  "id": "abc123def456",
  "timestamp": "2026-02-20T00:00:00.000Z",
  "type": "text",
  "input": "예시 텍스트",
  "unicode": [50696, 49884, ...],
  "bit": 999,
  "category": "기술",
  "view_count": 5,
  "results": [{
    "calculation": 1,
    "nb_max": 5968.1234,
    "nb_min": 0.0012,
    "difference": 5968.1222
  }]
}
```

## 🔧 환경 설정

### Node.js 패키지
```bash
cd web
npm install express body-parser geoip-lite
```

### Python 패키지
```bash
pip install -r 8BIT/requirements_naver_creator.txt
pip install -r 8BIT/requirements_crawler.txt
```

### Ollama 설정
```bash
ollama pull gpt-oss:120b-cloud
```

## 📜 라이센스

Copyright © 2026 참소식.com

## 👤 작성자

yoohyunseog

## 🔗 링크

- Repository: https://github.com/yoohyunseog/HANKOOKINTERNET-CHAMSOSIK
- Website: 참소식.com (한국인터넷.한국)
