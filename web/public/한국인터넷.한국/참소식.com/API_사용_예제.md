# API 사용 예제 - 빠른 참고

## 🎯 자주 사용하는 조회 방법

### 📅 최근 날짜순 100개 조회

```javascript
// JavaScript / Node.js
const response = await fetch('https://참소식.com/api/recent?limit=100');
const data = await response.json();

console.log(`총 ${data.count}개 조회됨`);
data.results.forEach((item, i) => {
    console.log(`${i+1}. [${item.id}] ${item.input} (${item.timestamp})`);
});
```

```powershell
# PowerShell
$recent = Invoke-RestMethod -Uri "https://참소식.com/api/recent?limit=100"
Write-Host "총 $($recent.count)개 조회"
$recent.results | Select-Object id, timestamp, input, view_count | Format-Table -AutoSize
```

```bash
# cURL
curl "https://참소식.com/api/recent?limit=100" | jq
```

---

### 🔥 조회수 많은 순 100개 조회 (인기 순위)

```javascript
// JavaScript / Node.js
const response = await fetch('https://참소식.com/api/most-viewed?limit=100');
const data = await response.json();

console.log(`조회수 TOP ${data.count}`);
data.results.forEach((item, i) => {
    console.log(`${i+1}위. 조회수 ${item.view_count}회 - [${item.id}] ${item.input}`);
});
```

```powershell
# PowerShell
$topViewed = Invoke-RestMethod -Uri "https://참소식.com/api/most-viewed?limit=100"
Write-Host "조회수 TOP $($topViewed.count)"
$topViewed.results | Select-Object @{N='순위';E={$topViewed.results.IndexOf($_)+1}}, view_count, input, id | Format-Table -AutoSize
```

```bash
# cURL
curl "https://참소식.com/api/most-viewed?limit=100" | jq
```

---

## 🔍 비교: 두 API의 차이점

| 구분 | `/api/recent` | `/api/most-viewed` |
|------|---------------|-------------------|
| **정렬 기준** | 생성 날짜 (최신순) | 조회수 (많은 순) |
| **사용 목적** | 최근에 생성된 데이터 확인 | 인기 많은 데이터 확인 |
| **응답 속도** | 빠름 (인덱스 사용) | 보통 (전체 파일 스캔) |
| **권장 limit** | 10~100 | 10~100 |

---

## 📋 전체 API 목록

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/calculate` | N/B 계산 및 저장 |
| POST | `/api/search` | 텍스트/유니코드 검색 |
| GET | `/api/calculation/:id` | ID로 단일 조회 (조회수+1) |
| GET | `/api/recent?limit=N` | 최근 N개 (날짜순) |
| GET | `/api/most-viewed?limit=N` | 조회수 TOP N (인기순) ⭐ |
| GET | `/api/calculations?limit=N` | 리스트 조회 (페이징) |
| GET | `/api/stats` | 통계 정보 |

---

## 💾 저장 예제 (N/B 계산 결과 저장)

`/api/calculate`는 계산과 동시에 데이터 저장을 수행합니다.
저장 결과는 `data/nb_max` 및 `data/nb_min` 경로에 생성됩니다.

```javascript
// JavaScript / Node.js
const response = await fetch('https://참소식.com/api/calculate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ input: '오늘 주요 뉴스' })
});

const data = await response.json();
console.log('saved:', data.saved, 'id:', data.calculation_id);
console.log('nb_max:', data.results?.[0]?.nb_max, 'nb_min:', data.results?.[0]?.nb_min);
```

```bash
curl -X POST "https://참소식.com/api/calculate" \
    -H "Content-Type: application/json" \
    -d '{"input":"오늘 주요 뉴스"}' | jq
```

### 🔎 저장 확인 (방금 저장된 결과 확인)

```javascript
// 최근 저장된 1개 확인
const recent = await fetch('https://참소식.com/api/recent?limit=1').then(r => r.json());
console.log(recent.results?.[0]);

// 계산 ID로 단일 조회
const id = recent.results?.[0]?.id;
if (id) {
    const detail = await fetch(`https://참소식.com/api/calculation/${id}`).then(r => r.json());
    console.log(detail.result);
}
```

```bash
# 최근 1개 확인
curl "https://참소식.com/api/recent?limit=1" | jq

# 계산 ID로 단일 조회
curl "https://참소식.com/api/calculation/{id}" | jq
```

### ✅ 응답 형식 (저장 결과)

```json
{
    "id": "1a250e38f2d96fe9",
    "calculation_id": "1a250e38f2d96fe9",
    "timestamp": "2026-02-19T16:45:00.000Z",
    "type": "text",
    "input": "오늘 주요 뉴스",
    "unicode": [50724, 51068, 32, 51452, 50836, 32, 45684, 49828],
    "bit": 999,
    "view_count": 0,
    "results": [
        { "nb_max": 12345.6789, "nb_min": 0.1234, "difference": 12345.5555 }
    ],
    "saved": true
}
```

---

## 💡 실전 예제

### 예제 1: 조회수 상위 10개와 최근 10개 비교

```javascript
// 조회수 TOP 10
const top10 = await fetch('/api/most-viewed?limit=10').then(r => r.json());

// 최근 10개
const recent10 = await fetch('/api/recent?limit=10').then(r => r.json());

console.log('=== 조회수 TOP 10 ===');
top10.results.forEach((item, i) => {
    console.log(`${i+1}위: ${item.view_count}회 - ${item.input}`);
});

console.log('\n=== 최근 10개 ===');
recent10.results.forEach((item, i) => {
    console.log(`${i+1}. ${item.timestamp} - ${item.input}`);
});
```

### 예제 2: PowerShell로 조회수 통계 분석

```powershell
# 조회수 TOP 100 가져오기
$data = Invoke-RestMethod -Uri "https://참소식.com/api/most-viewed?limit=100"

# 통계 계산
$totalViews = ($data.results | Measure-Object -Property view_count -Sum).Sum
$avgViews = ($data.results | Measure-Object -Property view_count -Average).Average
$maxViews = ($data.results | Measure-Object -Property view_count -Maximum).Maximum

Write-Host "=== 조회수 통계 ==="
Write-Host "총 조회수: $totalViews"
Write-Host "평균 조회수: $([Math]::Round($avgViews, 2))"
Write-Host "최대 조회수: $maxViews"

# 조회수 10회 이상만 필터링
$popular = $data.results | Where-Object { $_.view_count -ge 10 }
Write-Host "`n조회수 10회 이상: $($popular.Count)개"
```

### 예제 3: 특정 범위의 데이터 가져오기

```javascript
// 최근 50~100번째 데이터 (페이징)
const page1 = await fetch('/api/recent?limit=50').then(r => r.json());
const page2 = await fetch('/api/recent?limit=100').then(r => r.json());

// 50~100번째만 추출
const items50to100 = page2.results.slice(50);
console.log(`50~100번째 데이터: ${items50to100.length}개`);
```

---

## 🎯 성능 팁

1. **limit 값 최적화**
   - 필요한 만큼만 요청 (불필요하게 큰 값 지양)
   - 권장: 10~100개

2. **캐싱 활용**
   ```javascript
   // 5분마다 갱신
   let cachedTop100 = null;
   let lastFetch = 0;
   
   async function getTop100() {
       if (Date.now() - lastFetch > 300000) { // 5분
           cachedTop100 = await fetch('/api/most-viewed?limit=100').then(r => r.json());
           lastFetch = Date.now();
       }
       return cachedTop100;
   }
   ```

3. **병렬 요청**
   ```javascript
   // 동시에 두 API 호출
   const [recent, topViewed] = await Promise.all([
       fetch('/api/recent?limit=50').then(r => r.json()),
       fetch('/api/most-viewed?limit=50').then(r => r.json())
   ]);
   ```

---

## 📞 문의

- API 문서: https://참소식.com/api.html
- 데이터베이스: https://참소식.com/database.html
