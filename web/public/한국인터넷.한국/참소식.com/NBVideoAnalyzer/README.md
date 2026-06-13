# YouTube 키워드 파일 설명

이 폴더는 유튜브 분석기에서 사용할 키워드 JSON 파일과 로컬 분석 봇을 보관합니다.

현재 폴더 구조는 아래와 같습니다.

```text
NBVideoAnalyzer/
  analyze_keywords_bot.py
  run_keyword_analysis.bat
  README.md
  keywords/
    goemulddanji_keywords.json
    anime_keywords.json
  analysis_results/
    latest_keyword_analysis.json
```

키워드 JSON 파일은 반드시 `keywords/` 폴더 안에 둡니다. 분석 결과 JSON은 `analysis_results/` 폴더에 생성됩니다.

구조 원칙은 단순합니다.

```text
파일 1개 = 카테고리 1개 = keywords 배열 1개
```

파일 안에 하위 카테고리를 만들지 않습니다. 예를 들어 `괴물딴지` 파일 안에서 `UFO`, `심령`, `초능력` 같은 하위 묶음을 다시 만들지 않습니다. 그렇게 나누면 나중에 유튜브 조회수, 비디오 ID, 날짜별 조회수, N/B MAX, N/B MIN을 비교할 때 기준이 복잡해지기 때문입니다.

## 파일 목록

`goemulddanji_keywords.json`

괴물딴지 계열 키워드 파일입니다. UFO, 심령 현상, 초능력, 괴담, 미스테리 사건, 불가사의 사건 같은 콘텐츠를 찾기 위한 검색어가 들어 있습니다.

`anime_keywords.json`

애니메이션 계열 키워드 파일입니다. 일본 애니메이션 제목 중심으로 구성되어 있습니다.

## JSON 형식

각 파일은 같은 형식을 사용합니다.

```json
{
  "category": "카테고리 이름",
  "description": "파일 설명",
  "keywords": [
    "키워드1",
    "키워드2",
    "키워드3"
  ]
}
```

실제 분석 프로그램은 `keywords` 배열만 읽어서 유튜브 검색어로 사용하면 됩니다. `category`는 결과를 저장할 때 어떤 키워드 파일에서 나온 검색인지 표시하는 용도입니다.

## 검색 조합 방식

검색어는 기본적으로 키워드 하나를 그대로 사용합니다.

```text
괴물딴지 UFO
애니메이션 귀멸의 칼날
```

키워드 JSON에는 `UFO`, `귀멸의 칼날`처럼 원본 키워드만 저장합니다. 분석 봇이 실행될 때 `category + keyword` 형태의 `analysisKeyword`를 자동 생성합니다.

나중에 더 정밀하게 찾고 싶으면 프로그램 쪽에서 접미어를 붙일 수 있습니다.

```text
괴물딴지 UFO 미스터리
괴물딴지 UFO 실화
애니메이션 귀멸의 칼날 리뷰
애니메이션 귀멸의 칼날 분석
```

다만 키워드 파일 자체에는 조합 결과를 많이 넣지 않는 편이 좋습니다. 원본 키워드가 단순해야 어떤 키워드가 조회수 흐름을 만들었는지 추적하기 쉽습니다.

## 분석 결과와 연결되는 값

유튜브 분석기는 각 키워드로 영상을 조회한 뒤 다음 값을 저장하는 흐름을 권장합니다.

```text
category
keyword
videoId
title
publishedAt
collectedDate
viewCount
```

같은 `videoId`가 여러 날짜에 걸쳐 저장되면 날짜별 조회수 증가량을 만들 수 있습니다.

```text
2026-06-10 조회수 1000
2026-06-11 조회수 1350
2026-06-12 조회수 2100
```

분석용 배열은 누적 조회수가 아니라 증가량으로 만드는 것이 좋습니다.

```text
[350, 750]
```

이 배열을 `bitCalculation.v.0.1.js`의 `BIT_MAX_NB`, `BIT_MIN_NB`에 넣으면 영상별 N/B MAX, N/B MIN 분석값을 만들 수 있습니다.

## 키워드 추가 규칙

키워드를 추가할 때는 `keywords` 배열에 문자열만 추가합니다.

좋은 예:

```json
"외계인 인터뷰"
```

피하는 예:

```json
{
  "ufo": ["UFO", "로스웰 사건"]
}
```

하위 카테고리를 만들면 분석 결과를 합산하거나 비교할 때 기준이 흔들립니다. 이 프로젝트에서는 카테고리는 파일 단위로만 관리합니다.

## 로컬 키워드 분석 봇

`analyze_keywords_bot.py`는 유튜브 API를 사용하지 않습니다. `keywords/` 폴더의 `*_keywords.json` 파일만 읽어서 키워드 자체를 분석하고 결과 JSON을 생성합니다.

실행 방법:

```bat
run_keyword_analysis.bat
```

또는 명령 프롬프트/PowerShell에서 직접 실행할 수 있습니다.

```powershell
py analyze_keywords_bot.py
```

결과는 아래 폴더에 저장됩니다.

```text
analysis_results/
```

생성되는 파일은 두 종류입니다.

```text
keyword_analysis_YYYYMMDD_HHMMSS.json
latest_keyword_analysis.json
```

`keyword_analysis_YYYYMMDD_HHMMSS.json`은 실행 시각별 보관용 파일입니다. `latest_keyword_analysis.json`은 가장 최근 분석 결과를 항상 같은 이름으로 덮어쓰는 파일입니다.

분석 결과에는 다음 값이 들어갑니다.

```text
category
sourceFile
keywordCount
duplicateKeywords
averageKeywordLength
averageNbMax
averageNbMin
maxNbGap
languageCounts
similarKeywordPairs
keywords
```

각 키워드별 결과에는 다음 값이 들어갑니다.

```text
keyword
analysisKeyword
normalizedKeyword
language
characterCount
characterCountNoSpace
wordCount
unicodeValues
nbMax
nbMin
nbGap
queryVariants
```

`keyword`는 키워드 파일에 저장된 원본 값입니다. `analysisKeyword`는 분석에 실제로 사용하는 값이며, `괴물딴지 UFO`, `애니메이션 귀멸의 칼날`처럼 카테고리 이름과 키워드를 붙인 문자열입니다.

`nbMax`, `nbMin`, `nbGap`은 키워드 문자를 유니코드 숫자 배열로 바꾼 뒤 N/B 방식으로 계산한 값입니다. 이 값은 실제 유튜브 조회수 분석값이 아니라, 키워드 자체의 문자 흐름을 비교하기 위한 로컬 분석값입니다.

`queryVariants`는 실제 검색에 사용할 수 있는 검색어 후보입니다. 예를 들어 `UFO` 키워드는 `UFO 미스터리`, `UFO 실화`, `UFO 사건` 같은 후보를 만듭니다. 키워드 파일에는 원본 키워드만 유지하고, 조합 검색어는 분석 결과 JSON에서만 만들어집니다.
