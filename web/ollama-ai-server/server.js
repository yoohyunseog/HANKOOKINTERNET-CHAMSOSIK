const http = require("http");
const crypto = require("crypto");

const HOST = process.env.HOST || "0.0.0.0";
const PORT = Number(process.env.PORT || 3110);
const OLLAMA_URL = (process.env.OLLAMA_URL || "http://127.0.0.1:11434").replace(/\/$/, "");
const DEFAULT_MODEL = process.env.OLLAMA_MODEL || "kimi-k2.6:cloud";
const API_TOKEN = process.env.OLLAMA_PROXY_TOKEN || "";
const ALLOWED_ORIGIN = process.env.ALLOWED_ORIGIN || "*";
const MAX_BODY_BYTES = Number(process.env.MAX_BODY_BYTES || 1_000_000);
const NEWS_SEARCH_LIMIT = Number(process.env.NEWS_SEARCH_LIMIT || 10);
const roomMessages = [];
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
      messages: roomMessages.slice(-80)
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

    roomMessages.push({
      id: crypto.randomUUID(),
      visitorId: visitor.id,
      maskedIp: visitor.maskedIp,
      text,
      createdAt: new Date().toISOString()
    });

    while (roomMessages.length > 200) roomMessages.shift();

    sendJson(res, 200, {
      ok: true,
      visitor,
      messages: roomMessages.slice(-80)
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

  if (url.pathname === "/api/visitor-room" && (req.method === "GET" || req.method === "POST")) {
    handleVisitorRoom(req, res);
    return;
  }

  sendJson(res, 404, {
    ok: false,
    error: "Not found",
    routes: ["GET /health", "POST /api/chat", "POST /api/game-ai-advice", "GET|POST /api/issue-search", "GET|POST /api/visitor-room"]
  });
});

server.listen(PORT, HOST, () => {
  console.log(`Ollama AI server listening on http://${HOST}:${PORT}`);
  console.log(`Ollama target: ${OLLAMA_URL}`);
  console.log(`Default model: ${DEFAULT_MODEL}`);
  console.log(`Auth: ${API_TOKEN ? "enabled" : "disabled"}`);
});
