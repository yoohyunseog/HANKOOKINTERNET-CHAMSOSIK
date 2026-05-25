const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const OUTPUT_FILE = path.join(__dirname, "pc-parts-raw.json");
const DEFAULT_INTERVAL_SECONDS = 1800;
const SEARCH_ENGINE = process.env.PC_PARTS_SEARCH_ENGINE || "danawa";

const targets = [
  {
    id: "cpu-ryzen-5-9600",
    category: "CPU",
    query: "AMD Ryzen 5 9600 가격",
    name: "AMD Ryzen 5 9600",
    maker: "AMD",
    platform: "AM5",
    fallbackPriceKrw: 280000,
    performance: 78,
    powerWatts: 65,
    speedLabel: "최대 부스트 약 5.2GHz",
    tags: ["gaming", "office", "upgrade"],
    notes: "Chrome 검색 수집 기준으로 가격을 확인하는 AM5 CPU 후보입니다."
  },
  {
    id: "cpu-ryzen-7-9700x",
    category: "CPU",
    query: "AMD Ryzen 7 9700X 가격",
    name: "AMD Ryzen 7 9700X",
    maker: "AMD",
    platform: "AM5",
    fallbackPriceKrw: 430000,
    performance: 88,
    powerWatts: 65,
    speedLabel: "최대 부스트 약 5.5GHz",
    tags: ["gaming", "creator", "quiet"],
    notes: "Chrome 검색 수집 기준으로 가격을 확인하는 고효율 작업용 CPU 후보입니다."
  },
  {
    id: "cpu-core-ultra-5-245k",
    category: "CPU",
    query: "Intel Core Ultra 5 245K 가격",
    name: "Intel Core Ultra 5 245K",
    maker: "Intel",
    platform: "LGA1851",
    fallbackPriceKrw: 390000,
    performance: 82,
    powerWatts: 125,
    speedLabel: "최대 터보 약 5.2GHz",
    tags: ["gaming", "creator"],
    notes: "Chrome 검색 수집 기준으로 가격을 확인하는 인텔 플랫폼 CPU 후보입니다."
  },
  {
    id: "gpu-rtx-5060-ti",
    category: "GPU",
    query: "NVIDIA GeForce RTX 5060 Ti 16GB 가격",
    name: "NVIDIA GeForce RTX 5060 Ti",
    maker: "NVIDIA",
    platform: "PCIe",
    fallbackPriceKrw: 620000,
    performance: 82,
    powerWatts: 180,
    vramGb: 16,
    speedLabel: "16GB VRAM / PCIe 그래픽",
    tags: ["gaming", "ai", "creator"],
    notes: "Chrome 검색 수집 기준으로 가격을 확인하는 AI/게임 겸용 GPU 후보입니다."
  },
  {
    id: "gpu-rtx-5070",
    category: "GPU",
    query: "NVIDIA GeForce RTX 5070 가격",
    name: "NVIDIA GeForce RTX 5070",
    maker: "NVIDIA",
    platform: "PCIe",
    fallbackPriceKrw: 880000,
    performance: 93,
    powerWatts: 250,
    vramGb: 12,
    speedLabel: "12GB VRAM / 고성능 GPU",
    tags: ["gaming", "ai", "creator"],
    notes: "Chrome 검색 수집 기준으로 가격을 확인하는 고성능 GPU 후보입니다."
  },
  {
    id: "gpu-rx-9060-xt",
    category: "GPU",
    query: "AMD Radeon RX 9060 XT 16GB 가격",
    name: "AMD Radeon RX 9060 XT",
    maker: "AMD",
    platform: "PCIe",
    fallbackPriceKrw: 520000,
    performance: 78,
    powerWatts: 170,
    vramGb: 16,
    speedLabel: "16GB VRAM / PCIe 그래픽",
    tags: ["gaming", "value"],
    notes: "Chrome 검색 수집 기준으로 가격을 확인하는 가성비 GPU 후보입니다."
  },
  {
    id: "ram-ddr5-32-6000",
    category: "RAM",
    query: "DDR5 32GB 6000MHz 가격",
    name: "DDR5 32GB 6000MHz",
    maker: "Common",
    platform: "DDR5",
    fallbackPriceKrw: 140000,
    performance: 78,
    powerWatts: 12,
    speedLabel: "DDR5-6000",
    tags: ["gaming", "creator", "office"],
    notes: "Chrome 검색 수집 기준으로 가격을 확인하는 기본 메모리 후보입니다."
  },
  {
    id: "ram-ddr5-64-6000",
    category: "RAM",
    query: "DDR5 64GB 6000MHz 가격",
    name: "DDR5 64GB 6000MHz",
    maker: "Common",
    platform: "DDR5",
    fallbackPriceKrw: 260000,
    performance: 88,
    powerWatts: 18,
    speedLabel: "DDR5-6000",
    tags: ["creator", "ai"],
    notes: "Chrome 검색 수집 기준으로 가격을 확인하는 작업용 대용량 메모리 후보입니다."
  },
  {
    id: "ssd-nvme-1tb-gen4",
    category: "SSD",
    query: "NVMe Gen4 SSD 1TB 가격",
    name: "NVMe Gen4 SSD 1TB",
    maker: "Common",
    platform: "M.2",
    fallbackPriceKrw: 110000,
    performance: 76,
    powerWatts: 6,
    speedLabel: "순차 읽기 약 5,000MB/s급",
    tags: ["gaming", "office"],
    notes: "Chrome 검색 수집 기준으로 가격을 확인하는 기본 저장장치 후보입니다."
  },
  {
    id: "ssd-nvme-2tb-gen4",
    category: "SSD",
    query: "NVMe Gen4 SSD 2TB 가격",
    name: "NVMe Gen4 SSD 2TB",
    maker: "Common",
    platform: "M.2",
    fallbackPriceKrw: 190000,
    performance: 84,
    powerWatts: 7,
    speedLabel: "순차 읽기 약 7,000MB/s급",
    tags: ["gaming", "creator", "ai"],
    notes: "Chrome 검색 수집 기준으로 가격을 확인하는 대용량 저장장치 후보입니다."
  },
  {
    id: "mb-am5-b850",
    category: "Mainboard",
    query: "AM5 B850 메인보드 가격",
    name: "AM5 B850 Mainboard",
    maker: "Common",
    platform: "AM5",
    fallbackPriceKrw: 210000,
    performance: 76,
    powerWatts: 12,
    speedLabel: "DDR5 / PCIe 5.0 지원급",
    tags: ["gaming", "office", "upgrade"],
    notes: "Chrome 검색 수집 기준으로 가격을 확인하는 AM5 메인보드 후보입니다."
  },
  {
    id: "mb-lga1851-b860",
    category: "Mainboard",
    query: "LGA1851 B860 메인보드 가격",
    name: "LGA1851 B860 Mainboard",
    maker: "Common",
    platform: "LGA1851",
    fallbackPriceKrw: 240000,
    performance: 75,
    powerWatts: 12,
    speedLabel: "DDR5 / PCIe 5.0 지원급",
    tags: ["gaming", "office"],
    notes: "Chrome 검색 수집 기준으로 가격을 확인하는 인텔 메인보드 후보입니다."
  },
  {
    id: "psu-650w-gold",
    category: "PSU",
    query: "650W 80PLUS Gold 파워 가격",
    name: "650W 80PLUS Gold PSU",
    maker: "Common",
    platform: "ATX",
    fallbackPriceKrw: 120000,
    performance: 74,
    powerWatts: 0,
    wattCapacity: 650,
    speedLabel: "650W 출력",
    tags: ["office", "gaming", "value"],
    notes: "Chrome 검색 수집 기준으로 가격을 확인하는 기본 파워 후보입니다."
  },
  {
    id: "psu-850w-gold",
    category: "PSU",
    query: "850W 80PLUS Gold 파워 가격",
    name: "850W 80PLUS Gold PSU",
    maker: "Common",
    platform: "ATX",
    fallbackPriceKrw: 180000,
    performance: 86,
    powerWatts: 0,
    wattCapacity: 850,
    speedLabel: "850W 출력",
    tags: ["gaming", "creator", "ai"],
    notes: "Chrome 검색 수집 기준으로 가격을 확인하는 고용량 파워 후보입니다."
  }
];

function nowKst() {
  return new Date(Date.now() + 9 * 60 * 60 * 1000).toISOString().replace("Z", "+09:00");
}

function candidateChromePaths() {
  const local = process.env.LOCALAPPDATA || "";
  const programFiles = process.env.PROGRAMFILES || "C:\\Program Files";
  const programFilesX86 = process.env["PROGRAMFILES(X86)"] || "C:\\Program Files (x86)";
  return [
    process.env.CHROME_PATH,
    path.join(programFiles, "Google", "Chrome", "Application", "chrome.exe"),
    path.join(programFilesX86, "Google", "Chrome", "Application", "chrome.exe"),
    path.join(local, "Google", "Chrome", "Application", "chrome.exe"),
    path.join(programFiles, "Microsoft", "Edge", "Application", "msedge.exe"),
    path.join(programFilesX86, "Microsoft", "Edge", "Application", "msedge.exe"),
    path.join(local, "Microsoft", "Edge", "Application", "msedge.exe")
  ].filter(Boolean);
}

function findChromeExecutable() {
  const found = candidateChromePaths().find((item) => fs.existsSync(item));
  if (!found) {
    throw new Error("Chrome 또는 Edge 실행 파일을 찾지 못했습니다. CHROME_PATH 환경변수로 chrome.exe 경로를 지정하세요.");
  }
  return found;
}

function searchUrl(query) {
  if (SEARCH_ENGINE === "danawa") {
    return `https://search.danawa.com/dsearch.php?k1=${encodeURIComponent(query)}`;
  }
  if (SEARCH_ENGINE === "naver") {
    return `https://search.shopping.naver.com/search/all?query=${encodeURIComponent(query)}`;
  }
  return `https://www.google.com/search?tbm=shop&q=${encodeURIComponent(query)}`;
}

function stripHtml(html) {
  return String(html || "")
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;|&#160;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ")
    .trim();
}

function extractPrices(text) {
  const prices = [];
  const patterns = [
    /([0-9]{1,3}(?:,[0-9]{3})+)\s*원/g,
    /([0-9]{5,8})\s*원/g
  ];

  for (const pattern of patterns) {
    let match;
    while ((match = pattern.exec(text)) !== null) {
      const value = Number(match[1].replace(/,/g, ""));
      if (value >= 10000 && value <= 5000000) prices.push(value);
    }
  }

  return Array.from(new Set(prices)).sort((a, b) => a - b).slice(0, 12);
}

function normalizeComparableText(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9가-힣]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function targetMatchTokens(target) {
  const normalized = normalizeComparableText(`${target.name} ${target.query} ${target.platform || ""}`);
  const genericTokens = new Set(["가격", "price", "common", "mainboard", "psu", "nvidia", "geforce", "amd", "intel"]);
  return Array.from(new Set(normalized.split(" ")))
    .filter((token) => token.length >= 2 && !genericTokens.has(token));
}

function textMatchesTarget(text, target) {
  const haystack = normalizeComparableText(text);
  const tokens = targetMatchTokens(target);
  if (!tokens.length) return true;

  const modelTokens = tokens.filter((token) => /\d/.test(token) || /^[a-z]+\d+[a-z]*$/i.test(token));
  const required = modelTokens.length ? modelTokens : tokens.slice(0, 3);
  const matched = required.filter((token) => haystack.includes(token));
  return matched.length >= Math.min(2, required.length);
}

function pickLikelyPrice(prices, target) {
  const fallback = target.fallbackPriceKrw;
  const min = Math.max(10000, Math.round(fallback * 0.55));
  const max = Math.round(fallback * 2.2);
  const plausible = prices.filter((price) => price >= min && price <= max);
  return plausible[0] || fallback;
}

function collectOne(chromePath, target) {
  const url = searchUrl(target.query);
  const result = spawnSync(chromePath, [
    "--headless=new",
    "--disable-gpu",
    "--no-first-run",
    "--disable-extensions",
    "--lang=ko-KR",
    "--virtual-time-budget=8000",
    "--dump-dom",
    url
  ], {
    encoding: "utf8",
    timeout: 45000,
    windowsHide: true
  });

  const html = result.stdout || "";
  const text = stripHtml(html);
  const prices = extractPrices(text);
  const matchedTarget = textMatchesTarget(text, target);
  const collectedPrice = prices.length && matchedTarget ? pickLikelyPrice(prices, target) : target.fallbackPriceKrw;
  const status = prices.length && matchedTarget && collectedPrice !== target.fallbackPriceKrw
    ? "chrome-collected"
    : (prices.length && !matchedTarget ? "name-price-mismatch-skipped" : "fallback-price");

  return {
    ...target,
    estimatedPriceKrw: collectedPrice,
    collectedPricesKrw: prices,
    fallbackPriceKrw: target.fallbackPriceKrw,
    sourceQuery: target.query,
    sourceUrl: url,
    sourceEngine: SEARCH_ENGINE,
    sourceStatus: status,
    targetMatched: matchedTarget,
    sourceError: result.status === 0 ? "" : (result.stderr || `Chrome exit ${result.status}`).trim(),
    collectedAt: nowKst()
  };
}

function writeJson(payload) {
  const tempFile = `${OUTPUT_FILE}.tmp`;
  fs.writeFileSync(tempFile, JSON.stringify(payload, null, 2), "utf8");
  fs.renameSync(tempFile, OUTPUT_FILE);
}

function collectAll() {
  const chromePath = findChromeExecutable();
  const parts = [];
  const errors = [];

  for (const target of targets) {
    try {
      const item = collectOne(chromePath, target);
      parts.push(item);
      console.log(`[collect] ${item.category} ${item.name} ${item.estimatedPriceKrw.toLocaleString("ko-KR")}원 (${item.sourceStatus})`);
    } catch (error) {
      errors.push(`${target.name}: ${error.message}`);
      parts.push({
        ...target,
        estimatedPriceKrw: target.fallbackPriceKrw,
        collectedPricesKrw: [],
        sourceQuery: target.query,
        sourceUrl: searchUrl(target.query),
        sourceEngine: SEARCH_ENGINE,
        sourceStatus: "collector-error",
        sourceError: error.message,
        collectedAt: nowKst()
      });
    }
  }

  return {
    ok: true,
    topic: "Chrome 기반 컴퓨터 부품 가격 수집 원본",
    collectedAt: nowKst(),
    chromePath,
    searchEngine: SEARCH_ENGINE,
    count: parts.length,
    parts,
    errors
  };
}

async function runOnce() {
  const payload = collectAll();
  writeJson(payload);
  console.log(`[pc-parts-collector] wrote ${OUTPUT_FILE}`);
  console.log(`[pc-parts-collector] parts=${payload.parts.length}, errors=${payload.errors.length}`);
}

async function run() {
  if (process.argv.includes("--dry-run")) {
    const chromePath = findChromeExecutable();
    console.log(`[pc-parts-collector] chrome=${chromePath}`);
    console.log(`[pc-parts-collector] targets=${targets.length}`);
    return;
  }

  const loop = process.argv.includes("--loop");
  const intervalIndex = process.argv.indexOf("--interval");
  const intervalSeconds = intervalIndex >= 0
    ? Number(process.argv[intervalIndex + 1] || DEFAULT_INTERVAL_SECONDS)
    : DEFAULT_INTERVAL_SECONDS;
  const safeIntervalSeconds = Math.max(300, Number.isFinite(intervalSeconds) ? intervalSeconds : DEFAULT_INTERVAL_SECONDS);

  do {
    await runOnce();
    if (!loop) break;
    console.log(`[pc-parts-collector] next run in ${safeIntervalSeconds} seconds`);
    await new Promise((resolve) => setTimeout(resolve, safeIntervalSeconds * 1000));
  } while (true);
}

run().catch((error) => {
  console.error(`[pc-parts-collector] failed: ${error.message}`);
  process.exit(1);
});
