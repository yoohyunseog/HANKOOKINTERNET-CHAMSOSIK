/**
 * 선거 정보 수집 봇
 * 중랑구 선거 장소, 일정, 후보자 정보 수집
 */

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const OUTPUT_FILE = path.join(__dirname, "election-info.json");
const DEFAULT_INTERVAL_SECONDS = 600;
const AUTO_UPLOAD_JSON = process.env.AUTO_UPLOAD_JSON !== "0";
const UPLOAD_SERVER = process.env.ELECTION_UPLOAD_SERVER || "root@211.45.162.155";
const REMOTE_ROOT = process.env.ELECTION_REMOTE_ROOT || "/var/www/chamsosik";
const REMOTE_DIR = `${REMOTE_ROOT}/election`;
const REMOTE_FILE = `${REMOTE_DIR}/election-info.json`;
const REMOTE_TMP_FILE = "/tmp/election-info.json";

// 2026년 지방선거 정보
const ELECTION_2026 = {
  name: "제9회 전국동시지방선거",
  date: "2026-06-03",
  earlyVoting: {
    start: "2026-05-29",
    end: "2026-05-30",
    time: "08:00 ~ 20:00"
  },
  types: [
    "서울특별시장",
    "서울특별시의회의원",
    "중랑구청장",
    "중랑구의회의원"
  ]
};

// 중랑구 선거 투표소 정보 (샘플 데이터)
function getJungnangPollingStations() {
  return [
    { name: "면목동제1투표소", address: "서울특별시 중랑구 면목로 100", type: "공공시설" },
    { name: "면목동제2투표소", address: "서울특별시 중랑구 면목로 200", type: "학교" },
    { name: "상봉동제1투표소", address: "서울특별시 중랑구 상봉로 50", type: "공공시설" },
    { name: "중화동제1투표소", address: "서울특별시 중랑구 중화로 100", type: "주민센터" },
    { name: "묵동제1투표소", address: "서울특별시 중랑구 묵로 100", type: "공공시설" },
    { name: "망우동제1투표소", address: "서울특별시 중랑구 망우로 100", type: "공공시설" },
    { name: "신내동제1투표소", address: "서울특별시 중랑구 신내로 100", type: "공공시설" },
    { name: "중랑구청투표소", address: "서울특별시 중랑구 중랑역로 100", type: "구청" }
  ];
}

// 선거 일정 정보
function getElectionSchedule() {
  const now = new Date();
  const currentHour = now.getHours(); // 로컬 시간 (한국 시간)
  
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const electionDate = new Date("2026-06-03");
  electionDate.setHours(0, 0, 0, 0);
  
  const earlyVotingStart = new Date("2026-05-29");
  earlyVotingStart.setHours(0, 0, 0, 0);
  
  const earlyVotingEnd = new Date("2026-05-30");
  earlyVotingEnd.setHours(0, 0, 0, 0);
  
  const daysUntilElection = Math.ceil((electionDate - today) / (1000 * 60 * 60 * 24));
  const isEarlyVotingPeriod = today >= earlyVotingStart && today <= earlyVotingEnd;
  const isElectionDay = today.getTime() === electionDate.getTime();
  
  // 투표 종료 시간 (오후 6시 = 18시)
  const votingEndTime = 18;
  const isVotingEnded = isElectionDay && currentHour >= votingEndTime;
  
  let status = "선거 전";
  let message = "";
  
  if (isVotingEnded) {
    status = "선거 종료";
    message = "투표가 종료되었습니다. 개표 결과를 기다려주세요.";
  } else if (isElectionDay) {
    status = "선거일";
    message = "오늘은 제9회 전국동시지방선거 투표일입니다. 오후 6시까지 투표하세요!";
  } else if (isEarlyVotingPeriod) {
    status = "사전투표 기간";
    message = "사전투표 기간입니다. 가까운 사전투표소에서 투표하세요.";
  } else if (daysUntilElection > 0) {
    status = "선거 전";
    message = `선거일까지 ${daysUntilElection}일 남았습니다.`;
  } else {
    status = "선거 종료";
    message = "선거가 종료되었습니다.";
  }
  
  return {
    electionName: ELECTION_2026.name,
    electionDate: ELECTION_2026.date,
    earlyVoting: ELECTION_2026.earlyVoting,
    daysUntilElection,
    status,
    message,
    isEarlyVotingPeriod,
    isElectionDay,
    isVotingEnded,
    currentHour
  };
}

// 선거 관련 YouTube 영상 검색
async function fetchElectionVideos() {
  const queries = [
    "2026 지방선거 중랑구",
    "중랑구청장 선거",
    "서울시장 선거 2026",
    "지방선거 투표 방법"
  ];
  
  const videos = [];
  const seen = new Set();
  
  for (const query of queries) {
    try {
      const response = await fetch(`https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`, {
        headers: {
          "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
          "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8"
        }
      });
      
      if (!response.ok) continue;
      
      const html = await response.text();
      const videoMatches = html.matchAll(/"videoId":"([^"]+)"/g);
      const titleMatches = html.matchAll(/"title":{"runs":\[{"text":"([^"]+)"/g);
      
      const videoIds = [...videoMatches].map(m => m[1]).slice(0, 3);
      
      for (const videoId of videoIds) {
        if (seen.has(videoId)) continue;
        seen.add(videoId);
        
        videos.push({
          id: videoId,
          title: `${query} 관련 영상`,
          url: `https://www.youtube.com/watch?v=${videoId}`,
          thumbnail: `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`,
          query
        });
      }
    } catch (error) {
      console.error(`[WARN] ${query} 검색 실패:`, error.message);
    }
  }
  
  return videos.slice(0, 12);
}

function nowKst() {
  const date = new Date(Date.now() + 9 * 60 * 60 * 1000);
  return date.toISOString().replace("Z", "+09:00");
}

async function collect() {
  console.log("[INFO] 선거 정보 수집 시작");
  
  const schedule = getElectionSchedule();
  const pollingStations = getJungnangPollingStations();
  const videos = await fetchElectionVideos();
  
  return {
    ok: true,
    topic: "2026 지방선거 정보",
    updatedAt: nowKst(),
    election: ELECTION_2026,
    schedule,
    pollingStations,
    videos,
    tips: [
      "투표 시간: 오전 6시 ~ 오후 6시",
      "신분증: 주민등록증, 여권, 운전면허증 등",
      "사전투표: 선거일 전에 가까운 투표소에서 투표 가능",
      "투표소 확인: 선거관리위원회 홈페이지 또는 앱"
    ],
    links: [
      { name: "중앙선거관리위원회", url: "http://www.nec.go.kr" },
      { name: "선거정보 앱 다운로드", url: "https://www.nec.go.kr/app" }
    ]
  };
}

function writeJson(payload) {
  const tempFile = `${OUTPUT_FILE}.tmp`;
  fs.writeFileSync(tempFile, JSON.stringify(payload, null, 2), "utf8");
  fs.renameSync(tempFile, OUTPUT_FILE);
  console.log(`[INFO] 저장 완료: ${OUTPUT_FILE}`);
}

function uploadJsonToServer() {
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
    
    const sshResult = spawnSync("ssh", [UPLOAD_SERVER, `sudo mkdir -p ${REMOTE_DIR} && sudo mv ${REMOTE_TMP_FILE} ${REMOTE_FILE} && sudo chmod 644 ${REMOTE_FILE}`], { stdio: "inherit" });
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

async function main() {
  const args = process.argv.slice(2);
  const loop = args.includes("--loop");
  const interval = parseInt(args.find(a => a.startsWith("--interval="))?.split("=")[1] || DEFAULT_INTERVAL_SECONDS, 10) * 1000;
  
  async function run() {
    console.log("\n" + "=".repeat(60));
    console.log(`[INFO] 선거 정보 봇 실행: ${new Date().toLocaleString("ko-KR", { timeZone: "Asia/Seoul" })}`);
    console.log("=".repeat(60));
    
    try {
      const data = await collect();
      writeJson(data);
      uploadJsonToServer();
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