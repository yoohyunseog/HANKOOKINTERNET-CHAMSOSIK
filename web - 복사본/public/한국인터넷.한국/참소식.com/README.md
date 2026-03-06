# 참소식.com - N/B 데이터베이스 시스템

## 개요

참소식.com은 N/B 계산기의 결과를 저장하고 검색하는 데이터베이스 시스템입니다.

## 사이트 구조

```
참소식.com/
├── index.html           # 메인 랜딩 페이지
├── database.html        # 데이터베이스 검색 인터페이스
├── ErrPage/            # 커스텀 에러 페이지 (400, 401, 403, 404, 500, 502, 503)
└── www.xn--9l4b4xi9r.com_202506016D73B/  # SSL 인증서
```

## 주요 기능

### 1. 데이터베이스 검색 (database.html)
- **N/B MAX 범위 검색**: 최소값-최대값 범위로 검색
- **N/B MIN 범위 검색**: 최소값-최대값 범위로 검색
- **Unicode 배열 검색**: 쉼표로 구분된 Unicode 값 (예: 111,107,101,101,100,121)

### 2. 통계 대시보드
- 총 계산 수
- MAX 결과 수
- MIN 결과 수

### 3. 데이터베이스 구조 문서
- N/B 계산 결과 구조 (계층형 디렉터리)
- 인덱스 구조

## 데이터베이스 스키마

### N/B 계산 결과
```
data/nb_max/5/9/6/8/result_nb_calc_12345.json
data/nb_min/9/9/9/0/result_nb_calc_12345.json
```

**JSON 형식:**
```json
{
  "calculation_id": "nb_calc_12345",
  "input": "안녕하세요",
  "unicode": [50504, 45397, 54616, 49464, 50836],
  "bit": 999,
  "results": [
    { "iteration": 1, "nb_max": 5.9686932681, "nb_min": 999.0000000000 },
    { "iteration": 2, "nb_max": 5.9686932681, "nb_min": 999.0000000000 },
    { "iteration": 3, "nb_max": 5.9686932681, "nb_min": 999.0000000000 }
  ],
  "created_at": "2026-02-18T12:00:00Z"
}
```

### 인덱스
```
data/indexes/nb_max_index.json
data/indexes/nb_min_index.json
data/indexes/unicode_index.json
```

**nb_max_index.json:**
```json
{
  "5.9686932681": ["nb_calc_12345", "nb_calc_67890"]
}
```

**unicode_index.json:**
```json
{
  "50504,45397,54616,49464,50836": ["nb_calc_12345"]
}
```

## 배포 방법

### 로컬 → 서버 업로드
```bash
cd "E:\Ai project\사이트"
.\sync_chamsosik.bat
```

**배포 프로세스:**
1. SSH로 /var/www/chamsosik 폴더 생성
2. 로컬 파일을 /tmp/chamsosik_upload/에 업로드
3. sudo rsync로 /var/www/chamsosik/로 이동

### Nginx 설정 확인
```bash
ssh root@211.45.162.155
sudo cat /etc/nginx/sites-available/default
```

**location / 블록:**
```nginx
location / {
    try_files $uri $uri/ =404;
}
```

**Nginx 재시작:**
```bash
sudo nginx -t
sudo systemctl restart nginx
```

## 연동 시스템

### 한국인터넷.한국 (N/B 계산기)
- URL: http://한국인터넷.한국
- 기능: N/B MAX/MIN 계산 실행
- 연결: 계산 결과를 참소식.com 데이터베이스에 저장

### 참소식.com (데이터베이스)
- URL: https://참소식.com
- 기능: 계산 결과 검색, 통계 조회
- 연결: 한국인터넷.한국의 계산 결과를 조회/검색

## 향후 구현 예정

### Phase 1: 기본 저장 기능
- [ ] POST /api/calculate에 save_to_db 파라미터 추가
- [ ] 계층형 디렉터리 자동 생성
- [ ] result.json 파일 저장

### Phase 2: 검색 API
- [ ] GET /api/search?nb_max_min=5.0&nb_max_max=6.0
- [ ] GET /api/search?unicode=111,107,101,101,100,121
- [ ] GET /api/calculation/:calculation_id

### Phase 3: 인덱스 구축
- [ ] nb_max_index.json 자동 업데이트
- [ ] nb_min_index.json 자동 업데이트
- [ ] unicode_index.json 자동 업데이트
- [ ] 인덱스 기반 빠른 검색

### Phase 4: 고급 기능
- [ ] 계산 결과 비교 기능
- [ ] 통계 시각화 (차트)
- [ ] CSV/JSON 내보내기
- [ ] 중복 계산 방지

## API 설계 (예정)

### POST /api/calculate
```json
{
  "input": "안녕하세요",
  "bit": 999,
  "save_to_db": true
}
```

**응답:**
```json
{
  "calculation_id": "nb_calc_12345",
  "nb_max": 5.9686932681,
  "nb_min": 999.0000000000,
  "difference": 993.0313067319,
  "storage_path": "data/nb_max/5/9/6/8/result_nb_calc_12345.json"
}
```

### GET /api/search
```
/api/search?nb_max_min=5.0&nb_max_max=6.0
/api/search?unicode=50504,45397,54616,49464,50836
```

**응답:**
```json
{
  "total": 3,
  "results": [
    {
      "calculation_id": "nb_calc_12345",
      "input": "안녕하세요",
      "nb_max": 5.9686932681,
      "nb_min": 999.0000000000,
      "created_at": "2026-02-18T12:00:00Z"
    }
  ]
}
```

## 기술 스택

- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Backend**: Node.js + Express (한국인터넷.한국과 공유)
- **Storage**: 파일 기반 JSON (계층형 디렉터리)
- **Server**: Nginx + HTTPS (cafe24 SSL)
- **Domain**: 참소식.com (xn--9l4b4xi9r.com)

## 참고 링크

- [DATABASE_DESIGN.md](../../DATABASE_DESIGN.md) - 전체 데이터베이스 설계 문서
- [한국인터넷.한국 위키](http://한국인터넷.한국/#wiki) - N/B 계산기 지식 문서
- [한국인터넷.한국](http://한국인터넷.한국) - N/B 계산기

## 라이선스

© 2026 참소식.com | 8BIT Project

