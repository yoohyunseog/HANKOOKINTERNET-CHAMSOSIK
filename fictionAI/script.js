const steps = [
  { title: "세계 상태 초기화", detail: "기준 규칙, 시간축, 메모리 루트 설정" },
  { title: "장면 생성", detail: "시간, 장소, 인물, 환경을 결합해 Scene Birth 수행" },
  { title: "상호작용 발생", detail: "이동, 대화, 충돌, 선택 중 하나의 이벤트 발화" },
  { title: "물리·규칙 평가", detail: "가능 여부, 비용, 제약, 확률 가중치 계산" },
  { title: "상태 변화", detail: "과거, 현재, 미래, -0- 관계 갱신" },
  { title: "기억 저장", detail: "현재 장면 커밋 + prev / next 연결" },
  { title: "의미 해석", detail: "유사도, 변화율, 의도 점수 계산" },
  { title: "다음 장면 예측", detail: "미래 후보 장면 초안 생성" },
  { title: "검증·정정", detail: "충돌, 모순, 단절을 검사하고 수정" },
  { title: "연속 진입", detail: "세계 재초기화 없이 다음 장면 루프로 진입" }
];

const actors = ["기록자", "항해사", "감시자", "아이", "사서"];
const places = ["유리 온실", "침수된 광장", "기록 보관소", "해안 관측소", "철제 복도"];
const moods = ["긴장", "정적", "기대", "왜곡", "회복"];
const supportRoles = ["관찰자", "조력자", "반대자", "증인", "기록 대상"];

const MONITOR_JSON_URL = "/api/world-monitor";
const OLLAMA_URL = "/api/ollama-scene";
const OLLAMA_MODEL = "deepseek-v3.1:671b-cloud";

const state = {
  cycle: 0,
  activeStep: 0,
  memory: [],
  currentScene: null,
  futureDrafts: [],
  aiInterpretation: "",
  monitor: null,
  worldSeed: {
    id: "-0-",
    title: "유리 해안 기록권",
    premise: "바다가 도시에 스며든 뒤, 모든 기억은 장면 단위로 저장되고 미래는 초안 상태로만 존재한다.",
    era: "붕괴 이후 37년",
    tone: "잔잔하지만 불안정한 기록 판타지",
    rules: [
      "시간은 연속된다",
      "장면은 prev를 가진다",
      "미래는 복수 후보를 허용한다"
    ]
  }
};

const flowEl = document.getElementById("flow");
const worldIntro = document.getElementById("worldIntro");
const monitorCard = document.getElementById("monitorCard");
const cycleValue = document.getElementById("cycleValue");
const sceneValue = document.getElementById("sceneValue");
const actorValue = document.getElementById("actorValue");
const scoreValue = document.getElementById("scoreValue");
const summaryValue = document.getElementById("summaryValue");
const previousSceneCard = document.getElementById("previousSceneCard");
const rulesList = document.getElementById("rulesList");
const characterList = document.getElementById("characterList");
const logEl = document.getElementById("log");
const zeroCard = document.getElementById("zeroCard");
const pastCard = document.getElementById("pastCard");
const presentCard = document.getElementById("presentCard");
const futureList = document.getElementById("futureList");
const memoryList = document.getElementById("memoryList");
const aiCard = document.getElementById("aiCard");
const generateAiBtn = document.getElementById("generateAiBtn");

function pick(list, offset = 0) {
  return list[(state.cycle + offset) % list.length];
}

function renderFlow() {
  flowEl.innerHTML = "";
  steps.forEach((step, index) => {
    const node = document.createElement("div");
    node.className = `step${index === state.activeStep ? " active" : ""}`;
    node.innerHTML = `
      <div class="step-tag">Step ${index + 1}</div>
      <strong>${step.title}</strong>
      <small>${step.detail}</small>
    `;
    flowEl.appendChild(node);
  });
}

function renderWorldIntro() {
  const monitorHeadline = state.monitor ? state.monitor.headline : "세계 모니터가 아직 연결되지 않았습니다.";
  worldIntro.innerHTML = `
    <div class="world-card">
      <div class="world-title">${state.worldSeed.title}</div>
      <div class="world-meta">시대: ${state.worldSeed.era}</div>
      <div class="world-meta">톤: ${state.worldSeed.tone}</div>
      <p class="world-text">${state.worldSeed.premise}</p>
      <p class="world-text"><strong>현재 세계 헤드라인:</strong> ${monitorHeadline}</p>
      <ul class="world-rules">
        ${state.worldSeed.rules.map((rule) => `<li>${rule}</li>`).join("")}
      </ul>
    </div>
  `;
}

async function loadMonitorData() {
  try {
    const response = await fetch(MONITOR_JSON_URL);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    state.monitor = await response.json();
    addLog(`월드 모니터 로드 완료: ${state.monitor.model || OLLAMA_MODEL}`);
  } catch (error) {
    state.monitor = null;
    addLog(`월드 모니터 로드 실패: ${error.message}`);
  }
  renderWorld();
}

function renderMonitorCard() {
  if (!state.monitor) {
    monitorCard.innerHTML = `
      <div class="monitor-title">이벤트 데이터 없음</div>
      <div class="monitor-text">world-monitor-ai.json을 불러오지 못했습니다. fictionAI 서버를 통해 실행 중인지 확인해 주세요.</div>
      <div class="monitor-meta">API 경로: <code>${MONITOR_JSON_URL}</code></div>
    `;
    return;
  }

  const items = Array.isArray(state.monitor.items) ? state.monitor.items.slice(0, 3) : [];
  monitorCard.innerHTML = `
    <div class="monitor-title">${state.monitor.title || "월드 모니터 이벤트"}</div>
    <div class="monitor-meta">모델: ${state.monitor.model || OLLAMA_MODEL}</div>
    <div class="monitor-meta">업데이트: ${state.monitor.updated_at || "-"}</div>
    <div class="monitor-text">${state.monitor.summary || "요약 없음"}</div>
    <ul class="monitor-list">
      ${items.map((item) => `<li>${item.title || "이벤트"}</li>`).join("")}
    </ul>
  `;
}

function buildCast(mainActor, mood, eventLabel) {
  return [
    { name: mainActor, role: "주인공", state: `${mood} 상태`, intent: `${eventLabel}에 반응` },
    { name: pick(actors, 1), role: pick(supportRoles, 1), state: "장면 반응 추적", intent: "주인공의 선택을 관찰" },
    { name: pick(actors, 2), role: pick(supportRoles, 2), state: "긴장도 상승", intent: "갈등 또는 협력 가능성 보유" }
  ];
}

function buildScene() {
  const actor = pick(actors);
  const place = pick(places, 1);
  const mood = pick(moods, 2);
  const monitorItems = state.monitor && Array.isArray(state.monitor.items) ? state.monitor.items : [];
  const monitorEvent = monitorItems.length > 0 ? monitorItems[state.cycle % monitorItems.length] : null;
  const eventLabel = monitorEvent ? (monitorEvent.title || "세계 이벤트") : "기본 사건";
  const id = `scene-${String(state.cycle + 1).padStart(3, "0")}`;
  const prevScene = state.memory[0] || null;
  const prevId = prevScene ? prevScene.id : state.worldSeed.id;
  const score = Number((0.42 + ((state.cycle * 0.137) % 0.47)).toFixed(2));

  return {
    id,
    prev_id: prevId,
    actor,
    place,
    mood,
    event: eventLabel,
    score,
    cast: buildCast(actor, mood, eventLabel),
    previous_scene: prevScene,
    source_event: monitorEvent,
    monitor_summary: monitorEvent ? (monitorEvent.description || state.monitor?.summary || "") : "",
    summary: `${actor}가 ${place}에서 "${eventLabel}" 사건에 반응하며 ${mood} 상태를 만든 장면`,
    rules: [
      `${eventLabel} 가능 여부: 허용`,
      `비용 평가: ${2 + (state.cycle % 4)}`,
      "제약 검사: prev 연결 유지"
    ],
    validation: [
      "시간 역행 없음",
      "인물 중복 충돌 없음",
      `prev 연결: ${prevId}`
    ]
  };
}

function buildFutureDrafts(scene) {
  return [
    `${scene.actor}가 다음 장면에서 선택을 보류한다`,
    `${scene.place}의 환경 변수가 바뀌어 충돌 비용이 증가한다`,
    `${scene.prev_id}와의 의미 유사도가 높은 회상 장면이 개입한다`
  ];
}

function commitScene(scene) {
  state.memory.unshift({
    id: scene.id,
    prev_id: scene.prev_id,
    actor: scene.actor,
    place: scene.place,
    summary: scene.summary,
    score: scene.score
  });
  state.memory = state.memory.slice(0, 6);
}

function addLog(message) {
  const entry = document.createElement("div");
  entry.className = "log-entry";
  entry.textContent = message;
  logEl.prepend(entry);
  while (logEl.children.length > 8) {
    logEl.removeChild(logEl.lastChild);
  }
}

function renderRules() {
  rulesList.innerHTML = "";
  const rules = state.currentScene ? state.currentScene.rules : state.worldSeed.rules;
  rules.forEach((rule) => {
    const item = document.createElement("li");
    item.className = "rule-item";
    item.textContent = rule;
    rulesList.appendChild(item);
  });
}

function renderCharacters() {
  characterList.innerHTML = "";
  const cast = state.currentScene ? state.currentScene.cast : [];
  if (cast.length === 0) {
    const empty = document.createElement("div");
    empty.className = "character-card";
    empty.textContent = "세계관 소개 단계입니다. 첫 장면이 생성되면 등장인물 목록이 표시됩니다.";
    characterList.appendChild(empty);
    return;
  }

  cast.forEach((character) => {
    const card = document.createElement("div");
    card.className = "character-card";
    card.innerHTML = `
      <div class="character-head">
        <span class="character-name">${character.name}</span>
        <span class="character-role">${character.role}</span>
      </div>
      <div class="character-meta">상태: ${character.state}</div>
      <div class="character-meta">의도: ${character.intent}</div>
    `;
    characterList.appendChild(card);
  });
}

function renderPreviousScene() {
  previousSceneCard.innerHTML = "";
  if (!state.currentScene || !state.currentScene.previous_scene) {
    previousSceneCard.innerHTML = `
      <div class="flashback-card empty">
        <div class="flashback-title">세계관 시작점</div>
        <div class="flashback-text">첫 장면 전에는 과거 장면 대신 세계관 시드가 기준점으로 작동합니다.</div>
      </div>
    `;
    return;
  }

  const prev = state.currentScene.previous_scene;
  previousSceneCard.innerHTML = `
    <div class="flashback-card">
      <div class="flashback-title">포함된 과거 장면</div>
      <div class="flashback-text"><strong>${prev.id}</strong> | ${prev.summary}</div>
      <div class="flashback-meta">배우: ${prev.actor} | 장소: ${prev.place}</div>
      <div class="flashback-meta">현재 장면은 이 장면을 기억한 채 진행됩니다.</div>
    </div>
  `;
}

function renderFutureDrafts() {
  futureList.innerHTML = "";
  const drafts = state.futureDrafts.length > 0 ? state.futureDrafts : ["미래 후보가 아직 생성되지 않았습니다."];
  drafts.forEach((draft, index) => {
    const item = document.createElement("li");
    item.className = "future-item";
    item.textContent = state.futureDrafts.length > 0 ? `Draft ${index + 1}. ${draft}` : draft;
    futureList.appendChild(item);
  });
}

function renderMemory() {
  memoryList.innerHTML = "";
  if (state.memory.length === 0) {
    const empty = document.createElement("li");
    empty.className = "memory-item";
    empty.textContent = "아직 커밋된 장면이 없습니다.";
    memoryList.appendChild(empty);
    return;
  }

  state.memory.forEach((item) => {
    const row = document.createElement("li");
    row.className = "memory-item";
    row.innerHTML = `<strong>${item.id}</strong><br>prev: <code>${item.prev_id}</code><br>${item.summary}<br>score: ${item.score.toFixed(2)}`;
    memoryList.appendChild(row);
  });
}

function renderAiCard() {
  if (!state.aiInterpretation) {
    aiCard.innerHTML = `
      <div class="ai-title">AI 대기 상태</div>
      <div class="ai-meta">모델: ${OLLAMA_MODEL}</div>
      <div class="ai-text">장면 생성 후 "AI 장면 해석 생성" 버튼을 누르면 Ollama가 현재 장면을 해석합니다.</div>
    `;
    return;
  }

  aiCard.innerHTML = `
    <div class="ai-title">AI Scene Interpretation</div>
    <div class="ai-meta">모델: ${OLLAMA_MODEL}</div>
    <div class="ai-text">${state.aiInterpretation.replace(/\n/g, "<br>")}</div>
  `;
}

async function generateAiInterpretation() {
  if (!state.currentScene) {
    state.aiInterpretation = "현재 장면이 아직 없습니다. 먼저 한 사이클을 실행해 주세요.";
    renderAiCard();
    return;
  }

  generateAiBtn.disabled = true;
  state.aiInterpretation = "Ollama가 장면을 해석하는 중입니다...";
  renderAiCard();

  const prompt = [
    "당신은 세계관 기반 장면 해석 AI다.",
    "과거-현재-미래 장면 데이터베이스를 분석한다.",
    `세계관: ${state.worldSeed.title}`,
    `세계 설명: ${state.worldSeed.premise}`,
    `현재 장면 ID: ${state.currentScene.id}`,
    `현재 장면 요약: ${state.currentScene.summary}`,
    `장소: ${state.currentScene.place}`,
    `주요 인물: ${state.currentScene.cast.map((c) => `${c.name}(${c.role})`).join(", ")}`,
    `직전 장면: ${state.currentScene.previous_scene ? state.currentScene.previous_scene.summary : "없음"}`,
    `세계 모니터 헤드라인: ${state.monitor ? state.monitor.headline : "없음"}`,
    `이벤트 요약: ${state.currentScene.monitor_summary || "없음"}`,
    "요구사항: 1) 현재 장면 의미 2) 과거와의 연결 3) 다음 장면 예측을 한국어 3문단 이내로 작성"
  ].join("\n");

  try {
    const response = await fetch(OLLAMA_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    state.aiInterpretation = data.response?.trim() || "응답은 왔지만 비어 있습니다.";
    addLog(`Ollama 해석 완료: ${OLLAMA_MODEL}`);
  } catch (error) {
    state.aiInterpretation = `Ollama 호출 실패: ${error.message}\nfictionAI 서버와 Ollama 실행 상태를 확인해 주세요.`;
    addLog(`Ollama 호출 실패: ${error.message}`);
  } finally {
    generateAiBtn.disabled = false;
    renderAiCard();
  }
}

function renderWorld() {
  renderWorldIntro();
  renderMonitorCard();
  cycleValue.textContent = String(state.cycle);
  sceneValue.textContent = state.currentScene ? state.currentScene.id : "-0-";
  actorValue.textContent = state.currentScene ? state.currentScene.actor : "Observer";
  scoreValue.textContent = state.currentScene ? state.currentScene.score.toFixed(2) : "0.00";
  summaryValue.textContent = state.currentScene
    ? state.currentScene.summary
    : `${state.worldSeed.title}의 세계관이 준비되었습니다. 첫 장면을 실행해 주세요.`;

  zeroCard.textContent = `${state.worldSeed.title} | ${state.worldSeed.premise}`;
  pastCard.textContent = state.memory[1]
    ? `${state.memory[1].id} | ${state.memory[1].summary}`
    : "아직 저장된 과거 장면이 없습니다.";
  presentCard.textContent = state.currentScene
    ? `${state.currentScene.id} | prev: ${state.currentScene.prev_id} | ${state.currentScene.summary}`
    : "현재 장면이 생성되면 여기 표시됩니다.";

  renderRules();
  renderCharacters();
  renderPreviousScene();
  renderFutureDrafts();
  renderMemory();
  renderAiCard();
  renderFlow();
}

function runCycle() {
  state.cycle += 1;
  state.activeStep = 1;
  const scene = buildScene();
  state.currentScene = scene;
  addLog(`[${scene.id}] 장면 생성: ${scene.actor} @ ${scene.place}`);

  state.activeStep = 2;
  addLog(`[${scene.id}] 이벤트 발생: ${scene.event}`);

  state.activeStep = 3;
  addLog(`[${scene.id}] 규칙 평가 완료: 비용 ${2 + (state.cycle % 4)}`);

  state.activeStep = 4;
  addLog(`[${scene.id}] 상태 전이: past/present/future 갱신`);

  state.activeStep = 5;
  commitScene(scene);
  addLog(`[${scene.id}] 메모리 커밋: prev=${scene.prev_id}`);

  state.activeStep = 6;
  addLog(`[${scene.id}] 의미 해석: intent score ${scene.score.toFixed(2)}`);

  state.activeStep = 7;
  state.futureDrafts = buildFutureDrafts(scene);
  addLog(`[${scene.id}] 미래 초안 ${state.futureDrafts.length}개 생성`);

  state.activeStep = 8;
  addLog(`[${scene.id}] 검증 완료: ${scene.validation.join(", ")}`);

  state.activeStep = 9;
  addLog(`[${scene.id}] 다음 장면 루프로 연속 진입 준비`);
  renderWorld();
}

function advanceStep() {
  if (!state.currentScene || state.activeStep >= steps.length - 1) {
    runCycle();
    return;
  }
  state.activeStep += 1;
  addLog(`단계 이동: ${steps[state.activeStep].title}`);
  renderWorld();
}

function resetWorld() {
  state.cycle = 0;
  state.activeStep = 0;
  state.memory = [];
  state.currentScene = null;
  state.futureDrafts = [];
  state.aiInterpretation = "";
  logEl.innerHTML = "";
  addLog("세계 상태 초기화 완료. 세계관 시드가 다시 로드되었습니다.");
  renderWorld();
}

document.getElementById("runCycleBtn").addEventListener("click", runCycle);
document.getElementById("advanceStepBtn").addEventListener("click", advanceStep);
document.getElementById("resetBtn").addEventListener("click", resetWorld);
generateAiBtn.addEventListener("click", generateAiInterpretation);

resetWorld();
loadMonitorData();
