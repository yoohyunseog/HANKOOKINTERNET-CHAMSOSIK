# 보이니치 문서 + N/B 계산기 데이터베이스 설계

## 1. 개요

보이니치 필사본 해독 결과와 N/B 계산기 결과를 통합 관리하는 데이터베이스 시스템

### 핵심 목표
- 보이니치 문서의 각 페이지/단어를 N/B 계산 결과와 연결
- 계산 결과를 계층형 디렉터리 구조로 저장
- 빠른 검색과 조회를 위한 인덱싱
- 해독 과정의 추적 가능성 확보

---

## 2. 데이터 모델

### 2.1 보이니치 문서 데이터

#### 페이지 (VoynichPage)
```json
{
  "page_id": "f1r",
  "page_number": 1,
  "section": "herbal",
  "image_url": "/images/f1r.jpg",
  "created_at": "2026-02-18T00:00:00Z",
  "updated_at": "2026-02-18T00:00:00Z"
}
```

#### 단어/문장 (VoynichToken)
```json
{
  "token_id": "f1r_001",
  "page_id": "f1r",
  "position": 1,
  "original_text": "okeedy",
  "glyph_sequence": ["o", "k", "ee", "d", "y"],
  "unicode_values": [111, 107, 101, 101, 100, 121],
  "created_at": "2026-02-18T00:00:00Z"
}
```

#### 해독 결과 (Translation)
```json
{
  "translation_id": "f1r_001_trans_001",
  "token_id": "f1r_001",
  "method": "nb_calculation",
  "decoded_text": "example",
  "confidence_score": 0.85,
  "nb_calculation_id": "nb_calc_12345",
  "created_at": "2026-02-18T00:00:00Z"
}
```

---

### 2.2 N/B 계산 결과 데이터

#### 계산 세션 (NBCalculation)
```json
{
  "calculation_id": "nb_calc_12345",
  "input_type": "text",
  "input_raw": "okeedy",
  "unicode_array": [111, 107, 101, 101, 100, 121],
  "bit_value": 999,
  "calculation_count": 3,
  "created_at": "2026-02-18T00:00:00Z"
}
```

#### 계산 결과 (NBResult)
```json
{
  "result_id": "nb_result_67890",
  "calculation_id": "nb_calc_12345",
  "iteration": 1,
  "nb_max": 5.9686932681,
  "nb_min": 999.0000000000,
  "difference": 993.0313067319,
  "precision": 10,
  "created_at": "2026-02-18T00:00:00Z"
}
```

---

## 3. 계층형 디렉터리 구조

### 3.1 N/B 계산 결과 저장

#### 디렉터리 구조 (자릿수 기반)
```
data/
├── nb_max/
│   ├── 5/          # 첫째 자리
│   │   ├── 9/      # 둘째 자리
│   │   │   ├── 6/  # 셋째 자리
│   │   │   │   ├── 8/  # 넷째 자리
│   │   │   │   │   └── result_nb_calc_12345.json
```

#### result_nb_calc_12345.json
```json
{
  "calculation_id": "nb_calc_12345",
  "input": "okeedy",
  "unicode": [111, 107, 101, 101, 100, 121],
  "bit": 999,
  "results": [
    {
      "iteration": 1,
      "nb_max": 5.9686932681,
      "nb_min": 999.0000000000,
      "difference": 993.0313067319
    },
    {
      "iteration": 2,
      "nb_max": 5.9686932681,
      "nb_min": 999.0000000000,
      "difference": 993.0313067319
    },
    {
      "iteration": 3,
      "nb_max": 5.9686932681,
      "nb_min": 999.0000000000,
      "difference": 993.0313067319
    }
  ],
  "linked_voynich_tokens": ["f1r_001"],
  "created_at": "2026-02-18T00:00:00Z"
}
```

### 3.2 보이니치 문서 저장

```
data/
├── voynich/
│   ├── pages/
│   │   ├── f1r.json
│   │   ├── f1v.json
│   │   └── ...
│   ├── tokens/
│   │   ├── f1r/
│   │   │   ├── 001.json  # token_id별 상세 정보
│   │   │   ├── 002.json
│   │   │   └── ...
│   ├── translations/
│   │   ├── f1r/
│   │   │   ├── 001/
│   │   │   │   ├── trans_001.json
│   │   │   │   ├── trans_002.json  # 여러 해독 시도
│   │   │   │   └── ...
```

---

## 4. 인덱스 설계

### 4.1 검색 인덱스

#### nb_max_index.json
```json
{
  "5.9686932681": ["nb_calc_12345", "nb_calc_67890"],
  "8.6301234567": ["nb_calc_11111"]
}
```

#### unicode_index.json
```json
{
  "111,107,101,101,100,121": ["nb_calc_12345"],
  "97,98,99": ["nb_calc_22222"]
}
```

#### voynich_token_index.json
```json
{
  "f1r_001": {
    "original_text": "okeedy",
    "nb_calculations": ["nb_calc_12345"],
    "translations": ["f1r_001_trans_001"]
  }
}
```

---

## 5. API 설계

### 5.1 N/B 계산 API

#### POST /api/calculate
**요청:**
```json
{
  "input": "okeedy",
  "bit": 999,
  "save_to_db": true,
  "link_voynich_token": "f1r_001"
}
```

**응답:**
```json
{
  "calculation_id": "nb_calc_12345",
  "type": "text",
  "input": "okeedy",
  "unicode": [111, 107, 101, 101, 100, 121],
  "bit": 999,
  "results": [...],
  "storage_path": "data/nb_max/5/9/6/8/result_nb_calc_12345.json"
}
```

### 5.2 보이니치 문서 API

#### GET /api/voynich/page/:page_id
**응답:**
```json
{
  "page_id": "f1r",
  "tokens": [...],
  "image_url": "/images/f1r.jpg"
}
```

#### GET /api/voynich/token/:token_id
**응답:**
```json
{
  "token_id": "f1r_001",
  "original_text": "okeedy",
  "nb_calculations": [...],
  "translations": [...]
}
```

### 5.3 통합 검색 API

#### GET /api/search
**쿼리 파라미터:**
- `q`: 검색어
- `type`: voynich_token | nb_result | translation
- `nb_min`: N/B MIN 범위 (예: 5.0)
- `nb_max`: N/B MAX 범위 (예: 6.0)

**응답:**
```json
{
  "results": [
    {
      "type": "voynich_token",
      "token_id": "f1r_001",
      "original_text": "okeedy",
      "nb_calculations": [...]
    }
  ],
  "total": 1
}
```

---

## 6. 데이터 흐름

### 6.1 보이니치 해독 프로세스

```
1. 보이니치 원문 입력 (okeedy)
   ↓
2. Unicode 변환 [111, 107, 101, 101, 100, 121]
   ↓
3. N/B 계산 (3회)
   ↓
4. 결과 저장
   - data/nb_max/5/9/6/8/result_nb_calc_12345.json
   - data/nb_min/9/9/9/0/result_nb_calc_12345.json
   ↓
5. 보이니치 토큰과 연결
   - data/voynich/tokens/f1r/001.json
   ↓
6. 해독 결과 저장
   - data/voynich/translations/f1r/001/trans_001.json
```

### 6.2 검색 프로세스

```
1. 사용자 검색 (예: N/B MAX = 5.96)
   ↓
2. nb_max_index.json 조회
   ↓
3. 해당 calculation_id 목록 획득
   ↓
4. 각 계산 결과 파일 로드
   ↓
5. 연결된 보이니치 토큰 조회
   ↓
6. 통합 결과 반환
```

---

## 7. 구현 우선순위

### Phase 1: 기본 N/B 계산 저장
- [ ] 계층형 디렉터리 구조 생성
- [ ] N/B 계산 결과 JSON 저장
- [ ] 기본 인덱스 생성

### Phase 2: 보이니치 데이터 통합
- [ ] 보이니치 페이지/토큰 데이터 구조 생성
- [ ] N/B 계산과 보이니치 토큰 연결
- [ ] 해독 결과 저장 기능

### Phase 3: 검색 기능
- [ ] 인덱스 기반 검색 API
- [ ] N/B 값 범위 검색
- [ ] 보이니치 원문 검색

### Phase 4: 웹 UI
- [ ] 보이니치 페이지 뷰어
- [ ] N/B 계산 결과 시각화
- [ ] 해독 결과 편집기

---

## 8. 기술 스택

### 백엔드
- Node.js + Express (현재 구현)
- 파일 시스템 기반 스토리지 (계층 디렉터리)
- JSON 인덱스 파일

### 확장 가능성
- SQLite (관계형 데이터 추가 시)
- Elasticsearch (전문 검색 추가 시)
- MongoDB (문서형 DB로 마이그레이션 시)

---

## 9. 예제 시나리오

### 시나리오 1: 보이니치 f1r 페이지 해독

1. f1r 페이지의 첫 단어 "okeedy" 입력
2. N/B 계산 실행 (BIT=999, 3회)
3. 결과: MAX=5.9686932681, MIN=999.0000000000
4. 해독 시도: "okeedy" → "example" (신뢰도 85%)
5. 저장:
   - `data/nb_max/5/9/6/8/result_nb_calc_12345.json`
   - `data/voynich/tokens/f1r/001.json`
   - `data/voynich/translations/f1r/001/trans_001.json`

### 시나리오 2: 유사 N/B 값 검색

1. 사용자: "N/B MAX가 5.96~5.97 범위인 모든 단어 찾기"
2. 시스템: nb_max_index.json 조회
3. 결과: ["nb_calc_12345", "nb_calc_67890"]
4. 각 계산 결과의 원문 표시:
   - "okeedy" (f1r_001)
   - "oteedy" (f2r_005)

---

## 10. 참고 링크

- 한국인터넷.한국 N/B 계산기: http://한국인터넷.한국
- 보이니치 해독 문서: http://한국인터넷.한국/보이니치
- 참소식.com: https://참소식.com
