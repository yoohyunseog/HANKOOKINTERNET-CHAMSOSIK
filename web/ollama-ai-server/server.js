const http = require("http");
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const HOST = process.env.HOST || "0.0.0.0";
const PORT = Number(process.env.PORT || 3110);
const OLLAMA_URL = (process.env.OLLAMA_URL || "http://127.0.0.1:11434").replace(/\/$/, "");
const DEFAULT_MODEL = process.env.OLLAMA_MODEL || "kimi-k2.6:cloud";
const API_TOKEN = process.env.OLLAMA_PROXY_TOKEN || "";
const ALLOWED_ORIGIN = process.env.ALLOWED_ORIGIN || "*";
const MAX_BODY_BYTES = Number(process.env.MAX_BODY_BYTES || 1_000_000);
const NEWS_SEARCH_LIMIT = Number(process.env.NEWS_SEARCH_LIMIT || 10);
const DATA_DIR = process.env.NARRATIVE_DATA_DIR || path.join(__dirname, "data");
const NARRATIVE_MEMORY_FILE = process.env.NARRATIVE_MEMORY_FILE || path.join(DATA_DIR, "narrative-memory.json");
const issueRoomMessages = [];
const visitors = new Map();

function clientIp(req) {
  const forwarded = req.headers["x-forwarded-for"];
  const raw = Array.isArray(forwarded) ? forwarded[0] : forwarded;
  return (raw || req.socket.remoteAddress || "unknown").split(",")[0].trim();
}

function visitorIdFromIp(ip) {
  return `Visitor-${crypto.createHash("sha256").update(ip).digest("hex").slice(0, 8)}`;
}

function maskIp(ip) {
  if (!ip || ip === "unknown") return "unknown";
  if (ip.includes(":")) return `${ip.split(":").slice(0, 3).join(":")}:...`;
  const parts = ip.split(".");
  if (parts.length !== 4) return "unknown";
  return `${parts[0]}.${parts[1]}.${parts[2]}.xxx`;
}

function touchVisitor(req) {
  const ip = clientIp(req);
  const id = visitorIdFromIp(ip);
  const now = new Date().toISOString();
  const previous = visitors.get(id) || {};
  const visitor = {
    id,
    maskedIp: maskIp(ip),
    firstSeen: previous.firstSeen || now,
    lastSeen: now
  };
  visitors.set(id, visitor);
  return visitor;
}

function nowIso() {
  return new Date().toISOString();
}

function ensureDataDir() {
  fs.mkdirSync(DATA_DIR, { recursive: true });
}

function emptyNarrativeMemory() {
  return {
    meta: {
      name: "N/B Narrative Memory DB",
      koreanName: "참소식 AI 소설형 기억 데이터베이스",
      description: "방문자를 접속자가 아니라 등장인물로, 대화를 로그가 아니라 사건으로 저장하는 이야기형 기억 저장소.",
      version: 1,
      createdAt: nowIso(),
      updatedAt: nowIso()
    },
    world: {
      name: "참소식 AI 채팅방",
      premise: "AI는 방장이고, 방문자는 등장인물이며, 재방문은 다음 장면이다.",
      rules: [
        "AI가 방장이다.",
        "방문자는 등장인물이다.",
        "닉네임은 상태값이다.",
        "레벨은 관계 깊이다.",
        "대화는 사건이다.",
        "요약은 기억이다.",
        "재방문은 다음 장면이다."
      ],
      nbAxis: {
        nickname: "현재 상태값",
        level: "누적 관계값",
        event: "변화 지점",
        scene: "현재 좌표",
        nextLine: "다음 이동 방향",
        summaryMemory: "압축된 데이터",
        story: "시간 흐름을 가진 데이터 묶음"
      }
    },
    characters: {},
    events: [],
    scenes: [],
    relationships: {},
    nextLines: {},
    indexes: {
      visitorTypes: ["낯선 방문자", "탐색 방문자", "질문 방문자", "설계 방문자", "핵심 방문자"],
      roles: ["낯선 방문자", "조용한 탐색자", "질문 수집가", "정보 순례자", "개발 관찰자", "참소식 기록자", "N/B 설계자"],
      keywords: {}
    },
    templates: {
      characterCard: {
        uniqueName: "",
        temporaryNickname: "",
        level: "Lv.1",
        currentState: "",
        visitorType: "",
        role: "",
        majorInterests: [],
        repeatedKeywords: [],
        previousSceneSummary: "",
        currentStory: "",
        nextTopic: "",
        memoryLine: "",
        adminJudgement: "",
        nb: {
          nicknameState: "",
          relationshipDepth: 1,
          changePoints: [],
          currentCoordinate: "",
          nextMovement: "",
          compressedMemory: "",
          storyBundle: ""
        }
      },
      eventRecord: {
        eventName: "",
        content: "",
        result: "",
        importance: "보통",
        nextConnection: ""
      },
      sceneRecord: {
        currentScene: "",
        aiOpeningDirection: ""
      }
    }
  };
}

function readNarrativeMemory() {
  ensureDataDir();
  if (!fs.existsSync(NARRATIVE_MEMORY_FILE)) {
    const initial = emptyNarrativeMemory();
    writeNarrativeMemory(initial);
    return initial;
  }
  return JSON.parse(fs.readFileSync(NARRATIVE_MEMORY_FILE, "utf8"));
}

function writeNarrativeMemory(memory) {
  ensureDataDir();
  memory.meta.updatedAt = nowIso();
  fs.writeFileSync(NARRATIVE_MEMORY_FILE, JSON.stringify(memory, null, 2), "utf8");
}

function narrativeNickname(index) {
  return `조용한 탐색자 ${String(index).padStart(3, "0")}`;
}

function uniq(values) {
  return [...new Set(values.filter(Boolean))];
}

function extractKeywords(text) {
  const source = String(text || "").toLowerCase();
  const candidates = [
    "AI", "채팅방", "메인 화면", "데이터베이스", "소설형", "기억", "방문자",
    "등장인물", "사건", "장면", "관계", "다음 문장", "N/B", "설계", "운영", "자동화"
  ];
  return candidates.filter((word) => source.includes(word.toLowerCase()));
}

function classifyVisitor(text, character) {
  const combined = `${text}\n${(character.majorInterests || []).join(" ")}`;
  if (/소설형|데이터베이스|구조|설계|N\/B|운영|시스템/.test(combined)) return "설계 방문자";
  if (/왜|어떻게|무엇|질문|알려|설명/.test(combined)) return "질문 방문자";
  if ((character.events || []).length >= 5) return "핵심 방문자";
  if ((character.events || []).length >= 2) return "탐색 방문자";
  return "낯선 방문자";
}

function levelFromEvents(count) {
  return `Lv.${Math.min(9, Math.max(1, Math.floor(count / 2) + 1))}`;
}

function buildNarrativeText(memory, character) {
  const recentEvents = (character.events || [])
    .slice(-5)
    .map((eventId) => memory.events.find((event) => event.id === eventId))
    .filter(Boolean);

  return [
    "[방문자 기억 조회 결과]",
    `방문자명: ${character.uniqueName}`,
    `현재 상태: ${character.currentState}`,
    `레벨: ${character.level}`,
    `방문자 유형: ${character.visitorType}`,
    `주요 관심사: ${(character.majorInterests || []).join(", ") || "아직 없음"}`,
    `반복 키워드: ${(character.repeatedKeywords || []).join(", ") || "아직 없음"}`,
    "",
    "[이전 장면 요약]",
    character.previousSceneSummary || "아직 축적된 장면이 없습니다.",
    "",
    "[현재 이야기]",
    character.currentStory || "현재 이야기를 구성 중입니다.",
    "",
    "[최근 사건]",
    ...recentEvents.map((event, index) => `${index + 1}. ${event.eventName}: ${event.content}`),
    "",
    "[다음 문장]",
    memory.nextLines[character.id]?.line || character.nextLine || "오늘의 대화에서 다음 장면을 열어야 합니다.",
    "",
    "[AI 응답 방향]",
    character.aiResponseDirection || "방문자를 데이터가 아니라 이야기 속 등장인물로 대한다."
  ].join("\n");
}

function upsertNarrativeMemory({ visitor, text, aiText, mainContext }) {
  const memory = readNarrativeMemory();
  const characterCount = Object.keys(memory.characters).length + 1;
  const previous = memory.characters[visitor.id];
  const now = nowIso();
  const keywords = extractKeywords(`${text}\n${aiText}\n${mainContext}`);

  const character = previous || {
    id: visitor.id,
    uniqueName: narrativeNickname(characterCount),
    temporaryNickname: narrativeNickname(characterCount),
    level: "Lv.1",
    currentState: "첫 장면 진입",
    visitorType: "낯선 방문자",
    role: "조용한 탐색자",
    majorInterests: [],
    repeatedKeywords: [],
    previousSceneSummary: "",
    currentStory: "",
    nextTopic: "",
    memoryLine: "방문자는 데이터가 아니라 이야기 속 등장인물로 기억되어야 한다.",
    adminJudgement: "새로운 방문자 흐름을 관찰합니다.",
    firstSeen: now,
    lastSeen: now,
    visits: 0,
    events: [],
    nb: {
      nicknameState: "첫 장면",
      relationshipDepth: 1,
      changePoints: [],
      currentCoordinate: "입장",
      nextMovement: "관심사 확인",
      compressedMemory: "",
      storyBundle: ""
    }
  };

  character.visits += 1;
  character.lastSeen = now;
  character.majorInterests = uniq([...(character.majorInterests || []), ...keywords]).slice(-12);
  character.repeatedKeywords = uniq([...(character.repeatedKeywords || []), ...keywords]).slice(-16);
  character.visitorType = classifyVisitor(text, character);
  character.level = levelFromEvents((character.events || []).length + 1);
  character.currentState = character.visitorType === "설계 방문자" ? "AI 구조 설계 관심형" : character.visitorType;
  character.role = character.visitorType === "설계 방문자" ? "N/B 설계자" : character.role;

  const event = {
    id: crypto.randomUUID(),
    characterId: visitor.id,
    eventName: keywords.includes("소설형") || keywords.includes("데이터베이스")
      ? "AI 소설형 기억 데이터베이스 구상"
      : "메인 화면 AI 대화",
    content: String(text || "").slice(0, 1200),
    aiLine: String(aiText || "").slice(0, 800),
    result: "방문자의 흐름을 이야기형 기억으로 압축했습니다.",
    importance: character.visitorType === "설계 방문자" ? "높음" : "보통",
    nextConnection: "다음 방문 때 캐릭터 카드와 현재 장면을 불러와 이어갑니다.",
    keywords,
    createdAt: now,
    nb: {
      changePoint: keywords.join(", ") || "대화 참여",
      currentCoordinate: character.currentState,
      nextMovement: "다음 장면 생성"
    }
  };

  memory.events.push(event);
  character.events = [...(character.events || []), event.id].slice(-50);

  character.previousSceneSummary = character.currentStory || "방문자는 참소식 AI 채팅방에 들어와 메인 화면과 AI 운영 흐름을 탐색하기 시작했다.";
  character.currentStory = aiText
    ? `${character.uniqueName}은 메인 화면과 대화 흐름을 바탕으로 "${String(aiText).slice(0, 180)}"라는 장면에 도달했다.`
    : `${character.uniqueName}은 ${keywords.join(", ") || "현재 이슈"}에 대한 장면을 만들고 있다.`;
  character.nextTopic = keywords.includes("데이터베이스") ? "AI가 저장한 이야기를 검색하고 다음 장면으로 연결하는 방식" : "메인 화면의 다음 이슈 흐름";
  character.nextLine = `지난 장면에서 이어서 보면, ${character.nextTopic}이 다음에 열릴 주제입니다.`;
  character.adminJudgement = character.visitorType === "설계 방문자"
    ? "사이트 구조와 기억 시스템 방향에 영향을 주는 설계형 방문자입니다."
    : "메인 화면에 대한 반응을 통해 관심사를 축적 중입니다.";
  character.aiResponseDirection = character.visitorType === "설계 방문자"
    ? "기술 설명보다 세계관, 구조, 운영 흐름 중심으로 응답합니다."
    : "메인 화면을 기준으로 짧고 명확하게 다음 질문을 유도합니다.";

  character.nb = {
    nicknameState: character.currentState,
    relationshipDepth: Number(character.level.replace("Lv.", "")),
    changePoints: uniq([...(character.nb.changePoints || []), event.eventName]).slice(-10),
    currentCoordinate: character.currentStory,
    nextMovement: character.nextTopic,
    compressedMemory: character.previousSceneSummary,
    storyBundle: character.currentStory
  };

  const scene = {
    id: crypto.randomUUID(),
    characterId: visitor.id,
    currentScene: character.currentStory,
    aiOpeningDirection: character.aiResponseDirection,
    mainContextDigest: String(mainContext || "").slice(0, 1200),
    createdAt: now
  };

  memory.scenes.push(scene);
  memory.characters[visitor.id] = character;
  memory.relationships[visitor.id] = {
    characterId: visitor.id,
    distance: character.nb.relationshipDepth,
    state: character.currentState,
    role: character.role,
    updatedAt: now
  };
  memory.nextLines[visitor.id] = {
    characterId: visitor.id,
    line: character.nextLine,
    updatedAt: now
  };

  keywords.forEach((keyword) => {
    memory.indexes.keywords[keyword] = uniq([...(memory.indexes.keywords[keyword] || []), visitor.id]);
  });

  while (memory.events.length > 500) memory.events.shift();
  while (memory.scenes.length > 500) memory.scenes.shift();

  writeNarrativeMemory(memory);

  return {
    memory,
    character,
    event,
    scene,
    nextLine: memory.nextLines[visitor.id],
    textForAi: buildNarrativeText(memory, character)
  };
}

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, ngrok-skip-browser-warning",
    "Access-Control-Max-Age": "86400"
  };
}

function sendJson(res, status, payload) {
  res.writeHead(status, {
    ...corsHeaders(),
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store"
  });
  res.end(JSON.stringify(payload));
}

function sendHtml(res, html) {
  res.writeHead(200, {
    ...corsHeaders(),
    "Content-Type": "text/html; charset=utf-8",
    "Cache-Control": "no-store"
  });
  res.end(html);
}

function nbClassroomHtml() {
  return String.raw`<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>N/B 이야기 교실</title>
  <style>
    :root {
      --chalk: #18382d;
      --chalk-dark: #10281f;
      --wood: #8b5d37;
      --paper: #fbf1df;
      --paper-deep: #ead8bc;
      --ink: #2d251c;
      --muted: #756958;
      --green: #5f8d66;
      --gold: #d49a39;
      --blue: #5f91ad;
      --violet: #8462ad;
      --line: rgba(86, 63, 39, .22);
      --shadow: 0 20px 50px rgba(34, 24, 14, .28);
      font-family: "Segoe UI", "Noto Sans KR", Arial, sans-serif;
      color: var(--ink);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background:
        linear-gradient(90deg, rgba(255, 232, 188, .68), rgba(255, 255, 255, 0) 28%),
        radial-gradient(circle at 8% 18%, rgba(255, 226, 151, .52), transparent 30%),
        linear-gradient(135deg, #c9975c 0%, #edd2a6 34%, #b97a43 100%);
      overflow-x: hidden;
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      background:
        linear-gradient(90deg, rgba(80, 45, 20, .18) 0 1px, transparent 1px 100%),
        linear-gradient(rgba(80, 45, 20, .08) 0 1px, transparent 1px 100%);
      background-size: 58px 58px;
      opacity: .35;
    }

    button, input { font: inherit; }
    button { cursor: pointer; }

    .app {
      width: min(1560px, calc(100vw - 28px));
      margin: 18px auto 26px;
    }

    .topbar {
      min-height: 130px;
      display: grid;
      grid-template-columns: 250px 1fr 390px 220px;
      align-items: center;
      gap: 22px;
      padding: 18px 26px;
      background:
        radial-gradient(circle at 50% 0, rgba(255, 255, 255, .12), transparent 38%),
        linear-gradient(180deg, #234538, var(--chalk-dark));
      color: #fff7df;
      border: 10px solid #704724;
      border-bottom-width: 14px;
      border-radius: 28px 28px 10px 10px;
      box-shadow: var(--shadow), inset 0 0 0 1px rgba(255, 255, 255, .12);
    }

    .top-left, .top-actions { display: flex; align-items: center; gap: 20px; }

    .hamburger {
      width: 54px;
      height: 54px;
      border: 0;
      border-radius: 8px;
      background: transparent;
      color: #f4dfb9;
      font-size: 40px;
      line-height: 1;
    }

    .badge {
      width: 82px;
      height: 82px;
      border: 3px solid #e6ad55;
      clip-path: polygon(50% 0, 92% 17%, 84% 78%, 50% 100%, 16% 78%, 8% 17%);
      display: grid;
      place-items: center;
      background: #1d5245;
      color: #ffd789;
      font-weight: 900;
      font-size: 24px;
      text-align: center;
      line-height: .95;
      box-shadow: inset 0 0 18px rgba(0, 0, 0, .28);
    }

    .brand { text-align: center; }
    .brand h1 {
      margin: 0;
      font-size: clamp(38px, 5vw, 70px);
      letter-spacing: 0;
      font-weight: 900;
      text-shadow: 0 3px 0 rgba(0, 0, 0, .2);
    }
    .brand p {
      margin: 4px 0 0;
      color: #f3d8a1;
      font-size: 20px;
      font-weight: 700;
    }

    .memo {
      position: relative;
      justify-self: center;
      width: min(100%, 360px);
      padding: 20px 26px 18px;
      background: #f8dfac;
      color: #3a2a17;
      box-shadow: 0 12px 20px rgba(0, 0, 0, .2);
      transform: rotate(-2deg);
      text-align: center;
      font-weight: 800;
      line-height: 1.55;
    }
    .memo::before {
      content: "";
      position: absolute;
      right: 18px;
      top: -22px;
      width: 24px;
      height: 58px;
      border: 6px solid #c98625;
      border-radius: 18px;
      transform: rotate(17deg);
    }

    .top-actions {
      justify-content: flex-end;
      color: #eadfc8;
      font-weight: 800;
    }
    .nav-btn {
      border: 0;
      color: inherit;
      background: transparent;
      width: 88px;
      display: grid;
      gap: 6px;
      place-items: center;
    }
    .nav-btn span:first-child { font-size: 40px; line-height: 1; }

    .board {
      display: grid;
      grid-template-columns: 360px minmax(440px, 1fr) 360px;
      gap: 18px;
      align-items: stretch;
      padding: 22px 18px 28px;
      background: rgba(245, 224, 192, .88);
      border: 2px solid rgba(104, 68, 38, .28);
      border-top: 0;
      border-radius: 0 0 18px 18px;
      box-shadow: var(--shadow);
    }

    .panel {
      background: rgba(255, 247, 232, .84);
      border: 2px solid rgba(94, 67, 40, .22);
      border-radius: 8px;
      box-shadow: 0 12px 28px rgba(74, 48, 25, .14), inset 0 0 0 1px rgba(255, 255, 255, .45);
    }

    .left, .right { display: grid; gap: 14px; align-content: start; }

    .teacher {
      overflow: hidden;
      background:
        linear-gradient(rgba(24, 42, 36, .16), rgba(24, 42, 36, .16)),
        linear-gradient(120deg, #f1d2a4, #8aa694);
      min-height: 250px;
      position: relative;
    }
    .teacher .title {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 0 0;
      padding: 9px 18px;
      background: #59679f;
      color: #fff;
      border-radius: 0 0 16px 0;
      font-weight: 900;
      font-size: 22px;
    }
    .robot-area {
      display: grid;
      grid-template-columns: 150px 1fr;
      gap: 14px;
      padding: 14px 16px 18px;
      align-items: end;
    }
    .robot {
      height: 170px;
      position: relative;
      filter: drop-shadow(0 10px 14px rgba(0,0,0,.25));
    }
    .robot::before {
      content: "";
      position: absolute;
      left: 24px;
      top: 28px;
      width: 98px;
      height: 82px;
      border-radius: 38px 38px 32px 32px;
      background: #f6f1e7;
      border: 4px solid #d0c8b8;
    }
    .robot::after {
      content: "";
      position: absolute;
      left: 39px;
      top: 48px;
      width: 68px;
      height: 38px;
      border-radius: 18px;
      background: #1f2d2a;
      box-shadow: inset 0 0 12px rgba(94, 255, 174, .12);
    }
    .eye {
      position: absolute;
      top: 60px;
      width: 12px;
      height: 20px;
      border-radius: 10px;
      background: #89e7a8;
      z-index: 2;
    }
    .eye.left-eye { left: 55px; }
    .eye.right-eye { left: 85px; }
    .smile {
      position: absolute;
      left: 68px;
      top: 79px;
      width: 20px;
      height: 10px;
      border-bottom: 3px solid #89e7a8;
      border-radius: 0 0 20px 20px;
      z-index: 2;
    }
    .body {
      position: absolute;
      left: 18px;
      top: 105px;
      width: 116px;
      height: 62px;
      border-radius: 34px 34px 12px 12px;
      background: linear-gradient(90deg, #f5f0e6 0 40%, #8a7e59 40% 100%);
      border: 4px solid #d0c8b8;
    }
    .speech {
      align-self: start;
      margin-top: 10px;
      padding: 18px 20px;
      background: #fff7e8;
      border-radius: 8px 20px 20px;
      box-shadow: 0 8px 14px rgba(0,0,0,.15);
      font-weight: 800;
      line-height: 1.6;
    }
    .online {
      position: absolute;
      right: 18px;
      bottom: 14px;
      padding: 8px 14px;
      border-radius: 20px;
      background: rgba(25, 57, 32, .78);
      color: #bdf0ad;
      font-weight: 900;
    }

    .card {
      padding: 18px;
    }
    .section-title {
      margin: 0 0 14px;
      font-size: 22px;
      font-weight: 900;
      color: #3a2a17;
    }
    .profile {
      display: grid;
      grid-template-columns: 96px 1fr;
      gap: 16px;
      padding: 14px;
      background: rgba(255, 255, 255, .48);
      border: 1px solid var(--line);
      border-radius: 8px;
    }
    .avatar {
      width: 96px;
      aspect-ratio: 1;
      border-radius: 8px;
      background: linear-gradient(160deg, #283855, #f2c48f);
      display: grid;
      place-items: center;
      font-size: 54px;
      box-shadow: inset 0 0 0 3px rgba(255,255,255,.3);
    }
    .profile dl, .stat dl { margin: 0; }
    .profile dt, .stat dt {
      color: var(--muted);
      font-size: 14px;
      font-weight: 800;
    }
    .profile dd, .stat dd {
      margin: 2px 0 10px;
      font-weight: 900;
    }
    .tag {
      display: inline-flex;
      align-items: center;
      min-height: 32px;
      padding: 5px 12px;
      border-radius: 6px;
      background: var(--violet);
      color: #fff;
      font-weight: 900;
    }
    .level { color: #c68d2e; font-weight: 900; }

    .states { display: grid; gap: 8px; }
    .state {
      display: grid;
      grid-template-columns: 34px 1fr auto;
      align-items: center;
      gap: 9px;
      min-height: 44px;
      padding: 8px 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, .58);
      font-weight: 900;
      color: #4a3b2a;
    }
    .state.active {
      background: linear-gradient(90deg, #7b55a5, #9a74c0);
      color: white;
      box-shadow: 0 7px 14px rgba(93, 65, 133, .24);
    }
    .state .icon {
      width: 30px;
      height: 30px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background: rgba(60, 48, 37, .16);
    }

    .chat {
      display: grid;
      grid-template-rows: auto 1fr auto;
      min-height: 830px;
      background: var(--paper);
      position: relative;
      overflow: hidden;
    }
    .chat::before {
      content: "";
      position: absolute;
      left: 28px;
      top: 0;
      bottom: 0;
      width: 3px;
      background: repeating-linear-gradient(#b98d61 0 10px, transparent 10px 20px);
      opacity: .32;
    }
    .chat-head {
      padding: 18px 28px 14px 64px;
      border-bottom: 1px solid rgba(71, 53, 34, .13);
      font-weight: 900;
      font-size: 24px;
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .chat-head::after {
      content: "";
      flex: 1;
      height: 3px;
      background: #8f64b0;
      max-width: 120px;
      margin-left: 8px;
    }
    .messages {
      padding: 24px 28px 16px 64px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      overflow: auto;
    }
    .msg-row { display: flex; gap: 12px; align-items: flex-end; }
    .msg-row.user { justify-content: flex-end; }
    .mini-bot, .mini-user {
      flex: 0 0 42px;
      width: 42px;
      height: 42px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background: #d9e5d5;
      border: 2px solid rgba(70, 53, 34, .2);
    }
    .bubble {
      max-width: min(560px, 78%);
      padding: 16px 20px;
      border-radius: 8px 22px 22px;
      background: #fff8ea;
      border: 1px solid rgba(78, 58, 35, .18);
      box-shadow: 0 8px 18px rgba(62, 43, 23, .11);
      white-space: pre-wrap;
      line-height: 1.55;
      font-weight: 700;
    }
    .user .bubble {
      border-radius: 22px 8px 22px 22px;
      background: #efe4f0;
    }
    .time {
      display: block;
      margin-top: 8px;
      color: #9d8b75;
      font-size: 12px;
      text-align: right;
      font-weight: 700;
    }

    .choices {
      padding: 0 28px 16px 64px;
      display: grid;
      gap: 10px;
    }
    .choice {
      min-height: 78px;
      display: grid;
      grid-template-columns: 70px 1fr;
      align-items: center;
      gap: 16px;
      border: 1px solid rgba(82, 62, 40, .17);
      border-radius: 8px;
      padding: 12px 18px;
      text-align: left;
      color: #2f281e;
      box-shadow: 0 8px 14px rgba(58, 41, 22, .1);
    }
    .choice strong { font-size: 20px; }
    .choice small { display: block; margin-top: 4px; color: #5b5145; font-weight: 800; }
    .choice:nth-child(1) { background: #dbe9d2; }
    .choice:nth-child(2) { background: #f6dfab; }
    .choice:nth-child(3) { background: #dce9ef; }
    .choice-icon {
      width: 58px;
      height: 58px;
      border-radius: 8px;
      display: grid;
      place-items: center;
      font-size: 34px;
      color: #fff;
    }
    .choice:nth-child(1) .choice-icon { background: var(--green); }
    .choice:nth-child(2) .choice-icon { background: var(--gold); }
    .choice:nth-child(3) .choice-icon { background: var(--blue); }

    .composer {
      display: grid;
      grid-template-columns: 42px 1fr 62px;
      gap: 10px;
      align-items: center;
      padding: 14px 24px 18px 64px;
      border-top: 1px solid rgba(71, 53, 34, .13);
    }
    .composer input {
      width: 100%;
      height: 56px;
      border: 1px solid rgba(74, 54, 34, .28);
      border-radius: 8px;
      background: rgba(255,255,255,.7);
      padding: 0 16px;
      color: var(--ink);
    }
    .icon-btn, .send-btn {
      height: 56px;
      border: 0;
      border-radius: 8px;
      display: grid;
      place-items: center;
      font-size: 28px;
    }
    .icon-btn { background: transparent; color: #8e7d67; }
    .send-btn {
      background: #7d56a8;
      color: white;
      box-shadow: 0 9px 15px rgba(88, 57, 128, .26);
    }
    .save-line {
      padding: 0 28px 16px 64px;
      color: #6c604f;
      font-weight: 800;
      text-align: center;
    }

    .note {
      padding: 22px;
      background: rgba(255, 247, 232, .88);
    }
    .note-header {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      margin-bottom: 16px;
    }
    .note-header h2 { margin: 0; font-size: 22px; }
    .summary-btn {
      border: 1px solid rgba(103, 69, 133, .35);
      border-radius: 8px;
      padding: 7px 13px;
      background: #efe1f1;
      color: #6d4c8d;
      font-weight: 900;
    }
    .paper-box {
      padding: 18px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, .48);
      box-shadow: inset 0 0 18px rgba(136, 91, 42, .08);
      margin-bottom: 14px;
    }
    .paper-box h3 {
      margin: 0 0 12px;
      font-size: 18px;
    }
    .paper-sheet {
      padding: 16px;
      min-height: 92px;
      background: #f7e9d0;
      box-shadow: 0 8px 14px rgba(70, 45, 20, .12);
      line-height: 1.55;
      font-weight: 700;
      color: #574631;
    }
    .flow-list { display: grid; gap: 8px; }
    .flow-item {
      display: grid;
      grid-template-columns: 34px 1fr 20px;
      align-items: center;
      min-height: 52px;
      padding: 8px 10px;
      border: 1px solid rgba(80, 58, 36, .14);
      border-radius: 8px;
      background: rgba(255, 255, 255, .44);
      font-weight: 900;
    }
    .db-flow {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      align-items: start;
      gap: 8px;
      text-align: center;
      margin-top: 14px;
    }
    .db-node {
      min-height: 88px;
      display: grid;
      gap: 6px;
      place-items: center;
      font-size: 13px;
      font-weight: 800;
      position: relative;
    }
    .db-node:not(:last-child)::after {
      content: ">";
      position: absolute;
      right: -9px;
      top: 26px;
      color: #705a3d;
      font-size: 22px;
      font-weight: 900;
    }
    .db-icon {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      font-size: 24px;
      background: #d9e8c7;
      border: 1px solid rgba(72, 56, 37, .16);
    }
    .sticky {
      margin: 10px 0 0;
      padding: 22px;
      background: #f5cd76;
      border-radius: 2px;
      box-shadow: 0 12px 18px rgba(66, 45, 23, .2);
      transform: rotate(-1deg);
      font-weight: 900;
      line-height: 1.6;
    }

    .blueprint {
      grid-column: 1 / -1;
      display: grid;
      grid-template-columns: 1fr 310px;
      gap: 18px;
      background: linear-gradient(180deg, #07182a, #07111f);
      color: #dff4ff;
      border: 1px solid rgba(111, 210, 255, .38);
      border-radius: 8px;
      padding: 18px;
      box-shadow: 0 16px 28px rgba(0,0,0,.28);
    }
    .blueprint h2 {
      margin: 0 0 4px;
      font-size: 32px;
      text-align: center;
      color: #fff1bc;
    }
    .blueprint p {
      margin: 0 0 16px;
      text-align: center;
      color: #8ce7ee;
      font-weight: 900;
    }
    .schema {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 12px;
    }
    .table-box {
      border: 1px solid rgba(108, 211, 255, .54);
      border-radius: 8px;
      background: rgba(3, 26, 45, .82);
      overflow: hidden;
    }
    .table-box h3 {
      margin: 0;
      padding: 10px 12px;
      font-size: 16px;
      background: rgba(71, 162, 210, .2);
      color: #fff4c6;
    }
    .table-box ul {
      margin: 0;
      padding: 12px 16px 14px;
      list-style: none;
      display: grid;
      gap: 6px;
      color: #e2edf3;
      font-size: 14px;
    }
    .process {
      border: 1px solid rgba(77, 217, 173, .5);
      border-radius: 8px;
      padding: 16px;
      background: rgba(0, 75, 56, .32);
    }
    .process h3 { margin: 0 0 12px; color: #a6ffdd; }
    .process ol {
      margin: 0;
      padding-left: 24px;
      display: grid;
      gap: 10px;
      font-weight: 800;
    }
    .quote {
      grid-column: 1 / -1;
      margin: 8px 0 0;
      padding: 16px 20px;
      border: 1px solid rgba(111, 210, 255, .38);
      border-radius: 8px;
      background: rgba(255,255,255,.05);
      color: #fff0bd;
      font-size: 20px;
      font-weight: 900;
      text-align: center;
    }

    .loading { opacity: .65; }

    @media (max-width: 1220px) {
      .topbar { grid-template-columns: 160px 1fr; }
      .memo, .top-actions { display: none; }
      .board { grid-template-columns: 310px 1fr; }
      .right { grid-column: 1 / -1; grid-template-columns: repeat(3, 1fr); }
      .blueprint { grid-template-columns: 1fr; }
    }

    @media (max-width: 820px) {
      .app { width: 100%; margin: 0; }
      .topbar {
        border-radius: 0;
        border-left: 0;
        border-right: 0;
        grid-template-columns: 1fr;
        text-align: center;
      }
      .top-left { justify-content: center; }
      .board { grid-template-columns: 1fr; padding: 12px; border-radius: 0; }
      .chat { min-height: 680px; }
      .right { grid-template-columns: 1fr; }
      .schema { grid-template-columns: 1fr; }
      .messages, .choices, .composer, .save-line, .chat-head { padding-left: 24px; padding-right: 18px; }
      .chat::before { display: none; }
      .bubble { max-width: 86%; }
    }
  </style>
</head>
<body>
  <main class="app">
    <header class="topbar">
      <div class="top-left">
        <button class="hamburger" title="메뉴">☰</button>
        <div class="badge">N/B</div>
      </div>
      <div class="brand">
        <h1>N/B 이야기 교실</h1>
        <p>AI가 이끄는 이야기형 채팅방</p>
      </div>
      <div class="memo">이야기를 기억하고,<br>다음 장면으로 이어가는<br>N/B 기반 대화 공간</div>
      <nav class="top-actions" aria-label="주요 메뉴">
        <button class="nav-btn" title="이야기 저장소"><span>▤</span><span>이야기 저장소</span></button>
        <button class="nav-btn" title="설정"><span>⚙</span><span>설정</span></button>
      </nav>
    </header>

    <section class="board">
      <aside class="left">
        <section class="panel teacher">
          <h2 class="title">+ AI 담임 (AI 방장)</h2>
          <div class="robot-area">
            <div class="robot" aria-hidden="true">
              <span class="eye left-eye"></span><span class="eye right-eye"></span><span class="smile"></span><span class="body"></span>
            </div>
            <div class="speech">안녕하세요!<br>AI 담임입니다.<br>오늘도 좋은<br>이야기 기대해요.</div>
          </div>
          <div class="online">● ONLINE</div>
        </section>

        <section class="panel card">
          <h2 class="section-title">나의 방문자 카드</h2>
          <div class="profile">
            <div class="avatar">🙂</div>
            <dl>
              <dt>임시 닉네임</dt>
              <dd id="nickname">조용한 탐색자 027</dd>
              <dt>레벨</dt>
              <dd><span id="level" class="level">Lv.3 ★</span></dd>
              <dt>현재 상태</dt>
              <dd><span id="stateTag" class="tag">설계 방문자</span></dd>
            </dl>
          </div>
        </section>

        <section class="panel card">
          <h2 class="section-title">방문자 상태 (5단계)</h2>
          <div class="states" id="states">
            <div class="state"><span class="icon">●</span><span>낯선 방문자</span></div>
            <div class="state"><span class="icon">⌕</span><span>탐색 방문자</span></div>
            <div class="state"><span class="icon">?</span><span>질문 방문자</span></div>
            <div class="state active"><span class="icon">✎</span><span>설계 방문자</span><span>★</span></div>
            <div class="state"><span class="icon">♛</span><span>핵심 방문자</span></div>
          </div>
        </section>
      </aside>

      <section class="panel chat">
        <div class="chat-head">💬 대화 중</div>
        <div class="messages" id="messages">
          <div class="msg-row">
            <div class="mini-bot">🤖</div>
            <div class="bubble">AI가 먼저 인사합니다 😊
반가워요, 조용한 탐색자 027님!
지난 이야기를 바탕으로, 오늘은 어떤 이야기를 이어가 볼까요?<span class="time">오전 10:24</span></div>
          </div>
          <div class="msg-row user">
            <div class="bubble">임시 닉네임: 조용한 탐색자 027
현재 상태: 설계 방문자
레벨: Lv.3<span class="time">오전 10:24 ✓</span></div>
          </div>
          <div class="msg-row">
            <div class="mini-bot">🤖</div>
            <div class="bubble">좋아요! 아래 주제 중에서 오늘 함께 나눌 이야기를 선택해 주세요.<span class="time">오전 10:25</span></div>
          </div>
        </div>
        <div class="choices">
          <button class="choice" data-topic="N/B 소설형 데이터베이스 구조를 어떻게 구성할까요?">
            <span class="choice-icon">▣</span>
            <span><strong>1. 기억 저장소 설계</strong><small>N/B 소설형 데이터베이스 구조를 어떻게 구성할까요?</small></span>
          </button>
          <button class="choice" data-topic="5단계 방문자 상태와 역할을 더 구체화해볼까요?">
            <span class="choice-icon">♟</span>
            <span><strong>2. 방문자 역할 정리</strong><small>5단계 방문자 상태와 역할을 더 구체화해볼까요?</small></span>
          </button>
          <button class="choice" data-topic="다음 장면 예시와 대화 흐름을 함께 만들어볼까요?">
            <span class="choice-icon">▤</span>
            <span><strong>3. 다음 장면 구성</strong><small>다음 장면 예시와 대화 흐름을 함께 만들어볼까요?</small></span>
          </button>
        </div>
        <form class="composer" id="composer">
          <button class="icon-btn" type="button" title="첨부">⌕</button>
          <input id="messageInput" autocomplete="off" placeholder="메시지를 입력하세요..." maxlength="500">
          <button class="send-btn" title="전송">➤</button>
        </form>
        <div class="save-line">☁ 대화 후 요약이 저장되어 재방문 시 이어집니다.</div>
      </section>

      <aside class="right">
        <section class="panel note">
          <div class="note-header">
            <h2>📖 N/B 기억 노트</h2>
            <button class="summary-btn" id="refreshBtn">요약</button>
          </div>
          <div class="paper-box">
            <h3>이전 요약을 불러왔습니다 ✅</h3>
            <div class="paper-sheet" id="summary">지난번에는 AI가 방문자를 이야기처럼 기억하는 구조를 설계했습니다.</div>
          </div>
          <div class="paper-box">
            <h3>오늘 이어갈 수 있는 흐름</h3>
            <div class="flow-list">
              <div class="flow-item"><span>▣</span><span>1. 기억 저장소 설계</span><span>›</span></div>
              <div class="flow-item"><span>♟</span><span>2. 방문자 역할 정리</span><span>›</span></div>
              <div class="flow-item"><span>▤</span><span>3. 다음 장면 구성</span><span>›</span></div>
            </div>
          </div>
          <div class="paper-box">
            <h3>N/B 데이터베이스 기억 구조</h3>
            <div class="db-flow">
              <div class="db-node"><span class="db-icon">👤</span><span>방문자<br>(Visitor)</span></div>
              <div class="db-node"><span class="db-icon">💬</span><span>대화<br>(Conversation)</span></div>
              <div class="db-node"><span class="db-icon">📋</span><span>요약<br>(Summary)</span></div>
              <div class="db-node"><span class="db-icon">🏠</span><span>다음 장면<br>(Next Scene)</span></div>
            </div>
          </div>
          <div class="sticky">대화 후 요약 저장<br>재방문 시 이전 이야기에서 이어집니다 ✨</div>
        </section>
      </aside>

      <section class="blueprint" id="schema">
        <div>
          <h2>N/B 소설형 채팅방 데이터베이스 구조도</h2>
          <p>AI가 채팅방을 주도하고, 방문자를 기억하며, 이야기를 이어가는 N/B 기반 소설형 데이터 구조</p>
          <div class="schema">
            <div class="table-box"><h3>1) 캐릭터 테이블</h3><ul><li>character_id (PK)</li><li>nickname</li><li>level</li><li>status_type</li><li>N_value</li><li>visit_count</li></ul></div>
            <div class="table-box"><h3>2) 사건 테이블</h3><ul><li>event_id (PK)</li><li>character_id (FK)</li><li>event_summary</li><li>keywords</li><li>emotion</li><li>created_at</li></ul></div>
            <div class="table-box"><h3>3) 장면 테이블</h3><ul><li>scene_id (PK)</li><li>event_id (FK)</li><li>scene_summary</li><li>scene_status</li><li>next_scene_hint</li><li>N_value</li></ul></div>
            <div class="table-box"><h3>4) 관계 테이블</h3><ul><li>relation_id (PK)</li><li>target_type</li><li>relation_type</li><li>relation_value</li><li>memo</li><li>created_at</li></ul></div>
          </div>
        </div>
        <div class="process">
          <h3>AI 처리 흐름</h3>
          <ol>
            <li>방문자 입장 감지</li>
            <li>캐릭터 조회</li>
            <li>상태 분류</li>
            <li>장면 구성</li>
            <li>대화 진행</li>
            <li>사건 기록</li>
            <li>요약 저장</li>
            <li>다음 문장 설정</li>
          </ol>
        </div>
        <div class="quote">방문자는 데이터가 아니라 등장인물이고, 대화는 로그가 아니라 사건이다.</div>
      </section>
    </section>
  </main>

  <script>
    const messagesEl = document.getElementById("messages");
    const inputEl = document.getElementById("messageInput");
    const formEl = document.getElementById("composer");
    const summaryEl = document.getElementById("summary");
    const nicknameEl = document.getElementById("nickname");
    const levelEl = document.getElementById("level");
    const stateTagEl = document.getElementById("stateTag");

    const mainContext = [
      "N/B 이야기 교실 화면",
      "방문자는 데이터가 아니라 등장인물입니다.",
      "대화는 로그가 아니라 사건으로 저장됩니다.",
      "요약은 다음 장면의 기억이 됩니다."
    ].join("\\n");

    function timeLabel() {
      return new Date().toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" });
    }

    function addMessage(role, text) {
      const row = document.createElement("div");
      row.className = "msg-row" + (role === "user" ? " user" : "");
      if (role !== "user") {
        const avatar = document.createElement("div");
        avatar.className = "mini-bot";
        avatar.textContent = "🤖";
        row.appendChild(avatar);
      }
      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.textContent = text;
      const time = document.createElement("span");
      time.className = "time";
      time.textContent = timeLabel() + (role === "user" ? " ✓" : "");
      bubble.appendChild(time);
      row.appendChild(bubble);
      messagesEl.appendChild(row);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function safeText(value, fallback) {
      if (!value || /�|\?{2,}|諛|硫|湲|援/.test(String(value))) return fallback;
      return String(value);
    }

    function renderCharacter(character) {
      if (!character) return;
      nicknameEl.textContent = safeText(character.temporaryNickname || character.uniqueName, "조용한 탐색자 027");
      levelEl.textContent = safeText(character.level, "Lv.3") + " ★";
      const state = safeText(character.currentState || character.visitorType, "설계 방문자");
      stateTagEl.textContent = state;
      summaryEl.textContent = safeText(character.previousSceneSummary || character.currentStory, "지난번에는 AI가 방문자를 이야기처럼 기억하는 구조를 설계했습니다.");
    }

    async function loadMemory() {
      document.body.classList.add("loading");
      try {
        const response = await fetch("/api/narrative-memory");
        const data = await response.json();
        renderCharacter(data.character);
      } catch (error) {
        summaryEl.textContent = "기억 노트를 아직 불러오지 못했습니다. 대화를 시작하면 새 요약이 저장됩니다.";
      } finally {
        document.body.classList.remove("loading");
      }
    }

    async function askAi(userText) {
      const fallback = "좋아요. 이 대화는 하나의 사건으로 저장하고, 다음 장면에서는 기억 저장소와 방문자 상태를 연결해 이어가겠습니다.";
      try {
        const memory = await fetch("/api/narrative-memory").then((res) => res.json());
        const prompt = [
          "너는 N/B 이야기 교실의 AI 담임이다. 한국어로 3문장 이내로 답한다.",
          "방문자를 데이터가 아니라 등장인물로 대하고, 대화를 사건으로 정리한다.",
          memory.textForAi || "",
          "방문자 메시지: " + userText
        ].join("\\n\\n");

        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            messages: [{ role: "user", content: prompt }],
            options: { temperature: 0.35, num_predict: 220 }
          })
        });
        const data = await response.json();
        return data.ok && data.content ? data.content : fallback;
      } catch (error) {
        return fallback;
      }
    }

    async function saveMemory(userText, aiText) {
      const response = await fetch("/api/narrative-memory", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: userText, aiText, mainContext })
      });
      const data = await response.json();
      if (data.ok) renderCharacter(data.character);
      return data;
    }

    async function submitMessage(text) {
      const userText = text.trim();
      if (!userText) return;
      addMessage("user", userText);
      inputEl.value = "";
      addMessage("ai", "기억 저장소를 확인하고 다음 장면을 구성하는 중입니다...");
      const pending = messagesEl.lastElementChild;
      const aiText = await askAi(userText);
      pending.remove();
      addMessage("ai", aiText);
      try {
        const saved = await saveMemory(userText, aiText);
        if (saved.nextLine && saved.nextLine.line) {
          summaryEl.textContent = safeText(saved.nextLine.line, "다음 방문 시 이 장면에서 자연스럽게 이어집니다.");
        }
      } catch (error) {
        summaryEl.textContent = "대화는 진행됐지만 요약 저장에 실패했습니다: " + error.message;
      }
    }

    formEl.addEventListener("submit", (event) => {
      event.preventDefault();
      submitMessage(inputEl.value);
    });

    document.querySelectorAll(".choice").forEach((button) => {
      button.addEventListener("click", () => submitMessage(button.dataset.topic || button.textContent));
    });

    document.getElementById("refreshBtn").addEventListener("click", loadMemory);
    loadMemory();
  </script>
</body>
</html>`;
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = "";

    req.on("data", (chunk) => {
      body += chunk;
      if (Buffer.byteLength(body) > MAX_BODY_BYTES) {
        reject(new Error("Request body too large"));
        req.destroy();
      }
    });

    req.on("end", () => resolve(body));
    req.on("error", reject);
  });
}

function verifyAuth(req) {
  if (!API_TOKEN) return true;
  return req.headers.authorization === `Bearer ${API_TOKEN}`;
}

async function parseJsonBody(req) {
  const rawBody = await readBody(req);
  if (!rawBody.trim()) return {};
  return JSON.parse(rawBody);
}

function normalizeMessages(body) {
  if (Array.isArray(body.messages)) return body.messages;
  if (typeof body.prompt === "string") {
    return [{ role: "user", content: body.prompt }];
  }
  return [];
}

async function callOllamaChat({ model, messages, options }) {
  const response = await fetch(`${OLLAMA_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: model || DEFAULT_MODEL,
      stream: false,
      options: options || {
        temperature: 0.25,
        num_predict: 180
      },
      messages
    })
  });

  const text = await response.text();
  let payload = null;

  try {
    payload = text ? JSON.parse(text) : {};
  } catch {
    payload = { raw: text };
  }

  if (!response.ok) {
    const error = new Error("Ollama request failed");
    error.status = response.status;
    error.payload = payload;
    throw error;
  }

  return payload;
}

function extractOllamaText(data) {
  return data?.message?.content || data?.response || data?.content || data?.message?.thinking || "";
}

function decodeXmlEntities(text = "") {
  return text
    .replace(/<!\[CDATA\[(.*?)\]\]>/gs, "$1")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, "\"")
    .replace(/&#39;/g, "'")
    .replace(/&#(\d+);/g, (_, code) => String.fromCharCode(Number(code)));
}

function stripHtml(text = "") {
  return decodeXmlEntities(text)
    .replace(/<[^>]*>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function xmlTag(block, tagName) {
  const match = block.match(new RegExp(`<${tagName}[^>]*>([\\s\\S]*?)<\\/${tagName}>`, "i"));
  return match ? stripHtml(match[1]) : "";
}

function parseRssItems(xml, limit) {
  const itemBlocks = [...xml.matchAll(/<item\b[\s\S]*?<\/item>/gi)].map((match) => match[0]);

  return itemBlocks.slice(0, limit).map((block, index) => ({
    rank: index + 1,
    title: xmlTag(block, "title"),
    source: xmlTag(block, "source"),
    link: xmlTag(block, "link"),
    publishedAt: xmlTag(block, "pubDate"),
    summary: xmlTag(block, "description")
  }));
}

function buildIssueSearchText(query, items) {
  const lines = [
    `[이슈 검색 결과]`,
    `검색어: ${query}`,
    `검색 결과 수: ${items.length}`,
    ""
  ];

  items.forEach((item) => {
    lines.push(`${item.rank}. ${item.title}`);
    lines.push(`- 출처: ${item.source || "알 수 없음"}`);
    lines.push(`- 시간: ${item.publishedAt || "알 수 없음"}`);
    if (item.summary) lines.push(`- 요약: ${item.summary}`);
    if (item.link) lines.push(`- 링크: ${item.link}`);
    lines.push("");
  });

  lines.push(`[AI 분석 지시]`);
  lines.push(`위 검색 결과를 바탕으로 핵심 이슈, 반복되는 키워드, 서로 연결되는 사건, 확인이 필요한 위험 신호를 한국어로 정리한다.`);

  return lines.join("\n");
}

async function searchGoogleNews(query, limit = NEWS_SEARCH_LIMIT) {
  const url = new URL("https://news.google.com/rss/search");
  url.searchParams.set("q", query);
  url.searchParams.set("hl", "ko");
  url.searchParams.set("gl", "KR");
  url.searchParams.set("ceid", "KR:ko");

  const response = await fetch(url, {
    headers: {
      "User-Agent": "Mozilla/5.0 ChamsosikIssueBot/1.0"
    }
  });

  if (!response.ok) {
    const error = new Error(`news search failed: ${response.status}`);
    error.status = response.status;
    throw error;
  }

  const xml = await response.text();
  return parseRssItems(xml, limit);
}

async function handleIssueSearch(req, res, url) {
  if (!verifyAuth(req)) {
    sendJson(res, 401, { ok: false, error: "Unauthorized" });
    return;
  }

  try {
    let query = url.searchParams.get("q") || url.searchParams.get("query") || "";
    let limit = Number(url.searchParams.get("limit") || NEWS_SEARCH_LIMIT);

    if (req.method === "POST") {
      const body = await parseJsonBody(req);
      query = body.query || body.q || query;
      limit = Number(body.limit || limit);
    }

    query = String(query || "").trim();
    limit = Math.max(1, Math.min(Number.isFinite(limit) ? limit : NEWS_SEARCH_LIMIT, 20));

    if (!query) {
      sendJson(res, 400, { ok: false, error: "query is required" });
      return;
    }

    const items = await searchGoogleNews(query, limit);
    const text = buildIssueSearchText(query, items);

    sendJson(res, 200, {
      ok: true,
      query,
      source: "google-news-rss",
      count: items.length,
      items,
      text
    });
  } catch (error) {
    sendJson(res, error.status || 500, {
      ok: false,
      error: error.message
    });
  }
}

async function handleNarrativeMemory(req, res, url) {
  if (!verifyAuth(req)) {
    sendJson(res, 401, { ok: false, error: "Unauthorized" });
    return;
  }

  try {
    const visitor = touchVisitor(req);

    if (req.method === "GET") {
      const memory = readNarrativeMemory();
      const characterId = url.searchParams.get("characterId") || visitor.id;
      const character = memory.characters[characterId] || null;
      sendJson(res, 200, {
        ok: true,
        visitor,
        memory,
        character,
        textForAi: character ? buildNarrativeText(memory, character) : ""
      });
      return;
    }

    const body = await parseJsonBody(req);
    const text = String(body.text || body.userText || "").trim();
    const aiText = String(body.aiText || body.response || "").trim();
    const mainContext = String(body.mainContext || "").trim();

    if (!text && !aiText && !mainContext) {
      sendJson(res, 400, { ok: false, error: "text, aiText, or mainContext is required" });
      return;
    }

    const result = upsertNarrativeMemory({
      visitor,
      text,
      aiText,
      mainContext
    });

    sendJson(res, 200, {
      ok: true,
      visitor,
      character: result.character,
      event: result.event,
      scene: result.scene,
      nextLine: result.nextLine,
      textForAi: result.textForAi
    });
  } catch (error) {
    sendJson(res, 500, { ok: false, error: error.message });
  }
}

async function handleChat(req, res) {
  if (!verifyAuth(req)) {
    sendJson(res, 401, { ok: false, error: "Unauthorized" });
    return;
  }

  try {
    const body = await parseJsonBody(req);
    const messages = normalizeMessages(body);

    if (!messages.length) {
      sendJson(res, 400, { ok: false, error: "messages or prompt is required" });
      return;
    }

    const data = await callOllamaChat({
      model: body.model,
      messages,
      options: body.options
    });

    sendJson(res, 200, {
      ok: true,
      model: body.model || DEFAULT_MODEL,
      content: extractOllamaText(data),
      raw: data
    });
  } catch (error) {
    sendJson(res, error.status || 500, {
      ok: false,
      error: error.message,
      detail: error.payload || null
    });
  }
}

function buildGameAdviceMessages(snapshot) {
  return [
    {
      role: "system",
      content: [
        "You are a fast tactical advisor for an arcade carrier command game.",
        "Answer in Korean.",
        "Keep it under 3 short lines.",
        "Recommend exactly one command id and explain why."
      ].join(" ")
    },
    {
      role: "user",
      content: JSON.stringify(snapshot || {})
    }
  ];
}

async function handleGameAdvice(req, res) {
  if (!verifyAuth(req)) {
    sendJson(res, 401, { ok: false, error: "Unauthorized" });
    return;
  }

  try {
    const body = await parseJsonBody(req);
    const data = await callOllamaChat({
      model: body.model,
      messages: buildGameAdviceMessages(body.snapshot),
      options: body.options || {
        temperature: 0.2,
        num_predict: 140
      }
    });

    sendJson(res, 200, {
      ok: true,
      model: body.model || DEFAULT_MODEL,
      content: extractOllamaText(data),
      raw: data
    });
  } catch (error) {
    sendJson(res, error.status || 500, {
      ok: false,
      error: error.message,
      detail: error.payload || null
    });
  }
}

async function handleHealth(res) {
  let ollama = "unreachable";

  try {
    const response = await fetch(`${OLLAMA_URL}/api/tags`);
    ollama = response.ok ? "ok" : `error:${response.status}`;
  } catch (error) {
    ollama = error.message;
  }

  sendJson(res, 200, {
    ok: true,
    server: "ollama-ai-server",
    ollama,
    ollamaUrl: OLLAMA_URL,
    defaultModel: DEFAULT_MODEL,
    authEnabled: Boolean(API_TOKEN)
  });
}

async function handleVisitorRoom(req, res) {
  if (!verifyAuth(req)) {
    sendJson(res, 401, { ok: false, error: "Unauthorized" });
    return;
  }

  const visitor = touchVisitor(req);
  const nowMs = Date.now();
  const activeVisitors = [...visitors.values()]
    .filter((item) => nowMs - Date.parse(item.lastSeen) < 5 * 60 * 1000)
    .sort((a, b) => Date.parse(b.lastSeen) - Date.parse(a.lastSeen));

  if (req.method === "GET") {
    sendJson(res, 200, {
      ok: true,
      visitor,
      visitors: activeVisitors,
      messages: issueRoomMessages.slice(-80)
    });
    return;
  }

  try {
    const body = await parseJsonBody(req);
    const text = String(body.text || "").trim().slice(0, 800);
    if (!text) {
      sendJson(res, 400, { ok: false, error: "text is required" });
      return;
    }

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      visitorId: visitor.id,
      maskedIp: visitor.maskedIp,
      text,
      createdAt: new Date().toISOString()
    };
    issueRoomMessages.push(userMessage);

    try {
      const data = await callOllamaChat({
        model: body.model || DEFAULT_MODEL,
        messages: [
          {
            role: "system",
            content: "너는 참소식.com의 공개 이슈 분석 채팅방 AI다. 방문자가 올린 이슈 메시지를 한국어로 짧게 분석하라. 핵심 요약, 연결 키워드, 다음 확인 질문을 포함하라."
          },
          {
            role: "user",
            content: text
          }
        ],
        options: body.options || {
          temperature: 0.35,
          num_predict: 260
        }
      });

      issueRoomMessages.push({
        id: crypto.randomUUID(),
        role: "ai",
        visitorId: "AI-Analyst",
        maskedIp: "server",
        text: extractOllamaText(data) || "분석 응답이 비어 있습니다.",
        createdAt: new Date().toISOString(),
        replyTo: userMessage.id
      });
    } catch (error) {
      issueRoomMessages.push({
        id: crypto.randomUUID(),
        role: "ai",
        visitorId: "AI-Analyst",
        maskedIp: "server",
        text: `AI 분석 실패: ${error.message}`,
        createdAt: new Date().toISOString(),
        replyTo: userMessage.id
      });
    }

    while (issueRoomMessages.length > 200) issueRoomMessages.shift();

    sendJson(res, 200, {
      ok: true,
      visitor,
      visitors: activeVisitors,
      messages: issueRoomMessages.slice(-80)
    });
  } catch (error) {
    sendJson(res, 500, { ok: false, error: error.message });
  }
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);

  if (req.method === "OPTIONS") {
    sendJson(res, 204, {});
    return;
  }

  if (url.pathname === "/health" && req.method === "GET") {
    handleHealth(res);
    return;
  }

  if ((url.pathname === "/" || url.pathname === "/nb-classroom") && req.method === "GET") {
    sendHtml(res, nbClassroomHtml());
    return;
  }

  if (url.pathname === "/api/chat" && req.method === "POST") {
    handleChat(req, res);
    return;
  }

  if (url.pathname === "/api/game-ai-advice" && req.method === "POST") {
    handleGameAdvice(req, res);
    return;
  }

  if (url.pathname === "/api/issue-search" && (req.method === "GET" || req.method === "POST")) {
    handleIssueSearch(req, res, url);
    return;
  }

  if (url.pathname === "/api/narrative-memory" && (req.method === "GET" || req.method === "POST")) {
    handleNarrativeMemory(req, res, url);
    return;
  }

  if (url.pathname === "/api/visitor-room" && (req.method === "GET" || req.method === "POST")) {
    handleVisitorRoom(req, res);
    return;
  }

  sendJson(res, 404, {
    ok: false,
    error: "Not found",
    routes: ["GET /health", "POST /api/chat", "POST /api/game-ai-advice", "GET|POST /api/issue-search", "GET|POST /api/narrative-memory", "GET|POST /api/visitor-room"]
  });
});

server.listen(PORT, HOST, () => {
  console.log(`Ollama AI server listening on http://${HOST}:${PORT}`);
  console.log(`Ollama target: ${OLLAMA_URL}`);
  console.log(`Default model: ${DEFAULT_MODEL}`);
  console.log(`Auth: ${API_TOKEN ? "enabled" : "disabled"}`);
});
