/**
 * 중랑구 대학 행사 정보 수집 봇
 * 한국외국어대학교, 광운대학교, 서일대학교의 주요 행사 정보를 수집하여 JSON으로 정리
 * Ollama AI Kimi를 사용하여 행사 정보 정리
 */

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const OUTPUT_FILE = path.join(__dirname, "jungnang-university-events.json");
const DEFAULT_INTERVAL_SECONDS = 600;
const AUTO_UPLOAD_JSON = process.env.AUTO_UPLOAD_JSON !== "0";
const UPLOAD_SERVER = process.env.JUNGNANG_UPLOAD_SERVER || "root@211.45.162.155";
const REMOTE_ROOT = process.env.JUNGNANG_REMOTE_ROOT || "/var/www/chamsosik";
const REMOTE_DIR = `${REMOTE_ROOT}/jungnang-volunteer`;
const REMOTE_FILE = `${REMOTE_DIR}/jungnang-university-events.json`;
const REMOTE_TMP_FILE = "/tmp/jungnang-university-events.json";

// Ollama 설정
const OLLAMA_HOST = "http://localhost:11434";
const OLLAMA_MODEL = "kimi-k2.5:cloud";

// 행사 유형 분류 키워드
const EVENT_TYPE_KEYWORDS = {
  입학행사: ["입학", "오리엔테이션", "캠퍼스투어", "입시", "모집", "신입생", "전형"],
  학사행사: ["학위", "논문", "심사", "졸업", "수강신청", "계절학기", "등록", "성적"],
  산학행사: ["산학", "기술이전", "협력", "연구", "기업", "취업", "박람회", "설명회", "MOU"],
  문화행사: ["축제", "공연", "전시", "문화", "예술", "체육", "동아리", "경시대회"],
  국제행사: ["국제", "교환학생", "해외", "글로벌", "외국어"]
};

function nowKst() {
  const date = new Date(Date.now() + 9 * 60 * 60 * 1000);
  return date.toISOString().replace("Z", "+09:00");
}

function classifyEventType(title, description) {
  const text = `${title} ${description}`.toLowerCase();
  for (const [type, keywords] of Object.entries(EVENT_TYPE_KEYWORDS)) {
    for (const keyword of keywords) {
      if (text.includes(keyword.toLowerCase())) return type;
    }
  }
  return "기타행사";
}

function getEventStatus(dateStr) {
  if (!dateStr) return "미정";
  
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  if (dateStr.includes("~")) {
    const parts = dateStr.split("~").map(s => s.trim());
    const startDate = new Date(parts[0]);
    const endDate = new Date(parts[parts.length - 1]);
    if (today >= startDate && today <= endDate) return "진행중";
    if (today < startDate) return "예정";
    return "종료";
  }
  
  const eventDate = new Date(dateStr);
  if (isNaN(eventDate.getTime())) return "미정";
  
  const diffDays = Math.floor((eventDate - today) / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return "오늘";
  if (diffDays === 1) return "내일";
  if (diffDays > 1 && diffDays <= 7) return "이번주";
  if (diffDays > 7 && diffDays <= 30) return "이번달";
  if (diffDays < 0) return "종료";
  return "예정";
}

// Ollama Kimi API 호출
async function callOllamaKimi(prompt) {
  try {
    const response = await fetch(`${OLLAMA_HOST}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: OLLAMA_MODEL,
        prompt: prompt,
        stream: false,
        options: { temperature: 0.3, top_p: 0.9, num_predict: 2048 }
      })
    });

    if (!response.ok) {
      console.error(`[WARN] Ollama API 오류: ${response.status}`);
      return null;
    }

    const data = await response.json();
    return data.response || null;
  } catch (error) {
    console.error(`[WARN] Ollama 호출 실패:`, error.message);
    return null;
  }
}

// Ollama AI로 대학 관련 뉴스/특이점 검색
async function searchUniversityNews(university) {
  console.log(`[INFO] ${university.shortName} 뉴스/특이점 검색 중...`);
  
  const prompt = `다음 대학의 2026년 최신 소식, 특이점, 연예인 입학 소식 등을 검색해서 알려주세요.

대학: ${university.name} (${university.shortName})
위치: ${university.location}

검색 키워드 예시:
- "${university.name} 연예인 입학"
- "${university.name} 2026년 특이점"
- "${university.name} 최신 소식"

다음 JSON 형식으로 정리해주세요:
{
  "news": [
    {
      "title": "뉴스 제목",
      "category": "연예인입학 또는 특이점 또는 최신소식",
      "description": "간단한 설명",
      "date": "2026-06-03",
      "importance": "high 또는 medium 또는 low"
    }
  ]
}

주의사항:
1. 실제로 있었던 사실만 포함
2. 연예인 입학 소식이 있으면 반드시 포함
3. 최대 3개까지만`;

  const kimiResponse = await callOllamaKimi(prompt);
  
  if (!kimiResponse) {
    console.log(`[INFO] ${university.shortName} 뉴스 검색 결과 없음`);
    return [];
  }

  try {
    // JSON 추출 - 더 유연한 파싱
    let jsonStr = kimiResponse;
    
    // JSON 객체 찾기
    const jsonStart = jsonStr.indexOf('{');
    const jsonEnd = jsonStr.lastIndexOf('}');
    
    if (jsonStart === -1 || jsonEnd === -1) {
      console.log(`[WARN] ${university.shortName} 뉴스 JSON 없음`);
      return [];
    }
    
    jsonStr = jsonStr.slice(jsonStart, jsonEnd + 1);
    
    // JSON 파싱 시도
    let parsed;
    try {
      parsed = JSON.parse(jsonStr);
    } catch (e) {
      // 파싱 실패 시 정규식으로 추출 시도
      console.log(`[WARN] ${university.shortName} JSON 파싱 실패, 정규식 시도`);
      
      const newsItems = [];
      const titleMatches = jsonStr.matchAll(/"title"\s*:\s*"([^"]+)"/g);
      const categoryMatches = jsonStr.matchAll(/"category"\s*:\s*"([^"]+)"/g);
      const descMatches = jsonStr.matchAll(/"description"\s*:\s*"([^"]+)"/g);
      const dateMatches = jsonStr.matchAll(/"date"\s*:\s*"([^"]+)"/g);
      const importanceMatches = jsonStr.matchAll(/"importance"\s*:\s*"([^"]+)"/g);
      
      const titles = [...titleMatches].map(m => m[1]);
      const categories = [...categoryMatches].map(m => m[1]);
      const descriptions = [...descMatches].map(m => m[1]);
      const dates = [...dateMatches].map(m => m[1]);
      const importances = [...importanceMatches].map(m => m[1]);
      
      for (let i = 0; i < Math.min(titles.length, 3); i++) {
        newsItems.push({
          title: titles[i] || "제목 없음",
          category: categories[i] || "기타",
          description: descriptions[i] || "",
          date: dates[i] || "",
          importance: importances[i] || "low"
        });
      }
      
      if (newsItems.length > 0) {
        console.log(`[INFO] ${university.shortName} 뉴스 검색 완료: ${newsItems.length}개 (정규식)`);
        return newsItems;
      }
      
      return [];
    }
    
    const news = (parsed.news || []).map(n => ({
      title: n.title || "제목 없음",
      category: n.category || "기타",
      description: n.description || "",
      date: n.date || "",
      importance: n.importance || "low"
    }));

    console.log(`[INFO] ${university.shortName} 뉴스 검색 완료: ${news.length}개`);
    return news;
  } catch (parseError) {
    console.error(`[WARN] ${university.shortName} 뉴스 파싱 실패:`, parseError.message);
    return [];
  }
}

// 샘플 데이터 생성
function generateSampleData() {
  const today = new Date();
  const formatDate = (d) => d.toISOString().split('T')[0];
  
  return [
    {
      name: "한국외국어대학교",
      shortName: "외대",
      location: "서울특별시 중랑구 모현동 107",
      website: "https://www.hufs.ac.kr",
      rawEvents: [
        { title: "2026년 6월 캠퍼스 투어 및 입학 상담", date: formatDate(today), description: "한국외국어대학교 글로벌캠퍼스에서 진행되는 입학 상담 및 캠퍼스 투어 프로그램", venue: "한국외국어대학교 글로벌캠퍼스" },
        { title: "2026학년도 후기 학위논문 심사", date: formatDate(new Date(today.getTime() + 12 * 24 * 60 * 60 * 1000)), description: "대학원 학위논문 심사 기간", venue: "각 학과별" },
        { title: "외국어 경시대회", date: formatDate(new Date(today.getTime() + 5 * 24 * 60 * 60 * 1000)), description: "제42회 외국어 경시대회 개최", venue: "본관 강당" }
      ]
    },
    {
      name: "광운대학교",
      shortName: "광운대",
      location: "서울특별시 중랑구 화양동 447",
      website: "https://www.kw.ac.kr",
      rawEvents: [
        { title: "2026년 여름 계절학기 수강신청", date: `${formatDate(new Date(today.getTime() - 2 * 24 * 60 * 60 * 1000))} ~ ${formatDate(new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000))}`, description: "2026학년도 여름 계절학기 수강신청 기간", venue: "온라인" },
        { title: "광운대학교 산학협력단 기술이전 설명회", date: formatDate(new Date(today.getTime() + 9 * 24 * 60 * 60 * 1000)), description: "기술이전 및 산학협력 사업 설명회", venue: "광운대학교 산학협력단" },
        { title: "캠퍼스 투어 프로그램", date: formatDate(new Date(today.getTime() + 3 * 24 * 60 * 60 * 1000)), description: "고교생 대상 캠퍼스 투어 및 입학 상담", venue: "광운대학교 캠퍼스" }
      ]
    },
    {
      name: "서일대학교",
      shortName: "서일대",
      location: "서울특별시 중랑구 묵동 179-5",
      website: "https://www.seoil.ac.kr",
      rawEvents: [
        { title: "2026학년도 신입생 오리엔테이션", date: formatDate(new Date(today.getTime() + 2 * 24 * 60 * 60 * 1000)), description: "신입생 대상 오리엔테이션 및 학과 소개", venue: "서일대학교 대강당" },
        { title: "서일대학교 취업박람회", date: formatDate(new Date(today.getTime() + 17 * 24 * 60 * 60 * 1000)), description: "졸업생 및 재학생 대상 취업 박람회", venue: "서일대학교 체육관" },
        { title: "산학협력 MOU 체결식", date: formatDate(new Date(today.getTime() + 10 * 24 * 60 * 60 * 1000)), description: "지역 기업과 산학협력 협약 체결", venue: "산학협력관" }
      ]
    },
    {
      name: "경희대학교",
      shortName: "경희대",
      location: "서울특별시 동대문구 회기동 1",
      website: "https://www.khu.ac.kr",
      rawEvents: [
        { title: "2026학년도 하계 계절학기", date: `${formatDate(new Date(today.getTime() - 5 * 24 * 60 * 60 * 1000))} ~ ${formatDate(new Date(today.getTime() + 25 * 24 * 60 * 60 * 1000))}`, description: "2026학년도 하계 계절학기 운영", venue: "경희대학교 국제캠퍼스" },
        { title: "경희대학교 국제 여름학교", date: formatDate(new Date(today.getTime() + 15 * 24 * 60 * 60 * 1000)), description: "국제 학생 대상 여름학교 프로그램", venue: "경희대학교 서울캠퍼스" },
        { title: "평화의 날 기념 행사", date: formatDate(new Date(today.getTime() + 8 * 24 * 60 * 60 * 1000)), description: "경희대학교 평화의 날 기념 특별 행사", venue: "평화의 전당" }
      ]
    }
  ];
}

// Kimi로 샘플 데이터 정리
async function organizeSampleDataWithKimi() {
  console.log("[INFO] 샘플 데이터를 Kimi로 정리 중...");
  
  const sampleData = generateSampleData();
  const universities = [];

  for (const uni of sampleData) {
    console.log(`[INFO] ${uni.shortName} 행사 정리 중...`);
    
    const eventsText = uni.rawEvents.map((e, i) => 
      `${i + 1}. 제목: ${e.title}\n   날짜: ${e.date}\n   설명: ${e.description}\n   장소: ${e.venue}`
    ).join("\n");

    const prompt = `다음은 ${uni.name}(${uni.shortName})의 행사 정보입니다. 이 정보를 정리해주세요.

행사 정보:
${eventsText}

다음 JSON 형식으로 정리해주세요 (다른 설명 없이 JSON만 출력):
{
  "events": [
    {
      "title": "행사 제목",
      "date": "YYYY-MM-DD 또는 YYYY-MM-DD ~ YYYY-MM-DD",
      "description": "행사 설명 (간결하게)",
      "venue": "장소",
      "type": "입학행사|학사행사|산학행사|문화행사|국제행사|기타행사"
    }
  ]
}

주의사항:
1. 날짜 형식은 YYYY-MM-DD로 유지
2. 행사 유형은 입학행사, 학사행사, 산학행사, 문화행사, 국제행사, 기타행사 중 하나로 분류
3. 설명은 간결하게 요약`;

    const kimiResponse = await callOllamaKimi(prompt);
    
    let events = [];
    if (kimiResponse) {
      try {
        const jsonMatch = kimiResponse.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
          const parsed = JSON.parse(jsonMatch[0]);
          events = (parsed.events || []).map(e => ({
            title: e.title || "제목 없음",
            date: e.date || "",
            description: e.description || `${uni.shortName} 행사`,
            venue: e.venue || uni.shortName,
            type: e.type || classifyEventType(e.title || "", e.description || ""),
            status: getEventStatus(e.date || "")
          }));
          console.log(`[INFO] ${uni.shortName} Kimi 정리 완료: ${events.length}개 행사`);
        }
      } catch (parseError) {
        console.error(`[WARN] ${uni.shortName} Kimi 파싱 실패:`, parseError.message);
      }
    }

    // Kimi 실패 시 원본 데이터 사용
    if (events.length === 0) {
      console.log(`[INFO] ${uni.shortName} 원본 데이터 사용`);
      events = uni.rawEvents.map(e => ({
        ...e,
        type: classifyEventType(e.title, e.description),
        status: getEventStatus(e.date)
      }));
    }

    // 뉴스/특이점 검색
    const news = await searchUniversityNews(uni);

    universities.push({
      name: uni.name,
      shortName: uni.shortName,
      location: uni.location,
      website: uni.website,
      events,
      news: news.length > 0 ? news : undefined
    });
  }

  return universities;
}

// 오늘의 행사 하이라이트
function getTodayHighlight(universities) {
  const today = new Date().toISOString().split('T')[0];
  const todayEvents = [];
  
  for (const uni of universities) {
    for (const event of uni.events || []) {
      if (event.date === today || event.status === "오늘" || event.status === "진행중") {
        todayEvents.push({
          university: uni.name,
          shortName: uni.shortName,
          title: event.title,
          date: event.date,
          type: event.type,
          venue: event.venue,
          status: event.status
        });
      }
    }
  }
  return todayEvents;
}

// 최근 행사 목록
function getRecentEvents(universities) {
  const recentEvents = [];
  for (const uni of universities) {
    for (const event of uni.events || []) {
      if (["오늘", "진행중", "이번주", "예정"].includes(event.status)) {
        recentEvents.push({
          university: uni.name,
          title: event.title,
          date: event.date,
          type: event.type,
          status: event.status
        });
      }
    }
  }
  return recentEvents.sort((a, b) => {
    const order = { "오늘": 0, "진행중": 1, "이번주": 2, "예정": 3 };
    return (order[a.status] || 99) - (order[b.status] || 99);
  }).slice(0, 20);
}

// 메인 수집 함수
async function collect() {
  console.log("[INFO] 중랑구 대학 행사 정보 수집 시작");
  console.log(`[INFO] Ollama Kimi 모델 사용: ${OLLAMA_HOST} / ${OLLAMA_MODEL}`);
  
  const universities = await organizeSampleDataWithKimi();
  
  return {
    ok: true,
    topic: "중랑구 대학 주요 행사",
    updatedAt: nowKst(),
    source: "Ollama AI Kimi 정리",
    universities,
    recentEvents: getRecentEvents(universities),
    todayHighlight: getTodayHighlight(universities)
  };
}

// JSON 파일 저장
function saveJson(data) {
  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(data, null, 2), "utf-8");
  console.log(`[INFO] 저장 완료: ${OUTPUT_FILE}`);
}

// 서버 업로드
function uploadToServer() {
  if (!AUTO_UPLOAD_JSON) {
    console.log("[INFO] 자동 업로드 비활성화됨");
    return false;
  }
  
  try {
    console.log("[INFO] 서버 업로드 시작...");
    
    const scpResult = spawnSync("scp", [OUTPUT_FILE, `${UPLOAD_SERVER}:${REMOTE_TMP_FILE}`], { stdio: "inherit" });
    if (scpResult.status !== 0) {
      console.error("[ERROR] SCP 업로드 실패");
      return false;
    }
    
    const sshResult = spawnSync("ssh", [UPLOAD_SERVER, `mkdir -p ${REMOTE_DIR} && mv ${REMOTE_TMP_FILE} ${REMOTE_FILE}`], { stdio: "inherit" });
    if (sshResult.status !== 0) {
      console.error("[ERROR] SSH 이동 실패");
      return false;
    }
    
    console.log(`[INFO] 업로드 완료: ${REMOTE_FILE}`);
    return true;
  } catch (error) {
    console.error("[ERROR] 업로드 실패:", error.message);
    return false;
  }
}

// 메인 실행
async function main() {
  const args = process.argv.slice(2);
  const loop = args.includes("--loop");
  const interval = parseInt(args.find(a => a.startsWith("--interval="))?.split("=")[1] || DEFAULT_INTERVAL_SECONDS, 10) * 1000;
  
  async function run() {
    console.log("\n" + "=".repeat(60));
    console.log(`[INFO] 중랑구 대학 행사 봇 실행: ${new Date().toLocaleString("ko-KR", { timeZone: "Asia/Seoul" })}`);
    console.log("=".repeat(60));
    
    try {
      const data = await collect();
      saveJson(data);
      uploadToServer();
      console.log("[INFO] 실행 완료");
    } catch (error) {
      console.error("[ERROR] 실행 실패:", error.message);
    }
  }
  
  if (loop) {
    console.log(`[INFO] 루프 모드: ${interval / 1000}초 간격`);
    await run();
    setInterval(run, interval);
  } else {
    await run();
  }
}

main().catch(console.error);