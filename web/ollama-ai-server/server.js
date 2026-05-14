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
