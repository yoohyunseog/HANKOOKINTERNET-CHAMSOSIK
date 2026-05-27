// ...existing code...
// 한국 IP 여부 확인 API
// (app이 선언된 후 아래에 위치해야 함)
// ...existing code...
const express = require('express');
const bodyParser = require('body-parser');
const compression = require('compression');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const cors = require('cors');
const xss = require('xss-clean');
const hpp = require('hpp');
const path = require('path');
const fs = require('fs'); // fs require를 path와 함께 위쪽에 위치
const crypto = require('crypto');
const { calculateNB } = require('./calculate');
const storage = require('./storage');
const config = require('./config.json');

const app = express();

// Trust proxy - Nginx 리버스 프록시 뒤에서 실행
app.set('trust proxy', 1);

// 보안 미들웨어 적용
// 한국인터넷.한국은 아직 HTTPS 인증서가 없으므로 HSTS와 HTTP 자동 업그레이드를 끕니다.
app.use(helmet({
  strictTransportSecurity: false,
  contentSecurityPolicy: {
    directives: {
      ...helmet.contentSecurityPolicy.getDefaultDirectives(),
      'upgrade-insecure-requests': null
    }
  }
})); // HTTP 헤더 보안

// 기존 브라우저 HSTS 캐시 해제용 헤더
app.use((req, res, next) => {
  res.setHeader('Strict-Transport-Security', 'max-age=0');
  next();
});
app.use(cors()); // CORS 설정
app.use(xss()); // XSS 공격 방어
app.use(hpp()); // HTTP Parameter Pollution 방어

// Rate Limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15분
  max: 250, // IP당 최대 250 요청
  message: '너무 많은 요청이 발생했습니다. 잠시 후 다시 시도해주세요.',
  validate: {xForwardedForHeader: false}, // X-Forwarded-For validation 비활성화
  skip: (req) => {
    const path = req.path || '';
    const originalUrl = req.originalUrl || '';
    // SEO 및 주요 API 경로는 rate limit 제외
    return path === '/sitemap.xml' ||
           path === '/feed.xml' ||
           path === '/feed-popular.xml' ||
           path === '/robots.txt' ||
           path === '/ads.txt' ||
           path.startsWith('/api/recent') ||
           path.startsWith('/api/calculation') ||
           path.startsWith('/api/search') ||
           path.startsWith('/api/most-viewed') ||
           path.startsWith('/api/visits/') ||
           path.startsWith('/api/keywords/') ||
           path.startsWith('/api/radio-state') ||
           path.startsWith('/api/ollama-') ||
           originalUrl.startsWith('/api/radio-state') ||
           originalUrl.startsWith('/api/ollama-') ||
           path.startsWith('/api/stats') ||
           path === '/api/health' ||
           /^\/google[a-zA-Z0-9]+\.html$/.test(path);
  }
});
app.use(limiter);

app.use(compression()); // Gzip 압축 활성화
const PORT = process.env.PORT || 3000;
const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
const AI_TUNNEL_URL = (process.env.AI_TUNNEL_URL || 'https://gilbert-bases-tracked-hopes.trycloudflare.com').replace(/\/$/, '');
const AI_TUNNEL_FILE = process.env.AI_TUNNEL_FILE || path.join(__dirname, 'data', 'ai-tunnel-url.json');
const AI_CHAT_MODEL = process.env.AI_CHAT_MODEL || process.env.OLLAMA_MODEL || 'llama3';

// Ollama Web Search API 설정
const OLLAMA_API_KEY = process.env.OLLAMA_API_KEY || '';
const OLLAMA_WEB_SEARCH_URL = process.env.OLLAMA_WEB_SEARCH_URL || 'https://ollama.com/api/web_search';
const WEB_SEARCH_LIMIT = parseInt(process.env.WEB_SEARCH_LIMIT || '5', 10);
const WEB_SEARCH_TIMEOUT_MS = parseInt(process.env.WEB_SEARCH_TIMEOUT_MS || '20000', 10);
const TREND_DATA_PATH = path.join(__dirname, '..', 'data', 'naver_creator_trends', 'latest_trend_data.json');
const DEFAULT_MODEL = process.env.OLLAMA_MODEL || 'llama3';
const COUPANG_DOMAIN = 'https://api-gateway.coupang.com';
const COUPANG_ACCESS_KEY = process.env.COUPANG_ACCESS_KEY || 'a4672c2f-d1e7-4f48-9c34-30535528c8c7';
const COUPANG_SECRET_KEY = process.env.COUPANG_SECRET_KEY || 'ed03dd673ad780db96453e2c869cfc9861584802';
const COUPANG_SUB_ID = process.env.COUPANG_SUB_ID || '';
const coupangProductsCache = new Map();
const COUPANG_CACHE_TTL_MS = parseInt(process.env.COUPANG_CACHE_TTL_MS || '600000', 10);

// /api/recent 응답 캐시 (JSON 파일, limit별) - 최적화: TTL 증가
const RECENT_CACHE_TTL_MS = parseInt(process.env.RECENT_CACHE_TTL_MS || '30000', 10); // 10초 → 30초
const RECENT_CACHE_TTL_LIMIT_100_MS = parseInt(process.env.RECENT_CACHE_TTL_LIMIT_100_MS || '120000', 10); // 1분 → 2분
const RECENT_CACHE_TTL_LIMIT_1_MS = parseInt(process.env.RECENT_CACHE_TTL_LIMIT_1_MS || '30000', 10); // 10초 → 30초
const RECENT_CACHE_DIR = path.join(__dirname, '..', 'data', 'cache');
const RECENT_CACHE_FILE_PATH = path.join(RECENT_CACHE_DIR, 'recent_api_cache.json');
const RADIO_STATE_FILE_PATH = path.join(RECENT_CACHE_DIR, 'radio_state.json');

// 인기 키워드 캐시 설정 - 최적화: 5분으로 증가
const KEYWORDS_CACHE_TTL_MS = parseInt(process.env.KEYWORDS_CACHE_TTL_MS || '300000', 10); // 1분 → 5분
const KEYWORDS_CACHE_FILE_PATH = path.join(RECENT_CACHE_DIR, 'keywords_top_cache.json');
const KEYWORDS_REGION_CACHE_FILE_PATH = path.join(RECENT_CACHE_DIR, 'keywords_region_cache.json');

function getRecentCacheTtlMs(limit) {
    if (limit === 100) return RECENT_CACHE_TTL_LIMIT_100_MS;
    if (limit === 1) return RECENT_CACHE_TTL_LIMIT_1_MS;
    return RECENT_CACHE_TTL_MS;
}

function ensureRecentCacheDir() {
    if (!fs.existsSync(RECENT_CACHE_DIR)) {
        fs.mkdirSync(RECENT_CACHE_DIR, { recursive: true });
    }
}

function ensureRecentCacheFile() {
    try {
        ensureRecentCacheDir();
        if (!fs.existsSync(RECENT_CACHE_FILE_PATH)) {
            fs.writeFileSync(RECENT_CACHE_FILE_PATH, '{}', 'utf8');
            if (process.env.NODE_ENV !== 'production') {
                console.log(`[recent-cache] 캐시 파일 생성: ${RECENT_CACHE_FILE_PATH}`);
            }
        }
    } catch (error) {
        console.error('[recent-cache] 캐시 파일 초기화 오류:', error.message);
    }
}

function readRecentFileCache() {
    try {
        ensureRecentCacheFile();
        if (!fs.existsSync(RECENT_CACHE_FILE_PATH)) {
            return {};
        }
        const raw = fs.readFileSync(RECENT_CACHE_FILE_PATH, 'utf8');
        if (!raw) return {};
        return JSON.parse(raw);
    } catch (error) {
        console.error('[recent-cache] 파일 읽기 오류:', error.message);
        return {};
    }
}

function writeRecentFileCache(cacheObject) {
    try {
        ensureRecentCacheFile();
        fs.writeFileSync(RECENT_CACHE_FILE_PATH, JSON.stringify(cacheObject, null, 2), 'utf8');
        return true;
    } catch (error) {
        console.error('[recent-cache] 파일 쓰기 오류:', error.message);
        console.error('[recent-cache] 쓰기 대상 경로:', RECENT_CACHE_FILE_PATH);
        return false;
    }
}

function defaultRadioState() {
    const now = Date.now();
    return {
        stationUrl: 'https://soundcloud.com/revenue-589926433/sets/n-b-ai-dj',
        trackIndex: 0,
        trackId: null,
        trackTitle: '',
        artist: '',
        status: 'paused',
        positionMs: 0,
        startedAt: now,
        updatedAt: now,
        version: 1,
        source: 'server-default'
    };
}

function readRadioState() {
    try {
        ensureRecentCacheDir();
        if (!fs.existsSync(RADIO_STATE_FILE_PATH)) {
            const state = defaultRadioState();
            fs.writeFileSync(RADIO_STATE_FILE_PATH, JSON.stringify(state, null, 2), 'utf8');
            return state;
        }
        const raw = fs.readFileSync(RADIO_STATE_FILE_PATH, 'utf8');
        return raw ? { ...defaultRadioState(), ...JSON.parse(raw) } : defaultRadioState();
    } catch (error) {
        console.error('[radio-state] read error:', error.message);
        return defaultRadioState();
    }
}

function writeRadioState(nextState) {
    ensureRecentCacheDir();
    fs.writeFileSync(RADIO_STATE_FILE_PATH, JSON.stringify(nextState, null, 2), 'utf8');
}

function publicRadioState(state) {
    const now = Date.now();
    const livePositionMs = state.status === 'playing'
        ? Math.max(0, Number(state.positionMs || 0) + Math.max(0, now - Number(state.startedAt || now)))
        : Math.max(0, Number(state.positionMs || 0));

    return {
        ...state,
        serverNow: now,
        livePositionMs
    };
}

// 인기 키워드 캐시 파일 읽기/쓰기
function readKeywordsCache() {
    try {
        ensureRecentCacheDir();
        if (!fs.existsSync(KEYWORDS_CACHE_FILE_PATH)) {
            return null;
        }
        const raw = fs.readFileSync(KEYWORDS_CACHE_FILE_PATH, 'utf8');
        if (!raw) return null;
        return JSON.parse(raw);
    } catch (error) {
        console.error('[keywords-cache] 파일 읽기 오류:', error.message);
        return null;
    }
}

function writeKeywordsCache(data) {
    try {
        ensureRecentCacheDir();
        const cacheData = {
            timestamp: Date.now(),
            data: data
        };
        fs.writeFileSync(KEYWORDS_CACHE_FILE_PATH, JSON.stringify(cacheData, null, 2), 'utf8');
        console.log('[keywords-cache] 캐시 저장 완료');
        return true;
    } catch (error) {
        console.error('[keywords-cache] 파일 쓰기 오류:', error.message);
        return false;
    }
}

// 지역별 키워드 캐시 읽기/쓰기
function readRegionKeywordsCache() {
    try {
        ensureRecentCacheDir();
        if (!fs.existsSync(KEYWORDS_REGION_CACHE_FILE_PATH)) {
            return null;
        }
        const raw = fs.readFileSync(KEYWORDS_REGION_CACHE_FILE_PATH, 'utf8');
        if (!raw) return null;
        return JSON.parse(raw);
    } catch (error) {
        console.error('[region-keywords-cache] 파일 읽기 오류:', error.message);
        return null;
    }
}

function writeRegionKeywordsCache(data) {
    try {
        ensureRecentCacheDir();
        const cacheData = {
            timestamp: Date.now(),
            data: data
        };
        fs.writeFileSync(KEYWORDS_REGION_CACHE_FILE_PATH, JSON.stringify(cacheData, null, 2), 'utf8');
        console.log('[region-keywords-cache] 캐시 저장 완료');
        return true;
    } catch (error) {
        console.error('[region-keywords-cache] 파일 쓰기 오류:', error.message);
        return false;
    }
}

// MMDB 파일 경로 선언
const MMDB_PATH = path.join(__dirname, 'GeoLite2-Country.mmdb');

// GeoIP MMDB 라이브러리 추가
const maxmind = require('maxmind');
let geoipLookup = null;
if (fs.existsSync(MMDB_PATH)) {
    maxmind.open(MMDB_PATH)
        .then(lookup => {
            geoipLookup = lookup;
            console.log('[GeoIP] MMDB 로드 성공');
        })
        .catch(err => {
            console.error('[GeoIP] MMDB 로드 실패:', err);
        });
} else {
    console.warn(`[GeoIP] MMDB 파일이 없습니다. 다운로드 필요: ${MMDB_PATH}`);
    // MMDB 다운로드 안내
    console.warn('GeoLite2-Country.mmdb 파일을 https://dev.maxmind.com/geoip/geolite2-free-geolocation-data?lang=ko 에서 다운로드 후 server.js와 같은 폴더에 넣으세요.');
}


// 스토리지 초기화
storage.initStorage();
ensureRecentCacheFile();
console.log(`[recent-cache] 사용 경로: ${RECENT_CACHE_FILE_PATH}`);

// 도메인 검증 미들웨어 (CORS 전에 실행)
app.use((req, res, next) => {
    const host = req.get('host') || req.hostname || 'unknown';
    const allowedDomains = config.allowedDomains || [];
    
    // 포트 제거해서 도메인만 비교
    const hostWithoutPort = host.split(':')[0].toLowerCase();
    
    if (process.env.NODE_ENV !== 'production') {
        console.log(`[DEBUG] Host: ${host} | hostname: ${req.hostname} | hostWithoutPort: ${hostWithoutPort} | allowedDomains: ${allowedDomains.join(', ')}`);
    }
    
    // localhost는 항상 허용 (개발 환경)
    if (hostWithoutPort === 'localhost' || hostWithoutPort === '127.0.0.1' || hostWithoutPort === '::1') {
        if (process.env.NODE_ENV !== 'production') {
            console.log(`[허용됨] localhost 개발 환경`);
        }
        return next();
    }
    
    // 허용된 도메인 확인 (www 버전도 포함)
    const isAllowed = allowedDomains.some(domain => {
        const domainLower = domain.toLowerCase();
        return hostWithoutPort === domainLower || 
               hostWithoutPort === 'www.' + domainLower;
    });
    
    if (!isAllowed) {
        console.warn(`[차단됨] 허용되지 않은 도메인 접속 시도: ${hostWithoutPort} from IP: ${req.ip}`);
        // 연결을 즉시 끊음 (페이지 표시 안 함)
        return res.destroy();
    }
    
    if (process.env.NODE_ENV !== 'production') {
        console.log(`[허용됨] 도메인: ${hostWithoutPort}`);
    }
    next();
});

// CORS 설정
app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    if (req.method === 'OPTIONS') {
        return res.sendStatus(200);
    }
    next();
});

// 미들웨어
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Favicon 요청을 기본적으로 처리
app.get('/favicon.ico', (req, res) => {
    const host = (req.get('host') || '').split(':')[0].toLowerCase().replace(/^www\./, '');
    if (host === '참소식.com' || host === 'xn--9l4b4xi9r.com') {
        return res.redirect(302, '/favicon.svg');
    }
    return res.status(204).end();
});

function decodePathSafely(value) {
    try {
        return decodeURIComponent(value);
    } catch (error) {
        return value;
    }
}

function isClosedPagePath(req) {
    const rawPath = req.path || '';
    const rawOriginalPath = (req.originalUrl || '').split('?')[0];
    const paths = [
        rawPath,
        rawOriginalPath,
        decodePathSafely(rawPath),
        decodePathSafely(rawOriginalPath)
    ].map(value => String(value || '').toLowerCase());

    return paths.some(value =>
        value.startsWith('/api/radio-state') ||
        /(^|\/)(radio|radio\.html|chamsosik-radio|chamsosik-radio\.html|참소식-라디오|참소식라디오|라디오|ai-issue-briefing|chat-board)(\/|$)/i.test(value)
    );
}

app.use((req, res, next) => {
    if (!isClosedPagePath(req)) {
        return next();
    }

    res.setHeader('Cache-Control', 'no-store, max-age=0');
    if (req.path.startsWith('/api/') || req.accepts(['html', 'json']) === 'json') {
        return res.status(410).json({
            success: false,
            error: 'This page is permanently closed. Reason: suspicious attempts to access long-term archived private information related to the server administrator have been identified. A record showing unauthorized absence on the day a resignation letter was submitted 10 years ago has also been identified. The server administrator has only now, 10 years after the incident, identified these circumstances and records. Korean-language domains may require additional filtering and verification when Korean and English are mixed, while English-only domains may not face the same filtering burden. Additional related findings may be reported to ICANN and other domain or network management authorities.'
        });
    }

    return res.status(410).send(`<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <title>페이지 영구 폐쇄</title>
  <style>
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      font-family: Arial, "Noto Sans KR", sans-serif;
      color: #1f2933;
      background: #f5f7fa;
    }
    main {
      width: min(520px, calc(100% - 32px));
      text-align: center;
    }
    h1 {
      margin: 0 0 12px;
      font-size: 28px;
      line-height: 1.25;
    }
    p {
      margin: 0;
      color: #52606d;
      font-size: 16px;
      line-height: 1.6;
    }
    .notice-emphasis {
      display: block;
      margin: 18px 0;
      padding: 12px 14px;
      border-radius: 8px;
      background: #7f1d1d;
      color: #ffffff;
      font-size: 18px;
      font-weight: 900;
      line-height: 1.55;
    }
    .notice-emphasis.secondary {
      background: #1e3a8a;
    }
    a {
      display: inline-block;
      margin-top: 14px;
      color: #1d4ed8;
      font-weight: 800;
      text-decoration: underline;
      text-underline-offset: 3px;
    }
  </style>
</head>
<body>
  <main>
    <h1>🇰🇷 한글도메인 &lt;&gt; 🇺🇸 페이지가 영구적으로 폐쇄되었습니다</h1>
    <p>사유: 최근 서버 관리자와 관련된 장기 보관 사적 정보 데이터에 대해 비정상적인 조회 시도로 의심되는 정황을 확인하였습니다. 또한 10년 전 회사에 사직서를 제출한 날이 무단 결근으로 처리된 기록도 확인되었습니다. <span class="notice-emphasis">서버 관리자는 사건 발생 후 10년이 지난 현재에서야 위와 같은 정황과 기록을 확인하였습니다.</span> 한글 도메인은 한글·영문 혼용 과정에서 추가적인 필터링과 검증 부담이 발생할 수 있는 반면, 영문 도메인은 상대적으로 동일한 필터링 부담이 적은 경우가 있습니다. <span class="notice-emphasis secondary">서버 관리자에 대한 10년 전 데이터의 정보 유출로 인해 해당 페이지를 폐쇄 조치합니다.</span> 해당 데이터에는 민감한 공공·국가 관련 정보가 포함될 가능성이 있어, 관련 페이지 운영을 중단합니다. 관련 정황이 추가로 확인될 경우, ICANN 등 도메인 및 네트워크 관리 기관에 제보될 수 있습니다.</p>
    <a href="https://www.icann.org/compliance/complaint" target="_blank" rel="noopener noreferrer">ICANN Contractual Compliance Complaint</a>
  </main>
</body>
</html>`);
});

app.use((req, res, next) => {
    if ((req.path || '').toLowerCase() !== '/server-journal.html') {
        return next();
    }

    res.setHeader('Cache-Control', 'no-store, max-age=0');
    res.setHeader('X-Robots-Tag', 'noindex, nofollow, noarchive');
    res.setHeader('Referrer-Policy', 'no-referrer');
    res.setHeader('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()');
    res.setHeader('Cross-Origin-Resource-Policy', 'same-origin');
    next();
});

// 예전 domain-check.js가 보내던 잘못된 404 경로 호환 처리
app.use((req, res, next) => {
    if (req.originalUrl.includes('/xn--9l4b4xi9r.com') &&
        req.originalUrl.includes('/ErrPage/404/index.html')) {
        return res.redirect(302, '/참소식.com/ErrPage/404/index.html');
    }
    next();
});

// 도메인별 정적 파일 제공 미들웨어
app.use((req, res, next) => {
    // /api/* 요청은 정적 파일로 처리하지 않음
    if (req.path.startsWith('/api/') || req.path.startsWith('/feed') || req.path.startsWith('/sitemap')) {
        return next();
    }
    
    const host = req.get('host') || req.hostname || '한국인터넷.한국';
    const hostWithoutPort = host.split(':')[0].toLowerCase();
    
    // 도메인에 따라 정적 파일 경로 결정
    let staticDir = '한국인터넷.한국'; // 기본값
    
    // config.json의 allowedDomains에서 도메인 확인
    const domainMap = {
        '한국인터넷.한국': '한국인터넷.한국',
        'xn--3e0bx5eku0am2irhf.xn--3e0b707e': '한국인터넷.한국',
        '참소식.com': '한국인터넷.한국/참소식.com',
        'www.참소식.com': '한국인터넷.한국/참소식.com',
        'xn--9l4b4xi9r.com': '한국인터넷.한국/참소식.com',
        'www.xn--9l4b4xi9r.com': '한국인터넷.한국/참소식.com'
    };
    
    // www 제거해서 확인
    const domainKey = hostWithoutPort.replace(/^www\./, '');
    if (domainMap[domainKey] || domainMap[hostWithoutPort]) {
        staticDir = domainMap[domainKey] || domainMap[hostWithoutPort];
    }
    
    const fullPath = path.join(__dirname, 'public', staticDir);
    
    // 정적 파일 제공 - 최적화: 브라우저 캐싱 추가 (7일)
    express.static(fullPath, {
        maxAge: '7d', // 7일간 브라우저 캐시
        etag: true,    // ETag 헤더 활성화
        lastModified: true, // Last-Modified 헤더 활성화
        setHeaders: (res, path) => {
            // HTML은 짧게, CSS/JS/이미지는 길게
            if (path.endsWith('domain-check.js')) {
                res.setHeader('Cache-Control', 'no-cache, max-age=0');
            } else if (path.endsWith('.html')) {
                res.setHeader('Cache-Control', 'public, max-age=3600'); // 1시간
            } else if (path.match(/\.(css|js|jpg|jpeg|png|gif|ico|woff|woff2)$/)) {
                res.setHeader('Cache-Control', 'public, max-age=604800'); // 7일
            }
        }
    })(req, res, next);
});

// 방문 기록 미들웨어
app.use((req, res, next) => {
    const ip = req.headers['x-forwarded-for'] || req.connection.remoteAddress || 'unknown';
    const userAgent = req.headers['user-agent'] || 'unknown';
    const rawKeyword = req.query.keyword || req.query.nb || req.body.input || null;
    const keyword = normalizeKeyword(rawKeyword);
    
    storage.recordVisit(ip, req.path, userAgent, keyword);
    next();
});

const calculationConfig = {
    bitDefaultValue: 999,
    decimalPlaces: 10,
    calculationCountForText: 1
};

function normalizeKeyword(rawText) {
    if (!rawText || typeof rawText !== 'string') {
        return '';
    }
    const firstLine = rawText.split('\n')[0].trim();
    if (!firstLine || firstLine === '-') {
        return '';
    }
    return firstLine.slice(0, 60);
}

function normalizeCoupangKeyword(rawText) {
    const normalized = String(rawText || '')
        .replace(/[^\p{L}\p{N}\s.+#-]/gu, ' ')
        .replace(/\s+/g, ' ')
        .trim()
        .slice(0, 80);

    return extractCoupangProductKeyword(normalized);
}

function normalizeCoupangKeywords(input) {
    const values = Array.isArray(input) ? input : [input];
    const keywords = [];
    const seen = new Set();

    for (const value of values) {
        const parts = String(value || '')
            .split(/[,\n|]+/g)
            .map((item) => normalizeCoupangKeyword(item))
            .filter(Boolean);

        for (const keyword of parts) {
            const key = keyword.toLowerCase();
            if (!seen.has(key)) {
                seen.add(key);
                keywords.push(keyword);
            }
            if (keywords.length >= 8) return keywords;
        }
    }

    return keywords;
}

function extractCoupangProductKeyword(keyword) {
    if (!keyword) return '';

    const patterns = [
        /\bCore\s+i[3579][-\s]?\d{4,5}[A-Z]*\b/i,
        /\bi[3579][-\s]?\d{4,5}[A-Z]*\b/i,
        /\bCore\s+Ultra\s+[3579][-\s]?\d{3,5}[A-Z]*\b/i,
        /\bCore\s+9\s+\d{3,5}[A-Z]*\b/i,
        /\bRyzen\s+(?:AI\s+)?[3579]\s+\d{3,5}[A-Z0-9]*\b/i,
        /\bXeon\s+[A-Z0-9 -]{2,18}\b/i,
        /\bRTX\s?\d{4}(?:\s?Ti|\s?Super)?\b/i,
        /\bGTX\s?\d{4}(?:\s?Ti)?\b/i,
        /\bRX\s?\d{4}(?:\s?XT|\s?XTX)?\b/i,
        /\bFSR\s?\d(?:\.\d)?\b/i,
        /\bDLSS\s?\d(?:\.\d)?\b/i,
        /\bDDR[45][-\s]?\d{3,5}\b/i,
        /\bPCIe\s?\d(?:\.\d)?\b/i,
        /\b12V-?2x6\b/i,
        /\b12VHPWR\b/i
    ];

    for (const pattern of patterns) {
        const match = keyword.match(pattern);
        if (match && match[0]) {
            return match[0].replace(/\s+/g, ' ').trim().slice(0, 80);
        }
    }

    const phraseRules = [
        { test: /바틀렛\s?레이크|Bartlett\s+Lake/i, value: '인텔 바틀렛레이크 CPU' },
        { test: /그래니트\s?래피즈|Granite\s+Rapids/i, value: 'Intel Xeon Granite Rapids' },
        { test: /MRDIMM/i, value: 'MRDIMM 메모리' },
        { test: /라데온|Radeon/i, value: 'AMD Radeon 그래픽카드' },
        { test: /지포스|GeForce/i, value: 'NVIDIA GeForce 그래픽카드' },
        { test: /인텔|Intel/i, value: '인텔 CPU' },
        { test: /AMD/i, value: 'AMD CPU' },
        { test: /엔비디아|NVIDIA/i, value: 'NVIDIA 그래픽카드' }
    ];

    for (const rule of phraseRules) {
        if (rule.test.test(keyword)) return rule.value;
    }

    return keyword;
}

function createCoupangAuthorization(method, uri) {
    if (!COUPANG_ACCESS_KEY || !COUPANG_SECRET_KEY) {
        throw new Error('COUPANG_ACCESS_KEY 또는 COUPANG_SECRET_KEY가 비어 있습니다.');
    }

    const datetime = new Date()
        .toISOString()
        .slice(2, 19)
        .replace(/:/g, '')
        .replace(/-/g, '') + 'Z';

    const parts = uri.split('?');

    if (parts.length > 2) {
        throw new Error('incorrect uri format');
    }

    const path = parts[0];
    const query = parts[1] || '';

    const message = datetime + method.toUpperCase() + path + query;

    const signature = crypto
        .createHmac('sha256', COUPANG_SECRET_KEY)
        .update(message, 'utf8')
        .digest('hex');

    console.log('[coupang-signature-debug]', {
        datetime,
        method: method.toUpperCase(),
        path,
        query,
        message
    });

    return 'CEA algorithm=HmacSHA256, access-key=' + COUPANG_ACCESS_KEY +
        ', signed-date=' + datetime +
        ', signature=' + signature;
}

function mapCoupangProducts(payload, limit = 4) {
    const items = payload?.data?.productData || payload?.data || [];
    if (!Array.isArray(items)) return [];

    return items.slice(0, limit).map((item) => ({
        name: item.productName || item.name || '',
        price: Number(item.productPrice || item.price || 0),
        image: item.productImage || item.imageUrl || '',
        url: item.productUrl || item.url || '',
        rank: item.rank || null,
        isRocket: Boolean(item.isRocket),
        isFreeShipping: Boolean(item.isFreeShipping)
    })).filter((item) => item.name && item.url);
}

async function fetchCoupangProductsByKeyword(keyword, limit) {
    const path = '/v2/providers/affiliate_open_api/apis/openapi/products/search';

    const queryParams = new URLSearchParams({
        keyword,
        limit: String(limit)
    });

    if (COUPANG_SUB_ID) {
        queryParams.set('subId', COUPANG_SUB_ID);
    }

    const query = queryParams.toString();
    const uri = `${path}?${query}`;
    const url = `${COUPANG_DOMAIN}${uri}`;

    const response = await fetch(url, {
        method: 'GET',
        headers: {
            Authorization: createCoupangAuthorization('GET', uri),
            'Content-Type': 'application/json;charset=UTF-8'
        }
    });

    const text = await response.text();
    let payload = {};
    try {
        payload = JSON.parse(text);
    } catch {
        payload = { raw: text };
    }

    if (!response.ok) {
        const error = new Error('Coupang Partners API request failed.');
        error.status = response.status;
        error.payload = payload;
        throw error;
    }

    return mapCoupangProducts(payload, limit);
}

function loadTrendKeywords(limit) {
    if (!fs.existsSync(TREND_DATA_PATH)) {
        return [];
    }
    const raw = fs.readFileSync(TREND_DATA_PATH, 'utf-8');
    const data = JSON.parse(raw);
    const trends = Array.isArray(data.trend_data) ? data.trend_data : [];
    const keywords = trends
        .map(item => normalizeKeyword(item.raw_text || item.title || ''))
        .filter(Boolean);
    return keywords.slice(0, limit);
}

async function fetchPageText(url) {
    if (typeof fetch !== 'function') {
        return { url, title: '', description: '', text: '' };
    }
    const response = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } });
    const html = await response.text();
    const titleMatch = html.match(/<title>([^<]*)<\/title>/i);
    const descMatch = html.match(/<meta\s+name=["']description["']\s+content=["']([^"']*)["']\s*\/?/i);
    const bodyText = html
        .replace(/<script[\s\S]*?<\/script>/gi, ' ')
        .replace(/<style[\s\S]*?<\/style>/gi, ' ')
        .replace(/<[^>]+>/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
        .slice(0, 1200);
    return {
        url,
        title: titleMatch ? titleMatch[1].trim() : '',
        description: descMatch ? descMatch[1].trim() : '',
        text: bodyText
    };
}

async function callOllama(prompt, model) {
    if (typeof fetch !== 'function') {
        throw new Error('fetch API를 사용할 수 없습니다.');
    }
    const response = await fetch(`${OLLAMA_BASE_URL}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model, prompt, stream: false })
    });
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Ollama request failed: ${response.status} ${response.statusText} ${errorText.slice(0, 300)}`);
    }
    const data = await response.json();
    return (data && data.response) ? data.response.trim() : '';
}

function safeJsonParse(text) {
    try {
        return JSON.parse(text);
    } catch (error) {
        return null;
    }
}

function getAiTunnelUrl() {
    try {
        if (fs.existsSync(AI_TUNNEL_FILE)) {
            const data = safeJsonParse(fs.readFileSync(AI_TUNNEL_FILE, 'utf8'));
            const url = data?.url ? String(data.url).trim().replace(/\/$/, '') : '';
            if (/^https:\/\/[a-z0-9-]+\.trycloudflare\.com$/i.test(url)) {
                return url;
            }
        }
    } catch (error) {
        console.warn('[ai-tunnel] failed to read tunnel file:', error.message);
    }
    return AI_TUNNEL_URL;
}

// 홈페이지
app.post('/api/silverkmk-ai', async (req, res) => {
    try {
        const model = req.body?.model ? String(req.body.model) : DEFAULT_MODEL;
        const systemPrompt = req.body?.systemPrompt ? String(req.body.systemPrompt) : '';
        const userPrompt = req.body?.userPrompt ? String(req.body.userPrompt) : '';

        if (!userPrompt.trim()) {
            return res.status(400).json({ ok: false, error: 'userPrompt is required' });
        }

        const prompt = [
            systemPrompt.trim(),
            '',
            userPrompt.trim(),
            '',
            'Return JSON only.'
        ].join('\n').trim();

        const content = await callOllama(prompt, model);
        return res.json({ ok: true, model, content });
    } catch (error) {
        console.error('[silverkmk-ai] error:', error.message);
        return res.status(500).json({ ok: false, error: error.message || 'unknown error' });
    }
});

app.get('/api/ollama-health', async (req, res) => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);

    try {
        let response = null;
        let source = OLLAMA_BASE_URL;
        const tunnelUrl = getAiTunnelUrl();

        try {
            response = await fetch(`${OLLAMA_BASE_URL.replace(/\/$/, '')}/api/tags`, { signal: controller.signal });
        } catch (error) {
            console.warn('[ollama-health] local candidate failed:', error.message);
        }

        if ((!response || !response.ok) && tunnelUrl) {
            response = await fetch(`${tunnelUrl}/api/tags`, { signal: controller.signal });
            source = tunnelUrl;
        }

        const text = await response.text();
        const payload = safeJsonParse(text) || { raw: text };
        return res.status(200).json({
            ok: true,
            server: 'chamsosik-ai-chat',
            mode: response.ok
                ? (source === tunnelUrl ? 'cloudflare-quick-tunnel' : 'server-local-ollama')
                : 'server-built-in-fallback',
            ollamaUrl: source,
            defaultModel: AI_CHAT_MODEL,
            ollama: response.ok ? 'ok' : `error:${response.status}`,
            detail: payload
        });
    } catch (error) {
        console.error('[ollama-health] error:', error.message);
        return res.status(200).json({
            ok: true,
            server: 'chamsosik-ai-chat',
            mode: 'server-built-in-fallback',
            ollamaUrl: OLLAMA_BASE_URL,
            defaultModel: AI_CHAT_MODEL,
            ollama: error.message || 'unreachable'
        });
    } finally {
        clearTimeout(timeout);
    }
});

app.get('/api/ollama-proxy-info', (req, res) => {
    return res.json({
        ok: true,
        proxy: 'server-local-ai',
        target: OLLAMA_BASE_URL,
        tunnel: getAiTunnelUrl(),
        tunnelFile: AI_TUNNEL_FILE,
        model: AI_CHAT_MODEL,
        routes: ['/api/ollama-health', '/api/ollama-chat']
    });
});

app.get('/api/ai-tunnel-url', (req, res) => {
    return res.json({
        ok: true,
        url: getAiTunnelUrl(),
        file: AI_TUNNEL_FILE
    });
});

function normalizeChatMessages(body = {}) {
    if (Array.isArray(body.messages)) {
        return body.messages
            .filter(item => item && typeof item.content === 'string')
            .map(item => ({
                role: item.role === 'assistant' || item.role === 'system' ? item.role : 'user',
                content: item.content
            }));
    }

    const prompt = body.prompt || body.message || body.userPrompt || '';
    return prompt ? [{ role: 'user', content: String(prompt) }] : [];
}

function extractChatText(data) {
    return data?.message?.content || data?.content || data?.response || data?.answer || data?.reply || '';
}

function builtInChatReply(messages) {
    const prompt = messages.slice().reverse().find(item => item.role === 'user')?.content || '';
    const lower = prompt.toLowerCase();

    if (/^(안녕|안녕하세요|ㅎㅇ|hello|hi)(\s|[!.?。！？]|$)/i.test(prompt.trim())) {
        return [
            '안녕하세요. 참소식 AI입니다.',
            '',
            '뉴스 요약, 기사 제목 만들기, 팩트체크 체크리스트, 글 정리, 간단한 코드 리뷰를 도와드릴 수 있습니다.',
            '원문이나 초안을 붙여 주시면 바로 다듬어 드리겠습니다.'
        ].join('\n');
    }

    if (lower.includes('제목') || prompt.includes('기사')) {
        return [
            '참소식.com 기사 제목 후보입니다.',
            '',
            '1. 지금 확인해야 할 핵심 쟁점',
            '2. 데이터로 보는 오늘의 변화',
            '3. 현장에서 드러난 새로운 신호',
            '4. 독자가 놓치기 쉬운 사실관계',
            '5. 한눈에 정리한 주요 이슈',
            '6. 논란보다 사실을 먼저 보는 뉴스',
            '7. 다음 흐름을 가르는 결정적 장면',
            '',
            '리드문: 이번 사안은 단순한 사건보다 배경과 영향이 함께 읽혀야 합니다. 확인된 사실, 남은 쟁점, 독자가 알아야 할 변화를 중심으로 정리했습니다.'
        ].join('\n');
    }

    if (lower.includes('요약') || lower.includes('정리')) {
        return [
            '요약 틀입니다.',
            '',
            '핵심: 가장 중요한 사실을 첫 문장에 둡니다.',
            '배경: 왜 이 일이 중요한지 짧게 설명합니다.',
            '쟁점: 서로 다른 주장과 확인된 자료를 분리합니다.',
            '확인 필요: 출처, 날짜, 수치, 이해관계자를 다시 점검합니다.'
        ].join('\n');
    }

    if (lower.includes('팩트') || lower.includes('검증')) {
        return [
            '팩트체크 체크리스트입니다.',
            '',
            '1. 원 출처와 최초 발언 확인',
            '2. 날짜, 장소, 수치의 일치 여부 확인',
            '3. 공식 문서 또는 공개 데이터 대조',
            '4. 반론과 이해관계자 입장 분리',
            '5. 제목이 본문보다 과장되지 않았는지 확인'
        ].join('\n');
    }

    return [
        '참소식 AI 응답입니다.',
        '',
        '질문을 받았습니다. 현재 서버 내장 응답 모드에서는 뉴스 요약, 기사 제목, 팩트체크, 문장 정리처럼 정해진 작업을 중심으로 답변합니다.',
        '',
        '더 정확히 도와드리려면 원문, 기사 초안, 검증할 주장, 또는 원하는 출력 형식을 함께 보내 주세요.',
        '',
        `받은 질문: ${prompt}`
    ].join('\n');
}

async function postAiChatCandidate(url, payload, signal) {
    return fetch(`${url.replace(/\/$/, '')}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal
    });
}

app.post('/api/ollama-chat', async (req, res) => {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 90000);

    try {
        const messages = normalizeChatMessages(req.body || {});
        if (!messages.length) {
            return res.status(400).json({ ok: false, error: 'messages or prompt is required' });
        }

        const model = req.body?.model || AI_CHAT_MODEL;
        const localPayload = {
            model,
            stream: false,
            messages,
            options: {
                temperature: Number(req.body?.temperature || 0.5),
                num_predict: Number(req.body?.num_predict || 700)
            }
        };
        let response = null;
        let source = OLLAMA_BASE_URL;
        const tunnelUrl = getAiTunnelUrl();

        try {
            response = await postAiChatCandidate(OLLAMA_BASE_URL, localPayload, controller.signal);
        } catch (error) {
            console.warn('[ollama-chat] local candidate failed:', error.message);
        }

        if ((!response || !response.ok) && tunnelUrl) {
            response = await postAiChatCandidate(tunnelUrl, localPayload, controller.signal);
            source = tunnelUrl;
        }
        const text = await response.text();
        const payload = safeJsonParse(text) || { raw: text };

        if (!response.ok) {
            return res.status(200).json({
                ok: true,
                model,
                mode: 'server-built-in-fallback',
                content: builtInChatReply(messages),
                warning: `local ollama returned ${response.status}`,
                detail: payload
            });
        }

        return res.json({
            ok: true,
            model,
            mode: source === tunnelUrl ? 'cloudflare-quick-tunnel' : 'server-local-ollama',
            source,
            content: extractChatText(payload),
            raw: payload
        });
    } catch (error) {
        console.error('[ollama-chat] error:', error.message);
        const messages = normalizeChatMessages(req.body || {});
        return res.json({
            ok: true,
            model: req.body?.model || AI_CHAT_MODEL,
            mode: 'server-built-in-fallback',
            content: builtInChatReply(messages),
            warning: error.message || 'local ollama unavailable'
        });
    } finally {
        clearTimeout(timeout);
    }
});

// Ollama Web Search API
app.post('/api/ollama-web-search', async (req, res) => {
    try {
        const { query, max_results } = req.body || {};
        if (!query || !query.trim()) {
            return res.status(400).json({ ok: false, error: 'query is required' });
        }
        if (!OLLAMA_API_KEY) {
            return res.status(400).json({ ok: false, error: 'OLLAMA_API_KEY is not configured. Set it in web/.env file.' });
        }

        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), WEB_SEARCH_TIMEOUT_MS);
        const maxResults = Math.min(Math.max(parseInt(max_results || WEB_SEARCH_LIMIT, 10) || WEB_SEARCH_LIMIT, 1), 10);

        try {
            const response = await fetch(OLLAMA_WEB_SEARCH_URL, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${OLLAMA_API_KEY}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query: query.trim(), max_results: maxResults }),
                signal: controller.signal
            });

            const text = await response.text();
            let payload = null;
            try { payload = text ? JSON.parse(text) : {}; } catch { payload = { raw: text }; }

            if (!response.ok) {
                return res.status(response.status).json({ ok: false, error: `Web search API returned ${response.status}`, detail: payload });
            }

            return res.json({ ok: true, query: query.trim(), results: payload.results || payload.data || payload, source: 'ollama-web-search' });
        } catch (error) {
            if (error.name === 'AbortError') {
                return res.status(504).json({ ok: false, error: 'Web search timed out' });
            }
            throw error;
        } finally {
            clearTimeout(timeout);
        }
    } catch (error) {
        console.error('[ollama-web-search] error:', error.message);
        return res.status(500).json({ ok: false, error: error.message });
    }
});

// Ollama Web Search 결과를 AI 채팅 컨텍스트에 포함시켜 응답
// AI Proxy 서버 (http://127.0.0.1:3110/api/search-chat) 로 프록시
app.get('/api/ollama-chat-with-search', (req, res) => {
    return res.status(405).json({
        ok: false,
        error: '이 엔드포인트는 POST 메서드만 지원합니다. /api/ollama-chat-with-search 는 POST로 요청해주세요.',
        method: 'GET',
        allowed_methods: ['POST']
    });
});
app.post('/api/ollama-chat-with-search', async (req, res) => {
    const AI_PROXY_URL = process.env.AI_PROXY_URL || 'http://127.0.0.1:3110';

    try {
        const body = req.body || {};
        const searchQuery = body.search_query || body.prompt || body.message || '';
        const messages = normalizeChatMessages(body);

        const proxyResponse = await fetch(`${AI_PROXY_URL}/api/search-chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: body.model || AI_CHAT_MODEL,
                messages: messages.length > 0 ? messages : [{ role: 'user', content: searchQuery }],
                query: searchQuery,
                max_results: parseInt(body.max_results || WEB_SEARCH_LIMIT, 10),
                temperature: Number(body.temperature || 0.35),
                num_predict: Number(body.num_predict || 1200)
            }),
            signal: AbortSignal.timeout(120000)
        });

        const data = await proxyResponse.json();
        if (!proxyResponse.ok) {
            throw new Error(`AI Proxy returned ${proxyResponse.status}: ${data.error || 'unknown'}`);
        }

        return res.json({
            ok: true,
            model: data.model || body.model || AI_CHAT_MODEL,
            mode: 'ai-proxy-search',
            content: data.content || '',
            search: { query: data.query || searchQuery, results: data.results || [] },
            raw: data
        });
    } catch (error) {
        console.error('[ollama-chat-with-search] proxy error:', error.message);
        // 실패 시 일반 채팅으로 폴백
        try {
            const messages = normalizeChatMessages(req.body || {});
            const localPayload = {
                model: req.body?.model || AI_CHAT_MODEL,
                stream: false,
                messages,
                options: { temperature: Number(req.body?.temperature || 0.5), num_predict: 700 }
            };
            const tunnelUrl = getAiTunnelUrl();
            let response = null;
            let source = OLLAMA_BASE_URL;
            try { response = await postAiChatCandidate(OLLAMA_BASE_URL, localPayload, AbortSignal.timeout(30000)); } catch (e) {}
            if ((!response || !response.ok) && tunnelUrl) {
                response = await postAiChatCandidate(tunnelUrl, localPayload, AbortSignal.timeout(30000));
                source = tunnelUrl;
            }
            if (response && response.ok) {
                const text = await response.text();
                const payload = safeJsonParse(text) || { raw: text };
                return res.json({
                    ok: true, model: req.body?.model || AI_CHAT_MODEL,
                    mode: source === tunnelUrl ? 'cloudflare-quick-tunnel' : 'server-local-ollama',
                    content: extractChatText(payload),
                    search: { error: error.message }
                });
            }
        } catch (fallbackError) {
            console.error('[ollama-chat-with-search] fallback failed:', fallbackError.message);
        }

        return res.json({
            ok: true,
            model: req.body?.model || AI_CHAT_MODEL,
            mode: 'server-built-in-fallback',
            content: builtInChatReply(normalizeChatMessages(req.body || {})),
            search: { error: error.message }
        });
    }
});

// 스마트 채팅: AI Proxy 서버의 /api/smart-chat 으로 프록시
// 뉴스 질문은 검색+요약, 일반 질문은 바로 Ollama 응답
app.post('/api/smart-chat', async (req, res) => {
    const AI_PROXY_URL = process.env.AI_PROXY_URL || 'http://127.0.0.1:3110';
    try {
        const proxyResponse = await fetch(`${AI_PROXY_URL}/api/smart-chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(req.body || {}),
            signal: AbortSignal.timeout(120000)
        });
        const data = await proxyResponse.json();
        if (!proxyResponse.ok) {
            throw new Error(`AI Proxy returned ${proxyResponse.status}: ${data.error || 'unknown'}`);
        }
        return res.json(data);
    } catch (error) {
        console.error('[smart-chat] proxy error:', error.message);
        // 폴백: 일반 채팅
        try {
            const messages = normalizeChatMessages(req.body || {});
            const localPayload = {
                model: req.body?.model || AI_CHAT_MODEL,
                stream: false,
                messages,
                options: { temperature: Number(req.body?.temperature || 0.5), num_predict: 900 }
            };
            const tunnelUrl = getAiTunnelUrl();
            let response = null;
            let source = OLLAMA_BASE_URL;
            try { response = await postAiChatCandidate(OLLAMA_BASE_URL, localPayload, AbortSignal.timeout(30000)); } catch (e) {}
            if ((!response || !response.ok) && tunnelUrl) {
                response = await postAiChatCandidate(tunnelUrl, localPayload, AbortSignal.timeout(30000));
                source = tunnelUrl;
            }
            if (response && response.ok) {
                const text = await response.text();
                const payload = safeJsonParse(text) || { raw: text };
                return res.json({
                    ok: true, model: req.body?.model || AI_CHAT_MODEL,
                    mode: source === tunnelUrl ? 'cloudflare-quick-tunnel' : 'server-local-ollama',
                    content: extractChatText(payload)
                });
            }
        } catch (fallbackError) {
            console.error('[smart-chat] fallback failed:', fallbackError.message);
        }
        return res.json({
            ok: true,
            model: req.body?.model || AI_CHAT_MODEL,
            mode: 'server-built-in-fallback',
            content: builtInChatReply(normalizeChatMessages(req.body || {}))
        });
    }
});

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', '한국인터넷.한국', 'index.html'));
});

// API: 계산 요청
app.post('/api/calculate', async (req, res) => {
    try {
        const { input, bit = calculationConfig.bitDefaultValue, category = 'general' } = req.body;
        
        if (!input) {
            return res.status(400).json({ error: '입력값이 없습니다.' });
        }

        // 숫자 배열인지 확인
        let values = [];
        if (typeof input === 'string') {
            values = input.replace(/,/g, ' ').split(/\s+/).filter(x => x.trim()).map(parseFloat);
        } else if (Array.isArray(input)) {
            values = input;
        }

        // 숫자 검증
        if (Array.isArray(values) && values.length >= 2 && values.every(v => !isNaN(v))) {
            // 숫자 계산
            const maxResult = calculateNB(values, bit, false);
            const minResult = calculateNB(values, bit, true);
            
            const result = {
                type: 'number',
                input: values,
                bit: bit,
                category: category,
                nb_max: parseFloat(maxResult.toFixed(calculationConfig.decimalPlaces)),
                nb_min: parseFloat(minResult.toFixed(calculationConfig.decimalPlaces)),
                difference: parseFloat((maxResult - minResult).toFixed(calculationConfig.decimalPlaces))
            };

            // 데이터베이스에 저장
            const saveResult = await storage.saveCalculation(result);
            
            if (saveResult.success && saveResult.calculation) {
                // 저장된 완전한 객체(view_count 포함)를 반환
                return res.json({
                    ...saveResult.calculation,
                    saved: true,
                    calculation_id: saveResult.id
                });
            } else {
                result.saved = saveResult.success;
                result.calculation_id = saveResult.id;
                return res.json(result);
            }
        } else {
            // 문자 계산
            const unicodeArray = Array.from(input).map(char => char.charCodeAt(0));
            
            if (unicodeArray.length === 0) {
                return res.status(400).json({ error: '유효한 입력이 없습니다.' });
            }

            // 3회 계산
            const results = [];
            for (let i = 0; i < calculationConfig.calculationCountForText; i++) {
                const maxResult = calculateNB(unicodeArray, bit, false);
                const minResult = calculateNB(unicodeArray, bit, true);
                
                results.push({
                    calculation: i + 1,
                    nb_max: parseFloat(maxResult.toFixed(calculationConfig.decimalPlaces)),
                    nb_min: parseFloat(minResult.toFixed(calculationConfig.decimalPlaces)),
                    difference: parseFloat((maxResult - minResult).toFixed(calculationConfig.decimalPlaces))
                });
            }

            const result = {
                type: 'text',
                input: input,
                unicode: unicodeArray,
                bit: bit,
                category: category,
                results: results
            };

            // 데이터베이스에 저장
            const saveResult = await storage.saveCalculation(result);
            
            if (saveResult.success && saveResult.calculation) {
                // 저장된 완전한 객체(view_count 포함)를 반환
                return res.json({
                    ...saveResult.calculation,
                    saved: true,
                    calculation_id: saveResult.id
                });
            } else {
                result.saved = saveResult.success;
                result.calculation_id = saveResult.id;
                return res.json(result);
            }
        }
    } catch (error) {
        console.error('계산 오류:', error);
        res.status(500).json({ error: error.message });
    }
});

// API: 검색 (Unicode 배열 또는 텍스트)
// API: 검색 (POST + GET 지원, ID 검색 추가)
app.post('/api/search', async (req, res) => {
    try {
        const { text, unicode, id, limit } = req.body;
        
        let results = [];
        const searchLimit = parseInt(limit) || 10;
        
        if (id) {
            // ID로 검색 (조회수 증가)
            const calculation = await storage.loadCalculation(id, true);
            if (calculation) {
                results = [calculation];
            }
        } else if (unicode && Array.isArray(unicode)) {
            // Unicode 배열로 검색
            results = await storage.searchByUnicode(unicode);
        } else if (text) {
            // 텍스트로 검색
            results = await storage.searchByText(text, searchLimit);
        } else {
            return res.status(400).json({ error: '검색어를 입력해주세요.' });
        }
        
        return res.json({
            success: true,
            count: results.length,
            results: results
        });
    } catch (error) {
        console.error('검색 오류:', error);
        res.status(500).json({ error: error.message });
    }
});

// API: 검색 (GET 요청 지원 - 조회수 증가용)
app.get('/api/search', async (req, res) => {
    try {
        const { text, id, limit } = req.query;
        
        let results = [];
        const searchLimit = parseInt(limit) || 10;
        
        if (id) {
            // ID로 검색 (조회수 증가)
            const calculation = await storage.loadCalculation(id, true);
            if (calculation) {
                results = [calculation];
            }
        } else if (text) {
            // 텍스트로 검색
            results = await storage.searchByText(text, searchLimit);
        } else {
            return res.status(400).json({ error: '검색어를 입력해주세요.' });
        }
        
        return res.json({
            success: true,
            count: results.length,
            results: results
        });
    } catch (error) {
        console.error('검색 오류:', error);
        res.status(500).json({ error: error.message });
    }
});

// API: 최근 계산 결과
app.get('/api/recent', async (req, res) => {
    try {
        const limit = parseInt(req.query.limit) || 10;
        const ttlMs = getRecentCacheTtlMs(limit);
        const now = Date.now();
        const cacheKey = String(limit);
        const cacheStore = readRecentFileCache();
        const cached = cacheStore[cacheKey];

        // TTL 이내 캐시 응답
        if (cached && now - cached.cachedAt < ttlMs) {
            return res.json(cached.payload);
        }

        const results = await storage.getRecentCalculations(limit);
        const payload = {
            success: true,
            count: results.length,
            results: results
        };

        cacheStore[cacheKey] = { cachedAt: now, payload };
        writeRecentFileCache(cacheStore);
        return res.json(payload);
    } catch (error) {
        console.error('최근 결과 조회 오류:', error);

        // 오류 시 stale 캐시 fallback
        const limit = parseInt(req.query.limit) || 10;
        const staleStore = readRecentFileCache();
        const stale = staleStore[String(limit)];
        if (stale && stale.payload) {
            return res.status(200).json(stale.payload);
        }

        res.status(500).json({ error: error.message });
    }
});

// API: 통계
app.get('/api/stats', async (req, res) => {
    try {
        const stats = await storage.getStatistics();
        return res.json(stats);
    } catch (error) {
        console.error('통계 조회 오류:', error);
        res.status(500).json({ error: error.message });
    }
});

// API: RSS 피드 (dlvr.it용) - 캐싱 적용
const FEED_CACHE_TTL_MS = parseInt(process.env.FEED_CACHE_TTL_MS || '300000', 10); // 5분
const FEED_CACHE_FILE_PATH = path.join(RECENT_CACHE_DIR, 'feed_cache.json');

function readFeedCache() {
    try {
        if (!fs.existsSync(FEED_CACHE_FILE_PATH)) {
            return {};
        }
        const raw = fs.readFileSync(FEED_CACHE_FILE_PATH, 'utf8');
        if (!raw) return {};
        return JSON.parse(raw);
    } catch (error) {
        console.error('[feed-cache] 파일 읽기 오류:', error.message);
        return {};
    }
}

function writeFeedCache(cacheObject) {
    try {
        ensureRecentCacheDir();
        fs.writeFileSync(FEED_CACHE_FILE_PATH, JSON.stringify(cacheObject, null, 2), 'utf8');
        return true;
    } catch (error) {
        console.error('[feed-cache] 파일 쓰기 오류:', error.message);
        return false;
    }
}

app.get('/feed.xml', async (req, res) => {
    try {
        const limit = parseInt(req.query.limit) || 30;
        const cacheKey = String(limit);
        const now = Date.now();
        
        // 캐시 확인
        const cacheStore = readFeedCache();
        const cached = cacheStore[cacheKey];
        
        if (cached && cached.cachedAt && (now - cached.cachedAt) < FEED_CACHE_TTL_MS) {
            if (process.env.NODE_ENV !== 'production') {
                console.log(`[feed-cache] HIT: limit=${limit}, age=${Math.round((now - cached.cachedAt) / 1000)}s`);
            }
            res.type('application/xml; charset=utf-8');
            return res.send(cached.payload);
        }
        
        // 캐시 미스 - 데이터 로드
        if (process.env.NODE_ENV !== 'production') {
            console.log(`[feed-cache] MISS: limit=${limit}, generating...`);
        }
        
        const results = await storage.getRecentCalculations(limit);
        
        // RSS 2.0 형식의 XML 생성
        const siteUrl = 'https://xn--9l4b4xi9r.com'; // 참소식.com의 실제 도메인으로 변경 필요
        const feedUrl = `${siteUrl}/feed.xml`;
        
        const buildDate = new Date().toUTCString();
        
        // 각 항목의 아이템 생성
        const items = results.map(item => {
            const pubDate = new Date(item.timestamp).toUTCString();
            const category = item.category || '일반';
            const title = item.input instanceof Array ? `[${item.input.join(', ')}]` : item.input;
            const cleanTitle = typeof title === 'string' ? title.replace(/\*/g, '') : title;
            // nbMax, nbMin 제거
            // index.html 검색 링크 형식 (nbMax, nbMin은 여전히 링크에 포함)
            const nbMax = (item.results && item.results[0] && item.results[0].nb_max) || 0;
            const nbMin = (item.results && item.results[0] && item.results[0].nb_min) || 0;
            const itemLink = `${siteUrl}/index.html?search=${encodeURIComponent(cleanTitle)}&selected_max=${nbMax}&selected_min=${nbMin}`.replace(/&/g, '&amp;');
            // nb_max, nb_min 없는 description
            const description = `
                <p><strong>카테고리:</strong> ${category}</p>
                <p><strong>키워드:</strong> ${cleanTitle}</p>
                <p><strong>유형:</strong> ${item.type === 'text' ? '텍스트' : '숫자'} | <strong>조회수:</strong> ${item.view_count || 0}</p>
                <p><strong>이슈 맵 바로가기:</strong> 중동 정세·지정학 리스크·글로벌 경제 흐름 확인</p>
            `.trim();
            return `
    <item>
        <title><![CDATA[${title}]]></title>
        <description><![CDATA[${description}]]></description>
        <link>${itemLink}</link>
        <category><![CDATA[${category}]]></category>
        <pubDate>${pubDate}</pubDate>
        <guid>${siteUrl}#${item.id || item.timestamp}</guid>
    </item>
            `.trim();
        }).join('\n');
        
        const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>참소식.com | 실시간 이슈 맵 RSS</title>
        <link>${siteUrl}</link>
        <description>중동 정세, 지정학 리스크, 원유 공급, 글로벌 경제·부동산 이슈 흐름을 실시간으로 제공하는 참소식 RSS 피드</description>
        <language>ko-kr</language>
        <lastBuildDate>${buildDate}</lastBuildDate>
        <image>
            <title>참소식.com</title>
            <url>${siteUrl}/logo.png</url>
            <link>${siteUrl}</link>
        </image>
${items}
    </channel>
</rss>`;
        
        // 캐시 저장
        cacheStore[cacheKey] = { cachedAt: now, payload: rss };
        writeFeedCache(cacheStore);
        
        res.type('application/xml; charset=utf-8');
        res.send(rss);
    } catch (error) {
        console.error('RSS 피드 생성 오류:', error);
        
        // 오류 시 stale 캐시 fallback
        const limit = parseInt(req.query.limit) || 30;
        const staleStore = readFeedCache();
        const stale = staleStore[String(limit)];
        if (stale && stale.payload) {
            console.log(`[feed-cache] FALLBACK: 캐시된 피드 사용`);
            res.type('application/xml; charset=utf-8');
            return res.send(stale.payload);
        }
        
        res.status(500).type('application/xml').send(`<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>참소식.com - 오류</title>
        <link>https://xn--9l4b4xi9r.com</link>
        <description>오류가 발생했습니다.</description>
    </channel>
</rss>`);
    }
});

// API: 조회수가 가장 많은 결과
app.get('/api/most-viewed', async (req, res) => {
    try {
        const limit = parseInt(req.query.limit) || 10;
        const results = await storage.getMostViewedCalculations(limit);
        
        return res.json({
            success: true,
            count: results.length,
            results: results
        });
    } catch (error) {
        console.error('조회수 많은 순 조회 오류:', error);
        res.status(500).json({ error: error.message });
    }
});

// XML 이스케이프 함수
function escapeXml(str) {
    if (!str) return '';
    return str.replace(/[<>&'"]/g, (char) => {
        const entities = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&apos;',
            '"': '&quot;'
        };
        return entities[char] || char;
    });
}

// API: RSS 피드 - 인기글 (dlvr.it용) - 캐싱 적용
const FEED_POPULAR_CACHE_TTL_MS = parseInt(process.env.FEED_POPULAR_CACHE_TTL_MS || '600000', 10); // 10분
const FEED_POPULAR_CACHE_FILE_PATH = path.join(RECENT_CACHE_DIR, 'feed_popular_cache.json');

function readFeedPopularCache() {
    try {
        if (!fs.existsSync(FEED_POPULAR_CACHE_FILE_PATH)) {
            return {};
        }
        const raw = fs.readFileSync(FEED_POPULAR_CACHE_FILE_PATH, 'utf8');
        if (!raw) return {};
        return JSON.parse(raw);
    } catch (error) {
        console.error('[feed-popular-cache] 파일 읽기 오류:', error.message);
        return {};
    }
}

function writeFeedPopularCache(cacheObject) {
    try {
        ensureRecentCacheDir();
        fs.writeFileSync(FEED_POPULAR_CACHE_FILE_PATH, JSON.stringify(cacheObject, null, 2), 'utf8');
        return true;
    } catch (error) {
        console.error('[feed-popular-cache] 파일 쓰기 오류:', error.message);
        return false;
    }
}

app.get('/feed-popular.xml', async (req, res) => {
    try {
        const limit = parseInt(req.query.limit) || 30;
        const cacheKey = String(limit);
        const now = Date.now();
        
        // 캐시 확인
        const cacheStore = readFeedPopularCache();
        const cached = cacheStore[cacheKey];
        
        if (cached && cached.cachedAt && (now - cached.cachedAt) < FEED_POPULAR_CACHE_TTL_MS) {
            if (process.env.NODE_ENV !== 'production') {
                console.log(`[feed-popular-cache] HIT: limit=${limit}, age=${Math.round((now - cached.cachedAt) / 1000)}s`);
            }
            res.type('application/xml; charset=utf-8');
            return res.send(cached.payload);
        }
        
        // 캐시 미스 - 데이터 로드
        if (process.env.NODE_ENV !== 'production') {
            console.log(`[feed-popular-cache] MISS: limit=${limit}, generating...`);
        }
        
        const results = await storage.getMostViewedCalculations(limit);
        
        // RSS 2.0 형식의 XML 생성
        const siteUrl = 'https://xn--9l4b4xi9r.com'; // 참소식.com의 실제 도메인으로 변경 필요
        const feedUrl = `${siteUrl}/feed-popular.xml`;
        
        const buildDate = new Date().toUTCString();
        
        // 각 항목의 아이템 생성
        const items = results.map(item => {
            const pubDate = new Date(item.timestamp).toUTCString();
            const category = item.category || '일반';
            const title = item.input instanceof Array ? `[${item.input.join(', ')}]` : item.input;
            const cleanTitle = typeof title === 'string' ? title.replace(/\*/g, '') : title;
            // nbMax, nbMin 제거
            // index.html 검색 링크 형식 (nbMax, nbMin은 여전히 링크에 포함)
            const nbMax = (item.results && item.results[0] && item.results[0].nb_max) || 0;
            const nbMin = (item.results && item.results[0] && item.results[0].nb_min) || 0;
            const itemLink = `${siteUrl}/index.html?search=${encodeURIComponent(cleanTitle)}&selected_max=${nbMax}&selected_min=${nbMin}`.replace(/&/g, '&amp;');
            // nb_max, nb_min 없는 description
            const description = `
                <p><strong>카테고리:</strong> ${category}</p>
                <p><strong>키워드:</strong> ${cleanTitle}</p>
                <p><strong>유형:</strong> ${item.type === 'text' ? '텍스트' : '숫자'} | <strong>조회수:</strong> ${item.view_count || 0}</p>
                <p><strong>인기 이슈 맵 바로가기:</strong> 지정학 리스크·경제 영향 트렌드 확인</p>
            `.trim();
            return `
    <item>
        <title><![CDATA[${title}]]></title>
        <description><![CDATA[${description}]]></description>
        <link>${itemLink}</link>
        <category><![CDATA[${category}]]></category>
        <pubDate>${pubDate}</pubDate>
        <guid>${siteUrl}#${item.id || item.timestamp}</guid>
    </item>
            `.trim();
        }).join('\n');
        
        const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>참소식.com | 인기 이슈 RSS</title>
        <link>${siteUrl}</link>
        <description>조회수 높은 핵심 이슈를 빠르게 모아보는 참소식 인기 RSS 피드</description>
        <language>ko-kr</language>
        <lastBuildDate>${buildDate}</lastBuildDate>
        <image>
            <title>참소식.com</title>
            <url>${siteUrl}/logo.png</url>
            <link>${siteUrl}</link>
        </image>
${items}
    </channel>
</rss>`;
        
        // 캐시 저장
        cacheStore[cacheKey] = { cachedAt: now, payload: rss };
        writeFeedPopularCache(cacheStore);
        
        res.type('application/xml; charset=utf-8');
        res.send(rss);
    } catch (error) {
        console.error('인기글 RSS 피드 생성 오류:', error);
        
        // 오류 시 stale 캐시 fallback
        const limit = parseInt(req.query.limit) || 30;
        const staleStore = readFeedPopularCache();
        const stale = staleStore[String(limit)];
        if (stale && stale.payload) {
            console.log(`[feed-popular-cache] FALLBACK: 캐시된 피드 사용`);
            res.type('application/xml; charset=utf-8');
            return res.send(stale.payload);
        }
        
        res.status(500).type('application/xml').send(`<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>참소식.com - 오류</title>
        <link>https://xn--9l4b4xi9r.com</link>
        <description>오류가 발생했습니다.</description>
    </channel>
</rss>`);
    }
});

// API: Sitemap (SEO)
app.get('/sitemap.xml', async (req, res) => {
    try {
        const siteUrl = 'https://xn--9l4b4xi9r.com';
        const lastMod = new Date().toISOString().split('T')[0];
        
        let urls = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>${siteUrl}/</loc>
        <lastmod>${lastMod}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>${siteUrl}/index.html</loc>
        <lastmod>${lastMod}</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.9</priority>
    </url>
    <url>
        <loc>${siteUrl}/feed.xml</loc>
        <lastmod>${lastMod}</lastmod>
        <changefreq>hourly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>${siteUrl}/feed-popular.xml</loc>
        <lastmod>${lastMod}</lastmod>
        <changefreq>hourly</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>`;
        
        res.type('application/xml; charset=utf-8');
        res.send(urls);
    } catch (error) {
        console.error('Sitemap 생성 오류:', error);
        res.status(500).send('오류가 발생했습니다.');
    }
});

// API: robots.txt
app.get('/api/track-keyword', (req, res) => {
    const keyword = normalizeKeyword(req.query.keyword || '');
    if (!keyword) {
        return res.json({ success: false, message: 'keyword required' });
    }
    return res.json({ success: true });
});

// API: 트렌드 기반 AI 콘텐츠 생성 (Ollama)
app.post('/api/trend-ai', async (req, res) => {
    try {
        const limit = Math.min(parseInt(req.body.limit, 10) || 5, 20);
        const model = req.body.model || DEFAULT_MODEL;
        const keywords = loadTrendKeywords(limit);

        if (keywords.length === 0) {
            return res.status(404).json({
                success: false,
                error: '트렌드 키워드를 찾을 수 없습니다.'
            });
        }

        const results = [];
        for (const keyword of keywords) {
            const naverUrl = `https://search.naver.com/search.naver?query=${encodeURIComponent(keyword)}`;
            const youtubeUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(keyword)}`;

            const questionPrompt = `키워드: ${keyword}\n요구사항: 한국어 질문형 한 문장만 출력.`;
            let question = '';
            try {
                question = await callOllama(questionPrompt, model);
            } catch (error) {
                question = `${keyword}에 대해 알고 싶어요.`;
            }

            const [naverInfo, youtubeInfo] = await Promise.all([
                fetchPageText(naverUrl),
                fetchPageText(youtubeUrl)
            ]);

            const contentPrompt = [
                '다음 정보를 참고해 한국어로 JSON만 출력해줘.',
                '필드: title, summary, body',
                `키워드: ${keyword}`,
                `질문: ${question}`,
                `네이버 텍스트: ${naverInfo.title} ${naverInfo.description} ${naverInfo.text}`,
                `유튜브 텍스트: ${youtubeInfo.title} ${youtubeInfo.description} ${youtubeInfo.text}`,
                '제목은 40자 이내, summary는 2문장, body는 3~5문장으로 작성.'
            ].join('\n');

            let generated = { title: '', summary: '', body: '' };
            try {
                const response = await callOllama(contentPrompt, model);
                const parsed = safeJsonParse(response);
                if (parsed && parsed.title && parsed.summary && parsed.body) {
                    generated = parsed;
                } else {
                    generated = {
                        title: `${keyword} 관련 요약`,
                        summary: response.slice(0, 220),
                        body: response
                    };
                }
            } catch (error) {
                generated = {
                    title: `${keyword} 관련 요약`,
                    summary: '요약 생성에 실패했습니다.',
                    body: '본문 생성에 실패했습니다.'
                };
            }

            results.push({
                keyword,
                question,
                search: {
                    naver: naverUrl,
                    youtube: youtubeUrl
                },
                source_text: {
                    naver: naverInfo,
                    youtube: youtubeInfo
                },
                generated
            });
        }

        return res.json({
            success: true,
            model,
            count: results.length,
            results
        });
    } catch (error) {
        console.error('트렌드 AI 오류:', error);
        res.status(500).json({ error: error.message });
    }
});

// API: 단일 조회 (계산 ID로 조회)
app.get('/api/calculation/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const result = await storage.loadCalculation(id);
        
        if (result) {
            return res.json({
                success: true,
                result: result
            });
        } else {
            return res.status(404).json({
                success: false,
                error: '계산 결과를 찾을 수 없습니다.'
            });
        }
    } catch (error) {
        console.error('단일 조회 오류:', error);
        res.status(500).json({ error: error.message });
    }
});

// API: 리스트 조회 (페이징)
app.get('/api/calculations', async (req, res) => {
    try {
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 20;
        const results = await storage.getRecentCalculations(limit);
        
        return res.json({
            success: true,
            page: page,
            limit: limit,
            count: results.length,
            results: results
        });
    } catch (error) {
        console.error('리스트 조회 오류:', error);
        res.status(500).json({ error: error.message });
    }
});

// 헬스 체크
app.get('/api/health', (req, res) => {
    res.json({ status: 'OK', message: 'N/B 계산 서버 정상 작동 중' });
});

app.get('/api/coupang-products', async (req, res) => {
    try {
        if (!COUPANG_ACCESS_KEY || !COUPANG_SECRET_KEY) {
            return res.status(503).json({
                success: false,
                error: 'Coupang Partners API keys are not configured.'
            });
        }

        const keywords = normalizeCoupangKeywords(req.query.keywords || req.query.keyword);
        const limit = Math.min(Math.max(parseInt(req.query.limit, 10) || 4, 1), 8);
        if (!keywords.length) {
            return res.status(400).json({ success: false, error: 'keyword is required.' });
        }

        const cacheKey = `${keywords.join('|')}:${limit}`;
        const cached = coupangProductsCache.get(cacheKey);
        const now = Date.now();
        if (cached && now - cached.cachedAt < COUPANG_CACHE_TTL_MS) {
            return res.json({ ...cached.payload, cached: true });
        }

        let keyword = keywords[0];
        let products = [];
        let lastApiError = null;

        for (const candidate of keywords) {
            try {
                const candidateProducts = await fetchCoupangProductsByKeyword(candidate, limit);
                if (candidateProducts.length) {
                    keyword = candidate;
                    products = candidateProducts;
                    break;
                }
            } catch (error) {
                lastApiError = error;
                console.error('[coupang-products] API error:', error.status, error.payload || error.message);
            }
        }

        if (!products.length && lastApiError) {
            return res.status(lastApiError.status || 502).json({
                success: false,
                error: 'Coupang Partners API request failed.',
                coupangStatus: lastApiError.status || null,
                coupangMessage: lastApiError.payload?.message || lastApiError.payload?.raw || null,
                transactionId: lastApiError.payload?.transactionId || null,
                keywords
            });
        }

        const result = {
            success: true,
            keyword,
            keywords,
            products,
            disclosure: '이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.',
            cached: false
        };

        coupangProductsCache.set(cacheKey, {
            cachedAt: now,
            payload: result
        });

        return res.json(result);
    } catch (error) {
        console.error('[coupang-products] error:', error.message);
        return res.status(500).json({
            success: false,
            error: 'Failed to load Coupang products.'
        });
    }
});

app.options(['/api/radio-state', '/api/radio-state/'], (req, res) => {
    res.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    res.sendStatus(204);
});

app.get(['/api/radio-state', '/api/radio-state/'], (req, res) => {
    try {
        return res.json({
            success: true,
            state: publicRadioState(readRadioState())
        });
    } catch (error) {
        console.error('[radio-state] get error:', error);
        return res.status(500).json({ success: false, error: error.message });
    }
});

app.post(['/api/radio-state', '/api/radio-state/'], (req, res) => {
    try {
        const previous = readRadioState();
        const body = req.body || {};
        const now = Date.now();
        const status = body.status === 'playing' ? 'playing' : 'paused';
        const positionMs = Math.max(0, Math.floor(Number(body.positionMs || 0)));
        const nextState = {
            ...previous,
            stationUrl: String(body.stationUrl || previous.stationUrl || '').slice(0, 500),
            trackIndex: Math.max(0, Math.floor(Number(body.trackIndex ?? previous.trackIndex ?? 0))),
            trackId: body.trackId ?? previous.trackId ?? null,
            trackTitle: String(body.trackTitle || previous.trackTitle || '').slice(0, 300),
            artist: String(body.artist || previous.artist || '').slice(0, 200),
            status,
            positionMs,
            startedAt: status === 'playing' ? now - positionMs : now,
            updatedAt: now,
            version: Math.max(1, Number(previous.version || 1) + 1),
            source: String(body.source || 'browser').slice(0, 80)
        };

        writeRadioState(nextState);
        return res.json({
            success: true,
            state: publicRadioState(nextState)
        });
    } catch (error) {
        console.error('[radio-state] post error:', error);
        return res.status(500).json({ success: false, error: error.message });
    }
});

// ===== 방문 통계 API =====

// 시간대별 방문 통계
app.get('/api/visits/hourly', async (req, res) => {
    try {
        const hourly = await storage.getVisitsByHour();
        return res.json({
            success: true,
            data: hourly
        });
    } catch (error) {
        console.error('시간대별 방문 조회 오류:', error);
        res.status(500).json({ error: error.message });
    }
});

// 지역별 방문 통계
app.get('/api/visits/region', async (req, res) => {
    try {
        const regions = await storage.getVisitsByRegion();
        return res.json({
            success: true,
            data: regions
        });
    } catch (error) {
        console.error('지역별 방문 조회 오류:', error);
        res.status(500).json({ error: error.message });
    }
});

// 일별 방문 통계
app.get('/api/visits/daily', async (req, res) => {
    try {
        const days = parseInt(req.query.days) || 30;
        const daily = await storage.getVisitsByDay(days);
        return res.json({
            success: true,
            data: daily
        });
    } catch (error) {
        console.error('일별 방문 조회 오류:', error);
        res.status(500).json({ error: error.message });
    }
});

// 방문자 요약 통계
app.get('/api/visits/summary', async (req, res) => {
    try {
        const todayVisits = await storage.getTodayVisits();
        const totalVisits = await storage.getTotalVisits();
        return res.json({
            success: true,
            data: {
                today: todayVisits,
                total: totalVisits
            }
        });
    } catch (error) {
        console.error('방문자 요약 조회 오류:', error);
        res.status(500).json({ error: error.message });
    }
});

// ===== 키워드 통계 API =====

// 전체 인기 키워드
app.get('/api/keywords/top', async (req, res) => {
    try {
        const limit = Math.min(parseInt(req.query.limit) || 20, 100);
        // 캐시 확인
        const cache = readKeywordsCache();
        const now = Date.now();
        // 캐시가 유효한 경우 (5분 이내)
        if (cache && cache.timestamp && (now - cache.timestamp) < KEYWORDS_CACHE_TTL_MS) {
            if (process.env.NODE_ENV !== 'production') {
                console.log('[keywords-cache] 캐시에서 반환 (유효기간: ' + Math.floor((KEYWORDS_CACHE_TTL_MS - (now - cache.timestamp)) / 1000) + '초 남음)');
            }
            return res.json({
                success: true,
                count: cache.data.slice(0, limit).length,
                data: cache.data.slice(0, limit),
                cached: true,
                cacheAge: Math.floor((now - cache.timestamp) / 1000)
            });
        }
        // 캐시 만료 또는 없음 - DB에서 조회
        if (process.env.NODE_ENV !== 'production') {
            console.log('[keywords-cache] 캐시 만료 또는 없음, DB 조회 후 캐시 갱신');
        }
        const keywords = await storage.getTopKeywords(100); // 최대 100개 캐시
        // 캐시 저장
        writeKeywordsCache(keywords);
        return res.json({
            success: true,
            count: keywords.slice(0, limit).length,
            data: keywords.slice(0, limit),
            cached: false
        });
    } catch (error) {
        console.error('인기 키워드 조회 오류:', error);
        res.status(500).json({ error: error.message });
    }
});

// 지역별 인기 키워드
app.get('/api/keywords/by-region', async (req, res) => {
    try {
        const limit = Math.min(parseInt(req.query.limit) || 10, 50);
        const keywords = await storage.getKeywordsByRegion(limit);
        return res.json({
            success: true,
            data: keywords
        });
    } catch (error) {
        console.error('지역별 키워드 조회 오류:', error);
        res.status(500).json({ error: error.message });
    }
});

// 1주일 인기 키워드
app.get('/api/keywords/weekly', async (req, res) => {
    try {
        if (process.env.NODE_ENV !== 'production') {
            console.log('[API] /api/keywords/weekly 요청 시작');
        }
        const limit = Math.min(parseInt(req.query.limit) || 20, 100);
        
        if (!storage.getKeywordsByPeriod) {
            console.error('[API] storage.getKeywordsByPeriod 함수가 없습니다!');
            return res.status(500).json({ 
                success: false, 
                error: 'getKeywordsByPeriod function not available' 
            });
        }
        
        const keywords = await storage.getKeywordsByPeriod('week', limit);
        if (process.env.NODE_ENV !== 'production') {
            console.log(`[API] 1주일 키워드 ${keywords.length}개 반환`);
        }
        
        return res.json({
            success: true,
            count: keywords.length,
            data: keywords
        });
    } catch (error) {
        console.error('[API] 1주일 키워드 조회 오류:', error);
        console.error(error.stack);
        res.status(500).json({ 
            success: false, 
            error: error.message,
            stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
        });
    }
});

// 오늘 인기 키워드
app.get('/api/keywords/today', async (req, res) => {
    try {
        if (process.env.NODE_ENV !== 'production') {
            console.log('[API] /api/keywords/today 요청 시작');
        }
        const limit = Math.min(parseInt(req.query.limit) || 20, 100);
        
        if (!storage.getKeywordsByPeriod) {
            console.error('[API] storage.getKeywordsByPeriod 함수가 없습니다!');
            return res.status(500).json({ 
                success: false, 
                error: 'getKeywordsByPeriod function not available' 
            });
        }
        
        const keywords = await storage.getKeywordsByPeriod('today', limit);
        if (process.env.NODE_ENV !== 'production') {
            console.log(`[API] 오늘 키워드 ${keywords.length}개 반환`);
        }
        
        return res.json({
            success: true,
            count: keywords.length,
            data: keywords
        });
    } catch (error) {
        console.error('[API] 오늘 키워드 조회 오류:', error);
        console.error(error.stack);
        res.status(500).json({ 
            success: false, 
            error: error.message,
            stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
        });
    }
});

// 서버 시작
const server = app.listen(PORT, () => {
    console.log(`
╔════════════════════════════════════════════════════════════════════╗
║           N/B MAX, N/B MIN 계산 웹서버                           ║
║           서버 시작됨                                            ║
╚════════════════════════════════════════════════════════════════════╝

🌐 서버가 실행 중입니다:
   URL: http://localhost:${PORT}
   
📊 API 엔드포인트:
   POST /api/calculate         - N/B 계산 및 저장
   POST /api/search            - 검색 (텍스트/Unicode)
   GET  /api/recent            - 최근 계산 결과 (날짜순)
   GET  /api/most-viewed       - 조회수 많은 순 (NEW)
    POST /api/trend-ai          - 트렌드 AI 콘텐츠 생성 (Ollama)
   GET  /api/stats             - 통계 정보
   GET  /api/calculation/:id   - 단일 조회 (ID)
   GET  /api/calculations      - 리스트 조회 (페이징)
   GET  /api/health            - 헬스 체크
   GET  /api/coupang-products      - 쿠팡 상품 검색

💡 종료: Ctrl+C
    `);
});
