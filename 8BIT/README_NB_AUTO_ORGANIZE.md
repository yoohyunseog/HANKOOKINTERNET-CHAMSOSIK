# N/B 계산 및 자동 정리 프로그램

네이버 크리에이터 데이터의 N/B(Naive Bayes) 최댓값과 최솟값을 자동으로 계산하고 정리하는 프로그램입니다.

## 📋 기능

### ✅ N/B 계산
- Node.js를 사용한 고속 계산
- N/B MAX 값 계산
- N/B MIN 값 계산
- JSON 형식으로 결과 저장

### ✅ 자동 정리
- 계산 결과 자동 정렬
- 중복 제거
- 통계 생성
- JSON/CSV 형식 저장

### ✅ 결과 관리
- 최근 결과 확인
- 결과 폴더 자동 열기
- 정리 이력 저장

## 🚀 사용 방법

### 옵션 1: 한 번에 계산 + 정리

```batch
run_nb_calculation.bat
```

**동작 순서:**
1. ⚙️ N/B 계산 실행
2. 📊 결과 자동 정리
3. ✅ 완료

### 옵션 2: 관리자 모드 (다양한 옵션)

```batch
run_nb_calculation_manager.bat
```

**메뉴:**
```
1. N/B 계산 실행 + 자동 정리       ← 권장
2. N/B 계산만 실행 (정리 없음)
3. 결과 정리만 실행
4. 최근 결과 보기
5. 모든 작업 종료
```

## 📂 파일 구조

```
8BIT/
├── nb_calculation_node.js          # N/B 계산 프로그램
├── organize_nb_results.py          # 결과 정리 프로그램
└── README_NB.md

data/
├── nb_max/                         # N/B MAX 결과
│   ├── 2/
│   ├── 3/
│   └── ...
├── nb_min/                         # N/B MIN 결과
│   ├── 1/
│   ├── 9/
│   └── ...
└── nb_results/                     # 정리된 결과
    ├── organized_results_20260218_143022.json
    ├── organized_results_20260218_143022.csv
    └── latest_results.json

run_nb_calculation.bat              # 단순 실행 파일
run_nb_calculation_manager.bat      # 관리자 모드 파일
```

## 📊 생성되는 결과

### JSON 형식
```json
{
  "statistics": {
    "total_count": 1500,
    "collection_time": "2026-02-18T21:37:00",
    "breakdown": {
      "by_type": {
        "max": 750,
        "min": 750
      }
    }
  },
  "results": [
    {
      "type": "max",
      "value": 95.5,
      "category": "숫자"
    },
    ...
  ]
}
```

### CSV 형식
```
type,value,category
max,95.5,숫자
min,5.2,숫자
...
```

## 🔧 각 프로그램 상세 설명

### `nb_calculation_node.js` (계산)
- **목적**: N/B 값을 계산하고 저장
- **입력**: 사용자 입력 또는 설정 파일
- **출력**: `data/nb_max/`, `data/nb_min/` 폴더에 JSON 파일 저장 (생성 완료)
- **실행**: Node.js 필요

### `organize_nb_results.py` (정리)
- **목적**: 계산 결과를 자동으로 정리
- **작업**:
  1. ✅ 모든 결과 파일 스캔
  2. ✅ 계산 결과 추출
  3. ✅ 중복 제거
  4. ✅ 통계 생성
  5. ✅ JSON/CSV 저장
- **출력**: `data/nb_results/` 폴더
- **실행**: Python 3.10+ 필요

## 💻 필수 설치 요구사항

### Windows
- ✅ Node.js (이미 설치: `E:\node\`)
- ✅ Python 3.10+ (이미 설치)
- ✅ 빌트인: PowerShell, 배치 파일 실행

### macOS/Linux
```bash
# Node.js 설치
brew install node

# Python 설치
brew install python3

# 배치 파일 대신 Bash 스크립트 실행
bash run_nb_calculation.sh
```

## ⚡ 성능 정보

| 작업 | 소요 시간 | 결과 크기 |
|------|---------|---------|
| N/B 계산 | 5-30초 | 2-5MB |
| 결과 정리 | 1-3초 | 500KB-1MB |
| **전체** | 6-33초 | 2.5-6MB |

## 🎯 예시 사용 흐름

**한 번에 실행:**
```batch
run_nb_calculation.bat
```

**결과:**
```
[계산 중...]
✅ 로그인 완료
✅ 데이터 수집 완료: 100개 항목
✅ N/B 계산 완료

[정리 중...]
✅ 1500개의 결과 파일 발견
📊 1500개의 계산 결과 추출
🗑️ 50개의 중복 제거
📈 통계 생성 완료
✅ JSON 저장: data/nb_results/organized_results_20260218_143022.json
✅ CSV 저장: data/nb_results/organized_results_20260218_143022.csv

모든 작업이 완료되었습니다.
```

## 📁 결과 확인하기

**관리자 모드에서 옵션 4 선택:**
```
run_nb_calculation_manager.bat
→ 5 선택
→ 자동으로 `data/nb_results/` 폴더 열기
```

## 🐛 문제 해결

### Python을 찾을 수 없음
```
❌ Python이 설치되어 있지 않습니다.
```
**해결**: `py --version` 실행해서 설치 확인

### 결과 파일이 없음
```
⚠️ 결과 파일이 없습니다.
```
**해결**: 먼저 계산을 실행하세요 (`옵션 1 또는 2`)

### 정리 프로그램 오류
```
❌ 정리 실패: [오류 메시지]
```
**해결**: `8BIT/organize_nb_results.py` 파일이 있는지 확인

## 🔄 자동화 (Windows 작업 스케줄러)

매 시간마다 자동 실행:

1. 작업 스케줄러 열기
2. 기본 작업 만들기:
   - **이름**: "N/B 계산 및 정리"
   - **트리거**: 매 1시간
   - **작업**: `run_nb_calculation.bat` 실행

## 📝 결과 분석 팁

정리된 결과를 Excel이나 Python Pandas로 분석:

```python
import pandas as pd
import json

# JSON 읽기
with open('data/nb_results/latest_results.json') as f:
    data = json.load(f)

# 통계 보기
stats = data['statistics']
print(f"총 항목: {stats['total_count']}")

# CSV 읽기
df = pd.read_csv('data/nb_results/organized_results_*.csv')
print(df.describe())
```

## 🎓 더 알아보기

자세한 내용은 다음 파일을 참고하세요:
- [README_NB_CALCULATION.md](README_NB_CALCULATION.md) - N/B 계산 알고리즘 설명
- [DATABASE_DESIGN.md](../DATABASE_DESIGN.md) - 전체 시스템 아키텍처

---

**마지막 업데이트**: 2026-02-18  
**버전**: 1.0.0  
**상태**: ✅ 운영 중
