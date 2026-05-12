const http = require("http");
const fs = require("fs");
const path = require("path");

const HOST = "127.0.0.1";
const PORT = process.env.PORT || 3210;
const ROOT = __dirname;
const WORLD_MONITOR_URL = "https://xn--9l4b4xi9r.com/world-monitor-ai.json";
const OLLAMA_URL = "http://127.0.0.1:11434/api/generate";
const OLLAMA_MODEL = "deepseek-v3.1:671b-cloud";

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".ico": "image/x-icon",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".svg": "image/svg+xml"
};

function sendJson(res, statusCode, payload) {
  res.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store"
  });
  res.end(JSON.stringify(payload, null, 2));
}

function sendText(res, statusCode, text) {
  res.writeHead(statusCode, { "Content-Type": "text/plain; charset=utf-8" });
  res.end(text);
}

function safePathname(urlPath) {
  const pathname = urlPath === "/" ? "/index.html" : urlPath;
  const normalized = path.normalize(pathname).replace(/^(\.\.[/\\])+/, "");
  const target = path.join(ROOT, normalized);
  return target.startsWith(ROOT) ? target : null;
}

async function readBody(req) {
  const chunks = [];
  for await (const chunk of req) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
}

async function handleWorldMonitor(res) {
  try {
    const upstream = await fetch(WORLD_MONITOR_URL);
    const text = await upstream.text();
    res.writeHead(upstream.status, {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store"
    });
    res.end(text);
  } catch (error) {
    sendJson(res, 502, {
      success: false,
      error: `world monitor fetch failed: ${error.message}`
    });
  }
}

async function handleOllama(req, res) {
  try {
    const raw = await readBody(req);
    const payload = raw ? JSON.parse(raw) : {};
    const prompt = typeof payload.prompt === "string" ? payload.prompt.trim() : "";

    if (!prompt) {
      sendJson(res, 400, { success: false, error: "prompt is required" });
      return;
    }

    const upstream = await fetch(OLLAMA_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: OLLAMA_MODEL,
        prompt,
        stream: false
      })
    });

    const text = await upstream.text();
    res.writeHead(upstream.status, {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store"
    });
    res.end(text);
  } catch (error) {
    sendJson(res, 502, {
      success: false,
      error: `ollama proxy failed: ${error.message}`
    });
  }
}

function handleStatic(req, res) {
  const pathname = req.url.split("?")[0];
  const target = safePathname(decodeURIComponent(pathname));
  if (!target) {
    sendText(res, 403, "Forbidden");
    return;
  }

  fs.stat(target, (statError, stats) => {
    if (statError || !stats.isFile()) {
      sendText(res, 404, "Not found");
      return;
    }

    const ext = path.extname(target).toLowerCase();
    const type = MIME_TYPES[ext] || "application/octet-stream";
    res.writeHead(200, { "Content-Type": type });
    fs.createReadStream(target).pipe(res);
  });
}

const server = http.createServer(async (req, res) => {
  if (!req.url) {
    sendText(res, 400, "Bad request");
    return;
  }

  if (req.method === "GET" && req.url.startsWith("/api/world-monitor")) {
    await handleWorldMonitor(res);
    return;
  }

  if (req.method === "POST" && req.url.startsWith("/api/ollama-scene")) {
    await handleOllama(req, res);
    return;
  }

  if (req.method === "GET" && req.url.startsWith("/api/health")) {
    sendJson(res, 200, {
      success: true,
      port: PORT,
      world_monitor_url: WORLD_MONITOR_URL,
      ollama_model: OLLAMA_MODEL
    });
    return;
  }

  if (req.method === "GET") {
    handleStatic(req, res);
    return;
  }

  sendText(res, 405, "Method not allowed");
});

server.listen(PORT, HOST, () => {
  console.log(`fictionAI server running at http://${HOST}:${PORT}`);
});
