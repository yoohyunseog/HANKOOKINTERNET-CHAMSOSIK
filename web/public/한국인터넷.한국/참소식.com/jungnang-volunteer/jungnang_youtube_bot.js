const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const OUTPUT_FILE = path.join(__dirname, "jungnang-youtube.json");
const DEFAULT_INTERVAL_SECONDS = 600;
const RECENT_DAYS = 14;
const MAX_RESULTS_PER_QUERY = 10;
const MAX_OUTPUT_ITEMS = 24;
const AUTO_UPLOAD_JSON = process.env.AUTO_UPLOAD_JSON !== "0";
const UPLOAD_SERVER = process.env.JUNGNANG_UPLOAD_SERVER || "root@211.45.162.155";
const REMOTE_ROOT = process.env.JUNGNANG_REMOTE_ROOT || "/var/www/chamsosik";
const REMOTE_DIR = `${REMOTE_ROOT}/jungnang-volunteer`;
const REMOTE_FILE = `${REMOTE_DIR}/jungnang-youtube.json`;
const REMOTE_TMP_FILE = "/tmp/jungnang-youtube.json";
const QUERIES = [
  "중랑구 자원봉사 행사",
  "중랑구 자원봉사 모집",
  "중랑구 봉사활동",
  "중랑구 지역 행사",
  "중랑구청 자원봉사",
  "중랑구 행사"
];

function nowKst() {
  const date = new Date(Date.now() + 9 * 60 * 60 * 1000);
  return date.toISOString().replace("Z", "+09:00");
}

function youtubeSearchUrl(query) {
  return `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`;
}

function thumbnailFor(videoId) {
  return videoId ? `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg` : "";
}

function compactText(value, maxLength = 180) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 3).trim()}...`;
}

function parseUploadAgeDays(label) {
  const text = String(label || "").trim().toLowerCase();
  if (!text) return Number.POSITIVE_INFINITY;
  if (/(방금|오늘|now|just now|hour|hours|시간|minute|minutes|분|초)/i.test(text)) return 0;

  const match = text.match(/(\d+)\s*(일|day|days|주|week|weeks|개월|month|months|년|year|years)/i);
  if (!match) return Number.POSITIVE_INFINITY;

  const value = Number(match[1]);
  const unit = match[2];
  if (/일|day/.test(unit)) return value;
  if (/주|week/.test(unit)) return value * 7;
  if (/개월|month/.test(unit)) return value * 30;
  if (/년|year/.test(unit)) return value * 365;
  return Number.POSITIVE_INFINITY;
}

function classifyUpload(item) {
  const ageDays = parseUploadAgeDays(item.publishedAt);
  if (ageDays <= RECENT_DAYS) {
    return {
      include: true,
      status: ageDays <= 7 ? "최근 1주 영상" : "최근 2주 영상",
      uploadAgeDays: ageDays,
      reason: `업로드 ${RECENT_DAYS}일 이내`
    };
  }

  return {
    include: false,
    status: "최근 영상 제외",
    uploadAgeDays: Number.isFinite(ageDays) ? ageDays : null,
    reason: item.publishedAt ? `업로드 ${item.publishedAt}` : "업로드 시점 확인 불가"
  };
}

function findVideoRenderers(value, results = []) {
  if (!value || results.length >= MAX_RESULTS_PER_QUERY) return results;
  if (Array.isArray(value)) {
    for (const item of value) findVideoRenderers(item, results);
    return results;
  }
  if (typeof value !== "object") return results;
  if (value.videoRenderer) {
    results.push(value.videoRenderer);
    return results;
  }
  for (const child of Object.values(value)) findVideoRenderers(child, results);
  return results;
}

function textFromRuns(node) {
  if (!node) return "";
  if (node.simpleText) return node.simpleText;
  if (Array.isArray(node.runs)) return node.runs.map((run) => run.text || "").join("");
  return "";
}

function parseInitialData(html) {
  const marker = "var ytInitialData = ";
  const start = html.indexOf(marker);
  if (start < 0) throw new Error("ytInitialData not found");
  let index = start + marker.length;
  let depth = 0;
  let inString = false;
  let escaped = false;

  for (; index < html.length; index += 1) {
    const char = html[index];
    if (inString) {
      if (escaped) escaped = false;
      else if (char === "\\") escaped = true;
      else if (char === "\"") inString = false;
      continue;
    }
    if (char === "\"") inString = true;
    else if (char === "{") depth += 1;
    else if (char === "}") {
      depth -= 1;
      if (depth === 0) return JSON.parse(html.slice(start + marker.length, index + 1));
    }
  }
  throw new Error("ytInitialData parse failed");
}

async function fetchYoutubeResults(query) {
  const response = await fetch(youtubeSearchUrl(query), {
    headers: {
      "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
      "accept-language": "ko-KR,ko;q=0.9,en-US;q=0.8"
    }
  });
  if (!response.ok) throw new Error(`YouTube ${response.status}`);
  const html = await response.text();
  const data = parseInitialData(html);

  return findVideoRenderers(data).slice(0, MAX_RESULTS_PER_QUERY).map((video) => {
    const videoId = video.videoId || "";
    const title = textFromRuns(video.title) || `${query} 검색 결과`;
    const channel = textFromRuns(video.ownerText) || textFromRuns(video.shortBylineText) || "YouTube";
    const publishedAt = textFromRuns(video.publishedTimeText);
    const duration = textFromRuns(video.lengthText);
    const summary = textFromRuns(video.detailedMetadataSnippets?.[0]?.snippetText)
      || textFromRuns(video.descriptionSnippet)
      || "중랑구 자원봉사·지역 행사 관련 유튜브 검색 결과입니다.";

    const item = {
      id: videoId || `${query}:${title}`,
      title: compactText(title, 120),
      url: videoId ? `https://www.youtube.com/watch?v=${videoId}` : youtubeSearchUrl(query),
      channel: compactText(channel, 80),
      publishedAt,
      duration,
      thumbnail: thumbnailFor(videoId),
      query,
      summary: compactText(summary)
    };
    return { ...item, ...classifyUpload(item) };
  });
}

function fallbackItems(errorText) {
  return QUERIES.map((query, index) => ({
    id: `fallback-${index + 1}`,
    title: `${query} 최근 2주 유튜브 검색`,
    url: youtubeSearchUrl(`${query} 최근`),
    channel: "YouTube 검색",
    publishedAt: "",
    duration: "",
    thumbnail: "",
    query,
    summary: "자동 수집이 실패했을 때 최근 1~2주 영상만 직접 확인할 수 있는 검색 링크입니다.",
    status: "검색 링크",
    uploadAgeDays: null,
    scheduleFilter: "최근 14일 영상 검색",
    error: errorText
  }));
}

async function collect() {
  const errors = [];
  const excluded = [];
  const items = [];
  const seen = new Set();

  for (const query of QUERIES) {
    try {
      const results = await fetchYoutubeResults(query);
      for (const item of results) {
        const key = item.id || item.url || item.title;
        if (!key || seen.has(key)) continue;
        seen.add(key);
        if (item.include) {
          const { include, reason, ...publicItem } = item;
          items.push({ ...publicItem, scheduleFilter: reason });
        } else {
          excluded.push({
            title: item.title,
            query: item.query,
            publishedAt: item.publishedAt,
            uploadAgeDays: item.uploadAgeDays,
            status: item.status,
            reason: item.reason
          });
        }
      }
    } catch (error) {
      errors.push(`${query}: ${error.message}`);
    }
  }

  const finalItems = items.length ? items : fallbackItems(errors.join("; ") || "최근 14일 영상 결과 없음");
  return {
    ok: true,
    topic: "중랑구 자원봉사·지역 행사 유튜브 정리",
    filter: "최근 1~2주 이내 업로드 영상만 표시",
    recentDays: RECENT_DAYS,
    updatedAt: nowKst(),
    intervalSeconds: DEFAULT_INTERVAL_SECONDS,
    queries: QUERIES,
    count: finalItems.length,
    items: finalItems.slice(0, MAX_OUTPUT_ITEMS),
    excludedCount: excluded.length,
    excluded: excluded.slice(0, 30),
    errors
  };
}

function writeJson(payload) {
  const tempFile = `${OUTPUT_FILE}.tmp`;
  fs.writeFileSync(tempFile, JSON.stringify(payload, null, 2), "utf8");
  fs.renameSync(tempFile, OUTPUT_FILE);
}

function runUploadCommand(command, args) {
  const result = spawnSync(command, args, {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"]
  });
  if (result.status !== 0) {
    const detail = (result.stderr || result.stdout || "").trim();
    throw new Error(`${command} failed${detail ? `: ${detail}` : ""}`);
  }
}

function uploadJsonToServer() {
  if (!AUTO_UPLOAD_JSON) {
    console.log("[upload] skipped: AUTO_UPLOAD_JSON=0");
    return;
  }

  runUploadCommand("scp", [OUTPUT_FILE, `${UPLOAD_SERVER}:${REMOTE_TMP_FILE}`]);
  runUploadCommand("ssh", [
    UPLOAD_SERVER,
    `sudo mkdir -p ${REMOTE_DIR} && sudo mv ${REMOTE_TMP_FILE} ${REMOTE_FILE} && sudo chmod 644 ${REMOTE_FILE}`
  ]);
  console.log(`[upload] ${REMOTE_FILE}`);
}

async function runOnce() {
  const payload = await collect();
  writeJson(payload);
  console.log(`[${payload.updatedAt}] saved ${OUTPUT_FILE} (${payload.count} items, excluded ${payload.excludedCount || 0})`);
  try {
    uploadJsonToServer();
  } catch (error) {
    console.error(`[upload failed] ${error.message}`);
  }
}

async function main() {
  const loop = process.argv.includes("--loop");
  const intervalIndex = process.argv.indexOf("--interval");
  const intervalSeconds = intervalIndex >= 0
    ? Number(process.argv[intervalIndex + 1] || DEFAULT_INTERVAL_SECONDS)
    : DEFAULT_INTERVAL_SECONDS;

  do {
    await runOnce();
    if (!loop) break;
    await new Promise((resolve) => setTimeout(resolve, Math.max(30, intervalSeconds) * 1000));
  } while (true);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
