const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const OUTPUT_FILE = path.join(__dirname, "pc-parts-raw.json");
const NB_DATA_DIR = path.join(__dirname, "nbData");
const COLLECT_STATE_FILE = path.join(__dirname, "pc-parts-collector-state.json");
const DEFAULT_INTERVAL_SECONDS = 1800;
const SEARCH_ENGINE = process.env.PC_PARTS_SEARCH_ENGINE || "danawa";
const COLLECT_CATEGORIES = ["CPU", "GPU", "RAM", "SSD", "Mainboard", "PSU"];
const CATEGORY_COLLECT_LIMIT = 3;
const RUN_COLLECT_LIMIT = Math.max(1, Number(process.env.PC_PARTS_COLLECT_BATCH_SIZE || 3) || 3);
const CHROME_TIMEOUT_MS = Math.max(5000, Number(process.env.PC_PARTS_CHROME_TIMEOUT_MS || 15000) || 15000);
const ALLOW_FALLBACK_PARTS = process.env.PC_PARTS_ALLOW_FALLBACK_PARTS !== "0";
const AUTO_GENERATED_NOTES = "Auto-generated AI PC candidate added after the saved candidate list was exhausted.";
const AI_DISCOVERY_ENABLED = process.env.PC_PARTS_AI_DISCOVERY !== "0";
const AI_DISCOVERY_ATTEMPTS = Math.max(RUN_COLLECT_LIMIT, Number(process.env.PC_PARTS_AI_DISCOVERY_ATTEMPTS || 8) || 8);
const OLLAMA_MODEL = process.env.PC_PARTS_OLLAMA_MODEL || "gemma4:31b-cloud";
const OLLAMA_API_URL = process.env.PC_PARTS_OLLAMA_API_URL || "http://127.0.0.1:11434/api/generate";
const OLLAMA_TIMEOUT_MS = Math.max(5000, Number(process.env.PC_PARTS_OLLAMA_TIMEOUT_MS || 30000) || 30000);

const targets = [
  {
    id: "cpu-ryzen-5-9600",
    category: "CPU",
    query: "AMD Ryzen 5 9600 price",
    name: "AMD Ryzen 5 9600",
    maker: "AMD",
    platform: "AM5",
    fallbackPriceKrw: 280000,
    performance: 78,
    powerWatts: 65,
    speedLabel: "理쒕? 遺?ㅽ듃 ??5.2GHz",
    tags: ["gaming", "office", "upgrade"],
    notes: "Chrome 寃???섏쭛 湲곗??쇰줈 媛寃⑹쓣 ?뺤씤?섎뒗 AM5 CPU ?꾨낫?낅땲??"
  },
  {
    id: "cpu-ryzen-7-9700x",
    category: "CPU",
    query: "AMD Ryzen 7 9700X price",
    name: "AMD Ryzen 7 9700X",
    maker: "AMD",
    platform: "AM5",
    fallbackPriceKrw: 430000,
    performance: 88,
    powerWatts: 65,
    speedLabel: "理쒕? 遺?ㅽ듃 ??5.5GHz",
    tags: ["gaming", "creator", "quiet"],
    notes: "Chrome 寃???섏쭛 湲곗??쇰줈 媛寃⑹쓣 ?뺤씤?섎뒗 怨좏슚???묒뾽??CPU ?꾨낫?낅땲??"
  },
  {
    id: "cpu-core-ultra-5-245k",
    category: "CPU",
    query: "Intel Core Ultra 5 245K price",
    name: "Intel Core Ultra 5 245K",
    maker: "Intel",
    platform: "LGA1851",
    fallbackPriceKrw: 390000,
    performance: 82,
    powerWatts: 125,
    speedLabel: "理쒕? ?곕낫 ??5.2GHz",
    tags: ["gaming", "creator"],
    notes: "Chrome 寃???섏쭛 湲곗??쇰줈 媛寃⑹쓣 ?뺤씤?섎뒗 ?명뀛 ?뚮옯??CPU ?꾨낫?낅땲??"
  },
  {
    id: "gpu-rtx-5060-ti",
    category: "GPU",
    query: "NVIDIA GeForce RTX 5060 Ti price",
    name: "NVIDIA GeForce RTX 5060 Ti",
    maker: "NVIDIA",
    platform: "PCIe",
    fallbackPriceKrw: 620000,
    performance: 82,
    powerWatts: 180,
    vramGb: 16,
    speedLabel: "standard spec",
    tags: ["gaming", "ai", "creator"],
    notes: "Chrome 寃???섏쭛 湲곗??쇰줈 媛寃⑹쓣 ?뺤씤?섎뒗 AI/寃뚯엫 寃몄슜 GPU ?꾨낫?낅땲??"
  },
  {
    id: "gpu-rtx-5070",
    category: "GPU",
    query: "NVIDIA GeForce RTX 5070 price",
    name: "NVIDIA GeForce RTX 5070",
    maker: "NVIDIA",
    platform: "PCIe",
    fallbackPriceKrw: 880000,
    performance: 93,
    powerWatts: 250,
    vramGb: 12,
    speedLabel: "12GB VRAM / 怨좎꽦??GPU",
    tags: ["gaming", "ai", "creator"],
    notes: "Chrome 寃???섏쭛 湲곗??쇰줈 媛寃⑹쓣 ?뺤씤?섎뒗 怨좎꽦??GPU ?꾨낫?낅땲??"
  },
  {
    id: "gpu-rx-9060-xt",
    category: "GPU",
    query: "AMD Radeon RX 9060 XT price",
    name: "AMD Radeon RX 9060 XT",
    maker: "AMD",
    platform: "PCIe",
    fallbackPriceKrw: 520000,
    performance: 78,
    powerWatts: 170,
    vramGb: 16,
    speedLabel: "standard spec",
    tags: ["gaming", "value"],
    notes: "Chrome 寃???섏쭛 湲곗??쇰줈 媛寃⑹쓣 ?뺤씤?섎뒗 媛?깅퉬 GPU ?꾨낫?낅땲??"
  },
  {
    id: "ram-ddr5-32-6000",
    category: "RAM",
    query: "DDR5 32GB 6000MHz price",
    name: "DDR5 32GB 6000MHz",
    maker: "Common",
    platform: "DDR5",
    fallbackPriceKrw: 140000,
    performance: 78,
    powerWatts: 12,
    speedLabel: "DDR5-6000",
    tags: ["gaming", "creator", "office"],
    notes: "Chrome 寃???섏쭛 湲곗??쇰줈 媛寃⑹쓣 ?뺤씤?섎뒗 湲곕낯 硫붾え由??꾨낫?낅땲??"
  },
  {
    id: "ram-ddr5-64-6000",
    category: "RAM",
    query: "DDR5 64GB 6000MHz price",
    name: "DDR5 64GB 6000MHz",
    maker: "Common",
    platform: "DDR5",
    fallbackPriceKrw: 260000,
    performance: 88,
    powerWatts: 18,
    speedLabel: "DDR5-6000",
    tags: ["creator", "ai"],
    notes: "Chrome 寃???섏쭛 湲곗??쇰줈 媛寃⑹쓣 ?뺤씤?섎뒗 ?묒뾽????⑸웾 硫붾え由??꾨낫?낅땲??"
  },
  {
    id: "ssd-nvme-1tb-gen4",
    category: "SSD",
    query: "NVMe Gen4 SSD 1TB price",
    name: "NVMe Gen4 SSD 1TB",
    maker: "Common",
    platform: "M.2",
    fallbackPriceKrw: 110000,
    performance: 76,
    powerWatts: 6,
    speedLabel: "standard spec",
    tags: ["gaming", "office"],
    notes: "Chrome 寃???섏쭛 湲곗??쇰줈 媛寃⑹쓣 ?뺤씤?섎뒗 湲곕낯 ??μ옣移??꾨낫?낅땲??"
  },
  {
    id: "ssd-nvme-2tb-gen4",
    category: "SSD",
    query: "NVMe Gen4 SSD 2TB price",
    name: "NVMe Gen4 SSD 2TB",
    maker: "Common",
    platform: "M.2",
    fallbackPriceKrw: 190000,
    performance: 84,
    powerWatts: 7,
    speedLabel: "standard spec",
    tags: ["gaming", "creator", "ai"],
    notes: "Chrome 寃???섏쭛 湲곗??쇰줈 媛寃⑹쓣 ?뺤씤?섎뒗 ??⑸웾 ??μ옣移??꾨낫?낅땲??"
  },
  {
    id: "mb-am5-b850",
    category: "Mainboard",
    query: "AM5 B850 Mainboard price",
    name: "AM5 B850 Mainboard",
    maker: "Common",
    platform: "AM5",
    fallbackPriceKrw: 210000,
    performance: 76,
    powerWatts: 12,
    speedLabel: "DDR5 / PCIe 5.0 吏?먭툒",
    tags: ["gaming", "office", "upgrade"],
    notes: "Chrome 寃???섏쭛 湲곗??쇰줈 媛寃⑹쓣 ?뺤씤?섎뒗 AM5 硫붿씤蹂대뱶 ?꾨낫?낅땲??"
  },
  {
    id: "mb-lga1851-b860",
    category: "Mainboard",
    query: "LGA1851 B860 Mainboard price",
    name: "LGA1851 B860 Mainboard",
    maker: "Common",
    platform: "LGA1851",
    fallbackPriceKrw: 240000,
    performance: 75,
    powerWatts: 12,
    speedLabel: "DDR5 / PCIe 5.0 吏?먭툒",
    tags: ["gaming", "office"],
    notes: "Chrome 寃???섏쭛 湲곗??쇰줈 媛寃⑹쓣 ?뺤씤?섎뒗 ?명뀛 硫붿씤蹂대뱶 ?꾨낫?낅땲??"
  },
  {
    id: "psu-650w-gold",
    category: "PSU",
    query: "650W 80PLUS Gold PSU price",
    name: "650W 80PLUS Gold PSU",
    maker: "Common",
    platform: "ATX",
    fallbackPriceKrw: 120000,
    performance: 74,
    powerWatts: 0,
    wattCapacity: 650,
    speedLabel: "650W 異쒕젰",
    tags: ["office", "gaming", "value"],
    notes: "Chrome 寃???섏쭛 湲곗??쇰줈 媛寃⑹쓣 ?뺤씤?섎뒗 湲곕낯 ?뚯썙 ?꾨낫?낅땲??"
  },
  {
    id: "psu-850w-gold",
    category: "PSU",
    query: "850W 80PLUS Gold PSU price",
    name: "850W 80PLUS Gold PSU",
    maker: "Common",
    platform: "ATX",
    fallbackPriceKrw: 180000,
    performance: 86,
    powerWatts: 0,
    wattCapacity: 850,
    speedLabel: "850W 異쒕젰",
    tags: ["gaming", "creator", "ai"],
    notes: "Chrome 寃???섏쭛 湲곗??쇰줈 媛寃⑹쓣 ?뺤씤?섎뒗 怨좎슜???뚯썙 ?꾨낫?낅땲??"
  }
];

const replacementTargets = [
  {
    id: "cpu-ryzen-5-7600",
    category: "CPU",
    query: "AMD Ryzen 5 7600 price",
    name: "AMD Ryzen 5 7600",
    maker: "AMD",
    platform: "AM5",
    fallbackPriceKrw: 240000,
    performance: 74,
    powerWatts: 65,
    speedLabel: "理쒕? 遺?ㅽ듃 ??5.1GHz",
    tags: ["gaming", "office", "value"],
    notes: "?대? ??λ맂 CPU媛 諛섎났?????泥??섏쭛?섎뒗 AM5 ?꾨낫?낅땲??"
  },
  {
    id: "cpu-ryzen-7-7700",
    category: "CPU",
    query: "AMD Ryzen 7 7700 price",
    name: "AMD Ryzen 7 7700",
    maker: "AMD",
    platform: "AM5",
    fallbackPriceKrw: 330000,
    performance: 84,
    powerWatts: 65,
    speedLabel: "理쒕? 遺?ㅽ듃 ??5.3GHz",
    tags: ["gaming", "creator", "quiet"],
    notes: "?대? ??λ맂 CPU媛 諛섎났?????泥??섏쭛?섎뒗 怨좏슚???꾨낫?낅땲??"
  },
  {
    id: "cpu-ryzen-7-7800x3d",
    category: "CPU",
    query: "AMD Ryzen 7 7800X3D price",
    name: "AMD Ryzen 7 7800X3D",
    maker: "AMD",
    platform: "AM5",
    fallbackPriceKrw: 520000,
    performance: 92,
    powerWatts: 120,
    speedLabel: "3D V-Cache 寃뚯엫 ?뱁솕",
    tags: ["gaming", "creator"],
    notes: "?대? ??λ맂 CPU媛 諛섎났?????泥??섏쭛?섎뒗 寃뚯엫 ?뱁솕 ?꾨낫?낅땲??"
  },
  {
    id: "cpu-core-ultra-7-265k",
    category: "CPU",
    query: "Intel Core Ultra 7 265K price",
    name: "Intel Core Ultra 7 265K",
    maker: "Intel",
    platform: "LGA1851",
    fallbackPriceKrw: 520000,
    performance: 91,
    powerWatts: 125,
    speedLabel: "理쒕? ?곕낫 ??5.5GHz",
    tags: ["gaming", "creator", "ai"],
    notes: "?대? ??λ맂 CPU媛 諛섎났?????泥??섏쭛?섎뒗 ?명뀛 ?꾨낫?낅땲??"
  },
  {
    id: "gpu-rtx-4070-super",
    category: "GPU",
    query: "NVIDIA GeForce RTX 4070 SUPER price",
    name: "NVIDIA GeForce RTX 4070 SUPER",
    maker: "NVIDIA",
    platform: "PCIe",
    fallbackPriceKrw: 850000,
    performance: 90,
    powerWatts: 220,
    vramGb: 12,
    speedLabel: "12GB VRAM / 怨좎꽦??GPU",
    tags: ["gaming", "ai", "creator"],
    notes: "?대? ??λ맂 GPU媛 諛섎났?????泥??섏쭛?섎뒗 怨좎꽦???꾨낫?낅땲??"
  },
  {
    id: "gpu-rtx-5070-ti",
    category: "GPU",
    query: "NVIDIA GeForce RTX 5070 Ti price",
    name: "NVIDIA GeForce RTX 5070 Ti",
    maker: "NVIDIA",
    platform: "PCIe",
    fallbackPriceKrw: 1150000,
    performance: 98,
    powerWatts: 300,
    vramGb: 16,
    speedLabel: "16GB VRAM / ?곸쐞 GPU",
    tags: ["gaming", "ai", "creator"],
    notes: "?대? ??λ맂 GPU媛 諛섎났?????泥??섏쭛?섎뒗 ?곸쐞 ?꾨낫?낅땲??"
  },
  {
    id: "gpu-rx-7800-xt",
    category: "GPU",
    query: "AMD Radeon RX 7800 XT price",
    name: "AMD Radeon RX 7800 XT",
    maker: "AMD",
    platform: "PCIe",
    fallbackPriceKrw: 720000,
    performance: 86,
    powerWatts: 263,
    vramGb: 16,
    speedLabel: "16GB VRAM / 寃뚯엫??GPU",
    tags: ["gaming", "value", "creator"],
    notes: "?대? ??λ맂 GPU媛 諛섎났?????泥??섏쭛?섎뒗 ?쇰뜲???꾨낫?낅땲??"
  },
  {
    id: "gpu-rx-7700-xt",
    category: "GPU",
    query: "AMD Radeon RX 7700 XT price",
    name: "AMD Radeon RX 7700 XT",
    maker: "AMD",
    platform: "PCIe",
    fallbackPriceKrw: 580000,
    performance: 80,
    powerWatts: 245,
    vramGb: 12,
    speedLabel: "12GB VRAM / 媛?깅퉬 GPU",
    tags: ["gaming", "value"],
    notes: "?대? ??λ맂 GPU媛 諛섎났?????泥??섏쭛?섎뒗 媛?깅퉬 ?꾨낫?낅땲??"
  },
  {
    id: "ram-ddr5-32-6400",
    category: "RAM",
    query: "DDR5 32GB 6400MHz price",
    name: "DDR5 32GB 6400MHz",
    maker: "Common",
    platform: "DDR5",
    fallbackPriceKrw: 170000,
    performance: 82,
    powerWatts: 12,
    speedLabel: "DDR5-6400",
    tags: ["gaming", "creator"],
    notes: "?대? ??λ맂 RAM??諛섎났?????泥??섏쭛?섎뒗 怨좏겢???꾨낫?낅땲??"
  },
  {
    id: "ram-ddr5-64-6400",
    category: "RAM",
    query: "DDR5 64GB 6400MHz price",
    name: "DDR5 64GB 6400MHz",
    maker: "Common",
    platform: "DDR5",
    fallbackPriceKrw: 320000,
    performance: 92,
    powerWatts: 18,
    speedLabel: "DDR5-6400",
    tags: ["creator", "ai"],
    notes: "?대? ??λ맂 RAM??諛섎났?????泥??섏쭛?섎뒗 ??⑸웾 ?꾨낫?낅땲??"
  },
  {
    id: "ssd-samsung-990-pro-1tb",
    category: "SSD",
    query: "Samsung 990 PRO 1TB price",
    name: "Samsung 990 PRO 1TB",
    maker: "Samsung",
    platform: "M.2",
    fallbackPriceKrw: 160000,
    performance: 88,
    powerWatts: 8,
    speedLabel: "standard spec",
    tags: ["gaming", "creator"],
    notes: "?대? ??λ맂 SSD媛 諛섎났?????泥??섏쭛?섎뒗 怨좎꽦???꾨낫?낅땲??"
  },
  {
    id: "ssd-wd-sn850x-2tb",
    category: "SSD",
    query: "WD Black SN850X 2TB price",
    name: "WD Black SN850X 2TB",
    maker: "WD",
    platform: "M.2",
    fallbackPriceKrw: 260000,
    performance: 90,
    powerWatts: 8,
    speedLabel: "standard spec",
    tags: ["gaming", "creator", "ai"],
    notes: "?대? ??λ맂 SSD媛 諛섎났?????泥??섏쭛?섎뒗 ??⑸웾 ?꾨낫?낅땲??"
  },
  {
    id: "mb-am5-b650",
    category: "Mainboard",
    query: "AM5 B650 Mainboard price",
    name: "AM5 B650 Mainboard",
    maker: "Common",
    platform: "AM5",
    fallbackPriceKrw: 180000,
    performance: 72,
    powerWatts: 12,
    speedLabel: "DDR5 / PCIe 4.0 吏?먭툒",
    tags: ["gaming", "office", "value"],
    notes: "?대? ??λ맂 硫붿씤蹂대뱶媛 諛섎났?????泥??섏쭛?섎뒗 AM5 ?꾨낫?낅땲??"
  },
  {
    id: "mb-lga1851-z890",
    category: "Mainboard",
    query: "LGA1851 Z890 Mainboard price",
    name: "LGA1851 Z890 Mainboard",
    maker: "Common",
    platform: "LGA1851",
    fallbackPriceKrw: 360000,
    performance: 86,
    powerWatts: 16,
    speedLabel: "DDR5 / PCIe 5.0 ?곸쐞 吏?먭툒",
    tags: ["gaming", "creator", "ai"],
    notes: "?대? ??λ맂 硫붿씤蹂대뱶媛 諛섎났?????泥??섏쭛?섎뒗 ?명뀛 ?곸쐞 ?꾨낫?낅땲??"
  },
  {
    id: "psu-750w-gold",
    category: "PSU",
    query: "750W 80PLUS Gold PSU price",
    name: "750W 80PLUS Gold PSU",
    maker: "Common",
    platform: "ATX",
    fallbackPriceKrw: 140000,
    performance: 80,
    powerWatts: 0,
    wattCapacity: 750,
    speedLabel: "750W 異쒕젰",
    tags: ["gaming", "value", "creator"],
    notes: "?대? ??λ맂 ?뚯썙媛 諛섎났?????泥??섏쭛?섎뒗 以묎컙 ?⑸웾 ?꾨낫?낅땲??"
  },
  {
    id: "psu-1000w-gold",
    category: "PSU",
    query: "1000W 80PLUS Gold PSU price",
    name: "1000W 80PLUS Gold PSU",
    maker: "Common",
    platform: "ATX",
    fallbackPriceKrw: 240000,
    performance: 92,
    powerWatts: 0,
    wattCapacity: 1000,
    speedLabel: "1000W 異쒕젰",
    tags: ["gaming", "creator", "ai"],
    notes: "?대? ??λ맂 ?뚯썙媛 諛섎났?????泥??섏쭛?섎뒗 怨좎슜???꾨낫?낅땲??"
  }
];

const expansionTargets = [
  {
    id: "cpu-core-ultra-7-265k",
    category: "CPU",
    query: "Intel Core Ultra 7 265K price",
    name: "Intel Core Ultra 7 265K",
    maker: "Intel",
    platform: "LGA1851",
    fallbackPriceKrw: 520000,
    performance: 91,
    powerWatts: 125,
    speedLabel: "Max turbo 5.5GHz",
    tags: ["gaming", "creator", "ai"],
    notes: "Additional AI PC candidate collected when saved parts are already exhausted."
  },
  {
    id: "cpu-core-ultra-9-285k",
    category: "CPU",
    query: "Intel Core Ultra 9 285K price",
    name: "Intel Core Ultra 9 285K",
    maker: "Intel",
    platform: "LGA1851",
    fallbackPriceKrw: 780000,
    performance: 98,
    powerWatts: 125,
    speedLabel: "Max turbo 5.7GHz",
    tags: ["creator", "ai", "high-end"],
    notes: "Additional AI PC candidate collected when saved parts are already exhausted."
  },
  {
    id: "cpu-ryzen-9-9900x",
    category: "CPU",
    query: "AMD Ryzen 9 9900X price",
    name: "AMD Ryzen 9 9900X",
    maker: "AMD",
    platform: "AM5",
    fallbackPriceKrw: 650000,
    performance: 96,
    powerWatts: 120,
    speedLabel: "Max boost 5.6GHz",
    tags: ["creator", "ai", "high-end"],
    notes: "Additional AI PC candidate collected when saved parts are already exhausted."
  },
  {
    id: "gpu-rtx-5080",
    category: "GPU",
    query: "NVIDIA GeForce RTX 5080 price",
    name: "NVIDIA GeForce RTX 5080",
    maker: "NVIDIA",
    platform: "PCIe",
    fallbackPriceKrw: 1800000,
    performance: 100,
    powerWatts: 360,
    vramGb: 16,
    speedLabel: "16GB VRAM / high-end GPU",
    tags: ["gaming", "creator", "ai", "high-end"],
    notes: "Additional AI PC candidate collected when saved parts are already exhausted."
  },
  {
    id: "gpu-rtx-5090",
    category: "GPU",
    query: "NVIDIA GeForce RTX 5090 price",
    name: "NVIDIA GeForce RTX 5090",
    maker: "NVIDIA",
    platform: "PCIe",
    fallbackPriceKrw: 3600000,
    performance: 100,
    powerWatts: 575,
    vramGb: 32,
    speedLabel: "32GB VRAM / flagship AI GPU",
    tags: ["creator", "ai", "high-end"],
    notes: "Additional AI PC candidate collected when saved parts are already exhausted."
  },
  {
    id: "gpu-rx-7900-xtx",
    category: "GPU",
    query: "AMD Radeon RX 7900 XTX price",
    name: "AMD Radeon RX 7900 XTX",
    maker: "AMD",
    platform: "PCIe",
    fallbackPriceKrw: 1350000,
    performance: 94,
    powerWatts: 355,
    vramGb: 24,
    speedLabel: "24GB VRAM / creator GPU",
    tags: ["gaming", "creator", "ai"],
    notes: "Additional AI PC candidate collected when saved parts are already exhausted."
  },
  {
    id: "ram-ddr5-32-6400",
    category: "RAM",
    query: "DDR5 32GB 6400MHz price",
    name: "DDR5 32GB 6400MHz",
    maker: "Common",
    platform: "DDR5",
    fallbackPriceKrw: 170000,
    performance: 82,
    powerWatts: 12,
    speedLabel: "DDR5-6400",
    tags: ["gaming", "creator"],
    notes: "Additional AI PC candidate collected when saved parts are already exhausted."
  },
  {
    id: "ram-ddr5-64-6400",
    category: "RAM",
    query: "DDR5 64GB 6400MHz price",
    name: "DDR5 64GB 6400MHz",
    maker: "Common",
    platform: "DDR5",
    fallbackPriceKrw: 320000,
    performance: 92,
    powerWatts: 18,
    speedLabel: "DDR5-6400",
    tags: ["creator", "ai"],
    notes: "Additional AI PC candidate collected when saved parts are already exhausted."
  },
  {
    id: "ram-ddr5-96-6400",
    category: "RAM",
    query: "DDR5 96GB 6400MHz price",
    name: "DDR5 96GB 6400MHz",
    maker: "Common",
    platform: "DDR5",
    fallbackPriceKrw: 520000,
    performance: 96,
    powerWatts: 24,
    speedLabel: "DDR5-6400",
    tags: ["creator", "ai", "high-end"],
    notes: "Additional AI PC candidate collected when saved parts are already exhausted."
  },
  {
    id: "ssd-crucial-t700-2tb",
    category: "SSD",
    query: "Crucial T700 2TB price",
    name: "Crucial T700 2TB",
    maker: "Crucial",
    platform: "M.2",
    fallbackPriceKrw: 330000,
    performance: 96,
    powerWatts: 11,
    speedLabel: "PCIe 5.0 / up to 12,400MB/s",
    tags: ["creator", "ai", "high-end"],
    notes: "Additional AI PC candidate collected when saved parts are already exhausted."
  },
  {
    id: "ssd-samsung-9100-pro-2tb",
    category: "SSD",
    query: "Samsung 9100 PRO 2TB price",
    name: "Samsung 9100 PRO 2TB",
    maker: "Samsung",
    platform: "M.2",
    fallbackPriceKrw: 360000,
    performance: 98,
    powerWatts: 11,
    speedLabel: "PCIe 5.0 NVMe",
    tags: ["creator", "ai", "high-end"],
    notes: "Additional AI PC candidate collected when saved parts are already exhausted."
  },
  {
    id: "mb-am5-x870",
    category: "Mainboard",
    query: "AM5 X870 Mainboard price",
    name: "AM5 X870 Mainboard",
    maker: "Common",
    platform: "AM5",
    fallbackPriceKrw: 390000,
    performance: 88,
    powerWatts: 16,
    speedLabel: "DDR5 / PCIe 5.0",
    tags: ["gaming", "creator", "ai"],
    notes: "Additional AI PC candidate collected when saved parts are already exhausted."
  },
  {
    id: "mb-am5-x870e",
    category: "Mainboard",
    query: "AM5 X870E Mainboard price",
    name: "AM5 X870E Mainboard",
    maker: "Common",
    platform: "AM5",
    fallbackPriceKrw: 560000,
    performance: 94,
    powerWatts: 18,
    speedLabel: "DDR5 / PCIe 5.0 high-end",
    tags: ["creator", "ai", "high-end"],
    notes: "Additional AI PC candidate collected when saved parts are already exhausted."
  },
  {
    id: "mb-lga1851-z890-ai",
    category: "Mainboard",
    query: "LGA1851 Z890 AI Mainboard price",
    name: "LGA1851 Z890 AI Mainboard",
    maker: "Common",
    platform: "LGA1851",
    fallbackPriceKrw: 520000,
    performance: 92,
    powerWatts: 18,
    speedLabel: "DDR5 / PCIe 5.0 high-end",
    tags: ["creator", "ai", "high-end"],
    notes: "Additional AI PC candidate collected when saved parts are already exhausted."
  },
  {
    id: "psu-1200w-platinum",
    category: "PSU",
    query: "1200W 80PLUS Platinum PSU price",
    name: "1200W 80PLUS Platinum PSU",
    maker: "Common",
    platform: "ATX",
    fallbackPriceKrw: 420000,
    performance: 96,
    powerWatts: 0,
    wattCapacity: 1200,
    speedLabel: "1200W output",
    tags: ["creator", "ai", "high-end"],
    notes: "Additional AI PC candidate collected when saved parts are already exhausted."
  },
  {
    id: "psu-1300w-gold-atx31",
    category: "PSU",
    query: "1300W Gold ATX 3.1 PSU price",
    name: "1300W Gold ATX 3.1 PSU",
    maker: "Common",
    platform: "ATX",
    fallbackPriceKrw: 360000,
    performance: 94,
    powerWatts: 0,
    wattCapacity: 1300,
    speedLabel: "1300W ATX 3.1 output",
    tags: ["creator", "ai", "high-end"],
    notes: "Additional AI PC candidate collected when saved parts are already exhausted."
  }
];

function makeGeneratedTargets() {
  const cpus = [
    ["cpu-ryzen-5-7500f", "AMD Ryzen 5 7500F", "AMD", "AM5", 210000, 72, 65, "Max boost 5.0GHz", ["gaming", "value"]],
    ["cpu-ryzen-5-7600x", "AMD Ryzen 5 7600X", "AMD", "AM5", 280000, 78, 105, "Max boost 5.3GHz", ["gaming", "creator"]],
    ["cpu-ryzen-5-8600g", "AMD Ryzen 5 8600G", "AMD", "AM5", 260000, 76, 65, "Radeon iGPU APU", ["office", "value"]],
    ["cpu-ryzen-7-8700g", "AMD Ryzen 7 8700G", "AMD", "AM5", 390000, 84, 65, "Radeon iGPU APU", ["office", "creator"]],
    ["cpu-ryzen-7-9800x3d", "AMD Ryzen 7 9800X3D", "AMD", "AM5", 720000, 98, 120, "3D V-Cache gaming", ["gaming", "high-end"]],
    ["cpu-ryzen-9-7900", "AMD Ryzen 9 7900", "AMD", "AM5", 520000, 92, 65, "12-core efficient CPU", ["creator", "ai"]],
    ["cpu-ryzen-9-7950x", "AMD Ryzen 9 7950X", "AMD", "AM5", 780000, 100, 170, "16-core creator CPU", ["creator", "ai", "high-end"]],
    ["cpu-ryzen-9-9950x", "AMD Ryzen 9 9950X", "AMD", "AM5", 860000, 100, 170, "16-core Zen 5 CPU", ["creator", "ai", "high-end"]],
    ["cpu-core-i5-14400f", "Intel Core i5-14400F", "Intel", "LGA1700", 230000, 72, 65, "10-core value CPU", ["gaming", "value"]],
    ["cpu-core-i5-14600k", "Intel Core i5-14600K", "Intel", "LGA1700", 390000, 86, 125, "Hybrid gaming CPU", ["gaming", "creator"]],
    ["cpu-core-i7-14700k", "Intel Core i7-14700K", "Intel", "LGA1700", 560000, 94, 125, "Hybrid creator CPU", ["creator", "gaming"]],
    ["cpu-core-ultra-5-245kf", "Intel Core Ultra 5 245KF", "Intel", "LGA1851", 360000, 82, 125, "Arrow Lake value CPU", ["gaming", "creator"]],
    ["cpu-core-ultra-7-265kf", "Intel Core Ultra 7 265KF", "Intel", "LGA1851", 490000, 91, 125, "Arrow Lake creator CPU", ["creator", "gaming"]],
    ["cpu-core-ultra-9-285", "Intel Core Ultra 9 285", "Intel", "LGA1851", 690000, 96, 65, "Efficient Arrow Lake CPU", ["creator", "ai"]]
  ].map(([id, name, maker, platform, fallbackPriceKrw, performance, powerWatts, speedLabel, tags]) => ({
    id, category: "CPU", query: `${name} price`, name, maker, platform, fallbackPriceKrw,
    performance, powerWatts, speedLabel, tags, notes: AUTO_GENERATED_NOTES
  }));

  const gpus = [
    ["gpu-rtx-4060", "NVIDIA GeForce RTX 4060", "NVIDIA", 410000, 70, 115, 8, "8GB VRAM / entry GPU", ["gaming", "value"]],
    ["gpu-rtx-4060-ti-16gb", "NVIDIA GeForce RTX 4060 Ti 16GB", "NVIDIA", 620000, 78, 165, 16, "16GB VRAM / AI entry", ["gaming", "ai"]],
    ["gpu-rtx-4070", "NVIDIA GeForce RTX 4070", "NVIDIA", 760000, 86, 200, 12, "12GB VRAM / efficient GPU", ["gaming", "creator"]],
    ["gpu-rtx-4070-ti-super", "NVIDIA GeForce RTX 4070 Ti SUPER", "NVIDIA", 1150000, 96, 285, 16, "16GB VRAM / creator GPU", ["creator", "ai"]],
    ["gpu-rtx-4080-super", "NVIDIA GeForce RTX 4080 SUPER", "NVIDIA", 1550000, 99, 320, 16, "16GB VRAM / high-end GPU", ["creator", "ai", "high-end"]],
    ["gpu-rtx-5060", "NVIDIA GeForce RTX 5060", "NVIDIA", 480000, 76, 145, 8, "8GB VRAM / mainstream GPU", ["gaming", "value"]],
    ["gpu-rtx-5060-ti-8gb", "NVIDIA GeForce RTX 5060 Ti 8GB", "NVIDIA", 560000, 80, 180, 8, "8GB VRAM / mainstream GPU", ["gaming", "value"]],
    ["gpu-rx-7600", "AMD Radeon RX 7600", "AMD", 330000, 68, 165, 8, "8GB VRAM / value GPU", ["gaming", "value"]],
    ["gpu-rx-7600-xt", "AMD Radeon RX 7600 XT", "AMD", 430000, 72, 190, 16, "16GB VRAM / value GPU", ["gaming", "value"]],
    ["gpu-rx-7900-gre", "AMD Radeon RX 7900 GRE", "AMD", 780000, 88, 260, 16, "16GB VRAM / gaming GPU", ["gaming", "creator"]],
    ["gpu-rx-9070", "AMD Radeon RX 9070", "AMD", 850000, 91, 220, 16, "16GB VRAM / RDNA GPU", ["gaming", "creator"]],
    ["gpu-rx-9070-xt", "AMD Radeon RX 9070 XT", "AMD", 1050000, 96, 300, 16, "16GB VRAM / high-end GPU", ["gaming", "creator", "ai"]]
  ].map(([id, name, maker, fallbackPriceKrw, performance, powerWatts, vramGb, speedLabel, tags]) => ({
    id, category: "GPU", query: `${name} price`, name, maker, platform: "PCIe", fallbackPriceKrw,
    performance, powerWatts, vramGb, speedLabel, tags, notes: AUTO_GENERATED_NOTES
  }));

  const memory = [
    ["ram-ddr5-32-5600", "DDR5 32GB 5600MHz", 120000, 72, 12, "DDR5-5600", ["office", "gaming"]],
    ["ram-ddr5-48-6000", "DDR5 48GB 6000MHz", 210000, 84, 16, "DDR5-6000", ["creator", "ai"]],
    ["ram-ddr5-64-5600", "DDR5 64GB 5600MHz", 250000, 86, 18, "DDR5-5600", ["creator", "ai"]],
    ["ram-ddr5-64-7200", "DDR5 64GB 7200MHz", 390000, 96, 20, "DDR5-7200", ["creator", "high-end"]],
    ["ram-ddr5-128-5600", "DDR5 128GB 5600MHz", 620000, 98, 28, "DDR5-5600", ["ai", "creator", "high-end"]],
    ["ram-ddr5-128-6000", "DDR5 128GB 6000MHz", 720000, 100, 30, "DDR5-6000", ["ai", "creator", "high-end"]]
  ].map(([id, name, fallbackPriceKrw, performance, powerWatts, speedLabel, tags]) => ({
    id, category: "RAM", query: `${name} price`, name, maker: "Common", platform: "DDR5", fallbackPriceKrw,
    performance, powerWatts, speedLabel, tags, notes: AUTO_GENERATED_NOTES
  }));

  const ssds = [
    ["ssd-samsung-990-pro-2tb", "Samsung 990 PRO 2TB", "Samsung", 260000, 92, 8, "PCIe 4.0 NVMe", ["gaming", "creator"]],
    ["ssd-samsung-990-evo-plus-2tb", "Samsung 990 EVO Plus 2TB", "Samsung", 210000, 86, 7, "PCIe 4.0 NVMe", ["gaming", "value"]],
    ["ssd-wd-sn850x-1tb", "WD Black SN850X 1TB", "WD", 150000, 86, 7, "PCIe 4.0 NVMe", ["gaming", "value"]],
    ["ssd-wd-sn850x-4tb", "WD Black SN850X 4TB", "WD", 470000, 94, 9, "PCIe 4.0 NVMe", ["creator", "ai"]],
    ["ssd-crucial-t705-2tb", "Crucial T705 2TB", "Crucial", 430000, 100, 12, "PCIe 5.0 NVMe", ["creator", "high-end"]],
    ["ssd-sk-hynix-p41-2tb", "SK hynix Platinum P41 2TB", "SK hynix", 250000, 90, 8, "PCIe 4.0 NVMe", ["gaming", "creator"]],
    ["ssd-solidigm-p44-pro-2tb", "Solidigm P44 Pro 2TB", "Solidigm", 240000, 90, 8, "PCIe 4.0 NVMe", ["gaming", "creator"]],
    ["ssd-seagate-firecuda-540-2tb", "Seagate FireCuda 540 2TB", "Seagate", 360000, 96, 11, "PCIe 5.0 NVMe", ["creator", "high-end"]]
  ].map(([id, name, maker, fallbackPriceKrw, performance, powerWatts, speedLabel, tags]) => ({
    id, category: "SSD", query: `${name} price`, name, maker, platform: "M.2", fallbackPriceKrw,
    performance, powerWatts, speedLabel, tags, notes: AUTO_GENERATED_NOTES
  }));

  const boards = [
    ["mb-am5-a620", "AM5 A620 Mainboard", "AM5", 130000, 64, 10, "DDR5 / entry AM5", ["office", "value"]],
    ["mb-am5-b650e", "AM5 B650E Mainboard", "AM5", 280000, 82, 14, "DDR5 / PCIe 5.0", ["gaming", "creator"]],
    ["mb-am5-x670e", "AM5 X670E Mainboard", "AM5", 480000, 92, 18, "DDR5 / PCIe 5.0 high-end", ["creator", "high-end"]],
    ["mb-lga1700-b760", "LGA1700 B760 Mainboard", "LGA1700", 180000, 72, 12, "DDR4/DDR5 mainstream", ["gaming", "value"]],
    ["mb-lga1700-z790", "LGA1700 Z790 Mainboard", "LGA1700", 360000, 88, 16, "DDR5 / overclocking", ["gaming", "creator"]],
    ["mb-lga1851-h810", "LGA1851 H810 Mainboard", "LGA1851", 160000, 66, 10, "DDR5 / entry Intel", ["office", "value"]],
    ["mb-lga1851-b860m", "LGA1851 B860M Mainboard", "LGA1851", 220000, 74, 12, "DDR5 / compact Intel", ["gaming", "value"]]
  ].map(([id, name, platform, fallbackPriceKrw, performance, powerWatts, speedLabel, tags]) => ({
    id, category: "Mainboard", query: `${name} price`, name, maker: "Common", platform, fallbackPriceKrw,
    performance, powerWatts, speedLabel, tags, notes: AUTO_GENERATED_NOTES
  }));

  const psus = [
    ["psu-550w-bronze", "550W 80PLUS Bronze PSU", 70000, 64, 550, "550W Bronze", ["office", "value"]],
    ["psu-600w-gold", "600W 80PLUS Gold PSU", 95000, 70, 600, "600W Gold", ["office", "value"]],
    ["psu-700w-gold", "700W 80PLUS Gold PSU", 130000, 78, 700, "700W Gold", ["gaming", "value"]],
    ["psu-750w-platinum", "750W 80PLUS Platinum PSU", 190000, 86, 750, "750W Platinum", ["gaming", "creator"]],
    ["psu-850w-platinum", "850W 80PLUS Platinum PSU", 260000, 90, 850, "850W Platinum", ["creator", "ai"]],
    ["psu-1000w-platinum", "1000W 80PLUS Platinum PSU", 340000, 94, 1000, "1000W Platinum", ["creator", "ai"]],
    ["psu-1200w-gold-atx31", "1200W Gold ATX 3.1 PSU", 320000, 92, 1200, "1200W ATX 3.1", ["creator", "ai"]],
    ["psu-1600w-titanium", "1600W 80PLUS Titanium PSU", 720000, 100, 1600, "1600W Titanium", ["ai", "high-end"]]
  ].map(([id, name, fallbackPriceKrw, performance, wattCapacity, speedLabel, tags]) => ({
    id, category: "PSU", query: `${name} price`, name, maker: "Common", platform: "ATX", fallbackPriceKrw,
    performance, powerWatts: 0, wattCapacity, speedLabel, tags, notes: AUTO_GENERATED_NOTES
  }));

  return [...cpus, ...gpus, ...memory, ...ssds, ...boards, ...psus];
}

function uniqueCandidates(items) {
  const unique = new Map();
  for (const item of items) {
    if (!item?.id || unique.has(item.id)) continue;
    unique.set(item.id, item);
  }
  return Array.from(unique.values());
}

const generatedTargets = makeGeneratedTargets();
const candidateTargets = uniqueCandidates([...targets, ...replacementTargets, ...expansionTargets, ...generatedTargets]);

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
    throw new Error("Chrome ?먮뒗 Edge ?ㅽ뻾 ?뚯씪??李얠? 紐삵뻽?듬땲?? CHROME_PATH ?섍꼍蹂?섎줈 chrome.exe 寃쎈줈瑜?吏?뺥븯?몄슂.");
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
    /([0-9]{1,3}(?:,[0-9]{3})+)\s*(?:원|KRW)?/gi,
    /([0-9]{5,8})\s*(?:원|KRW)?/gi
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
    .replace(/[^a-z0-9]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function hasBrokenKorean(value) {
  const text = String(value || "");
  return /[�]|[媛-힣][-￿]|[理쒕꾨낫寃섏쭛湲곗쒖쇰줈뺤씤]/.test(text)
    || text.includes("??")
    || text.includes("?")
    || text.includes("?꾨")
    || text.includes("?섏");
}

function readableNotesForPart(part) {
  const category = part.category;
  if (category === "CPU") return `${part.name}은 가격과 성능, 플랫폼 호환성을 함께 확인할 CPU 후보입니다.`;
  if (category === "GPU") return `${part.name}은 게임, 작업, AI 활용을 함께 검토할 그래픽카드 후보입니다.`;
  if (category === "RAM") return `${part.name}은 용량과 클럭을 함께 보는 DDR5 메모리 후보입니다.`;
  if (category === "SSD") return `${part.name}은 운영체제, 게임, 작업 파일 저장용으로 검토할 NVMe SSD 후보입니다.`;
  if (category === "Mainboard") return `${part.name}은 CPU 소켓, 메모리 규격, 확장성을 함께 확인할 메인보드 후보입니다.`;
  if (category === "PSU") return `${part.name}은 출력, 효율, 그래픽카드 전원 여유를 함께 볼 파워서플라이 후보입니다.`;
  return `${part.name}은 AI가 검사해 정리한 PC 부품 후보입니다.`;
}

function readableSpeedLabelForPart(part) {
  const current = String(part.speedLabel || "");
  if (part.category === "CPU") {
    const ghz = current.match(/([0-9]+(?:\.[0-9]+)?)\s*GHz/i)?.[1];
    if (ghz) return `${part.maker === "Intel" ? "최대 터보" : "최대 부스트"} 약 ${ghz}GHz`;
    return "CPU 성능 등급";
  }
  if (part.category === "GPU") return part.vramGb ? `${part.vramGb}GB VRAM / 그래픽카드` : "그래픽카드 성능 등급";
  if (part.category === "RAM") return current && !hasBrokenKorean(current) ? current : "DDR5 메모리";
  if (part.category === "SSD") return current && !hasBrokenKorean(current) && current !== "standard spec" ? current : "NVMe SSD";
  if (part.category === "Mainboard") {
    if (current.includes("5.0")) return "DDR5 / PCIe 5.0 지원";
    if (current.includes("4.0")) return "DDR5 / PCIe 4.0 지원";
    return "메인보드 확장성 등급";
  }
  if (part.category === "PSU") return part.wattCapacity ? `${part.wattCapacity}W 출력` : "파워서플라이 출력 등급";
  return current || "부품 사양";
}

function repairPartTextFields(part) {
  const fixed = { ...part };
  const speedBroken = hasBrokenKorean(fixed.speedLabel) || String(fixed.speedLabel || "") === "standard spec";
  const notesBroken = hasBrokenKorean(fixed.notes) || !String(fixed.notes || "").trim();
  if (speedBroken) fixed.speedLabel = readableSpeedLabelForPart(fixed);
  if (notesBroken) fixed.notes = readableNotesForPart(fixed);
  if (speedBroken || notesBroken) {
    fixed.textRepair = {
      checkedAt: nowKst(),
      method: "ai-text-sanity-rules",
      repairedFields: [
        ...(speedBroken ? ["speedLabel"] : []),
        ...(notesBroken ? ["notes"] : [])
      ]
    };
  }
  return fixed;
}

function targetMatchTokens(target) {
  const normalized = normalizeComparableText(`${target.name} ${target.query} ${target.platform || ""}`);
  const genericTokens = new Set(["price", "common", "mainboard", "psu", "nvidia", "geforce", "amd", "intel"]);
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
    timeout: CHROME_TIMEOUT_MS,
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

function chromeSearchText(chromePath, query) {
  const url = searchUrl(query);
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
    timeout: CHROME_TIMEOUT_MS,
    windowsHide: true
  });

  const text = stripHtml(result.stdout || "");
  return {
    query,
    url,
    text,
    prices: extractPrices(text),
    error: result.status === 0 ? "" : (result.stderr || `Chrome exit ${result.status}`).trim()
  };
}

function extractJsonObject(text) {
  const raw = String(text || "").trim();
  try {
    return JSON.parse(raw);
  } catch {
    const match = raw.match(/\{[\s\S]*\}/);
    if (!match) throw new Error("AI response did not contain JSON");
    return JSON.parse(match[0]);
  }
}

function askOllamaJson(prompt) {
  const body = JSON.stringify({
    model: OLLAMA_MODEL,
    prompt,
    stream: false,
    options: { temperature: 0.35 }
  });
  const apiResult = spawnSync("curl", [
    "-s",
    OLLAMA_API_URL,
    "-H",
    "Content-Type: application/json",
    "-d",
    body
  ], {
    cwd: __dirname,
    encoding: "utf8",
    timeout: OLLAMA_TIMEOUT_MS,
    windowsHide: true
  });

  if (!apiResult.error && apiResult.status === 0 && apiResult.stdout) {
    const payload = JSON.parse(apiResult.stdout);
    if (payload.error) throw new Error(payload.error);
    return extractJsonObject(payload.response || "");
  }

  const cliResult = spawnSync("ollama", ["run", OLLAMA_MODEL, prompt], {
    cwd: __dirname,
    encoding: "utf8",
    timeout: OLLAMA_TIMEOUT_MS,
    windowsHide: true
  });
  if (!cliResult.error && cliResult.status === 0 && cliResult.stdout) {
    return extractJsonObject(cliResult.stdout);
  }

  const apiMessage = apiResult.error?.message || apiResult.stderr || `ollama api exit ${apiResult.status}`;
  const cliMessage = cliResult.error?.message || cliResult.stderr || `ollama cli exit ${cliResult.status}`;
  throw new Error(`${apiMessage.trim()} / ${cliMessage.trim()}`);
}

function safePartId(category, name) {
  return `${categoryFolder(category)}-${safeFileName(name)}`;
}

function categoryDefaults(category) {
  const defaults = {
    CPU: { maker: "Common", platform: "CPU", performance: 75, powerWatts: 65, speedLabel: "AI discovered CPU", tags: ["ai-discovered"] },
    GPU: { maker: "Common", platform: "PCIe", performance: 80, powerWatts: 180, speedLabel: "AI discovered GPU", tags: ["ai-discovered"] },
    RAM: { maker: "Common", platform: "DDR5", performance: 75, powerWatts: 12, speedLabel: "AI discovered memory", tags: ["ai-discovered"] },
    SSD: { maker: "Common", platform: "M.2", performance: 75, powerWatts: 7, speedLabel: "AI discovered storage", tags: ["ai-discovered"] },
    Mainboard: { maker: "Common", platform: "Mainboard", performance: 75, powerWatts: 12, speedLabel: "AI discovered board", tags: ["ai-discovered"] },
    PSU: { maker: "Common", platform: "ATX", performance: 75, powerWatts: 0, speedLabel: "AI discovered power supply", tags: ["ai-discovered"] }
  };
  return defaults[category] || defaults.CPU;
}

function normalizeAiPart(part, searchResult) {
  const category = COLLECT_CATEGORIES.includes(part?.category) ? part.category : "";
  const name = String(part?.name || "").trim();
  if (!category || !name) return null;
  const defaults = categoryDefaults(category);
  const prices = searchResult.prices || [];
  const aiPrice = Number(part.estimatedPriceKrw || 0);
  const estimatedPriceKrw = aiPrice > 0 ? aiPrice : (prices[0] || 100000);
  const maker = String(part.maker || defaults.maker || "Common").trim() || "Common";
  const platform = String(part.platform || defaults.platform || "").trim();
  return {
    id: safePartId(category, name),
    category,
    query: searchResult.query,
    name,
    maker,
    platform,
    fallbackPriceKrw: estimatedPriceKrw,
    estimatedPriceKrw,
    performance: Number(part.performance || defaults.performance || 75),
    powerWatts: Number(part.powerWatts ?? defaults.powerWatts ?? 0),
    wattCapacity: Number(part.wattCapacity || 0) || undefined,
    vramGb: Number(part.vramGb || 0) || undefined,
    speedLabel: String(part.speedLabel || defaults.speedLabel || "AI discovered part"),
    tags: Array.isArray(part.tags) && part.tags.length ? part.tags : defaults.tags,
    notes: String(part.notes || "AI searched, judged, and added this PC part candidate."),
    collectedPricesKrw: prices,
    sourceQuery: searchResult.query,
    sourceUrl: searchResult.url,
    sourceEngine: SEARCH_ENGINE,
    sourceStatus: "ai-discovered",
    targetMatched: true,
    sourceError: searchResult.error,
    collectedAt: nowKst()
  };
}

function savedNamesForPrompt(previousParts, limit = 120) {
  return Array.from(previousParts.values())
    .map((part) => `${part.category}: ${part.name}`)
    .slice(-limit)
    .join("\n");
}

function buildAiSearchPrompt(previousParts, history, attempt) {
  return [
    "You are an autonomous PC parts research agent.",
    "Create the next Korean or English shopping/search query to discover a real PC component that is not already saved.",
    "Focus only on CPU, GPU, RAM, SSD, Mainboard, or PSU.",
    "Avoid generic category searches when possible; use product families, model numbers, current-generation parts, and adjacent variants.",
    "Do not repeat recently failed exact models. If the recent searches are all one product family, switch to a different category or brand.",
    "Return JSON only: {\"query\":\"...\",\"reason\":\"...\"}",
    "",
    `Attempt: ${attempt}`,
    "Already saved parts:",
    savedNamesForPrompt(previousParts),
    "",
    "Recent AI searches:",
    (history || []).slice(-12).map((item) => `${item.query} => ${item.outcome || ""}`).join("\n")
  ].join("\n");
}

function buildAiJudgePrompt(previousParts, history, searchResult) {
  return [
    "You are judging a PC parts shopping/search result.",
    "Decide whether the result contains a concrete PC component not already saved.",
    "Different capacity, chipset, model suffix, VRAM size, wattage, or generation means it is a different new part. Example: Samsung 990 PRO 4TB is new even if Samsung 990 PRO 1TB/2TB is saved.",
    "If the search query itself names a specific real PC part and the result text is thin, you may still collect it using observed prices if any, otherwise a reasonable estimated Korean street price.",
    "Do not get stuck on one model. If a query fails, produce nextQueries for a different product family and category.",
    "If yes, return JSON only with collect=true and a complete part object.",
    "If no, return collect=false and nextQueries with better follow-up searches.",
    "Allowed categories: CPU, GPU, RAM, SSD, Mainboard, PSU.",
    "Part JSON shape:",
    "{\"collect\":true,\"part\":{\"category\":\"GPU\",\"name\":\"...\",\"maker\":\"...\",\"platform\":\"...\",\"estimatedPriceKrw\":123000,\"performance\":80,\"powerWatts\":180,\"vramGb\":16,\"wattCapacity\":0,\"speedLabel\":\"...\",\"tags\":[\"gaming\",\"ai\"],\"notes\":\"...\"},\"nextQueries\":[\"...\"]}",
    "Or:",
    "{\"collect\":false,\"reason\":\"...\",\"nextQueries\":[\"...\"]}",
    "",
    "Already saved parts:",
    savedNamesForPrompt(previousParts),
    "",
    "Recent searches:",
    (history || []).slice(-10).map((item) => `${item.query} => ${item.outcome || ""}`).join("\n"),
    "",
    `Search query: ${searchResult.query}`,
    `Observed prices KRW: ${(searchResult.prices || []).join(", ") || "none"}`,
    "Search text excerpt:",
    searchResult.text.slice(0, 5000)
  ].join("\n");
}

function discoverAiParts(chromePath, previousParts, partsById, collectState, collectedThisRun, updatedThisRun, errors, duplicateSkipped, skippedSaved) {
  if (!AI_DISCOVERY_ENABLED) return collectState.aiSearchHistory || [];
  const history = Array.isArray(collectState.aiSearchHistory) ? [...collectState.aiSearchHistory] : [];
  const queue = [];
  let noCollectStreak = 0;

  for (let attempt = 1; collectedThisRun.length < RUN_COLLECT_LIMIT && attempt <= AI_DISCOVERY_ATTEMPTS; attempt += 1) {
    if (noCollectStreak >= 2) queue.length = 0;
    let query = queue.shift();
    try {
      if (!query) {
        const planned = askOllamaJson(buildAiSearchPrompt(previousParts, history, attempt));
        query = String(planned.query || "").trim();
      }
      if (!query) {
        skippedSaved.push(`ai-empty-query-${attempt}`);
        continue;
      }

      console.log(`[ai-search] ${query}`);
      const searchResult = chromeSearchText(chromePath, query);
      const judged = askOllamaJson(buildAiJudgePrompt(previousParts, history, searchResult));
      if (Array.isArray(judged.nextQueries)) {
        const nextQueries = noCollectStreak >= 1 ? judged.nextQueries.slice(0, 1) : judged.nextQueries;
        for (const nextQuery of nextQueries.map((item) => String(item || "").trim()).filter(Boolean)) {
          if (!queue.includes(nextQuery)) queue.push(nextQuery);
        }
      }

      if (!judged.collect) {
        noCollectStreak += 1;
        history.push({ query, outcome: `skip:${judged.reason || "no concrete new part"}`, at: nowKst() });
        console.log(`[ai-skip] ${query} (${judged.reason || "no concrete new part"})`);
        continue;
      }

      const item = normalizeAiPart(judged.part, searchResult);
      if (!item) {
        history.push({ query, outcome: "skip:invalid-ai-part-json", at: nowKst() });
        skippedSaved.push(`ai-invalid-${attempt}`);
        continue;
      }

      if (partsById.has(item.id) || findSavedPartByName(previousParts, item)) {
        duplicateSkipped.push(item.id);
        history.push({ query, outcome: `duplicate:${item.name}`, at: nowKst() });
        continue;
      }

      partsById.set(item.id, item);
      previousParts.set(item.id, item);
      collectedThisRun.push(item.id);
      noCollectStreak = 0;
      history.push({ query, outcome: `collect:${item.category}:${item.name}`, at: nowKst() });
      console.log(`[ai-collect] ${item.category} ${item.name} ${item.estimatedPriceKrw.toLocaleString("ko-KR")} KRW (${collectedThisRun.length}/${RUN_COLLECT_LIMIT})`);
    } catch (error) {
      errors.push(`ai-discovery: ${error.message}`);
      history.push({ query: query || "(planner)", outcome: `error:${error.message}`, at: nowKst() });
      console.log(`[ai-skip] ${query || "(planner)"} (${error.message})`);
    }
  }

  collectState.aiSearchQueue = [];
  return history.slice(-60);
}

function writeJson(payload) {
  const tempFile = `${OUTPUT_FILE}.tmp`;
  fs.writeFileSync(tempFile, JSON.stringify(payload, null, 2), "utf8");
  fs.renameSync(tempFile, OUTPUT_FILE);
}

function safeFileName(value) {
  return String(value || "part")
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    || "part";
}

function categoryFolder(category) {
  return String(category || "part").toLowerCase();
}

function readJsonFile(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  } catch (error) {
    console.error(`[pc-parts-collector] json load skipped: ${filePath} (${error.message})`);
    return null;
  }
}

function loadRawParts() {
  if (!fs.existsSync(OUTPUT_FILE)) return new Map();
  const payload = readJsonFile(OUTPUT_FILE);
  const rawParts = Array.isArray(payload?.parts) ? payload.parts : [];
  return new Map(rawParts.map((part) => [part.id, part]));
}

function loadNbDataParts() {
  const manifestPath = path.join(NB_DATA_DIR, "manifest.json");
  if (!fs.existsSync(manifestPath)) return new Map();
  const manifest = readJsonFile(manifestPath);
  const parts = new Map();

  for (const [folder, files] of Object.entries(manifest?.categories || {})) {
    for (const fileName of files || []) {
      const filePath = path.join(NB_DATA_DIR, folder, fileName);
      if (!fs.existsSync(filePath)) continue;
      const part = readJsonFile(filePath);
      if (part?.id) parts.set(part.id, part);
    }
  }

  return parts;
}

function loadPreviousParts() {
  const nbParts = loadNbDataParts();
  const rawParts = loadRawParts();
  const merged = new Map(nbParts);

  for (const [id, rawPart] of rawParts.entries()) {
    if (!merged.has(id)) merged.set(id, rawPart);
  }

  if (merged.size) {
    console.log(`[pc-parts-collector] previous parts loaded nbData=${nbParts.size}, rawFallback=${rawParts.size}, merged=${merged.size}`);
    return merged;
  }

  return new Map();
}

function loadCollectState() {
  if (!fs.existsSync(COLLECT_STATE_FILE)) return { nextCandidateIndex: 0 };
  const state = readJsonFile(COLLECT_STATE_FILE) || {};
  const nextCandidateIndex = Number(state.nextCandidateIndex || 0);
  return {
    ...state,
    nextCandidateIndex: Number.isFinite(nextCandidateIndex) ? nextCandidateIndex : 0
  };
}

function writeCollectState(state) {
  const payload = {
    schema: "pc-parts-collector-state.v1",
    updatedAt: nowKst(),
    ...state
  };
  fs.writeFileSync(`${COLLECT_STATE_FILE}.tmp`, JSON.stringify(payload, null, 2), "utf8");
  fs.renameSync(`${COLLECT_STATE_FILE}.tmp`, COLLECT_STATE_FILE);
}

function orderedCandidatesFromCursor(startIndex) {
  if (!candidateTargets.length) return [];
  const normalizedStart = ((startIndex % candidateTargets.length) + candidateTargets.length) % candidateTargets.length;
  return [
    ...candidateTargets.slice(normalizedStart),
    ...candidateTargets.slice(0, normalizedStart)
  ].filter((candidate) => COLLECT_CATEGORIES.includes(candidate.category));
}

function nbDataPartPayload(part, existing = null) {
  const repaired = repairPartTextFields({
    ...(existing || {}),
    ...part
  });
  return {
    ...repaired,
    schema: existing?.schema || "pc-part-nb-collector-file.v1",
    updatedAt: part.collectedAt || nowKst(),
    category: repaired.category,
    id: repaired.id,
    name: repaired.name,
    maker: repaired.maker || "Common",
    platform: repaired.platform || "",
    estimatedPriceKrw: Number(repaired.estimatedPriceKrw || 0),
    speedLabel: repaired.speedLabel || "",
    performance: Number(repaired.performance || 60),
    powerWatts: Number(repaired.powerWatts || 0),
    tags: repaired.tags || [],
    sourceType: repaired.sourceStatus || repaired.sourceType || "collector",
    sourceUrl: repaired.sourceUrl || null,
    sourceQuery: repaired.sourceQuery || "",
    collectedPricesKrw: repaired.collectedPricesKrw || [],
    targetMatched: repaired.targetMatched ?? null,
    notes: repaired.notes || readableNotesForPart(repaired),
    textRepair: repaired.textRepair || existing?.textRepair || null
  };
}

function writeNbDataFromCollectedParts(payload) {
  fs.mkdirSync(NB_DATA_DIR, { recursive: true });
  const categories = new Set(["cpu", "gpu", "ram", "ssd", "mainboard", "psu"]);
  const previous = loadNbDataParts();

  for (const part of payload.parts || []) {
    if (!part?.id || !part?.category) continue;
    const folder = categoryFolder(part.category);
    categories.add(folder);
    const categoryDir = path.join(NB_DATA_DIR, folder);
    fs.mkdirSync(categoryDir, { recursive: true });
    const filePath = path.join(categoryDir, `${safeFileName(part.id)}.json`);
    const partPayload = nbDataPartPayload(part, previous.get(part.id));
    fs.writeFileSync(`${filePath}.tmp`, JSON.stringify(partPayload, null, 2), "utf8");
    fs.renameSync(`${filePath}.tmp`, filePath);
  }

  const manifest = {
    schema: "pc-parts-nb-database-manifest.v1",
    updatedAt: payload.collectedAt,
    sourceType: "chrome-collector",
    root: "nbData",
    storageMode: "nbData-primary-collector",
    totalParts: 0,
    categories: {}
  };

  for (const folder of Array.from(categories).sort()) {
    const categoryDir = path.join(NB_DATA_DIR, folder);
    if (!fs.existsSync(categoryDir)) continue;
    const files = fs.readdirSync(categoryDir)
      .filter((fileName) => fileName.endsWith(".json") && fileName !== "index.json")
      .sort();
    manifest.categories[folder] = files;
    manifest.totalParts += files.length;

    const categoryIndex = {
      schema: "pc-parts-nb-category-index.v1",
      updatedAt: payload.collectedAt,
      category: folder,
      count: files.length,
      files
    };
    const indexPath = path.join(categoryDir, "index.json");
    fs.writeFileSync(`${indexPath}.tmp`, JSON.stringify(categoryIndex, null, 2), "utf8");
    fs.renameSync(`${indexPath}.tmp`, indexPath);
  }

  const manifestPath = path.join(NB_DATA_DIR, "manifest.json");
  fs.writeFileSync(`${manifestPath}.tmp`, JSON.stringify(manifest, null, 2), "utf8");
  fs.renameSync(`${manifestPath}.tmp`, manifestPath);
  return manifest.totalParts;
}

function isSameSavedPart(previous, current) {
  if (!previous || !current) return false;
  return normalizeComparableText(previous.name) === normalizeComparableText(current.name)
    && Number(previous.estimatedPriceKrw || 0) === Number(current.estimatedPriceKrw || 0);
}

function isSamePartName(previous, current) {
  if (!previous || !current) return false;
  return normalizeComparableText(previous.category) === normalizeComparableText(current.category)
    && normalizeComparableText(previous.name) === normalizeComparableText(current.name);
}

function findSavedPartByName(previousParts, current) {
  return Array.from(previousParts.values()).find((previous) => isSamePartName(previous, current)) || null;
}

function hasDifferentPrice(previous, current) {
  return Number(previous?.estimatedPriceKrw || 0) !== Number(current?.estimatedPriceKrw || 0);
}

function isAlreadySavedPart(previousParts, current) {
  return Array.from(previousParts.values()).some((previous) => isSameSavedPart(previous, current));
}

function isValidCollectedPart(item) {
  const hasPrice = Number(item?.estimatedPriceKrw || 0) > 0;
  if (!hasPrice) return false;
  if (item?.sourceStatus === "chrome-collected") return item.targetMatched !== false;
  return ALLOW_FALLBACK_PARTS && ["fallback-price", "name-price-mismatch-skipped"].includes(item?.sourceStatus);
}

function findReplacementPart(chromePath, category, previousParts, usedIds) {
  const candidates = candidateTargets.filter((candidate) => candidate.category === category && !usedIds.has(candidate.id));

  for (const candidate of candidates) {
    try {
      const item = collectOne(chromePath, candidate);
      if (!isValidCollectedPart(item)) {
        console.log(`[skip] ${item.category} ${item.name} ${item.estimatedPriceKrw.toLocaleString("ko-KR")}??(${item.sourceStatus}, invalid replacement)`);
        continue;
      }
      const sameNamePrevious = findSavedPartByName(previousParts, item);
      if (sameNamePrevious && hasDifferentPrice(sameNamePrevious, item)) {
        return {
          ...sameNamePrevious,
          ...item,
          id: sameNamePrevious.id,
          sourceStatus: "price-updated",
          previousPriceKrw: sameNamePrevious.estimatedPriceKrw,
          priceUpdatedAt: item.collectedAt
        };
      }
      if (isAlreadySavedPart(previousParts, item)) {
        console.log(`[skip] ${item.category} ${item.name} ${item.estimatedPriceKrw.toLocaleString("ko-KR")}??(already-saved replacement)`);
        continue;
      }
      return item;
    } catch (error) {
      console.log(`[skip] ${candidate.category} ${candidate.name} (replacement-error: ${error.message})`);
    }
  }

  return null;
}

function savedFallback(previous, item, reason) {
  if (!previous) return null;
  return {
    ...previous,
    collectedAt: item.collectedAt,
    lastCheckedAt: item.collectedAt,
    sourceStatus: reason,
    collectedPricesKrw: item.collectedPricesKrw,
    sourceQuery: item.sourceQuery,
    sourceUrl: item.sourceUrl,
    sourceEngine: item.sourceEngine,
    targetMatched: item.targetMatched
  };
}

function collectAll() {
  const chromePath = findChromeExecutable();
  const previousParts = loadPreviousParts();
  const collectState = loadCollectState();
  const partsById = new Map(previousParts);
  const errors = [];
  const skippedSaved = [];
  const duplicateSkipped = [];
  const collectedThisRun = [];
  const updatedThisRun = [];
  const usedIds = new Set();
  const startIndex = collectState.nextCandidateIndex || 0;
  const orderedCandidates = orderedCandidatesFromCursor(startIndex);
  let scanned = 0;
  let nextCandidateIndex = startIndex;
  const aiSearchHistory = discoverAiParts(
    chromePath,
    previousParts,
    partsById,
    collectState,
    collectedThisRun,
    updatedThisRun,
    errors,
    duplicateSkipped,
    skippedSaved
  );

  for (const target of orderedCandidates) {
    if (collectedThisRun.length >= RUN_COLLECT_LIMIT) break;
    const originalIndex = candidateTargets.indexOf(target);
    if (originalIndex >= 0) nextCandidateIndex = (originalIndex + 1) % candidateTargets.length;
    scanned += 1;

    if (usedIds.has(target.id)) continue;
    usedIds.add(target.id);

    if (previousParts.has(target.id) || findSavedPartByName(previousParts, target)) {
      duplicateSkipped.push(target.id);
      console.log(`[duplicate] ${target.category} ${target.name} (already-saved target)`);
      continue;
    }

    try {
      const item = collectOne(chromePath, target);
      if (!isValidCollectedPart(item)) {
        skippedSaved.push(item.id);
        console.log(`[skip] ${item.category} ${item.name} ${item.estimatedPriceKrw.toLocaleString("ko-KR")} KRW (${item.sourceStatus}, invalid)`);
        continue;
      }

      const sameNamePrevious = findSavedPartByName(previousParts, item);
      if (sameNamePrevious && isSameSavedPart(sameNamePrevious, item)) {
        duplicateSkipped.push(item.id);
        console.log(`[duplicate] ${item.category} ${item.name} ${item.estimatedPriceKrw.toLocaleString("ko-KR")} KRW (same-name-same-price)`);
        continue;
      }

      if (sameNamePrevious && hasDifferentPrice(sameNamePrevious, item)) {
        const updatedItem = {
          ...sameNamePrevious,
          ...item,
          id: sameNamePrevious.id,
          sourceStatus: "price-updated",
          previousPriceKrw: sameNamePrevious.estimatedPriceKrw,
          priceUpdatedAt: item.collectedAt
        };
        partsById.set(updatedItem.id, updatedItem);
        updatedThisRun.push(updatedItem.id);
        console.log(`[update-price] ${updatedItem.category} ${updatedItem.name} ${Number(sameNamePrevious.estimatedPriceKrw).toLocaleString("ko-KR")} -> ${updatedItem.estimatedPriceKrw.toLocaleString("ko-KR")} KRW (new ${collectedThisRun.length}/${RUN_COLLECT_LIMIT})`);
        continue;
      }

      partsById.set(item.id, item);
      collectedThisRun.push(item.id);
      console.log(`[collect] ${item.category} ${item.name} ${item.estimatedPriceKrw.toLocaleString("ko-KR")} KRW (${collectedThisRun.length}/${RUN_COLLECT_LIMIT})`);
    } catch (error) {
      errors.push(`${target.name}: ${error.message}`);
      console.log(`[skip] ${target.category} ${target.name} (collector-error: ${error.message})`);
    }
  }

  writeCollectState({
    nextCandidateIndex,
    batchSize: RUN_COLLECT_LIMIT,
    candidateCount: candidateTargets.length,
    scannedThisRun: scanned,
    aiDiscoveryEnabled: AI_DISCOVERY_ENABLED,
    aiSearchHistory,
    aiSearchQueue: collectState.aiSearchQueue || [],
    collectedThisRun,
    updatedThisRun
  });

  const parts = Array.from(partsById.values()).sort((a, b) => {
    if (a.category !== b.category) return String(a.category).localeCompare(String(b.category));
    return String(a.name).localeCompare(String(b.name));
  });

  return {
    ok: true,
    topic: "Chrome-based PC parts price collection source",
    collectedAt: nowKst(),
    chromePath,
    searchEngine: SEARCH_ENGINE,
    count: parts.length,
    previousCount: previousParts.size,
    batchSize: RUN_COLLECT_LIMIT,
    candidateStartIndex: startIndex,
    candidateNextIndex: nextCandidateIndex,
    scannedThisRun: scanned,
    aiDiscoveryEnabled: AI_DISCOVERY_ENABLED,
    newOrReplacementCount: collectedThisRun.length,
    updatedCount: updatedThisRun.length,
    parts,
    collectedThisRun,
    updatedThisRun,
    skippedSaved,
    duplicateSkipped,
    errors
  };
}

async function runOnce() {
  const payload = collectAll();
  writeJson(payload);
  const nbDataCount = writeNbDataFromCollectedParts(payload);
  console.log(`[pc-parts-collector] wrote ${OUTPUT_FILE}`);
  console.log(`[pc-parts-collector] wrote nbData files ${NB_DATA_DIR}`);
  console.log(`[pc-parts-collector] parts=${payload.parts.length}, nbData=${nbDataCount}, previous=${payload.previousCount}, new=${payload.newOrReplacementCount}, updated=${payload.updatedCount}, invalidSkipped=${payload.skippedSaved.length}, duplicateSkipped=${payload.duplicateSkipped.length}, errors=${payload.errors.length}`);
}

async function run() {
  if (process.argv.includes("--dry-run")) {
    const chromePath = findChromeExecutable();
    console.log(`[pc-parts-collector] chrome=${chromePath}`);
    console.log(`[pc-parts-collector] aiDiscovery=${AI_DISCOVERY_ENABLED}, model=${OLLAMA_MODEL}`);
    console.log(`[pc-parts-collector] baseTargets=${targets.length}, replacementTargets=${replacementTargets.length}, expansionTargets=${expansionTargets.length}, generatedTargets=${generatedTargets.length}, totalCandidates=${candidateTargets.length}`);
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


