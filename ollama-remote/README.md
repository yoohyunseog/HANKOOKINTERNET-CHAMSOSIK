# Ollama 원격 서버 관리 가이드

## 📋 개요

이 디렉토리는 웹 서버(211.45.162.155)의 Ollama 서비스를 원격으로 관리하기 위한 스크립트들을 포함하고 있습니다.

## 🔒 보안 기능

### 한국 IP만 접근 허용

Ollama API는 다음과 같은 보안 계층을 통해 보호됩니다:

1. **로컬호스트 전용 리스닝**: Ollama는 `127.0.0.1:11434`에서만 리스닝
2. **웹 서버 프록시**: 외부 접근은 웹 서버(server.js)를 통해서만 가능
3. **GeoIP 필터링**: 한국(KR) IP만 API 사용 가능
4. **API Key 인증**: Ollama Cloud API Key 필요

### 보안 아키텍처

```
외부 요청 → 웹 서버(server.js) → GeoIP 확인 → 한국 IP만 허용 → Ollama API
                    ↓
              한국 IP가 아니면 403 차단
```

## 📁 파일 설명

| 파일 | 설명 |
|------|------|
| `run_ollama_server_remote.bat` | Ollama 서버 시작 (보안 모드) |
| `stop_ollama_server_remote.bat` | Ollama 서버 중지 |
| `status_ollama_server_remote.bat` | Ollama 서버 상태 확인 |
| `install_ollama_server.bat` | Ollama 서버 설치 |
| `login_ollama_remote.bat` | Ollama 클라우드 로그인 |
| `setup_external_access.bat` | 외부 접속 설정 (보안 모드) |
| `test_cloud_model.bat` | 클라우드 모델 테스트 |

## 🚀 사용 방법

### 1. Ollama 서버 시작

```batch
run_ollama_server_remote.bat
```

이 스크립트는 다음을 수행합니다:
1. 기존 Ollama 서비스 중지
2. 한국 IP만 접근 허용 설정
3. 로컬호스트 전용 리스닝 설정
4. Ollama 서비스 시작
5. 클라우드 모델 로그인
6. 서버 상태 확인

### 2. Ollama 서버 중지

```batch
stop_ollama_server_remote.bat
```

### 3. 서버 상태 확인

```batch
status_ollama_server_remote.bat
```

### 4. 클라우드 모델 테스트

```batch
test_cloud_model.bat
```

## 🔧 설정

### 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `OLLAMA_HOST` | `127.0.0.1:11434` | Ollama 리스닝 주소 |
| `OLLAMA_API_KEY` | (설정됨) | Ollama Cloud API Key |
| `OLLAMA_NO_CLOUD` | `false` | 클라우드 모델 사용 여부 |

### 웹 서버 설정 (server.js)

웹 서버의 `server.js`에서 다음 미들웨어가 적용됩니다:

```javascript
// 한국 IP만 Ollama API 접근 허용
app.use('/api/ollama-', (req, res, next) => {
    const ip = getClientIp(req);
    const countryCode = getRequestCountryCode(req, ip);
    
    if (countryCode && countryCode !== 'KR') {
        return res.status(403).json({
            error: 'Access denied. Korean IP only.',
            country: countryCode
        });
    }
    next();
});
```

## 📊 설치된 모델

| 모델명 | 크기 | 유형 | 설명 |
|--------|------|------|------|
| `llama3.2:3b` | 2.0 GB | 로컬 | Llama 3.2 3B (로컬 실행) |
| `deepseek-v4-pro:cloud` | - | 클라우드 | DeepSeek V4 Pro (API 호출) |
| `kimi-k2.5:cloud` | - | 클라우드 | Kimi K2.5 (API 호출) |
| `glm-5:cloud` | - | 클라우드 | GLM-5 (API 호출) |

## ⚠️ 주의사항

### 1. 외부 IP 차단

다음 IP들은 차단됩니다:
- 한국(KR) 이외의 모든 국가 IP
- 알 수 없는 IP (GeoIP 확인 불가)

### 2. API 사용량 모니터링

클라우드 모델(`:cloud` 태그)은 Ollama Cloud API를 사용하므로 사용량이 청구됩니다.

```bash
# 사용량 확인
ssh root@211.45.162.155 "ollama list"
```

### 3. 로그 확인

```bash
# 실시간 로그
ssh root@211.45.162.155 "journalctl -u ollama -f"

# 최근 로그
ssh root@211.45.162.155 "journalctl -u ollama --since '1 hour ago'"
```

## 🛠️ 문제 해결

### Q: 외부에서 API 접근이 안 돼요

**A:** 정상입니다. 보안을 위해 한국 IP만 접근 가능합니다. 웹 서버를 통해 접근하세요.

### Q: 한국인데 접근이 안 돼요

**A:** VPN이나 프록시를 사용 중인 경우 한국 IP로 인식되지 않을 수 있습니다.

### Q: 클라우드 모델 사용량이 많아요

**A:** 다음을 확인하세요:
1. 외부 IP에서 무단 사용 여부
2. 로그에서 비정상적인 요청 패턴
3. API Key 노출 여부

### Q: Ollama 서버가 시작되지 않아요

**A:** 다음을 확인하세요:
```bash
# 서비스 상태
ssh root@211.45.162.155 "systemctl status ollama"

# 포트 확인
ssh root@211.45.162.155 "ss -tlnp | grep 11434"

# 로그 확인
ssh root@211.45.162.155 "journalctl -u ollama -n 50"
```

## 📞 지원

문제가 지속되면 다음을 확인하세요:
1. SSH 연결 상태
2. 서버 디스크 용량
3. 메모리 사용량
4. Ollama 서비스 로그

---

**마지막 업데이트**: 2026-06-12
**버전**: 2.0.0 (보안 강화 버전)