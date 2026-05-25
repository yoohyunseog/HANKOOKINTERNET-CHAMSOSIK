const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const SCRIPT_DIR = __dirname;
const OUTPUT_FILE = path.join(__dirname, "pc-parts-data.json");
const RAW_INPUT_FILE = path.join(__dirname, "pc-parts-raw.json");
const ASSEMBLY_STATE_FILE = path.join(__dirname, "pc-assembly-state.json");
const OLLAMA_CACHE_FILE = path.join(__dirname, "pc-ollama-build-cache.json");
const NB_DATA_DIR = path.join(__dirname, "nbData");
const DEFAULT_INTERVAL_SECONDS = 600;
const NB_SCORE_SCALE = 1000;
const OLLAMA_MODEL = process.env.PC_PARTS_OLLAMA_MODEL || "gemma4:31b-cloud";
const OLLAMA_API_URL = process.env.PC_PARTS_OLLAMA_API_URL || "http://127.0.0.1:11434/api/generate";
const OLLAMA_TIMEOUT_MS = Number(process.env.PC_PARTS_OLLAMA_TIMEOUT_MS || 20000);
const OLLAMA_MAX_BUILDS = Number(process.env.PC_PARTS_OLLAMA_MAX_BUILDS || 3);
const CATEGORY_IMAGES = {
  CPU: "./img/cpu.svg",
  GPU: "./img/gpu.svg",
  RAM: "./img/ram.svg",
  SSD: "./img/ssd.svg",
  Mainboard: "./img/mainboard.svg",
  PSU: "./img/psu.svg"
};

const parts = [
  {
    id: "cpu-ryzen-5-9600",
    category: "CPU",
    name: "AMD Ryzen 5 9600",
    maker: "AMD",
    platform: "AM5",
    estimatedPriceKrw: 280000,
    performance: 78,
    powerWatts: 65,
    speedLabel: "최대 부스트 약 5.2GHz",
    tags: ["gaming", "office", "upgrade"],
    notes: "AM5 보급형 고성능 CPU 후보. DDR5 메모리와 AM5 메인보드가 필요합니다."
  },
  {
    id: "cpu-ryzen-7-9700x",
    category: "CPU",
    name: "AMD Ryzen 7 9700X",
    maker: "AMD",
    platform: "AM5",
    estimatedPriceKrw: 430000,
    performance: 88,
    powerWatts: 65,
    speedLabel: "최대 부스트 약 5.5GHz",
    tags: ["gaming", "creator", "quiet"],
    notes: "전력 대비 성능이 좋아 게임과 작업을 함께 보는 구성에 적합합니다."
  },
  {
    id: "cpu-core-ultra-5-245k",
    category: "CPU",
    name: "Intel Core Ultra 5 245K",
    maker: "Intel",
    platform: "LGA1851",
    estimatedPriceKrw: 390000,
    performance: 82,
    powerWatts: 125,
    speedLabel: "최대 터보 약 5.2GHz",
    tags: ["gaming", "creator"],
    notes: "신형 인텔 플랫폼 후보. 메인보드 가격까지 함께 확인해야 합니다."
  },
  {
    id: "gpu-rtx-5060-ti",
    category: "GPU",
    name: "NVIDIA GeForce RTX 5060 Ti",
    maker: "NVIDIA",
    platform: "PCIe",
    estimatedPriceKrw: 620000,
    performance: 82,
    powerWatts: 180,
    vramGb: 16,
    speedLabel: "16GB VRAM / PCIe 그래픽",
    tags: ["gaming", "ai", "creator"],
    notes: "DLSS, CUDA, 영상 작업과 AI 실험까지 함께 보는 그래픽카드 후보입니다."
  },
  {
    id: "gpu-rtx-5070",
    category: "GPU",
    name: "NVIDIA GeForce RTX 5070",
    maker: "NVIDIA",
    platform: "PCIe",
    estimatedPriceKrw: 880000,
    performance: 93,
    powerWatts: 250,
    vramGb: 12,
    speedLabel: "12GB VRAM / 고성능 GPU",
    tags: ["gaming", "ai", "creator"],
    notes: "고주사율 게임과 영상 작업에 강한 상위 후보. 전원 공급 장치 여유가 필요합니다."
  },
  {
    id: "gpu-rx-9060-xt",
    category: "GPU",
    name: "AMD Radeon RX 9060 XT",
    maker: "AMD",
    platform: "PCIe",
    estimatedPriceKrw: 520000,
    performance: 78,
    powerWatts: 170,
    vramGb: 16,
    speedLabel: "16GB VRAM / PCIe 그래픽",
    tags: ["gaming", "value"],
    notes: "VRAM 여유와 가격을 함께 보는 가성비 게임용 후보입니다."
  },
  {
    id: "ram-ddr5-32-6000",
    category: "RAM",
    name: "DDR5 32GB 6000MHz",
    maker: "Common",
    platform: "DDR5",
    estimatedPriceKrw: 140000,
    performance: 78,
    powerWatts: 12,
    speedLabel: "DDR5-6000",
    tags: ["gaming", "creator", "office"],
    notes: "현재 조립 PC의 균형점. 16GB보다 여유롭고 작업용으로도 무난합니다."
  },
  {
    id: "ram-ddr5-64-6000",
    category: "RAM",
    name: "DDR5 64GB 6000MHz",
    maker: "Common",
    platform: "DDR5",
    estimatedPriceKrw: 260000,
    performance: 88,
    powerWatts: 18,
    speedLabel: "DDR5-6000",
    tags: ["creator", "ai"],
    notes: "영상 편집, 개발, 로컬 AI 테스트처럼 메모리 사용량이 큰 작업에 적합합니다."
  },
  {
    id: "ssd-nvme-1tb-gen4",
    category: "SSD",
    name: "NVMe Gen4 SSD 1TB",
    maker: "Common",
    platform: "M.2",
    estimatedPriceKrw: 110000,
    performance: 76,
    powerWatts: 6,
    speedLabel: "순차 읽기 약 5,000MB/s급",
    tags: ["gaming", "office"],
    notes: "운영체제와 기본 게임/작업 파일용으로 적당한 기본 용량입니다."
  },
  {
    id: "ssd-nvme-2tb-gen4",
    category: "SSD",
    name: "NVMe Gen4 SSD 2TB",
    maker: "Common",
    platform: "M.2",
    estimatedPriceKrw: 190000,
    performance: 84,
    powerWatts: 7,
    speedLabel: "순차 읽기 약 7,000MB/s급",
    tags: ["gaming", "creator", "ai"],
    notes: "게임, 영상, AI 모델 파일을 함께 보관할 때 체감이 좋은 용량입니다."
  },
  {
    id: "mb-am5-b850",
    category: "Mainboard",
    name: "AM5 B850 Mainboard",
    maker: "Common",
    platform: "AM5",
    estimatedPriceKrw: 210000,
    performance: 76,
    powerWatts: 12,
    speedLabel: "DDR5 / PCIe 5.0 지원급",
    tags: ["gaming", "office", "upgrade"],
    notes: "Ryzen 9000 계열과 맞는 AM5 보급형 메인보드 후보입니다."
  },
  {
    id: "mb-lga1851-b860",
    category: "Mainboard",
    name: "LGA1851 B860 Mainboard",
    maker: "Common",
    platform: "LGA1851",
    estimatedPriceKrw: 240000,
    performance: 75,
    powerWatts: 12,
    speedLabel: "DDR5 / PCIe 5.0 지원급",
    tags: ["gaming", "office"],
    notes: "Core Ultra 200 계열 후보와 함께 확인할 인텔 플랫폼 메인보드입니다."
  },
  {
    id: "psu-650w-gold",
    category: "PSU",
    name: "650W 80PLUS Gold PSU",
    maker: "Common",
    platform: "ATX",
    estimatedPriceKrw: 120000,
    performance: 74,
    powerWatts: 0,
    wattCapacity: 650,
    speedLabel: "650W 출력",
    tags: ["office", "gaming", "value"],
    notes: "중급 그래픽카드까지 안정적으로 보는 기본 전원 후보입니다."
  },
  {
    id: "psu-850w-gold",
    category: "PSU",
    name: "850W 80PLUS Gold PSU",
    maker: "Common",
    platform: "ATX",
    estimatedPriceKrw: 180000,
    performance: 86,
    powerWatts: 0,
    wattCapacity: 850,
    speedLabel: "850W 출력",
    tags: ["gaming", "creator", "ai"],
    notes: "상위 그래픽카드와 향후 업그레이드 여유를 보는 전원 후보입니다."
  }
];

const buildProfiles = [
  {
    id: "balanced-gaming",
    title: "균형형 게임/작업 PC",
    purpose: "게임, 문서, 가벼운 영상 편집을 함께 보는 구성",
    partIds: ["cpu-ryzen-5-9600", "gpu-rtx-5060-ti", "ram-ddr5-32-6000", "ssd-nvme-1tb-gen4", "mb-am5-b850", "psu-650w-gold"]
  },
  {
    id: "creator-ai",
    title: "AI/크리에이터 작업 PC",
    purpose: "로컬 AI 테스트, 영상 편집, 개발 작업을 우선하는 구성",
    partIds: ["cpu-ryzen-7-9700x", "gpu-rtx-5070", "ram-ddr5-64-6000", "ssd-nvme-2tb-gen4", "mb-am5-b850", "psu-850w-gold"]
  },
  {
    id: "value-gaming",
    title: "가성비 게임 PC",
    purpose: "가격 대비 프레임과 넉넉한 VRAM을 보는 구성",
    partIds: ["cpu-ryzen-5-9600", "gpu-rx-9060-xt", "ram-ddr5-32-6000", "ssd-nvme-1tb-gen4", "mb-am5-b850", "psu-650w-gold"]
  }
];

function nowKst() {
  return new Date(Date.now() + 9 * 60 * 60 * 1000).toISOString().replace("Z", "+09:00");
}

function priceToScore(price) {
  if (!price) return 0;
  return Math.max(1, Math.round(10000000 / price));
}

function initializeNbArrays(count) {
  return {
    BIT_START_A50: new Array(count).fill(0),
    BIT_START_A100: new Array(count).fill(0),
    BIT_START_B50: new Array(count).fill(0),
    BIT_START_B100: new Array(count).fill(0),
    BIT_START_NBA100: new Array(count).fill(0)
  };
}

function calculateNbBit(nb, bit = 5.5, reverse = false) {
  const values = nb.filter((value) => Number.isFinite(value));
  if (values.length < 2) return bit / 100;

  const max = Math.max(...values);
  const min = Math.min(...values);
  const countPerValue = 50;
  const totalSlots = countPerValue * values.length;
  const negativeRange = min < 0 ? Math.abs(min) : 0;
  const positiveRange = max > 0 ? max : 0;
  const negativeIncrement = negativeRange / Math.max(totalSlots - 1, 1);
  const positiveIncrement = positiveRange / Math.max(totalSlots - 1, 1);
  const arrays = initializeNbArrays(totalSlots);
  let cursor = 0;
  let totalSum = 0;

  for (const value of values) {
    for (let i = 0; i < countPerValue; i += 1) {
      const bitEnd = 1;
      const increment = value < 0 ? negativeIncrement : positiveIncrement;
      const a50 = min + increment * (cursor + 1);
      const a100 = (cursor + 1) * bit / totalSlots;
      const b50 = a50 - increment * 2;
      const b100 = a50 + increment;
      const nba100 = a100 / Math.max(values.length - bitEnd, 1);

      arrays.BIT_START_A50[cursor] = a50;
      arrays.BIT_START_A100[cursor] = a100;
      arrays.BIT_START_B50[cursor] = b50;
      arrays.BIT_START_B100[cursor] = b100;
      arrays.BIT_START_NBA100[cursor] = nba100;
      cursor += 1;
    }
    totalSum += value;
  }

  if (reverse) arrays.BIT_START_NBA100.reverse();

  let nb50 = 0;
  for (const value of values) {
    for (let i = 0; i < arrays.BIT_START_NBA100.length; i += 1) {
      if (arrays.BIT_START_B50[i] <= value && arrays.BIT_START_B100[i] >= value) {
        nb50 += arrays.BIT_START_NBA100[Math.min(i, arrays.BIT_START_NBA100.length - 1)];
        break;
      }
    }
  }

  const averageRatio = (totalSum / (values.length * Math.abs(max || 1))) * 100;
  nb50 = Math.min((nb50 / 100) * averageRatio, bit);
  return values.length === 2 ? bit - nb50 : nb50;
}

function bitMaxNb(nb, bit = 5.5) {
  const result = calculateNbBit(nb, bit, false);
  return Number.isFinite(result) && !Number.isNaN(result) ? result : 0;
}

function bitMinNb(nb, bit = 5.5) {
  const result = calculateNbBit(nb, bit, true);
  return Number.isFinite(result) && !Number.isNaN(result) ? result : 0;
}

function normalizeMetric(value, maxValue) {
  if (!Number.isFinite(value) || !Number.isFinite(maxValue) || maxValue <= 0) return 0;
  return Math.round((value / maxValue) * 1000) / 10;
}

function clampScore(value, min = 0, max = 100) {
  if (!Number.isFinite(value)) return min;
  return Math.max(min, Math.min(max, value));
}

function normalizeToNbScore(value, maxValue) {
  if (!Number.isFinite(value) || !Number.isFinite(maxValue) || maxValue <= 0) return 100;
  return Math.round(Math.max(100, Math.min(NB_SCORE_SCALE, (value / maxValue) * NB_SCORE_SCALE)));
}

function priceBandFor(price) {
  if (price < 150000) return "15만원 미만";
  if (price < 300000) return "15~30만원";
  if (price < 600000) return "30~60만원";
  return "60만원 이상";
}

function nbBandFor(score) {
  if (score >= 850) return "850~1000";
  if (score >= 700) return "700~849";
  if (score >= 500) return "500~699";
  return "100~499";
}

function speedMetricFor(part) {
  const metrics = {
    "cpu-ryzen-5-9600": {
      kind: "cpu_boost_clock",
      label: "CPU 최대 부스트 클럭",
      value: 5.2,
      unit: "GHz",
      group: "CPU",
      compareNote: "CPU끼리는 GHz와 코어 수, 캐시, 세대 차이를 함께 봐야 합니다."
    },
    "cpu-ryzen-7-9700x": {
      kind: "cpu_boost_clock",
      label: "CPU 최대 부스트 클럭",
      value: 5.5,
      unit: "GHz",
      group: "CPU",
      compareNote: "CPU끼리는 GHz와 코어 수, 캐시, 세대 차이를 함께 봐야 합니다."
    },
    "cpu-core-ultra-5-245k": {
      kind: "cpu_turbo_clock",
      label: "CPU 최대 터보 클럭",
      value: 5.2,
      unit: "GHz",
      group: "CPU",
      compareNote: "Intel CPU는 P코어/E코어 구조도 같이 확인해야 합니다."
    },
    "gpu-rtx-5060-ti": {
      kind: "gpu_memory_capacity",
      label: "그래픽 메모리",
      value: 16,
      unit: "GB VRAM",
      group: "GPU",
      compareNote: "GPU는 GHz보다 코어 구조, VRAM, 메모리 대역폭, 전력 제한이 더 중요할 수 있습니다."
    },
    "gpu-rtx-5070": {
      kind: "gpu_memory_capacity",
      label: "그래픽 메모리",
      value: 12,
      unit: "GB VRAM",
      group: "GPU",
      compareNote: "GPU는 GHz보다 코어 구조, VRAM, 메모리 대역폭, 전력 제한이 더 중요할 수 있습니다."
    },
    "gpu-rx-9060-xt": {
      kind: "gpu_memory_capacity",
      label: "그래픽 메모리",
      value: 16,
      unit: "GB VRAM",
      group: "GPU",
      compareNote: "GPU는 GHz보다 코어 구조, VRAM, 메모리 대역폭, 전력 제한이 더 중요할 수 있습니다."
    },
    "ram-ddr5-32-6000": {
      kind: "memory_transfer_rate",
      label: "메모리 전송률",
      value: 6000,
      unit: "MT/s",
      group: "RAM",
      compareNote: "RAM은 GHz 표기보다 DDR 전송률과 지연 시간(CL)을 함께 봐야 합니다."
    },
    "ram-ddr5-64-6000": {
      kind: "memory_transfer_rate",
      label: "메모리 전송률",
      value: 6000,
      unit: "MT/s",
      group: "RAM",
      compareNote: "RAM은 GHz 표기보다 DDR 전송률과 지연 시간(CL)을 함께 봐야 합니다."
    },
    "ssd-nvme-1tb-gen4": {
      kind: "sequential_read",
      label: "순차 읽기 속도",
      value: 5000,
      unit: "MB/s",
      group: "SSD",
      compareNote: "SSD는 순차 읽기뿐 아니라 랜덤 읽기, 컨트롤러, DRAM 캐시도 체감에 영향을 줍니다."
    },
    "ssd-nvme-2tb-gen4": {
      kind: "sequential_read",
      label: "순차 읽기 속도",
      value: 7000,
      unit: "MB/s",
      group: "SSD",
      compareNote: "SSD는 순차 읽기뿐 아니라 랜덤 읽기, 컨트롤러, DRAM 캐시도 체감에 영향을 줍니다."
    },
    "mb-am5-b850": {
      kind: "platform_io",
      label: "플랫폼 지원",
      value: 5,
      unit: "PCIe 세대",
      group: "Mainboard",
      compareNote: "메인보드는 GHz보다 CPU 소켓, 메모리 규격, PCIe 세대, 확장성을 봐야 합니다."
    },
    "mb-lga1851-b860": {
      kind: "platform_io",
      label: "플랫폼 지원",
      value: 5,
      unit: "PCIe 세대",
      group: "Mainboard",
      compareNote: "메인보드는 GHz보다 CPU 소켓, 메모리 규격, PCIe 세대, 확장성을 봐야 합니다."
    },
    "psu-650w-gold": {
      kind: "power_output",
      label: "정격 출력",
      value: 650,
      unit: "W",
      group: "PSU",
      compareNote: "파워는 속도가 아니라 정격 출력, 효율, 보호 회로, 품질을 비교해야 합니다."
    },
    "psu-850w-gold": {
      kind: "power_output",
      label: "정격 출력",
      value: 850,
      unit: "W",
      group: "PSU",
      compareNote: "파워는 속도가 아니라 정격 출력, 효율, 보호 회로, 품질을 비교해야 합니다."
    }
  };

  return metrics[part.id] || {
    kind: "unknown",
    label: "속도 기준",
    value: null,
    unit: "",
    group: part.category,
    compareNote: "부품군별 기준으로 비교해야 합니다."
  };
}

function analyzePart(part) {
  const valueIndex = Math.round((part.performance / Math.max(part.estimatedPriceKrw / 100000, 1)) * 10) / 10;
  const efficiencyIndex = part.powerWatts ? Math.round((part.performance / part.powerWatts) * 100) / 100 : null;
  const aiUseScore = (part.tags || []).includes("ai")
    ? Math.min(100, part.performance + (part.vramGb || 0))
    : Math.round(part.performance * 0.65);
  const totalScore = Math.round((part.performance * 0.5) + (priceToScore(part.estimatedPriceKrw) * 0.2) + (valueIndex * 0.3));
  const speedMetric = speedMetricFor(part);
  const unifiedSpeedScore = speedScoreForMetric(speedMetric);
  const nbDatabase = createPartNbDatabase(part, {
    valueIndex,
    aiUseScore,
    unifiedSpeedScore,
    speedMetric
  });
  const aiExplanation = explainPart(part, { valueIndex, efficiencyIndex, aiUseScore, totalScore });

  return {
    ...part,
    imageUrl: CATEGORY_IMAGES[part.category] || "./img/cpu.svg",
    speedMetric,
    unifiedSpeedScore,
    nbDatabase,
    nbWeightedScore: nbDatabase.weightedScore,
    nbMax: nbDatabase.nbMax,
    nbMin: nbDatabase.nbMin,
    nbBand: nbDatabase.nbBand,
    priceBand: priceBandFor(part.estimatedPriceKrw),
    valueIndex,
    efficiencyIndex,
    aiUseScore,
    totalScore,
    aiExplanation,
    priceSourceStatus: "초기 기준값",
    sourceQueries: [
      `${part.name} 가격`,
      `${part.name} 성능`,
      `${part.name} 벤치마크`
    ]
  };
}

function speedScoreForMetric(metric) {
  if (metric.group === "CPU") return normalizeToNbScore(metric.value || 0, 6);
  if (metric.group === "GPU") return normalizeToNbScore(metric.value || 0, 24);
  if (metric.group === "RAM") return normalizeToNbScore(metric.value || 0, 8000);
  if (metric.group === "SSD") return normalizeToNbScore(metric.value || 0, 8000);
  if (metric.group === "Mainboard") return normalizeToNbScore(metric.value || 0, 5);
  if (metric.group === "PSU") return normalizeToNbScore(metric.value || 0, 1000);
  return 100;
}

function createPartNbDatabase(part, scores) {
  const speedScore = scores.unifiedSpeedScore || 100;
  const performanceScore = normalizeToNbScore(part.performance || 0, 100);
  const valueScore = normalizeToNbScore(scores.valueIndex || 0, 75);
  const aiScore = normalizeToNbScore(scores.aiUseScore || 0, 100);
  const priceScore = priceToScore(part.estimatedPriceKrw) * 10;
  const powerScore = part.powerWatts
    ? normalizeToNbScore((part.performance || 0) / Math.max(part.powerWatts, 1), 3)
    : normalizeToNbScore(part.performance || 0, 100);
  const speedWeight = part.category === "CPU" || part.category === "GPU" || part.category === "RAM" || part.category === "SSD"
    ? 0.42
    : 0.32;
  const nbVector = [
    speedScore,
    performanceScore,
    valueScore,
    aiScore,
    priceScore,
    powerScore
  ].map((value) => Math.round(value * 100) / 100);
  const nbMax = bitMaxNb(nbVector, NB_SCORE_SCALE);
  const nbMin = bitMinNb(nbVector, NB_SCORE_SCALE);
  const weightedScore = Math.round(Math.max(100, Math.min(NB_SCORE_SCALE,
    (speedScore * speedWeight) +
    (performanceScore * 0.2) +
    (valueScore * 0.14) +
    (aiScore * 0.1) +
    (priceScore * 0.08) +
    (powerScore * 0.06)
  )));

  return {
    schema: "pc-part-nb-database.v1",
    unit: "100~1000",
    priority: "speed-first",
    category: part.category,
    partId: part.id,
    partName: part.name,
    speed: {
      score: speedScore,
      weight: speedWeight,
      metric: scores.speedMetric
    },
    scores: {
      speed: speedScore,
      performance: performanceScore,
      value: valueScore,
      aiFit: aiScore,
      priceEfficiency: priceScore,
      powerEfficiency: powerScore
    },
    nbVector,
    vectorLabels: ["속도", "성능", "가성비", "AI 적합", "가격 효율", "전력 효율"],
    nbMax: Math.round(nbMax * 1000) / 1000,
    nbMin: Math.round(nbMin * 1000) / 1000,
    weightedScore,
    nbBand: nbBandFor(weightedScore),
    summary: `${part.category} ${part.name} 부품을 속도 중심 N/B 데이터베이스 점수 ${weightedScore}점으로 저장했습니다.`
  };
}

function explainPart(part, scores) {
  const strengths = [];
  const cautions = [];

  if (scores.valueIndex >= 55) strengths.push("가격 대비 성능 점수가 높아 예산형 구성에서 우선 검토할 만합니다");
  if (scores.aiUseScore >= 85) strengths.push("AI 작업 또는 크리에이터 작업 후보로 분류할 수 있습니다");
  if (scores.efficiencyIndex && scores.efficiencyIndex >= 1.1) strengths.push("전력 대비 성능이 좋아 발열과 소음 관리에 유리합니다");
  if ((part.tags || []).includes("gaming")) strengths.push("게임용 조립 PC 후보에 넣기 좋습니다");
  if ((part.tags || []).includes("upgrade")) strengths.push("향후 업그레이드 여지를 함께 볼 수 있습니다");

  if (part.category === "GPU" && part.vramGb && part.vramGb < 16) {
    cautions.push("AI 모델이나 고해상도 텍스처 작업에서는 VRAM 용량을 다시 확인해야 합니다");
  }
  if (part.powerWatts >= 200) cautions.push("파워 용량과 케이스 내부 발열 여유를 같이 확인해야 합니다");
  if (part.category === "CPU") cautions.push(`${part.platform} 메인보드와 DDR5 메모리 호환성을 함께 확인해야 합니다`);
  if (part.category === "Mainboard") cautions.push("CPU 소켓, 메모리 규격, BIOS 지원 여부 확인이 필요합니다");

  return {
    summary: `${part.name}은 ${part.category} 부품군에서 총점 ${scores.totalScore}점, 가성비 ${scores.valueIndex}로 계산된 후보입니다.`,
    strengths: strengths.slice(0, 3),
    cautions: cautions.slice(0, 2),
    userLevel: classifyUserLevel(part, scores),
    recommendation: scores.totalScore >= 75
      ? "우선 검토 후보"
      : scores.totalScore >= 60
        ? "조건부 검토 후보"
        : "가격 변동 확인 후보"
  };
}

function classifyUserLevel(part, scores) {
  const highPower = part.powerWatts >= 200;
  const highPrice = part.estimatedPriceKrw >= 600000;
  const tuningSensitive = ["GPU", "CPU", "Mainboard"].includes(part.category);
  const simpleInstall = ["RAM", "SSD", "PSU"].includes(part.category);

  if (simpleInstall && !highPrice && !(part.tags || []).includes("ai")) {
    return {
      level: "초보자용",
      reason: "선택 기준이 비교적 단순하고 체감 개선이 쉬워 처음 조립하는 사용자도 접근하기 좋습니다."
    };
  }

  if (highPower || highPrice || (part.tags || []).includes("ai")) {
    return {
      level: "고수용",
      reason: "성능은 높지만 가격, 전력, 호환성 확인 부담이 커서 조립 경험이 있는 사용자에게 적합합니다."
    };
  }

  if (tuningSensitive || scores.totalScore >= 65) {
    return {
      level: "중수용",
      reason: "가격과 성능 균형은 좋지만 플랫폼, 전력, 업그레이드 방향을 함께 비교해야 합니다."
    };
  }

  return {
    level: "중수용",
    reason: "기본 호환성 확인 후 선택하기 좋은 일반 사용자용 후보입니다."
  };
}

function createLevelAnalysis(items) {
  const levels = ["초보자용", "중수용", "고수용"];
  return levels.map((level) => {
    const levelItems = items.filter((item) => item.aiExplanation.userLevel.level === level);
    const topItems = levelItems
      .slice()
      .sort((a, b) => b.totalScore - a.totalScore)
      .slice(0, 5);

    return {
      level,
      count: levelItems.length,
      summary: {
        "초보자용": "설치와 선택 기준이 단순하고 가격 부담이 낮은 부품을 우선 정리합니다.",
        "중수용": "가격, 성능, 플랫폼 호환성을 함께 비교해야 하는 균형형 부품을 정리합니다.",
        "고수용": "고성능, 고전력, AI 작업, 상위 GPU처럼 확인할 요소가 많은 부품을 정리합니다."
      }[level],
      recommendedParts: topItems.map((item) => ({
        id: item.id,
        category: item.category,
        name: item.name,
        speedLabel: item.speedLabel,
        estimatedPriceKrw: item.estimatedPriceKrw,
        totalScore: item.totalScore,
        reason: item.aiExplanation.userLevel.reason,
        imageUrl: item.imageUrl
      }))
    };
  });
}

function partMap(items) {
  return new Map(items.map((item) => [item.id, item]));
}

function calculateBuildWeight(selected) {
  const totalPrice = selected.reduce((sum, item) => sum + item.estimatedPriceKrw, 0);
  const totalPower = selected.reduce((sum, item) => sum + (item.powerWatts || 0), 0);
  const avgPerformance = selected.reduce((sum, item) => sum + item.performance, 0) / Math.max(selected.length, 1);
  const avgValue = selected.reduce((sum, item) => sum + item.valueIndex, 0) / Math.max(selected.length, 1);
  const avgAi = selected.reduce((sum, item) => sum + item.aiUseScore, 0) / Math.max(selected.length, 1);
  const speedSum = selected.reduce((sum, item) => sum + (item.unifiedSpeedScore || 100), 0);
  const avgSpeed = speedSum / Math.max(selected.length, 1);
  const priceEfficiency = normalizeToNbScore(avgValue, 75);
  const powerEfficiency = normalizeToNbScore(totalPower ? avgPerformance / Math.max(totalPower / selected.length, 1) : avgPerformance, 3);
  const nbVector = [
    normalizeToNbScore(avgPerformance, 100),
    normalizeToNbScore(avgValue, 75),
    normalizeToNbScore(avgAi, 100),
    avgSpeed,
    priceEfficiency,
    powerEfficiency
  ].map((value) => Math.round(value * 100) / 100);
  const bitMax = bitMaxNb(nbVector, NB_SCORE_SCALE);
  const bitMin = bitMinNb(nbVector, NB_SCORE_SCALE);
  const balanceScore = Math.round(Math.max(100, NB_SCORE_SCALE - Math.abs(bitMax - bitMin)) * 10) / 10;
  const weightedScore = Math.round(Math.max(100, Math.min(NB_SCORE_SCALE, (nbVector[0] * 0.28) + (nbVector[1] * 0.18) + (nbVector[2] * 0.14) + (nbVector[3] * 0.18) + (nbVector[4] * 0.12) + (nbVector[5] * 0.1))));

  return {
    source: "bitCalculation.v.0.1.js 기반 N/B 가중치",
    bitMax: Math.round(bitMax * 1000) / 1000,
    bitMin: Math.round(bitMin * 1000) / 1000,
    balanceScore: Math.round(balanceScore * 10) / 10,
    weightedScore,
    nbBand: nbBandFor(weightedScore),
    nbVector,
    vectorLabels: ["평균 성능", "평균 가성비", "AI 적합도", "통합 속도", "가격 효율", "전력 효율"],
    summary: `완성 조합의 통합 속도와 가격 효율을 100~1000점으로 변환해 N/B 상한 ${Math.round(bitMax * 1000) / 1000}, 하한 ${Math.round(bitMin * 1000) / 1000}, 조합 가중치 ${weightedScore}점으로 계산했습니다.`
  };
}

function analyzeBuild(profile, itemsById) {
  const selected = profile.partIds.map((id) => itemsById.get(id)).filter(Boolean);
  const totalPrice = selected.reduce((sum, item) => sum + item.estimatedPriceKrw, 0);
  const estimatedLoadWatts = selected.reduce((sum, item) => sum + (item.powerWatts || 0), 0);
  const psu = selected.find((item) => item.category === "PSU");
  const score = Math.round(selected.reduce((sum, item) => sum + item.totalScore, 0) / selected.length);
  const warnings = [];

  const cpu = selected.find((item) => item.category === "CPU");
  const mainboard = selected.find((item) => item.category === "Mainboard");
  if (cpu && mainboard && cpu.platform !== mainboard.platform) {
    warnings.push("CPU와 메인보드 플랫폼이 맞지 않습니다.");
  }
  if (psu?.wattCapacity && estimatedLoadWatts > psu.wattCapacity * 0.72) {
    warnings.push("전원 공급 장치 여유가 작을 수 있습니다.");
  }
  const nbWeight = calculateBuildWeight(selected);

  return {
    ...profile,
    optimizationTarget: profile.optimizationTarget || "N/B MAX",
    totalPriceKrw: totalPrice,
    estimatedLoadWatts,
    recommendedPsuHeadroomWatts: psu?.wattCapacity ? psu.wattCapacity - estimatedLoadWatts : null,
    score,
    nbWeight,
    warnings,
    aiExplanation: explainBuild(profile, selected, {
      totalPrice,
      estimatedLoadWatts,
      psu,
      score,
      warnings
    }),
    parts: selected.map((item) => ({
      category: item.category,
      name: item.name,
      maker: item.maker,
      platform: item.platform,
      priceKrw: item.estimatedPriceKrw,
      speedLabel: item.speedLabel,
      unifiedSpeedScore: item.unifiedSpeedScore,
      performance: item.performance,
      valueIndex: item.valueIndex,
      aiUseScore: item.aiUseScore,
      score: item.totalScore,
      powerWatts: item.powerWatts || null,
      tags: item.tags || [],
      sourceType: item.sourceType,
      sourceUrl: item.sourceUrl || null
    }))
  };
}

function buildCompatibilityWarnings(selected) {
  const warnings = [];
  const cpu = selected.find((item) => item.category === "CPU");
  const mainboard = selected.find((item) => item.category === "Mainboard");
  const psu = selected.find((item) => item.category === "PSU");
  const estimatedLoadWatts = selected.reduce((sum, item) => sum + (item.powerWatts || 0), 0);

  if (cpu && mainboard && cpu.platform !== mainboard.platform) {
    warnings.push("CPU와 메인보드 플랫폼이 맞지 않습니다.");
  }
  if (psu?.wattCapacity && estimatedLoadWatts > psu.wattCapacity * 0.72) {
    warnings.push("전원 공급 장치 여유가 작을 수 있습니다.");
  }
  if (!cpu || !mainboard || !psu) {
    warnings.push("필수 부품 구성이 완전하지 않습니다.");
  }

  return warnings;
}

function takeTopByCategory(items, category, limit = 8) {
  return items
    .filter((item) => item.category === category)
    .sort((a, b) => {
      const scoreA = (a.totalScore * 0.36) + (a.unifiedSpeedScore * 0.3) + (a.valueIndex * 0.2) + (a.aiUseScore * 0.14);
      const scoreB = (b.totalScore * 0.36) + (b.unifiedSpeedScore * 0.3) + (b.valueIndex * 0.2) + (b.aiUseScore * 0.14);
      return scoreB - scoreA;
    })
    .slice(0, limit);
}

function createOptimizedBuilds(analyzedParts, maxBuilds = 12, options = {}) {
  const cpus = takeTopByCategory(analyzedParts, "CPU");
  const gpus = takeTopByCategory(analyzedParts, "GPU");
  const rams = takeTopByCategory(analyzedParts, "RAM");
  const ssds = takeTopByCategory(analyzedParts, "SSD");
  const mainboards = takeTopByCategory(analyzedParts, "Mainboard");
  const psus = takeTopByCategory(analyzedParts, "PSU");
  const excludedKeys = options.excludedKeys || new Set();
  const candidates = [];
  let testedCount = 0;

  for (const cpu of cpus) {
    for (const gpu of gpus) {
      for (const ram of rams) {
        for (const ssd of ssds) {
          for (const mainboard of mainboards) {
            for (const psu of psus) {
              const selected = [cpu, gpu, ram, ssd, mainboard, psu];
              testedCount += 1;
              const warnings = buildCompatibilityWarnings(selected);
              if (warnings.length) continue;

              const nbWeight = calculateBuildWeight(selected);
              const totalPrice = selected.reduce((sum, item) => sum + item.estimatedPriceKrw, 0);
              const avgPerformance = selected.reduce((sum, item) => sum + item.performance, 0) / selected.length;
              const pricePerformanceIndex = Math.round((avgPerformance / Math.max(totalPrice / 1000000, 0.1)) * 10) / 10;
              const optimizationScore = Math.round(((nbWeight.bitMax * 0.48) + (nbWeight.weightedScore * 0.34) + (pricePerformanceIndex * 0.18)) * 10) / 10;
              const candidateKey = selected.map((item) => item.id).join("|");

              candidates.push({
                id: `optimized-${candidates.length + 1}`,
                buildKey: candidateKey,
                title: `N/B MAX 최적화 조립 #${candidates.length + 1}`,
                purpose: "Chrome 검색 수집 부품을 조합해 N/B MAX와 가격 대비 성능을 동시에 높인 구성",
                optimizationTarget: "N/B MAX 상승",
                partIds: selected.map((item) => item.id),
                nbWeight,
                totalPriceKrw: totalPrice,
                avgPerformance: Math.round(avgPerformance * 10) / 10,
                pricePerformanceIndex,
                optimizationScore
              });
            }
          }
        }
      }
    }
  }

  const unique = new Map();
  for (const candidate of candidates) {
    const key = candidate.buildKey || candidate.partIds.join("|");
    if (!unique.has(key)) unique.set(key, candidate);
  }

  const ranked = Array.from(unique.values())
    .sort((a, b) => {
      if (b.nbWeight.bitMax !== a.nbWeight.bitMax) return b.nbWeight.bitMax - a.nbWeight.bitMax;
      if (b.optimizationScore !== a.optimizationScore) return b.optimizationScore - a.optimizationScore;
      return b.pricePerformanceIndex - a.pricePerformanceIndex;
    });
  const unexplored = ranked.filter((candidate) => !excludedKeys.has(candidate.buildKey || candidate.partIds.join("|")));
  const exhausted = ranked.length > 0 && unexplored.length === 0;
  const sourceProfiles = unexplored.length ? unexplored : ranked;
  const profiles = sourceProfiles
    .slice(0, maxBuilds)
    .map((candidate, index) => ({
      ...candidate,
      id: `optimized-${index + 1}`,
      title: exhausted
        ? `검토 완료 상위 조립 #${index + 1}`
        : `N/B MAX 최적화 조립 #${index + 1}`,
      alreadyExplored: exhausted || excludedKeys.has(candidate.buildKey || candidate.partIds.join("|"))
    }));

  return {
    testedCount,
    validCount: candidates.length,
    uniqueCount: ranked.length,
    skippedDuplicateCount: ranked.length - unexplored.length,
    remainingCount: Math.max(unexplored.length - profiles.length, 0),
    exhausted,
    selectedCount: profiles.length,
    profiles
  };
}

function explainBuild(profile, selected, stats) {
  const gpu = selected.find((item) => item.category === "GPU");
  const cpu = selected.find((item) => item.category === "CPU");
  const ram = selected.find((item) => item.category === "RAM");
  const ssd = selected.find((item) => item.category === "SSD");
  const priceText = `${Math.round(stats.totalPrice / 10000).toLocaleString("ko-KR")}만원대`;
  const reasons = [];

  if (cpu && gpu) reasons.push(`${cpu.name}와 ${gpu.name} 조합으로 CPU와 GPU 성능 균형을 맞췄습니다`);
  if (ram) reasons.push(`${ram.name}를 넣어 게임, 작업, 브라우저 동시 사용 여유를 확보했습니다`);
  if (ssd) reasons.push(`${ssd.name}로 운영체제와 작업 파일 저장 공간을 확보했습니다`);
  if (stats.psu?.wattCapacity) reasons.push(`${stats.psu.wattCapacity}W 파워 기준 예상 부하 ${stats.estimatedLoadWatts}W로 계산했습니다`);

  return {
    summary: `${profile.title}은 ${priceText} 예산에서 ${profile.purpose}에 맞춰 계산된 조립 후보입니다.`,
    reasons,
    verdict: stats.warnings.length
      ? "구매 전 호환성 재확인 필요"
      : stats.score >= 70
        ? "현재 자료 기준 추천 가능"
        : "가격 변동을 보고 재검토"
  };
}

function loadOllamaCache() {
  if (!fs.existsSync(OLLAMA_CACHE_FILE)) return {};
  try {
    return JSON.parse(fs.readFileSync(OLLAMA_CACHE_FILE, "utf8"));
  } catch (error) {
    console.error(`[pc-parts-ai] ollama cache load failed: ${error.message}`);
    return {};
  }
}

function saveOllamaCache(cache) {
  const tempFile = `${OLLAMA_CACHE_FILE}.tmp`;
  fs.writeFileSync(tempFile, JSON.stringify(cache, null, 2), "utf8");
  fs.renameSync(tempFile, OLLAMA_CACHE_FILE);
}

function buildOllamaPrompt(build) {
  const partsText = (build.parts || [])
    .map((part) => `${part.category}: ${part.name}, ${part.priceKrw}원, 통합속도 ${part.unifiedSpeedScore}점`)
    .join("\n");
  return [
    "너는 조립 PC 추천 분석 AI다.",
    "아래 완성 PC 조립을 한국어로 짧고 명확하게 평가해라.",
    "출력은 3문장 이내로 한다.",
    "과장하지 말고 가격, 성능, 호환성, 용도를 함께 설명한다.",
    "",
    `조립명: ${build.title}`,
    `총액: ${build.totalPriceKrw}원`,
    `N/B MAX: ${build.nbWeight?.bitMax ?? "-"}`,
    `조합 가중치: ${build.nbWeight?.weightedScore ?? "-"}점`,
    `예상 부하: ${build.estimatedLoadWatts ?? "-"}W`,
    partsText
  ].join("\n");
}

function askOllama(build) {
  const prompt = buildOllamaPrompt(build);
  const cliResult = spawnSync("ollama", ["run", OLLAMA_MODEL, prompt], {
    cwd: SCRIPT_DIR,
    encoding: "utf8",
    timeout: OLLAMA_TIMEOUT_MS,
    windowsHide: true
  });

  if (!cliResult.error && cliResult.status === 0) {
    return String(cliResult.stdout || "").trim().replace(/\s+/g, " ");
  }

  const body = JSON.stringify({
    model: OLLAMA_MODEL,
    prompt,
    stream: false,
    options: {
      temperature: 0.2
    }
  });
  const apiResult = spawnSync("curl", [
    "-s",
    OLLAMA_API_URL,
    "-H",
    "Content-Type: application/json",
    "-d",
    body
  ], {
    cwd: SCRIPT_DIR,
    encoding: "utf8",
    timeout: OLLAMA_TIMEOUT_MS,
    windowsHide: true
  });

  if (!apiResult.error && apiResult.status === 0 && apiResult.stdout) {
    try {
      const payload = JSON.parse(apiResult.stdout);
      if (payload.response) return String(payload.response).trim().replace(/\s+/g, " ");
      if (payload.error) throw new Error(payload.error);
    } catch (error) {
      throw new Error(`ollama api parse failed: ${error.message}`);
    }
  }

  const cliMessage = cliResult.error?.message || cliResult.stderr || `ollama cli exit ${cliResult.status}`;
  const apiMessage = apiResult.error?.message || apiResult.stderr || `ollama api exit ${apiResult.status}`;
  throw new Error(`${cliMessage.trim()} / ${apiMessage.trim()}`);
}

function enrichBuildsWithOllama(builds) {
  if (process.env.PC_PARTS_USE_OLLAMA === "0") return builds;
  const limit = Math.max(0, Number.isFinite(OLLAMA_MAX_BUILDS) ? OLLAMA_MAX_BUILDS : 3);
  if (!limit) return builds;

  const cache = loadOllamaCache();
  let changed = false;
  let used = 0;

  const enriched = builds.map((build) => {
    if (used >= limit) return build;
    const key = buildKey(build);
    if (!key) return build;
    used += 1;

    try {
      if (!cache[key]) {
        cache[key] = {
          model: OLLAMA_MODEL,
          generatedAt: nowKst(),
          summary: askOllama(build)
        };
        changed = true;
      }
      return {
        ...build,
        ollamaModel: cache[key].model || OLLAMA_MODEL,
        aiExplanation: {
          ...(build.aiExplanation || {}),
          summary: cache[key].summary || build.aiExplanation?.summary,
          source: `ollama:${cache[key].model || OLLAMA_MODEL}`
        }
      };
    } catch (error) {
      return {
        ...build,
        ollamaModel: OLLAMA_MODEL,
        aiExplanation: {
          ...(build.aiExplanation || {}),
          source: "local-fallback",
          ollamaError: error.message
        }
      };
    }
  });

  if (changed) saveOllamaCache(cache);
  return enriched;
}

function createTop10(items) {
  return items
    .slice()
    .sort((a, b) => {
      const scoreA = (a.totalScore * 0.55) + (a.valueIndex * 0.25) + (a.aiUseScore * 0.2);
      const scoreB = (b.totalScore * 0.55) + (b.valueIndex * 0.25) + (b.aiUseScore * 0.2);
      return scoreB - scoreA;
    })
    .slice(0, 10)
    .map((item, index) => ({
      rank: index + 1,
      id: item.id,
      category: item.category,
      name: item.name,
      estimatedPriceKrw: item.estimatedPriceKrw,
      speedLabel: item.speedLabel,
      unifiedSpeedScore: item.unifiedSpeedScore,
      totalScore: item.totalScore,
      valueIndex: item.valueIndex,
      aiUseScore: item.aiUseScore,
      recommendation: item.aiExplanation.recommendation,
      aiSummary: item.aiExplanation.summary,
      aiReason: [
        ...item.aiExplanation.strengths,
        item.notes
      ].filter(Boolean).slice(0, 4),
      cautions: item.aiExplanation.cautions,
      sourceQueries: item.sourceQueries,
      imageUrl: item.imageUrl
    }));
}

function createPayload() {
  const source = loadSourceParts();
  const analyzedParts = source.parts.map(analyzePart).sort((a, b) => b.totalScore - a.totalScore);
  const itemsById = partMap(analyzedParts);
  const top10 = createTop10(analyzedParts);
  const levelAnalysis = createLevelAnalysis(analyzedParts);
  const previousState = loadAssemblyState();
  const resetExplored = process.argv.includes("--reset-explored") || previousState?.sourceUpdatedAt !== source.sourceUpdatedAt;
  const exploredKeys = resetExplored ? [] : (previousState?.exploredBuildKeys || []);
  const optimization = createOptimizedBuilds(analyzedParts, 12, {
    excludedKeys: new Set(exploredKeys)
  });
  let builds = optimization.profiles.length
    ? optimization.profiles.map((profile) => analyzeBuild(profile, itemsById))
    : createBuilds(analyzedParts, itemsById, source.sourceType);
  const assemblyState = updateAssemblyState(builds, previousState, {
    sourceUpdatedAt: source.sourceUpdatedAt,
    resetExplored
  });
  builds = ensureCurrentBuildVisible(builds, assemblyState);
  builds = markCurrentAssembly(builds, assemblyState);
  builds = enrichBuildsWithOllama(builds);

  return {
    ok: true,
    topic: "AI 컴퓨터 부품 가격·성능 분석 자료",
    updatedAt: nowKst(),
    intervalSeconds: DEFAULT_INTERVAL_SECONDS,
    speedScoreScale: {
      min: 100,
      max: NB_SCORE_SCALE,
      description: "부품 상태에서는 GHz, MT/s, MB/s, VRAM, W, PCIe 세대처럼 서로 다른 속도·성능 단위를 부품군별 기준으로 100~1000점 통합 속도 점수로 변환합니다."
    },
    nbScoreScale: {
      min: 100,
      max: NB_SCORE_SCALE,
      description: "N/B 값은 부품 단독이 아니라 조립이 완료된 컴퓨터 구성에 대해서만 계산합니다."
    },
    currency: "KRW",
    sourceType: source.sourceType,
    sourceUpdatedAt: source.sourceUpdatedAt,
    nbDatabaseStorage: {
      mode: "per-part-json-files",
      root: "nbData",
      pattern: "nbData/{category}/{part-id}.json",
      categoryFolders: ["cpu", "gpu", "ram", "ssd", "mainboard", "psu"],
      serverLoadPolicy: "현재 수집된 부품만 카테고리별 JSON 파일로 나누어 저장하고, Top 15 랜덤 조합 계산은 사용자 브라우저에서 버튼 클릭 시 실행합니다.",
      partField: "parts[].nbDatabase"
    },
    optimization: {
      target: "가격대와 N/B MAX 값을 함께 높이는 조립 탐색",
      mode: "반복 조립이 아니라 현재 조립 상태를 유지하며 가격대와 N/B MAX가 모두 높아지는 후보가 있을 때만 갱신",
      testedCombinations: optimization.testedCount,
      validCombinations: optimization.validCount,
      uniqueCombinations: optimization.uniqueCount,
      skippedAlreadyChecked: optimization.skippedDuplicateCount,
      remainingCombinations: optimization.remainingCount,
      exhausted: optimization.exhausted,
      selectedBuilds: optimization.selectedCount,
      ranking: "이미 검토한 조립은 제외하고 N/B MAX 우선, 조합 가중치와 가격 대비 성능 보조"
    },
    skippedDuplicateParts: source.skippedDuplicateParts || [],
    assemblyState,
    notice: source.sourceType === "chrome-collected"
      ? "Chrome 브라우저 검색 수집 결과를 우선 사용했습니다. 실제 구매 전에는 판매처 가격과 재고를 다시 확인해야 합니다."
      : "현재 자료는 초기 기준값으로 생성되었습니다. 실제 구매 전에는 판매처 가격과 재고를 다시 확인해야 합니다.",
    method: {
      performance: "성능 지수, 가격, 전력, 용도 태그를 함께 계산합니다.",
      valueIndex: "성능 지수를 예상 가격으로 나누어 가성비를 비교합니다.",
      compatibility: "CPU와 메인보드 플랫폼, 전원 공급 장치 여유를 점검합니다.",
      nextStep: "가격 검색 API, 쇼핑몰 크롤러, 벤치마크 데이터 수집기를 연결하면 자동 갱신형 추천으로 확장할 수 있습니다."
    },
    categories: ["CPU", "GPU", "RAM", "SSD", "Mainboard", "PSU"],
    top10,
    levelAnalysis,
    parts: analyzedParts,
    builds
  };
}

function loadAssemblyState() {
  if (!fs.existsSync(ASSEMBLY_STATE_FILE)) return null;
  try {
    return JSON.parse(fs.readFileSync(ASSEMBLY_STATE_FILE, "utf8"));
  } catch (error) {
    console.error(`[pc-parts-ai] assembly state load failed: ${error.message}`);
    return null;
  }
}

function saveAssemblyState(state) {
  const tempFile = `${ASSEMBLY_STATE_FILE}.tmp`;
  fs.writeFileSync(tempFile, JSON.stringify(state, null, 2), "utf8");
  fs.renameSync(tempFile, ASSEMBLY_STATE_FILE);
}

function buildKey(build) {
  return (build.partIds || []).join("|");
}

function stateFromBuild(build, previousState = null, reason = "initial-assembly", options = {}) {
  const now = nowKst();
  const previousHistory = Array.isArray(previousState?.history) ? previousState.history : [];
  const previousExplored = Array.isArray(previousState?.exploredBuildKeys) ? previousState.exploredBuildKeys : [];
  const exploredBuildKeys = Array.from(new Set([...(options.exploredBuildKeys || previousExplored), buildKey(build)].filter(Boolean)));
  const historyHighestPrice = previousHistory.reduce((max, item) => Math.max(max, Number(item.totalPriceKrw || 0)), 0);
  const state = {
    ok: true,
    mode: "continuous-assembled-state",
    description: "컴퓨터는 계속 조립된 상태로 유지됩니다. 새 후보가 현재 N/B MAX를 넘을 때만 조립 상태를 갱신합니다.",
    sourceUpdatedAt: options.sourceUpdatedAt || previousState?.sourceUpdatedAt || null,
    startedAt: previousState?.startedAt || now,
    lastCheckedAt: now,
    lastChangedAt: reason === "kept-current-assembly" ? previousState?.lastChangedAt || now : now,
    reason,
    currentBuildKey: buildKey(build),
    currentBuild: {
      title: build.title,
      purpose: build.purpose,
      partIds: build.partIds,
      totalPriceKrw: build.totalPriceKrw,
      score: build.score,
      estimatedLoadWatts: build.estimatedLoadWatts,
      recommendedPsuHeadroomWatts: build.recommendedPsuHeadroomWatts,
      pricePerformanceIndex: build.pricePerformanceIndex,
      avgPerformance: build.avgPerformance,
      nbWeight: build.nbWeight,
      warnings: build.warnings || [],
      aiExplanation: build.aiExplanation,
      parts: build.parts
    },
    bestNbMax: Math.max(previousState?.bestNbMax || 0, build.nbWeight?.bitMax || 0),
    highestPriceKrw: Math.max(previousState?.highestPriceKrw || 0, previousState?.currentBuild?.totalPriceKrw || 0, historyHighestPrice, build.totalPriceKrw || 0),
    progressionRule: "현재 조립보다 가격대와 N/B MAX가 모두 높아지는 후보가 있을 때만 다음 조립으로 갱신합니다.",
    exploredBuildKeys,
    exploredCount: exploredBuildKeys.length,
    history: previousHistory
  };

  if (reason !== "kept-current-assembly") {
    state.history = [
      {
        changedAt: now,
        reason,
        title: build.title,
        nbMax: build.nbWeight?.bitMax || 0,
        weightedScore: build.nbWeight?.weightedScore || 0,
        totalPriceKrw: build.totalPriceKrw,
        priceIncreaseKrw: Math.max(0, (build.totalPriceKrw || 0) - (previousState?.currentBuild?.totalPriceKrw || 0)),
        partIds: build.partIds
      },
      ...previousHistory
    ].slice(0, 30);
  }

  return state;
}

function updateAssemblyState(builds, previousState = loadAssemblyState(), options = {}) {
  const candidates = builds
    .filter((build) => build?.nbWeight && Array.isArray(build.partIds))
    .sort((a, b) => {
      if (b.nbWeight.bitMax !== a.nbWeight.bitMax) return b.nbWeight.bitMax - a.nbWeight.bitMax;
      return b.nbWeight.weightedScore - a.nbWeight.weightedScore;
    });
  const exploredBuildKeys = Array.from(new Set([
    ...(options.resetExplored ? [] : (previousState?.exploredBuildKeys || [])),
    ...candidates.map(buildKey)
  ].filter(Boolean)));
  const bestCandidate = candidates[0];
  if (!bestCandidate) {
    const fallbackState = previousState ? {
      ...previousState,
      reason: "no-new-unique-assembly",
      sourceUpdatedAt: options.sourceUpdatedAt || previousState.sourceUpdatedAt || null,
      lastCheckedAt: nowKst(),
      exploredBuildKeys,
      exploredCount: exploredBuildKeys.length
    } : {
      ok: false,
      mode: "continuous-assembled-state",
      description: "유지할 조립 후보가 아직 없습니다.",
      sourceUpdatedAt: options.sourceUpdatedAt || null,
      lastCheckedAt: nowKst(),
      exploredBuildKeys,
      exploredCount: exploredBuildKeys.length
    };
    saveAssemblyState(fallbackState);
    return fallbackState;
  }

  if (!previousState?.currentBuild?.partIds?.length) {
    const nextState = stateFromBuild(bestCandidate, previousState, "initial-assembly", {
      exploredBuildKeys,
      sourceUpdatedAt: options.sourceUpdatedAt
    });
    saveAssemblyState(nextState);
    return nextState;
  }

  const previousNbMax = Number(previousState.bestNbMax || previousState.currentBuild?.nbWeight?.bitMax || 0);
  const previousPriceKrw = Number(previousState.highestPriceKrw || previousState.currentBuild?.totalPriceKrw || 0);
  const currentPriceKrw = Number(previousState.currentBuild?.totalPriceKrw || 0);
  const currentDroppedBelowPriceFloor = currentPriceKrw > 0 && previousPriceKrw > currentPriceKrw;
  const priceFloorCandidate = currentDroppedBelowPriceFloor
    ? candidates
      .filter((build) => Number(build.totalPriceKrw || 0) >= previousPriceKrw)
      .sort((a, b) => {
        const priceStepA = Number(a.totalPriceKrw || 0) - previousPriceKrw;
        const priceStepB = Number(b.totalPriceKrw || 0) - previousPriceKrw;
        if (priceStepA !== priceStepB) return priceStepA - priceStepB;
        return Number(b.nbWeight?.bitMax || 0) - Number(a.nbWeight?.bitMax || 0);
      })[0]
    : null;

  if (priceFloorCandidate) {
    const restoredState = stateFromBuild(priceFloorCandidate, previousState, "price-floor-restored", {
      exploredBuildKeys,
      sourceUpdatedAt: options.sourceUpdatedAt
    });
    saveAssemblyState(restoredState);
    return restoredState;
  }

  const progressiveCandidate = candidates
    .filter((build) => Number(build.totalPriceKrw || 0) > previousPriceKrw)
    .filter((build) => Number(build.nbWeight?.bitMax || 0) > previousNbMax)
    .sort((a, b) => {
      const priceStepA = Number(a.totalPriceKrw || 0) - previousPriceKrw;
      const priceStepB = Number(b.totalPriceKrw || 0) - previousPriceKrw;
      if (priceStepA !== priceStepB) return priceStepA - priceStepB;
      return Number(b.nbWeight?.bitMax || 0) - Number(a.nbWeight?.bitMax || 0);
    })[0];

  if (progressiveCandidate) {
    const nextState = stateFromBuild(progressiveCandidate, previousState, "price-and-nb-max-improved", {
      exploredBuildKeys,
      sourceUpdatedAt: options.sourceUpdatedAt
    });
    saveAssemblyState(nextState);
    return nextState;
  }

  const matchingCurrent = candidates.find((build) => buildKey(build) === previousState.currentBuildKey);
  const keptBuild = matchingCurrent || {
    title: previousState.currentBuild.title,
    purpose: previousState.currentBuild.purpose,
    partIds: previousState.currentBuild.partIds,
    totalPriceKrw: previousState.currentBuild.totalPriceKrw,
    score: previousState.currentBuild.score,
    estimatedLoadWatts: previousState.currentBuild.estimatedLoadWatts,
    recommendedPsuHeadroomWatts: previousState.currentBuild.recommendedPsuHeadroomWatts,
    pricePerformanceIndex: previousState.currentBuild.pricePerformanceIndex,
    avgPerformance: previousState.currentBuild.avgPerformance,
    nbWeight: previousState.currentBuild.nbWeight,
    warnings: previousState.currentBuild.warnings || [],
    aiExplanation: previousState.currentBuild.aiExplanation,
    parts: previousState.currentBuild.parts
  };
  const keptState = stateFromBuild(keptBuild, previousState, "kept-current-assembly", {
    exploredBuildKeys,
    sourceUpdatedAt: options.sourceUpdatedAt
  });
  saveAssemblyState(keptState);
  return keptState;
}

function ensureCurrentBuildVisible(builds, assemblyState) {
  if (!assemblyState?.currentBuildKey || !assemblyState.currentBuild) return builds;
  if (builds.some((build) => buildKey(build) === assemblyState.currentBuildKey)) return builds;
  const current = {
    id: "current-assembly",
    title: assemblyState.currentBuild.title,
    purpose: assemblyState.currentBuild.purpose,
    optimizationTarget: "현재 유지 중인 조립",
    partIds: assemblyState.currentBuild.partIds,
    totalPriceKrw: assemblyState.currentBuild.totalPriceKrw,
    score: assemblyState.currentBuild.score || 0,
    estimatedLoadWatts: assemblyState.currentBuild.estimatedLoadWatts || 0,
    recommendedPsuHeadroomWatts: assemblyState.currentBuild.recommendedPsuHeadroomWatts || 0,
    pricePerformanceIndex: assemblyState.currentBuild.pricePerformanceIndex,
    avgPerformance: assemblyState.currentBuild.avgPerformance,
    nbWeight: assemblyState.currentBuild.nbWeight,
    warnings: assemblyState.currentBuild.warnings || [],
    aiExplanation: assemblyState.currentBuild.aiExplanation,
    parts: assemblyState.currentBuild.parts || []
  };
  return [current, ...builds];
}

function markCurrentAssembly(builds, assemblyState) {
  if (!assemblyState?.currentBuildKey) return builds;
  const marked = builds.map((build) => ({
    ...build,
    currentAssembly: buildKey(build) === assemblyState.currentBuildKey
  }));
  const currentIndex = marked.findIndex((build) => build.currentAssembly);
  if (currentIndex <= 0) return marked;
  const current = marked.splice(currentIndex, 1)[0];
  return [current, ...marked];
}

function normalizePartKey(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9가-힣]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function dedupePartsByNameAndPrice(sourceParts) {
  const seen = new Set();
  const skipped = [];
  const parts = [];

  for (const part of sourceParts) {
    const price = Number(part.estimatedPriceKrw || part.fallbackPriceKrw || 0);
    const key = `${normalizePartKey(part.category)}|${normalizePartKey(part.name)}|${price}`;
    if (seen.has(key)) {
      skipped.push({
        id: part.id,
        category: part.category,
        name: part.name,
        estimatedPriceKrw: price,
        reason: "same-part-and-price"
      });
      continue;
    }

    seen.add(key);
    parts.push(part);
  }

  return { parts, skipped };
}

function loadSourceParts() {
  if (fs.existsSync(RAW_INPUT_FILE)) {
    try {
      const raw = JSON.parse(fs.readFileSync(RAW_INPUT_FILE, "utf8"));
      if (Array.isArray(raw.parts) && raw.parts.length) {
        const deduped = dedupePartsByNameAndPrice(raw.parts);
        if (deduped.skipped.length) {
          console.log(`[pc-parts-ai] skipped duplicate part+price entries=${deduped.skipped.length}`);
        }
        return {
          sourceType: "chrome-collected",
          sourceUpdatedAt: raw.collectedAt || "",
          skippedDuplicateParts: deduped.skipped,
          parts: deduped.parts.map((item) => ({
            id: item.id,
            category: item.category,
            name: item.name,
            maker: item.maker || "Common",
            platform: item.platform || "",
            estimatedPriceKrw: Number(item.estimatedPriceKrw || item.fallbackPriceKrw || 0),
            performance: Number(item.performance || 60),
            powerWatts: Number(item.powerWatts || 0),
            wattCapacity: item.wattCapacity,
            vramGb: item.vramGb,
            speedLabel: item.speedLabel || "",
            tags: item.tags || [],
            notes: item.notes || "Chrome 검색 수집 결과를 바탕으로 분석한 후보입니다.",
            sourceQuery: item.sourceQuery,
            sourceUrl: item.sourceUrl,
            sourceStatus: item.sourceStatus,
            collectedPricesKrw: item.collectedPricesKrw || []
          }))
        };
      }
    } catch (error) {
      console.error(`[pc-parts-ai] raw load failed: ${error.message}`);
    }
  }

  return {
    sourceType: "sample-seed",
    sourceUpdatedAt: "",
    skippedDuplicateParts: [],
    parts
  };
}

function bestPart(items, category, predicate = () => true) {
  return items
    .filter((item) => item.category === category && predicate(item))
    .sort((a, b) => b.nbWeightCandidateScore - a.nbWeightCandidateScore)[0]
    || items.filter((item) => item.category === category).sort((a, b) => b.totalScore - a.totalScore)[0];
}

function createDynamicProfiles(items) {
  const enriched = items.map((item) => ({
    ...item,
    nbWeightCandidateScore: (item.totalScore * 0.42) + (item.unifiedSpeedScore * 0.28) + (item.valueIndex * 0.2) + (item.aiUseScore * 0.1)
  }));

  const budget = [
    bestPart(enriched, "CPU", (item) => item.estimatedPriceKrw < 350000),
    bestPart(enriched, "GPU", (item) => item.estimatedPriceKrw < 700000),
    bestPart(enriched, "RAM", (item) => item.estimatedPriceKrw < 180000),
    bestPart(enriched, "SSD", (item) => item.estimatedPriceKrw < 150000),
    bestPart(enriched, "Mainboard", (item) => item.estimatedPriceKrw < 230000),
    bestPart(enriched, "PSU", (item) => item.estimatedPriceKrw < 150000)
  ].filter(Boolean);

  const creator = [
    bestPart(enriched, "CPU", (item) => item.tags.includes("creator") || item.tags.includes("ai")),
    bestPart(enriched, "GPU", (item) => item.tags.includes("ai") || item.tags.includes("creator")),
    bestPart(enriched, "RAM", (item) => item.tags.includes("ai") || item.name.includes("64")),
    bestPart(enriched, "SSD", (item) => item.tags.includes("ai") || item.name.includes("2TB")),
    bestPart(enriched, "Mainboard"),
    bestPart(enriched, "PSU", (item) => item.tags.includes("ai") || item.wattCapacity >= 800)
  ].filter(Boolean);

  const value = [
    bestPart(enriched, "CPU"),
    bestPart(enriched, "GPU", (item) => item.tags.includes("value") || item.estimatedPriceKrw < 650000),
    bestPart(enriched, "RAM"),
    bestPart(enriched, "SSD"),
    bestPart(enriched, "Mainboard"),
    bestPart(enriched, "PSU")
  ].filter(Boolean);

  return [
    {
      id: "dynamic-budget",
      title: "Chrome 수집 기반 실속형 PC",
      purpose: "검색 수집 가격을 바탕으로 예산 부담을 낮춘 구성",
      partIds: budget.map((item) => item.id)
    },
    {
      id: "dynamic-creator-ai",
      title: "Chrome 수집 기반 AI/작업 PC",
      purpose: "AI, 영상, 개발 작업을 우선해 성능 여유를 둔 구성",
      partIds: creator.map((item) => item.id)
    },
    {
      id: "dynamic-value-gaming",
      title: "Chrome 수집 기반 가성비 게임 PC",
      purpose: "가격 대비 프레임과 통합 속도 점수를 함께 본 구성",
      partIds: value.map((item) => item.id)
    }
  ];
}

function createBuilds(analyzedParts, itemsById, sourceType) {
  const optimized = createOptimizedBuilds(analyzedParts);
  if (optimized.profiles.length) {
    return optimized.profiles.map((profile) => analyzeBuild(profile, itemsById));
  }

  const profiles = sourceType === "chrome-collected"
    ? createDynamicProfiles(analyzedParts)
    : buildProfiles;
  return profiles.map((profile) => analyzeBuild(profile, itemsById));
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

function writeNbDatabaseFiles(payload) {
  const categories = ["CPU", "GPU", "RAM", "SSD", "Mainboard", "PSU"];
  fs.mkdirSync(NB_DATA_DIR, { recursive: true });

  const manifest = {
    schema: "pc-parts-nb-database-manifest.v1",
    updatedAt: payload.updatedAt,
    sourceType: payload.sourceType,
    root: "nbData",
    totalParts: payload.parts.length,
    categories: {}
  };

  for (const category of categories) {
    const folderName = category.toLowerCase();
    const categoryDir = path.join(NB_DATA_DIR, folderName);
    fs.mkdirSync(categoryDir, { recursive: true });
    const categoryParts = payload.parts.filter((part) => part.category === category);
    manifest.categories[folderName] = categoryParts.map((part) => `${safeFileName(part.id)}.json`);

    const categoryIndex = {
      schema: "pc-parts-nb-category-index.v1",
      updatedAt: payload.updatedAt,
      category,
      count: categoryParts.length,
      files: manifest.categories[folderName]
    };

    for (const part of categoryParts) {
      const partPayload = {
        schema: "pc-part-nb-database-file.v1",
        updatedAt: payload.updatedAt,
        category,
        id: part.id,
        name: part.name,
        maker: part.maker,
        platform: part.platform,
        estimatedPriceKrw: part.estimatedPriceKrw,
        priceBand: part.priceBand,
        speedLabel: part.speedLabel,
        speedMetric: part.speedMetric,
        unifiedSpeedScore: part.unifiedSpeedScore,
        performance: part.performance,
        valueIndex: part.valueIndex,
        aiUseScore: part.aiUseScore,
        powerWatts: part.powerWatts || null,
        tags: part.tags || [],
        nbDatabase: part.nbDatabase,
        nbWeightedScore: part.nbWeightedScore,
        nbMax: part.nbMax,
        nbMin: part.nbMin,
        nbBand: part.nbBand,
        sourceType: part.sourceType,
        sourceUrl: part.sourceUrl || null,
        notes: part.notes || ""
      };
      const filePath = path.join(categoryDir, `${safeFileName(part.id)}.json`);
      fs.writeFileSync(`${filePath}.tmp`, JSON.stringify(partPayload, null, 2), "utf8");
      fs.renameSync(`${filePath}.tmp`, filePath);
    }

    const indexPath = path.join(categoryDir, "index.json");
    fs.writeFileSync(`${indexPath}.tmp`, JSON.stringify(categoryIndex, null, 2), "utf8");
    fs.renameSync(`${indexPath}.tmp`, indexPath);
  }

  const manifestPath = path.join(NB_DATA_DIR, "manifest.json");
  fs.writeFileSync(`${manifestPath}.tmp`, JSON.stringify(manifest, null, 2), "utf8");
  fs.renameSync(`${manifestPath}.tmp`, manifestPath);
}

async function runOnce() {
  const payload = createPayload();
  writeJson(payload);
  writeNbDatabaseFiles(payload);
  console.log(`[${payload.updatedAt}] [pc-parts-ai] wrote ${OUTPUT_FILE}`);
  console.log(`[pc-parts-ai] wrote N/B database files ${NB_DATA_DIR}`);
  console.log(`[pc-parts-ai] parts=${payload.parts.length}, top10=${payload.top10.length}, builds=${payload.builds.length}`);
}

async function run() {
  const loop = process.argv.includes("--loop");
  const intervalIndex = process.argv.indexOf("--interval");
  const intervalSeconds = intervalIndex >= 0
    ? Number(process.argv[intervalIndex + 1] || DEFAULT_INTERVAL_SECONDS)
    : DEFAULT_INTERVAL_SECONDS;
  const safeIntervalSeconds = Math.max(30, Number.isFinite(intervalSeconds) ? intervalSeconds : DEFAULT_INTERVAL_SECONDS);

  do {
    await runOnce();
    if (!loop) break;
    console.log(`[pc-parts-ai] next run in ${safeIntervalSeconds} seconds`);
    await new Promise((resolve) => setTimeout(resolve, safeIntervalSeconds * 1000));
  } while (true);
}

run().catch((error) => {
  console.error(`[pc-parts-ai] failed: ${error.message}`);
  process.exit(1);
});
