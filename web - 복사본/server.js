const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');
const fs = require('fs');
const { calculateNB } = require('./calculate');
const storage = require('./storage');

const app = express();
const PORT = process.env.PORT || 3000;
const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
const TREND_DATA_PATH = path.join(__dirname, '..', 'data', 'naver_creator_trends', 'latest_trend_data.json');
const DEFAULT_MODEL = process.env.OLLAMA_MODEL || 'llama3';

// 스토리지 초기화
storage.initStorage();

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
app.use(express.static(path.join(__dirname, 'public', '한국인터넷.한국')));

// 방문 기록 미들웨어
app.use((req, res, next) => {
    const ip = req.headers['x-forwarded-for'] || req.connection.remoteAddress || 'unknown';
    const userAgent = req.headers['user-agent'] || 'unknown';
    const rawKeyword = req.query.keyword || req.query.nb || req.body.input || null;
    const keyword = normalizeKeyword(rawKeyword);
    
    storage.recordVisit(ip, req.path, userAgent, keyword);
    next();
});

// 설정 로드
const config = {
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

// 홈페이지
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', '한국인터넷.한국', 'index.html'));
});

// API: 계산 요청
app.post('/api/calculate', async (req, res) => {
    try {
        const { input, bit = config.bitDefaultValue, category = 'general' } = req.body;
        
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
                nb_max: parseFloat(maxResult.toFixed(config.decimalPlaces)),
                nb_min: parseFloat(minResult.toFixed(config.decimalPlaces)),
                difference: parseFloat((maxResult - minResult).toFixed(config.decimalPlaces))
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
            for (let i = 0; i < config.calculationCountForText; i++) {
                const maxResult = calculateNB(unicodeArray, bit, false);
                const minResult = calculateNB(unicodeArray, bit, true);
                
                results.push({
                    calculation: i + 1,
                    nb_max: parseFloat(maxResult.toFixed(config.decimalPlaces)),
                    nb_min: parseFloat(minResult.toFixed(config.decimalPlaces)),
                    difference: parseFloat((maxResult - minResult).toFixed(config.decimalPlaces))
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
app.post('/api/search', async (req, res) => {
    try {
        const { text, unicode } = req.body;
        
        let results = [];
        
        if (unicode && Array.isArray(unicode)) {
            // Unicode 배열로 검색
            results = await storage.searchByUnicode(unicode);
        } else if (text) {
            // 텍스트로 검색
            results = await storage.searchByText(text);
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
        const results = await storage.getRecentCalculations(limit);
        
        return res.json({
            success: true,
            count: results.length,
            results: results
        });
    } catch (error) {
        console.error('최근 결과 조회 오류:', error);
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

// API: 키워드 클릭 추적
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

// ===== 키워드 통계 API =====

// 전체 인기 키워드
app.get('/api/keywords/top', async (req, res) => {
    try {
        const limit = Math.min(parseInt(req.query.limit) || 20, 100);
        const keywords = await storage.getTopKeywords(limit);
        return res.json({
            success: true,
            count: keywords.length,
            data: keywords
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

// 서버 시작
app.listen(PORT, () => {
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

💡 종료: Ctrl+C
    `);
});
