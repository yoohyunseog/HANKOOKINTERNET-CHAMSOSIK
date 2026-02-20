/**
 * N/B 계산 결과 파일 기반 데이터베이스
 * 계층형 디렉터리 구조: data/nb_max/5/9/6/8/result_{id}.json
 */

const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');
const geoip = require('geoip-lite');

const DATA_DIR = path.join(__dirname, '..', 'data');
const NB_MAX_DIR = path.join(DATA_DIR, 'nb_max');
const NB_MIN_DIR = path.join(DATA_DIR, 'nb_min');
const INDEX_FILE = path.join(DATA_DIR, 'index.json');
const VISITS_FILE = path.join(DATA_DIR, 'visits.json');

// 초기화
async function initStorage() {
    try {
        await fs.mkdir(DATA_DIR, { recursive: true });
        await fs.mkdir(NB_MAX_DIR, { recursive: true });
        await fs.mkdir(NB_MIN_DIR, { recursive: true });
        
        // 인덱스 파일이 없으면 생성
        try {
            await fs.access(INDEX_FILE);
        } catch {
            await fs.writeFile(INDEX_FILE, JSON.stringify({
                total_calculations: 0,
                total_max_results: 0,
                total_min_results: 0,
                unicode_index: {},
                text_index: {}
            }, null, 2));
        }

        // 방문 로그 파일 초기화 (기존 데이터 보존)
        try {
            await fs.access(VISITS_FILE);
            // 파일이 이미 존재하면 그대로 둠
            console.log('[INFO] visits.json already exists, data preserved');
        } catch {
            // 파일이 없으면만 생성
            await fs.writeFile(VISITS_FILE, JSON.stringify([], null, 2));
            console.log('[INFO] visits.json created');
        }
    } catch (error) {
        console.error('Storage initialization error:', error);
    }
}

// 숫자를 디렉터리 경로로 변환 (5968 -> 5/9/6/8)
function numberToPath(num) {
    const numStr = num.toString().replace('.', '').replace('-', '_');
    const digits = numStr.split('').slice(0, 4); // 최대 4자리
    return digits.join('/');
}

// 계산 결과 저장
async function saveCalculation(data) {
    try {
        const calculationId = crypto.randomBytes(8).toString('hex');
        const timestamp = new Date().toISOString();
        
        const calculation = {
            id: calculationId,
            timestamp: timestamp,
            type: data.type,
            input: data.input,
            unicode: data.unicode || null,
            bit: data.bit,
            category: data.category || 'general',
            view_count: 0,
            results: data.results || [{
                nb_max: data.nb_max,
                nb_min: data.nb_min,
                difference: data.difference || (data.nb_max - data.nb_min)
            }]
        };

        // MAX 결과 저장
        const maxValue = Array.isArray(data.results) ? data.results[0].nb_max : data.nb_max;
        const maxPath = numberToPath(Math.floor(maxValue));
        const maxDir = path.join(NB_MAX_DIR, maxPath);
        await fs.mkdir(maxDir, { recursive: true });
        
        const maxFile = path.join(maxDir, `result_${calculationId}.json`);
        await fs.writeFile(maxFile, JSON.stringify(calculation, null, 2));

        // MIN 결과 저장
        const minValue = Array.isArray(data.results) ? data.results[0].nb_min : data.nb_min;
        const minPath = numberToPath(Math.floor(minValue));
        const minDir = path.join(NB_MIN_DIR, minPath);
        await fs.mkdir(minDir, { recursive: true });
        
        const minFile = path.join(minDir, `result_${calculationId}.json`);
        await fs.writeFile(minFile, JSON.stringify(calculation, null, 2));

        // 인덱스 업데이트
        await updateIndex(calculation);

        return { success: true, id: calculationId, timestamp: timestamp, calculation: calculation };
    } catch (error) {
        console.error('Save calculation error:', error);
        return { success: false, error: error.message };
    }
}

// 인덱스 업데이트
async function updateIndex(calculation) {
    try {
        const indexData = await readIndex();
        
        indexData.total_calculations++;
        indexData.total_max_results++;
        indexData.total_min_results++;

        // Unicode 배열로 인덱싱
        if (calculation.unicode && Array.isArray(calculation.unicode)) {
            const unicodeKey = calculation.unicode.join(',');
            if (!indexData.unicode_index[unicodeKey]) {
                indexData.unicode_index[unicodeKey] = [];
            }
            indexData.unicode_index[unicodeKey].push({
                id: calculation.id,
                timestamp: calculation.timestamp,
                input: calculation.input
            });
        }

        // 텍스트로 인덱싱 (검색용)
        if (calculation.type === 'text' && calculation.input) {
            const textKey = calculation.input.toLowerCase();
            if (!indexData.text_index[textKey]) {
                indexData.text_index[textKey] = [];
            }
            indexData.text_index[textKey].push({
                id: calculation.id,
                timestamp: calculation.timestamp
            });
        }

        await fs.writeFile(INDEX_FILE, JSON.stringify(indexData, null, 2));
    } catch (error) {
        console.error('Update index error:', error);
    }
}

// 인덱스 읽기
async function readIndex() {
    try {
        const content = await fs.readFile(INDEX_FILE, 'utf-8');
        return JSON.parse(content);
    } catch {
        return {
            total_calculations: 0,
            total_max_results: 0,
            total_min_results: 0,
            unicode_index: {},
            text_index: {}
        };
    }
}

// Unicode 배열로 검색
async function searchByUnicode(unicodeArray) {
    try {
        const indexData = await readIndex();
        const unicodeKey = unicodeArray.join(',');
        
        const matches = indexData.unicode_index[unicodeKey] || [];
        
        // 각 매치에 대한 상세 정보 로드
        const results = [];
        for (const match of matches.slice(0, 10)) { // 최대 10개
            const result = await loadCalculation(match.id, false);
            if (result) {
                results.push(result);
            }
        }
        
        return results;
    } catch (error) {
        console.error('Search by unicode error:', error);
        return [];
    }
}

// 텍스트로 검색
async function searchByText(text, limit = 10, incrementView = false) {
    try {
        const indexData = await readIndex();
        const textKey = text.toLowerCase();
        
        const matches = indexData.text_index[textKey] || [];
        
        // 각 매치에 대한 상세 정보 로드
        const results = [];
        const maxResults = Math.min(limit, matches.length);
        for (const match of matches.slice(0, maxResults)) {
            const result = await loadCalculation(match.id, incrementView);
            if (result) {
                results.push(result);
            }
        }
        
        return results;
    } catch (error) {
        console.error('Search by text error:', error);
        return [];
    }
}

// ID로 계산 결과 로드
async function loadCalculation(id, incrementView = true) {
    try {
        // MAX 디렉터리에서 검색
        const maxResults = await findFileById(NB_MAX_DIR, id);
        if (maxResults.length > 0) {
            const content = await fs.readFile(maxResults[0], 'utf-8');
            const calculation = JSON.parse(content);
            
            // 조회수 증가
            if (incrementView) {
                calculation.view_count = (calculation.view_count || 0) + 1;
                calculation.last_viewed = new Date().toISOString();
                
                // 파일 업데이트
                await updateCalculationFiles(calculation);
            }
            
            return calculation;
        }
        
        return null;
    } catch (error) {
        console.error('Load calculation error:', error);
        return null;
    }
}

// 재귀적으로 파일 찾기
async function findFileById(dir, id, results = []) {
    try {
        const entries = await fs.readdir(dir, { withFileTypes: true });
        
        for (const entry of entries) {
            const fullPath = path.join(dir, entry.name);
            
            if (entry.isDirectory()) {
                await findFileById(fullPath, id, results);
            } else if (entry.isFile() && entry.name.includes(id)) {
                results.push(fullPath);
            }
        }
        
        return results;
    } catch {
        return results;
    }
}

// 모든 계산 결과 파일 찾기
async function getAllCalculationFiles() {
    const results = [];
    
    async function scanDirectory(dir) {
        try {
            const entries = await fs.readdir(dir, { withFileTypes: true });
            
            for (const entry of entries) {
                const fullPath = path.join(dir, entry.name);
                
                if (entry.isDirectory()) {
                    await scanDirectory(fullPath);
                } else if (entry.isFile() && entry.name.startsWith('result_')) {
                    results.push(fullPath);
                }
            }
        } catch (error) {
            // 디렉토리 접근 오류 무시
        }
    }
    
    await scanDirectory(NB_MAX_DIR);
    return results;
}

// 최근 계산 결과 가져오기
async function getRecentCalculations(limit = 10) {
    try {
        const files = await getAllCalculationFiles();
        if (files.length === 0) {
            return [];
        }

        const fileStats = await Promise.all(
            files.map(async (filePath) => {
                try {
                    const stat = await fs.stat(filePath);
                    return { filePath, ctimeMs: stat.ctimeMs };
                } catch {
                    return null;
                }
            })
        );

        const recentFiles = fileStats
            .filter(Boolean)
            .sort((a, b) => b.ctimeMs - a.ctimeMs)
            .slice(0, limit);

        const results = [];
        for (const item of recentFiles) {
            try {
                const content = await fs.readFile(item.filePath, 'utf-8');
                const calculation = JSON.parse(content);
                results.push(calculation);
            } catch {
                // 파일 읽기 오류 무시
            }
        }

        return results;
    } catch (error) {
        console.error('Get recent calculations error:', error);
        return [];
    }
}

// 조회수가 가장 많은 계산 결과 가져오기
async function getMostViewedCalculations(limit = 10) {
    try {
        // 모든 파일 찾기
        const files = await getAllCalculationFiles();
        const calculations = [];
        
        // 각 파일 로드 (조회수 증가하지 않음)
        for (const filePath of files) {
            try {
                const content = await fs.readFile(filePath, 'utf-8');
                const calculation = JSON.parse(content);
                calculations.push(calculation);
            } catch (error) {
                // 파일 읽기 오류 무시
            }
        }
        
        // 조회수 기준 내림차순 정렬
        calculations.sort((a, b) => {
            const viewsA = a.view_count || 0;
            const viewsB = b.view_count || 0;
            return viewsB - viewsA;
        });
        
        // 최대 limit개 반환
        return calculations.slice(0, limit);
    } catch (error) {
        console.error('Get most viewed calculations error:', error);
        return [];
    }
}

// 계산 결과 파일 업데이트
async function updateCalculationFiles(calculation) {
    try {
        const maxValue = calculation.results[0].nb_max;
        const minValue = calculation.results[0].nb_min;
        
        const maxPath = numberToPath(Math.floor(maxValue));
        const minPath = numberToPath(Math.floor(minValue));
        
        const maxFile = path.join(NB_MAX_DIR, maxPath, `result_${calculation.id}.json`);
        const minFile = path.join(NB_MIN_DIR, minPath, `result_${calculation.id}.json`);
        
        const content = JSON.stringify(calculation, null, 2);
        
        await fs.writeFile(maxFile, content);
        await fs.writeFile(minFile, content);
        
        return true;
    } catch (error) {
        console.error('Update calculation files error:', error);
        return false;
    }
}

// 통계 가져오기
async function getStatistics() {
    try {
        const indexData = await readIndex();
        return {
            total_calculations: indexData.total_calculations,
            total_max_results: indexData.total_max_results,
            total_min_results: indexData.total_min_results
        };
    } catch (error) {
        console.error('Get statistics error:', error);
        return {
            total_calculations: 0,
            total_max_results: 0,
            total_min_results: 0
        };
    }
}

module.exports = {
    initStorage,
    saveCalculation,
    searchByUnicode,
    searchByText,
    loadCalculation,
    getRecentCalculations,
    getMostViewedCalculations,
    getStatistics,
    recordVisit,
    getVisitsByHour,
    getVisitsByRegion,
    getTopKeywords,
    getKeywordsByRegion
};

// ===== 방문 통계 함수 =====

// 방문 기록 저장
async function recordVisit(ip, path, userAgent, keyword = null) {
    try {
        let visits = [];
        try {
            const content = await fs.readFile(VISITS_FILE, 'utf-8');
            visits = JSON.parse(content);
        } catch (err) {
            console.log('[DEBUG] visits.json 초기 생성:', VISITS_FILE);
            visits = [];
        }

        const geo = geoip.lookup(ip);
        const country = geo ? (geo.country === 'KR' ? '한국' : geo.country) : '미분류';

        const visit = {
            ip: ip || 'unknown',
            path: path || '/',
            country: country,
            timestamp: new Date().toISOString(),
            userAgent: userAgent || 'unknown',
            keyword: keyword
        };

        visits.push(visit);
        console.log('[DEBUG] Visit recorded:', country, keyword, 'Total visits:', visits.length);
        
        // 최근 10000개만 유지
        if (visits.length > 10000) {
            visits = visits.slice(-10000);
        }

        await fs.writeFile(VISITS_FILE, JSON.stringify(visits, null, 2));
    } catch (error) {
        console.error('Record visit error:', error);
    }
}

// 시간대별 방문 통계
async function getVisitsByHour() {
    try {
        const content = await fs.readFile(VISITS_FILE, 'utf-8');
        const visits = JSON.parse(content);
        
        const hourly = {};
        visits.forEach(visit => {
            const date = new Date(visit.timestamp);
            const hour = `${date.getHours()}:00`;
            hourly[hour] = (hourly[hour] || 0) + 1;
        });

        return Object.keys(hourly)
            .sort()
            .map(hour => ({ hour, count: hourly[hour] }));
    } catch (error) {
        console.error('Get visits by hour error:', error);
        return [];
    }
}

// 지역별 방문 통계
async function getVisitsByRegion() {
    try {
        console.log('[DEBUG] VISITS_FILE path:', VISITS_FILE);
        const content = await fs.readFile(VISITS_FILE, 'utf-8');
        const visits = JSON.parse(content);
        console.log('[DEBUG] Total visits loaded:', visits.length);
        
        const regions = {};
        visits.forEach(visit => {
            const country = visit.country || 'unknown';
            regions[country] = (regions[country] || 0) + 1;
        });

        const result = Object.entries(regions)
            .map(([region, count]) => ({ region, count }))
            .sort((a, b) => b.count - a.count);
        
        console.log('[DEBUG] Region stats:', result);
        
        return result;
    } catch (error) {
        console.error('Get visits by region error:', error);
        return [];
    }
}

// 인기 키워드
async function getTopKeywords(limit = 20) {
    try {
        const files = await getAllCalculationFiles();
        const keywords = {};

        for (const filePath of files) {
            try {
                const content = await fs.readFile(filePath, 'utf-8');
                const calculation = JSON.parse(content);
                if (calculation.input) {
                    keywords[calculation.input] = (keywords[calculation.input] || 0) + (calculation.view_count || 0);
                }
            } catch {
                // 파일 읽기 오류 무시
            }
        }

        return Object.entries(keywords)
            .map(([keyword, count]) => ({ keyword, count }))
            .sort((a, b) => b.count - a.count)
            .slice(0, limit);
    } catch (error) {
        console.error('Get top keywords error:', error);
        return [];
    }
}

// 지역별 인기 키워드
async function getKeywordsByRegion(limit = 10) {
    try {
        const content = await fs.readFile(VISITS_FILE, 'utf-8');
        const visits = JSON.parse(content);
        
        const regionKeywords = {};
        
        visits.forEach(visit => {
            if (visit.keyword) {
                const region = visit.country || 'unknown';
                if (!regionKeywords[region]) {
                    regionKeywords[region] = {};
                }
                regionKeywords[region][visit.keyword] = (regionKeywords[region][visit.keyword] || 0) + 1;
            }
        });

        const result = {};
        Object.keys(regionKeywords).forEach(region => {
            result[region] = Object.entries(regionKeywords[region])
                .map(([keyword, count]) => ({ keyword, count }))
                .sort((a, b) => b.count - a.count)
                .slice(0, limit);
        });

        return result;
    } catch (error) {
        console.error('Get keywords by region error:', error);
        return {};
    }
}
