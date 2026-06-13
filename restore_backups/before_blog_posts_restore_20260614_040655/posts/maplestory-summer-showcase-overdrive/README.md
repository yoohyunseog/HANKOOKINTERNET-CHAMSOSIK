# 메이플스토리 SUMMER SHOWCASE OVERDRIVE 포스터 자료

이 폴더는 `2026 MapleStory SUMMER SHOWCASE - OVERDRIVE` 글과 네이버 블로그 복붙용 HTML 포스터를 만들기 위한 원본 자료 묶음입니다.

## 폴더 구성

| 파일 | 용도 |
| --- | --- |
| `maplestory-summer-showcase-overdrive.txt` | 쇼케이스 영상/자료 전사 텍스트입니다. 일부 한글 OCR 또는 인코딩은 깨져 있지만, 영어 전사와 시간대가 같이 있어 본문 작성 근거로 사용했습니다. |
| `chrome-capture-2026-06-13 (1).png` | 여름 이벤트와 OVERDRIVE 흐름의 도입 이미지입니다. |
| `chrome-capture-2026-06-13 (2).png` | 스펙터 블래스트와 시즌별 경험치 콘텐츠 설명 이미지입니다. |
| `chrome-capture-2026-06-13 (3).png` | 하이퍼 블링크와 200~260 성장 구간 설명 이미지입니다. |
| `chrome-capture-2026-06-13 (4).png` | 버닝 비욘드와 280레벨 성장 보상 설명 이미지입니다. |
| `chrome-capture-2026-06-13 (5).png` | 아이템 버닝 플러스와 장비 성장 미션 개편 이미지입니다. |
| `chrome-capture-2026-06-13 (6).png` | 도전의 문장 획득 방식 개편 이미지입니다. |
| `chrome-capture-2026-06-13 (7).png` | 제네시스 패스 플러스 보스 미션과 보상 이미지입니다. |
| `chrome-capture-2026-06-13 (8).png` | 챌린저스 월드 시즌 4 미션 개편 이미지입니다. |
| `chrome-capture-2026-06-13 (9).png` | OVERDRIVE 최종 정리와 업데이트 요약 이미지입니다. |
| `naver-blog-poster.html` | 네이버 블로그에 복사해서 붙여넣기 좋은 HTML 포스터입니다. |

## 생성된 게시글

참소식 블로그용 실제 게시글 파일은 이 폴더 바깥의 아래 위치에 있습니다.

```text
../2026-06-13-maplestory-summer-showcase-overdrive.html
```

블로그 목록 데이터는 아래 파일의 첫 번째 항목으로 연결됩니다.

```text
../index.json
```

현재 `index.json`의 메이플스토리 항목은 다음 내용을 가리킵니다.

```json
{
  "title": "2026 MapleStory SUMMER SHOWCASE - OVERDRIVE, 다시 속도를 올리는 메이플스토리",
  "category": "게임 업데이트",
  "href": "posts/2026-06-13-maplestory-summer-showcase-overdrive.html",
  "image": "assets/2026-06-13-maplestory-summer-showcase-overdrive.png"
}
```

## 네이버 블로그 복붙용 포스터

네이버 블로그에 붙여넣을 때는 아래 파일을 브라우저에서 열고, 본문 영역을 선택해서 복사하면 됩니다.

```text
naver-blog-poster.html
```

이 파일은 네이버 편집기에서 스타일이 최대한 유지되도록 다음 방식으로 작성했습니다.

- 외부 CSS 파일에 의존하지 않고 대부분의 스타일을 인라인으로 작성했습니다.
- 문단마다 `<br>` 줄바꿈을 많이 넣어 한 칸 한 칸 읽히는 포스터형 문장 구조로 만들었습니다.
- 제목은 `h1`, 섹션은 `h2`, 이미지 설명은 별도 문단으로 구분했습니다.
- 이미지 9장을 모두 포함했습니다.
- 이미지 경로는 복붙 후에도 표시될 가능성을 높이기 위해 절대 URL을 사용했습니다.
- 핵심 단어에는 구글 검색 링크를 걸었습니다.
- 모든 검색 링크에는 새 창 열기용 `target="_blank"`와 보안용 `rel="noopener noreferrer"`를 넣었습니다.

## 링크가 걸린 핵심 단어

`naver-blog-poster.html`에는 아래 핵심어에 구글 검색 링크가 적용되어 있습니다.

- OVERDRIVE
- 스펙터 블래스트
- 하이퍼 블링크
- 버닝 비욘드
- 아이템 버닝
- 도전의 문장
- 제네시스 패스 플러스
- 챌린저스 월드 시즌 4
- 2026 MapleStory SUMMER SHOWCASE OVERDRIVE

## 이미지 경로 정책

참소식 블로그 본문에서는 사이트 내부 상대 경로를 사용합니다.

```html
<img src="maplestory-summer-showcase-overdrive/chrome-capture-2026-06-13%20(1).png">
```

네이버 블로그 복붙용 포스터에서는 외부 편집기에서도 이미지를 불러올 수 있도록 절대 URL을 사용합니다.

```html
<img src="https://www.xn--9l4b4xi9r.com/blog/posts/maplestory-summer-showcase-overdrive/chrome-capture-2026-06-13%20(1).png">
```

만약 네이버가 외부 이미지 표시를 제한하거나 이미지를 자체 서버로 재업로드하지 않으면, 붙여넣기 후 이미지가 비어 보일 수 있습니다. 이 경우에는 같은 폴더의 PNG 파일 9장을 네이버 편집기에 직접 업로드한 뒤, 포스터 본문의 이미지 위치에 맞춰 배치하면 됩니다.

## 본문 구성 요약

포스터와 블로그 본문은 다음 순서로 구성되어 있습니다.

1. OVERDRIVE 쇼케이스 도입
2. 여름 이벤트와 스펙터 블래스트
3. 하이퍼 블링크와 200~260 성장 구간
4. 버닝 비욘드와 280레벨 성장 목표
5. 아이템 버닝과 장비 성장 미션
6. 도전의 문장 획득 방식 개편
7. 제네시스 패스 플러스와 해방 이후 목표
8. 챌린저스 월드 시즌 4 미션 개편
9. OVERDRIVE 업데이트의 의미와 정리

## 수정할 때 주의할 점

- `naver-blog-poster.html`은 네이버 블로그 복붙용이므로 인라인 스타일을 유지하는 편이 좋습니다.
- 파일명에 공백과 괄호가 있으므로 HTML 경로에서는 공백을 `%20`으로 인코딩했습니다.
- `index.json`은 블로그 목록에서 사용되므로 JSON 문법을 반드시 유지해야 합니다.
- 블로그 목록에 새 글을 추가할 때는 `href`가 `posts/...html` 형식을 따르도록 맞추는 것이 좋습니다.
- 네이버용 포스터를 목록에 직접 노출하고 싶다면 별도 항목을 추가할 수 있지만, 현재는 중복 노출을 피하기 위해 대표 블로그 글만 `index.json`에 연결해 두었습니다.

## 빠른 검증 체크리스트

- `naver-blog-poster.html` 안의 `<img>` 태그는 총 9개입니다.
- `naver-blog-poster.html` 안의 `target="_blank"` 링크는 총 9개입니다.
- `../index.json`의 첫 번째 항목은 메이플스토리 OVERDRIVE 대표 글을 가리킵니다.
- 대표 이미지는 `../../assets/2026-06-13-maplestory-summer-showcase-overdrive.png`를 사용합니다.
