# 서버 작업 일지

## 2026년 6월 4일 (수)

### 🎯 바티칸 교황청 소식 페이지 실시간 업데이트 구현

#### 1. 메인 페이지 동적 데이터 로드 구현
- **파일**: `web/public/한국인터넷.한국/참소식.com/vatican/index.html`
- **작업 내용**:
  - JavaScript 추가하여 `vatican_news.json`에서 동적으로 뉴스 데이터 로드
  - JavaScript 추가하여 `vatican_videos.json`에서 동적으로 영상 데이터 로드
  - 뉴스 카드 섹션 실시간 렌더링 구현
  - YouTube 영상 섹션 추가 (사이드바)
  - 5분마다 자동 새로고침 기능 구현
  - 업데이트 시간 표시 기능 추가

#### 2. 게시판 페이지 생성
- **파일**: `web/public/한국인터넷.한국/참소식.com/vatican/board/index.html`
- **작업 내용**:
  - 전체 뉴스 목록을 볼 수 있는 게시판 페이지 생성
  - 검색 기능 (제목/내용 검색)
  - 언어 필터 (전체/한국어/영어)
  - 페이지네이션 기능 (10개씩 표시)
  - "더보기" 링크를 게시판으로 연결

#### 3. 향상된 Vatican Bot 생성
- **파일**: `web/public/한국인터넷.한국/참소식.com/vatican/bot/vatican_bot_enhanced.py`
- **작업 내용**:
  - 뉴스 소스 확장 (8개 소스):
    - Vatican News 한국어/영어/이탈리아어
    - News.va 한국어
    - Vatican Official
    - Catholic News Agency
    - National Catholic Register
    - Crux Now
  - AI 기반 한글 번역 기능 (kimi-k2.5:cloud 모델 사용)
  - AI 기반 요약 기능 (3문장 요약)
  - 카테고리 분류 기능
  - 향상된 본문 추출 알고리즘
  - 키워드 점수 시스템 개선

#### 4. Bot 실행 주기 변경
- **파일**: `web/public/한국인터넷.한국/참소식.com/vatican/bot/run_vatican_bot.bat`
- **작업 내용**:
  - 실행 주기: 30분 → 10분으로 단축

#### 5. 서버 배포
- **배포 파일**:
  - `/var/www/chamsosik/vatican/index.html` - 메인 페이지
  - `/var/www/chamsosik/vatican/board/index.html` - 게시판 페이지
  - `/var/www/chamsosik/vatican/vatican_news.json` - 뉴스 데이터 (15개)
  - `/var/www/chamsosik/vatican/vatican_videos.json` - 영상 데이터 (6개)

#### 6. 수집 결과
- **뉴스**: 15개 기사 (AI 요약 및 번역 포함)
- **영상**: 6개 YouTube 영상
- **소스**: Vatican News, Catholic News Agency, National Catholic Register, Crux Now

---

## 2026년 6월 3일 (화)

### 🎯 웹 서버 설정 및 nginx 구성

#### 1. nginx 사이트 설정
- **작업 내용**:
  - `/etc/nginx/sites-enabled/default` 설정 수정
  - `한국인터넷.한국` 도메인 설정
  - Node.js 백엔드 프록시 설정
  - SSL 인증서 설정 확인

#### 2. Node.js 서버 실행
- **작업 내용**:
  - PM2를 통한 Node.js 서버 관리
  - 서버 로그 확인 및 디버깅
  - 포트 3000에서 서버 실행

#### 3. 도메인 및 DNS 설정
- **작업 내용**:
  - `한국인터넷.한국` (Punycode: `xn--3e0bx5eku0am2irhf.xn--3e0b707e`) 도메인 설정
  - nginx 가상 호스트 설정
  - CORS 및 보안 헤더 설정

---

## 2026년 6월 2일 (월)

### 🎯 프로젝트 초기 설정 및 구조 파악

#### 1. 프로젝트 구조 확인
- **위치**: `e:\Ai project\사이트`
- **주요 디렉토리**:
  - `web/public/한국인터넷.한국/참소식.com/` - 참소식 웹사이트
  - `vatican/` - 바티칸 교황청 소식 페이지
  - `bot/` - 뉴스 수집 봇

#### 2. 기존 Vatican Bot 분석
- **파일**: `vatican_bot.py`
- **기능**:
  - Vatican News에서 뉴스 수집
  - YouTube 영상 정보 수집
  - Ollama AI를 통한 요약

#### 3. 서버 환경 확인
- **서버**: `211.45.162.155`
- **Ollama**: `http://211.45.162.155:11434`
- **모델**: `kimi-k2.5:cloud`, `glm-5:cloud`

---

## 요약

### 완료된 작업
1. ✅ 바티칸 소식 페이지 실시간 업데이트 구현
2. ✅ 게시판 페이지 생성
3. ✅ 향상된 뉴스 수집 봇 개발
4. ✅ AI 번역 및 요약 기능 구현
5. ✅ 서버 배포 완료

### 개선 필요 사항
1. ⚠️ AI 번역/요약 안정화 (일부 기사만 번역됨)
2. ⚠️ 뉴스 소스 다양화
3. ⚠️ 에러 처리 강화

### 기술 스택
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Backend**: Python, Selenium, BeautifulSoup
- **AI**: Ollama (kimi-k2.5:cloud)
- **Server**: nginx, Node.js
- **Data**: JSON 파일 기반

---

*최종 업데이트: 2026년 6월 4일*