```markdown
# YouTube 채널 키워드 분석 리포트

## 1. Executive Summary

본 리포트는 제공된 15개 키워드에 대한 YouTube 채널 분석 데이터를 검토한 결과입니다. **현재 모든 키워드의 성과 지표(nb_score, video_count, avg_views 등)가 0으로 표기**되어 있어 정량적 성과 분석은 불가능한 상태입니다. 다만, 키워드 구성을 통해 채널의 콘텐츠 전략 방향성과 데이터 수집 필요성을 도출할 수 있습니다.

## 2. Keyword Category Analysis

제공된 키워드는 다음 4개 카테고리로 분류됩니다:

### 금융·경제 (Financial & Economic) - 53%
- **시장 동향**: 주식시장 급락 전망, 비트코인 시세 분석, 금융 시장 변동성
- **거시 경제**: 미국 금리 인상 영향, 원달러 환율 전망, 경상수지 흑자 기록
- **산업 동향**: 반도체 시총 감소, 무역협상 중국산 부품

### 정치·사회 (Political & Social) - 20%
- 오늘의 주요 뉴스 🔒, 지방선거 결과 분석, EU 확대 제안

### 기술·부동산 (Tech & Real Estate) - 20%
- AI 기업 양산 경쟁, 주상복합 동선 가치

### 문화·엔터테인먼트 (Culture) - 7%
- K팝 스타 일정

*참고: "자 분석" 키워드는 데이터 오류 또는 잘린 문자열로 추정됩니다.*

## 3. Data Integrity Assessment

| 지표 | 상태 | 분석 |
|------|------|------|
| **nb_score** | 0 (100%) | 키워드 경쟁력 점수 미수집 |
| **video_count** | 0 (100%) | 검색 결과 영상 수 미확인 |
| **avg_views** | 0 (100%) | 평균 조회수 데이터 누락 |
| **views/videos** | Empty | 상세 메타데이터 미수집 |

**진단**: API 연결 오류, 검색 필터 미적용, 또는 초기화된 샘플 데이터로 판단됩니다.

## 4. Strategic Recommendations

### 즉시 조치 필요사항
1. **데이터 재수집**: YouTube Data API v3 또는 외부 분석 툴(예: VidIQ, TubeBuddy)을 통해 실제 메트릭 수집 필요
2. **키워드 정제**: "자 분석" 등 불완전한 키워드 제거 및 "주식 자동 분석" 등으로 보완

### 콘텐츠 전략 제안
- **시너지 효과**: "미국 금리 인상" → "원달러 환율" → "반도체 시총" 순서로 기획 시 시청자 여정(Viewer Journey) 구축 가능
- **틈새 기회**: "주상복합 동선 가치"는 부동산 세부 niched topic으로 경쟁이 적을 가능성이 높음 (데이터 수집 후 검증 필요)
- **리스크 관리**: "주식시장 급락" 등 부정적 키워드는 알고리즘 노출 제한 가능성을 고려하여 "대응 전략" 중심으로 각도 조정 필요

**결론**: 현재 데이터는 의사결정 기준으로 부적합하며, 정상적인 메트릭 확보 후 재분석이 필수적입니다.

---
*Report Generated: Analysis Incomplete (Data Quality Issue)*
*Recommendation: Re-collect metrics before strategic implementation*
```