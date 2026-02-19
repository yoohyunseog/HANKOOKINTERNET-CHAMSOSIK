# N/B 계산 프로그램 - 사용 가이드

## 📌 프로그램 정보

JavaScript 기반 N/B MAX, N/B MIN 계산 프로그램
- **개발 언어**: JavaScript (Node.js)
- **BIT 계산**: 음수/양수 범위 기반 가중치 분석
- **주요 기능**: N/B MAX/MIN 동시 계산, 자동 3회 계산

---

## 🚀 실행 방법

### 방법 1: 배치 파일 실행 (추천 - Windows)
```bash
run_nb_calculation.bat
```
더블클릭으로 실행 가능합니다.

### 방법 2: PowerShell 실행
```powershell
E:\node\node.exe nb_calculation_node.js
```

### 방법 3: 명령 프롬프트 실행
```cmd
cd e:\Ai project\사이트\8BIT\js
E:\node\node.exe nb_calculation_node.js
```

---

## 📖 사용 방법

### 1️⃣ 숫자 입력 (정상 계산 - 1회)
```
문자를 입력하세요 (또는 q를 입력하여 종료): 1.5 2.5 3.5
✓ 정상 입력: 1번 계산 실행
BIT 값을 입력하세요 (기본값: 5.5): 5.5

입력값: [1.5, 2.5, 3.5]
BIT 값: 5.5

✓ N/B MAX 결과: 1.676190
✓ N/B MIN 결과: 4.255952
✓ 차이 (MAX - MIN): -2.579762
```

### 2️⃣ 문자 입력 (자동 3회 계산)
```
문자를 입력하세요 (또는 q를 입력하여 종료): hello

⚠ 문자 입력 감지: 'hello'
✓ 자동으로 3번 계산을 실행합니다.

[계산 1/3]
BIT 값을 입력하세요 (기본값: 5.5): 5.5
✓ N/B MAX 결과: 0.055000
✓ N/B MIN 결과: 0.055000
...
```

### 3️⃣ 종료
```
프로그램을 종료합니다.
```

---

## 💡 입력 형식

| 입력 | 동작 | 결과 |
|------|------|------|
| `숫자 숫자 ...` | 1번 계산 | N/B MAX/MIN 계산 |
| `숫자,숫자,...` | 1번 계산 | 쉼표로도 구분 가능 |
| `문자/특수문자` | 3번 계산 | 자동 3회 반복 |
| `q` | 종료 | 프로그램 종료 |

---

## ⚙️ BIT 값

- **기본값**: 5.5
- **범위**: 양수 (권장: 1.0 ~ 10.0)
- **입력 생략**: Enter 입력 시 5.5 사용

---

## 📊 결과 해석

| 항목 | 설명 |
|------|------|
| **N/B MAX** | 시간 흐름 상한치 (Forward Time Flow) |
| **N/B MIN** | 시간 흐름 하한치 (Reverse Time Flow) |
| **차이** | MAX - MIN 값 |

---

## 🔧 설치된 도구

- **Node.js**: v20.10.0 (E:\node)
- **실행 파일**: nb_calculation_node.js
- **배치 파일**: run_nb_calculation.bat

---

## 📝 파일 위치

```
e:\Ai project\사이트\8BIT\
├── js\
│   ├── nb_calculation_node.js (메인 프로그램)
│   ├── run_nb_calculation.bat (실행 스크립트)
│   ├── bitCalculation.v.0.1.js (원본 로직)
│   └── test_node_program.js (자동 테스트)
├── nb_calculation.py (Python 버전)
└── README.md
```

---

## 🎯 주요 기능

✅ 음수/양수 범위 구분 계산
✅ 자동 3회 계산 (문자 입력 시)
✅ 커스텀 BIT 값 지원
✅ 실시간 결과 표시
✅ SUPER_BIT 캐싱

---

## 📞 문제 발생 시

1. **Node.js 오류**: `E:\node\node.exe --version` 실행하여 확인
2. **파일 없음**: 경로 확인 (E:\Ai project\사이트\8BIT\js)
3. **권한 오류**: 관리자 권한으로 실행

---

**마지막 업데이트**: 2026.02.18
**버전**: 1.0.0
