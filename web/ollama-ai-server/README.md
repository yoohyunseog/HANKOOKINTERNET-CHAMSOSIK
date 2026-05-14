# Ollama AI Server

외부 브라우저가 Ollama를 직접 호출하지 않도록 중간에서 대신 호출하는 작은 Node 서버입니다.

## 실행

```powershell
cd "E:\Ai project\사이트\web\ollama-ai-server"
$env:PORT="3110"
$env:OLLAMA_URL="http://127.0.0.1:11434"
$env:OLLAMA_MODEL="kimi-k2.6:cloud"
node server.js
```

선택 인증 토큰:

```powershell
$env:OLLAMA_PROXY_TOKEN="원하는_비밀값"
```

토큰을 설정하면 요청 헤더에 다음이 필요합니다.

```text
Authorization: Bearer 원하는_비밀값
```

## 엔드포인트

- `GET /health`
- `POST /api/chat`
- `POST /api/game-ai-advice`
- `GET /api/issue-search?q=검색어`
- `POST /api/issue-search`

이슈 검색 예시:

```powershell
Invoke-RestMethod "http://127.0.0.1:3110/api/issue-search?q=AI%20반도체&limit=5"
```

응답에는 AI가 바로 읽기 좋은 `text` 필드가 포함됩니다.

## 외부 공개

Ollama `11434` 포트를 직접 공개하지 말고, 이 서버 포트만 터널 또는 포트포워딩으로 공개하세요.

예:

```text
외부 사용자 -> https://터널주소/api/game-ai-advice -> 이 서버 -> http://127.0.0.1:11434/api/chat
```
