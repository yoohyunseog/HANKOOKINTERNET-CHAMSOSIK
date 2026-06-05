# 고전 문헌 데이터 수집 및 처리 가이드

이 폴더는 중국 고전 문헌(논어, 맹자, 순자, 사기, 한서, 삼국지, 초한지)을 수집하고 RAG/파인튜닝용 데이터로 변환하기 위한 시스템입니다.

## ⚠️ 저작권 주의사항

**원문은 비교적 안전하지만, 현대 한국어 번역은 반드시 라이선스를 확인해야 합니다.**

- 원문(한문): 대부분 퍼블릭 도메인
- 현대 번역: 번역자의 저작권이 존재할 수 있음
- 상업적 이용 시 반드시 확인 필요

## 📁 폴더 구조

```
Fine-tuning/
├── raw/                    # 수집된 원문 텍스트
│   ├── 논어.txt
│   ├── 맹자.txt
│   ├── 순자.txt
│   ├── 사기.txt
│   ├── 한서.txt
│   ├── 삼국지.txt
│   └── 사기_초한_항우본기.txt
│
├── processed/              # JSONL 변환 데이터
│   ├── 논어.jsonl
│   ├── 맹자.jsonl
│   └── ...
│
├── metadata/               # 메타데이터
│   ├── people.json         # 인물 정보
│   ├── periods.json        # 시대 정보
│   └── keywords.json       # 키워드 정보
│
├── scripts/                # 처리 스크립트
│   ├── fetch_ctext.py      # Chinese Text Project 수집
│   ├── fetch_wikisource.py # 위키문헌 수집
│   ├── fetch_gutenberg.py  # Project Gutenberg 수집
│   ├── convert_to_jsonl.py # JSONL 변환
│   ├── translate_korean.py # 한국어 번역
│   └── validate_data.py    # 데이터 검증
│
└── README.md               # 이 파일
```

## 🚀 사용 순서

### 1단계: 원문 수집

```bash
# Chinese Text Project에서 수집
python scripts/fetch_ctext.py

# 위키문헌에서 수집
python scripts/fetch_wikisource.py

# Project Gutenberg에서 수집
python scripts/fetch_gutenberg.py
```

### 2단계: JSONL 변환

```bash
python scripts/convert_to_jsonl.py
```

### 3단계: 한국어 번역 (선택사항)

```bash
# OpenAI API 사용
python scripts/translate_korean.py

# 또는 Ollama 로컬 모델 사용
# translate_korean.py에서 Ollama 옵션 선택
```

### 4단계: 데이터 검증

```bash
python scripts/validate_data.py
```

## 📚 문헌별 수집 가이드

| 문헌 | 추천 출처 | 비고 |
|------|----------|------|
| 논어 | Chinese Text Project + 한국어 위키문헌 | 원문 + 번역 |
| 맹자 | Chinese Text Project + 한국어 위키문헌 | 원문 + 번역 |
| 순자 | Chinese Text Project | 원문 위주 |
| 사기 | Chinese Text Project + 위키문헌 | 원문 |
| 한서 | Chinese Text Project + 위키문헌 | 원문 |
| 삼국지 | Project Gutenberg (정사) | 영문 번역본 |
| 초한지 | 사기 항우본기/고조본기 중심 | 역사 기반 |

## 📋 JSONL 데이터 형식

```json
{
  "id": "lunyu_001_001",
  "book": "논어",
  "chapter": "학이",
  "type": "유가",
  "period": "춘추전국",
  "original": "子曰 學而時習之 不亦說乎",
  "korean": "공자께서 말씀하셨다. 배우고 때때로 익히면 또한 기쁘지 아니한가.",
  "people": ["공자"],
  "keywords": ["학습", "수양"]
}
```

## 🔧 의존성 설치

```bash
pip install requests
```

## 📖 참고 자료

- [Chinese Text Project](https://ctext.org/) - 고문헌 디지털 라이브러리
- [위키문헌](https://ko.wikisource.org/) - 자유 저작물 문헌
- [Project Gutenberg](https://www.gutenberg.org/) - 퍼블릭 도메인 도서

## ⚡ 빠른 시작

```bash
# 1. 전체 수집 (선택적으로)
python scripts/fetch_ctext.py  # 번호 선택

# 2. JSONL 변환
python scripts/convert_to_jsonl.py

# 3. 검증
python scripts/validate_data.py
```

## 📝 라이선스

- 원문: 퍼블릭 도메인 (대부분)
- 수집된 번역: 각 출처의 라이선스 확인 필요
- 생성된 코드: MIT License