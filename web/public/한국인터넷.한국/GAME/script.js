const canvas = document.querySelector("#battlefield");
const ctx = canvas.getContext("2d");

const state = {
  minute: 12 * 60,
  phase: 1,
  paused: false,
  gameOver: false,
  needsRender: false,
  activeScreen: "situation",
  selectedZone: 1,
  nextCalcIn: 5,
  autoSortPlans: true,
  planSort: "weight",
  resources: {
    hull: 100,
    fuel: 78,
    ammo: 72,
    morale: 84,
    intel: 42,
    deck: 82
  },
  zones: [
    { id: "nw", name: "북서 해역", x: 220, y: 170, radius: 96, threat: 62, detected: true, enemy: "미사일 기지", operation: "타격 대기", control: 44, kind: "missile" },
    { id: "ne", name: "북동 공역", x: 710, y: 145, radius: 104, threat: 58, detected: true, enemy: "적 전투기", operation: "CAP 필요", control: 48, kind: "air" },
    { id: "east", name: "동해 항로", x: 785, y: 430, radius: 102, threat: 43, detected: true, enemy: "잠수함", operation: "보급선 감시", control: 57, kind: "sub" },
    { id: "ew", name: "전자전 구역", x: 475, y: 255, radius: 92, threat: 36, detected: true, enemy: "교란 신호", operation: "주파수 분석", control: 61, kind: "ew" },
    { id: "deep", name: "심해 접촉 구역", x: 315, y: 500, radius: 105, threat: 48, detected: false, enemy: "정체불명", operation: "정찰 필요", control: 51, kind: "unknown" }
  ],
  carrier: { x: 480, y: 430 },
  escorts: [
    { id: "DDG-1", x: 390, y: 380, orbit: 0.2, radius: 112, color: "#7ee083" },
    { id: "DDG-2", x: 580, y: 380, orbit: 2.2, radius: 125, color: "#7ee083" },
    { id: "FFG-1", x: 430, y: 520, orbit: 4.1, radius: 104, color: "#4ab3ff" }
  ],
  units: [
    { id: "CAP-1", label: "FTR", type: "fighter", color: "#42e6d8", x: 470, y: 415, target: null, status: "대기", ready: true, speed: 1.35 },
    { id: "CAP-2", label: "FTR", type: "fighter", color: "#42e6d8", x: 500, y: 420, target: null, status: "대기", ready: true, speed: 1.3 },
    { id: "REC-1", label: "REC", type: "recon", color: "#b784ff", x: 460, y: 450, target: null, status: "대기", ready: true, speed: 1.05, scan: 90 },
    { id: "ASW-1", label: "ASW", type: "heli", color: "#7ee083", x: 515, y: 450, target: null, status: "대기", ready: true, speed: 0.9 },
    { id: "SUP-1", label: "SUP", type: "supply", color: "#f4d35e", x: 445, y: 470, target: null, status: "대기", ready: true, speed: 0.78 }
  ],
  plans: [
    { id: "PL-07", name: "우회 기동 후 타격", desc: "방공 밀도가 낮은 외곽 항로로 접근한 뒤 핵심 위협을 타격합니다.", weight: 31, success: 68, survival: 58, fatigue: 42, time: 15, tags: ["AIR", "NAVY", "EW"] },
    { id: "PL-12", name: "유인 작전", desc: "가짜 항적과 전자 신호로 적 미사일 발사 타이밍을 끌어냅니다.", weight: 28, success: 62, survival: 71, fatigue: 36, time: 12, tags: ["EW", "DRONE"] },
    { id: "PL-03", name: "야간 침투 작전", desc: "저피탐 경로를 이용해 정체불명 접촉을 가까이서 식별합니다.", weight: 26, success: 57, survival: 52, fatigue: 55, time: 18, tags: ["UDT", "RECON"] },
    { id: "PL-15", name: "전자전 교란 후 타격", desc: "교란으로 적 탐지망을 낮춘 뒤 타격 편대를 투입합니다.", weight: 38, success: 73, survival: 64, fatigue: 47, time: 14, tags: ["EW", "AIR"] },
    { id: "PL-02", name: "대잠 집중 탐색", desc: "헬기와 음탐 정보를 묶어 보급선 주변 잠수함을 추적합니다.", weight: 34, success: 70, survival: 67, fatigue: 45, time: 13, tags: ["ASW", "NAVY"] },
    { id: "PL-09", name: "다축 동시 압박", desc: "공중, 해상, 전자전 압박을 동시에 걸어 위협 성장을 늦춥니다.", weight: 24, success: 61, survival: 49, fatigue: 64, time: 20, tags: ["AIR", "NAVY", "EW"] },
    { id: "PL-18", name: "정밀 타격", desc: "정찰 데이터가 충분할 때 미사일 기지 위협을 크게 낮춥니다.", weight: 33, success: 76, survival: 55, fatigue: 50, time: 16, tags: ["AIR", "INTEL"] },
    { id: "PL-05", name: "연막 기동 후 철수", desc: "위협 과포화 시 항모 기동로를 숨기고 전단을 재정렬합니다.", weight: 22, success: 60, survival: 82, fatigue: 34, time: 10, tags: ["NAVY", "EW"] }
  ],
  crew: [
    { name: "강하준", role: "함장", dept: "함교 운영", focus: 88, fatigue: 22, stress: 31, ready: 91, plans: 2, status: "정상" },
    { name: "서민재", role: "항공전술장교", dept: "항공운용", focus: 82, fatigue: 38, stress: 44, ready: 78, plans: 3, status: "주의" },
    { name: "윤지오", role: "전투정보장교", dept: "전투정보", focus: 91, fatigue: 34, stress: 39, ready: 84, plans: 4, status: "임무 중" },
    { name: "박도현", role: "대잠전술장교", dept: "대잠전", focus: 76, fatigue: 46, stress: 48, ready: 72, plans: 2, status: "주의" },
    { name: "한유라", role: "전자전장교", dept: "전자전", focus: 86, fatigue: 29, stress: 37, ready: 86, plans: 3, status: "정상" },
    { name: "정시우", role: "UDT 지휘관", dept: "특수전", focus: 72, fatigue: 58, stress: 54, ready: 63, plans: 1, status: "피로" },
    { name: "오나린", role: "의무장교", dept: "의무/지원", focus: 79, fatigue: 24, stress: 28, ready: 88, plans: 1, status: "정상" },
    { name: "문태성", role: "기관장", dept: "정비/무장", focus: 74, fatigue: 51, stress: 52, ready: 67, plans: 2, status: "피로" }
  ],
  enemies: [],
  projectiles: [],
  effects: [],
  logs: [],
  mapMessages: [],
  result: ""
};

const commands = [
  { id: "cap", name: "긴급 CAP", desc: "공중 위협 감소", unit: "fighter", cost: { fuel: 8, deck: 4 }, tags: ["AIR"] },
  { id: "strike", name: "타격", desc: "큰 위협 제압", unit: "fighter", cost: { fuel: 12, ammo: 16, deck: 6 }, tags: ["AIR", "NAVY"] },
  { id: "asw", name: "대잠 탐지", desc: "잠수함 추적", unit: "heli", cost: { fuel: 9, deck: 4 }, tags: ["ASW"] },
  { id: "recon", name: "장거리 정찰", desc: "숨은 위협 공개", unit: "recon", cost: { fuel: 7, deck: 3 }, tags: ["RECON"] },
  { id: "ew", name: "전자전 교란", desc: "전체 위협 둔화", unit: null, cost: { intel: 16 }, tags: ["EW"] },
  { id: "supply", name: "보급선 보호", desc: "연료와 탄약 회복", unit: "supply", cost: { deck: 5 }, tags: ["NAVY"] },
  { id: "repair", name: "갑판 복구", desc: "갑판과 함체 회복", unit: null, cost: { morale: 6 }, tags: ["MAINT"] }
];

const labels = { hull: "함체", fuel: "연료", ammo: "탄약", morale: "사기", intel: "정보", deck: "갑판" };
const threatLabels = { air: "공중", missile: "미사일", sub: "잠수함", ew: "전자전", unknown: "보급선" };

function clamp(value, min = 0, max = 100) {
  return Math.max(min, Math.min(max, value));
}

function formatTime(minute) {
  const h = Math.floor(minute / 60);
  const m = minute % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

function addLog(message, type = "info") {
  state.logs.unshift({ time: formatTime(state.minute), message, type });
  state.logs = state.logs.slice(0, 18);
  state.mapMessages.unshift({ time: formatTime(state.minute), message, type, life: 360, max: 360 });
  state.mapMessages = state.mapMessages.slice(0, 4);
  state.needsRender = true;
}

function selectedZone() {
  return state.zones[state.selectedZone];
}

function spend(cost) {
  const possible = Object.entries(cost).every(([key, value]) => state.resources[key] >= value);
  if (!possible) return false;
  Object.entries(cost).forEach(([key, value]) => {
    state.resources[key] = clamp(state.resources[key] - value);
  });
  return true;
}

function averageControl() {
  return state.zones.reduce((sum, zone) => sum + zone.control, 0) / state.zones.length;
}

function averageCrew(field) {
  return state.crew.reduce((sum, crew) => sum + crew[field], 0) / state.crew.length;
}

function moveToward(obj, target, speed) {
  const dx = target.x - obj.x;
  const dy = target.y - obj.y;
  const length = Math.hypot(dx, dy);
  if (length < speed) {
    obj.x = target.x;
    obj.y = target.y;
    return true;
  }
  obj.x += (dx / length) * speed;
  obj.y += (dy / length) * speed;
  return false;
}

function nearestReadyUnit(type) {
  return state.units.find((unit) => unit.type === type && unit.ready);
}

function command(id) {
  if (id === "restart") {
    window.location.reload();
    return;
  }
  if (state.gameOver) return;

  const config = commands.find((item) => item.id === id);
  if (!config) return;

  if (!spend(config.cost)) {
    addLog("자원이 부족해 명령을 실행할 수 없습니다.", "warn");
    render();
    return;
  }

  stressCrew(config.tags, id === "repair" ? -4 : 4);

  if (id === "ew") {
    state.zones.forEach((zone) => {
      zone.threat = clamp(zone.threat - 7);
      zone.detected = true;
    });
    state.resources.intel = clamp(state.resources.intel + 5);
    state.effects.push({ type: "jam", x: state.carrier.x, y: state.carrier.y, life: 90, max: 90 });
    addLog("전자전 교란 카드 실행. 적 탐지와 유도 체계가 둔화됩니다.", "good");
    render();
    return;
  }

  if (id === "repair") {
    state.resources.deck = clamp(state.resources.deck + 18);
    state.resources.hull = clamp(state.resources.hull + 8);
    state.effects.push({ type: "repair", x: state.carrier.x, y: state.carrier.y, life: 70, max: 70 });
    addLog("갑판 복구 카드 실행. 발함 능력과 함체 손상이 회복됩니다.", "good");
    render();
    return;
  }

  const unit = nearestReadyUnit(config.unit);
  if (!unit) {
    Object.entries(config.cost).forEach(([key, value]) => {
      state.resources[key] = clamp(state.resources[key] + value);
    });
    addLog("가용 편대가 없어 명령을 보류했습니다.", "warn");
    render();
    return;
  }

  const zone = selectedZone();
  unit.ready = false;
  unit.command = id;
  unit.target = zone.id;
  unit.status = `${zone.name} 이동`;
  zone.operation = `${config.name} 진행`;
  addLog(`${unit.id} ${config.name} 출격: ${zone.name}`);
  render();
}

function stressCrew(tags, delta) {
  const tagDept = {
    AIR: "항공운용",
    ASW: "대잠전",
    EW: "전자전",
    NAVY: "함교 운영",
    RECON: "전투정보",
    MAINT: "정비/무장",
    UDT: "특수전",
    INTEL: "전투정보"
  };
  tags.forEach((tag) => {
    state.crew.filter((crew) => crew.dept === tagDept[tag]).forEach((crew) => {
      crew.fatigue = clamp(crew.fatigue + delta);
      crew.stress = clamp(crew.stress + delta * 0.8);
      crew.ready = clamp(crew.ready - delta * 0.7);
      crew.status = crew.fatigue > 55 ? "피로" : crew.stress > 50 ? "주의" : "정상";
    });
  });
}

function resolveUnit(unit) {
  const zone = state.zones.find((item) => item.id === unit.target);
  if (!zone) return;

  const effects = { cap: 24, strike: zone.threat > 65 ? 34 : 24, asw: 31, recon: 8, supply: -10 };

  if (unit.command === "recon") {
    zone.detected = true;
    state.resources.intel = clamp(state.resources.intel + 18);
    addLog(`${unit.id} 정찰 완료. ${zone.name} 위협 정보가 갱신됐습니다.`, "good");
  } else if (unit.command === "supply") {
    state.resources.fuel = clamp(state.resources.fuel + 20);
    state.resources.ammo = clamp(state.resources.ammo + 16);
    zone.control = clamp(zone.control + 5);
    addLog(`${unit.id} 보급선 보호 완료. 연료와 탄약을 확보했습니다.`, "good");
  } else {
    const kindBonus = (unit.command === "cap" && ["air", "missile"].includes(zone.kind)) || (unit.command === "asw" && ["sub", "unknown"].includes(zone.kind));
    const effect = (effects[unit.command] || 10) + (kindBonus ? 8 : 0);
    zone.threat = clamp(zone.threat - effect);
    zone.control = clamp(zone.control + effect * 0.45);
    addLog(`${unit.id} 교전 완료. ${zone.name} 위협도 ${Math.round(effect)} 감소.`, "good");
  }

  if (Math.random() * 100 < Math.max(4, zone.threat / 7)) {
    state.resources.morale = clamp(state.resources.morale - 3);
    state.resources.deck = clamp(state.resources.deck - 3);
    addLog(`${unit.id} 귀환 중 손상 보고. 갑판 정비 부담이 증가했습니다.`, "warn");
  }

  state.effects.push({ type: "burst", x: zone.x, y: zone.y, life: 44, max: 44 });
  unit.target = null;
  unit.command = null;
  unit.status = "귀환";
}

function tacticalCalculation() {
  state.minute += 10;
  state.phase += 1;

  let totalThreat = 0;
  state.zones.forEach((zone) => {
    const pressure = Math.random() * 5 + 1.8;
    const intelReduction = state.resources.intel / 90;
    const controlReduction = zone.control / 120;
    zone.threat = clamp(zone.threat + pressure - intelReduction - controlReduction);
    zone.control = clamp(zone.control - zone.threat / 80);
    totalThreat += zone.threat;
  });

  state.crew.forEach((crew) => {
    crew.fatigue = clamp(crew.fatigue + Math.random() * 2.2 - 0.4);
    crew.stress = clamp(crew.stress + Math.random() * 1.8 - 0.3);
    crew.focus = clamp(crew.focus - crew.fatigue / 220 + Math.random() * 0.8);
    crew.ready = clamp(crew.ready - crew.stress / 260 + Math.random() * 0.5);
    crew.status = crew.fatigue > 62 ? "피로" : crew.stress > 58 ? "주의" : crew.status === "임무 중" ? "임무 중" : "정상";
  });

  updatePlanWeights();

  const hotZones = state.zones.filter((zone) => zone.threat >= 72);
  if (hotZones.length) {
    const damage = hotZones.reduce((sum, zone) => sum + (zone.threat - 68) / 12, 0);
    state.resources.hull = clamp(state.resources.hull - damage);
    state.resources.morale = clamp(state.resources.morale - damage * 0.7);
    addLog(`고위협 해역 방치. 항모전단 피해 ${damage.toFixed(1)}% 발생.`, "danger");
  }

  if (Math.random() < 0.45) spawnEnemy();
  if (Math.random() < 0.32) launchMissile();

  state.resources.fuel = clamp(state.resources.fuel - 1.2);
  state.resources.morale = clamp(state.resources.morale - 0.5);
  state.resources.intel = clamp(state.resources.intel + 0.8);
  state.nextCalcIn = 5;
  state.needsRender = true;

  checkEnd(totalThreat / state.zones.length);
}

function updatePlanWeights() {
  const threat = threatWeights();
  state.plans.forEach((plan) => {
    const tagPressure = plan.tags.reduce((sum, tag) => {
      if (tag === "AIR") return sum + threat.air + threat.missile;
      if (tag === "ASW") return sum + threat.sub;
      if (tag === "EW") return sum + threat.ew;
      if (tag === "NAVY") return sum + threat.unknown;
      if (tag === "RECON" || tag === "INTEL") return sum + (100 - state.resources.intel);
      return sum + 24;
    }, 0) / Math.max(1, plan.tags.length);
    const crewPenalty = averageCrew("fatigue") * 0.15;
    plan.weight = clamp(plan.weight * 0.72 + tagPressure * 0.28 - crewPenalty * 0.08);
    plan.success = clamp(plan.success + (state.resources.intel - 45) / 30 - averageCrew("fatigue") / 90);
  });
}

function spawnEnemy() {
  const zone = state.zones[Math.floor(Math.random() * state.zones.length)];
  const typeMap = { air: "적기", missile: "미사일", sub: "잠수함", ew: "신호", unknown: "접촉" };
  state.enemies.push({
    type: typeMap[zone.kind] || "접촉",
    x: zone.x + (Math.random() - 0.5) * 100,
    y: zone.y + (Math.random() - 0.5) * 80,
    zone: zone.id,
    life: 420,
    phase: Math.random() * Math.PI * 2
  });
  addLog(`${zone.name}에서 ${typeMap[zone.kind] || "정체불명 접촉"} 탐지.`, zone.detected ? "warn" : "danger");
}

function launchMissile() {
  const source = state.zones.reduce((hot, zone) => (zone.threat > hot.threat ? zone : hot), state.zones[0]);
  if (source.threat < 52) return;
  state.projectiles.push({ x: source.x, y: source.y, targetX: state.carrier.x, targetY: state.carrier.y, speed: 2.2 + source.threat / 80, life: 520, trail: [] });
  addLog(`${source.name}에서 항모 방향 미사일 경고선 포착.`, "danger");
}

function checkEnd(avgThreat) {
  const control = averageControl();
  if (state.resources.hull <= 0) finish("패배", "항모가 전투 지속 능력을 상실했습니다.");
  else if (state.resources.morale <= 0) finish("패배", "전단 사기가 붕괴했습니다.");
  else if (state.resources.fuel <= 0) finish("패배", "연료가 고갈되어 작전 기동이 불가능합니다.");
  else if (state.minute >= 18 * 60 && control >= 52 && avgThreat < 72) finish("승리", "18:00까지 항모가 생존했고 해역 통제율을 유지했습니다.");
  else if (state.minute >= 18 * 60) finish("패배", "시간은 버텼지만 해역 통제율이 부족합니다.");
}

function finish(title, text) {
  state.gameOver = true;
  state.result = { title, text };
  addLog(`작전 ${title}: ${text}`, title === "승리" ? "good" : "danger");
}

function updateWorld(now) {
  if (state.paused || state.gameOver) return;
  const elapsed = Math.min(0.05, (now - (state.lastFrame || now)) / 1000);
  state.lastFrame = now;
  state.nextCalcIn -= elapsed;
  if (state.nextCalcIn <= 0) tacticalCalculation();

  state.units.forEach((unit) => {
    if (unit.target) {
      const zone = state.zones.find((item) => item.id === unit.target);
      if (moveToward(unit, zone, unit.speed * 60 * elapsed)) resolveUnit(unit);
    } else if (!unit.ready) {
      if (moveToward(unit, state.carrier, unit.speed * 64 * elapsed)) {
        unit.ready = true;
        unit.status = "대기";
      }
    }
  });

  state.enemies.forEach((enemy) => {
    enemy.life -= 1;
    enemy.phase += elapsed * 3;
    enemy.x += Math.cos(enemy.phase) * 0.22;
    enemy.y += Math.sin(enemy.phase * 0.8) * 0.18;
  });
  state.enemies = state.enemies.filter((enemy) => enemy.life > 0);

  state.escorts.forEach((ship) => {
    ship.orbit += elapsed * 0.18;
    ship.x = state.carrier.x + Math.cos(ship.orbit) * ship.radius;
    ship.y = state.carrier.y + Math.sin(ship.orbit) * ship.radius * 0.62;
  });

  state.projectiles.forEach((missile) => {
    missile.life -= 1;
    missile.trail.push({ x: missile.x, y: missile.y });
    missile.trail = missile.trail.slice(-22);
    const hit = moveToward(missile, { x: missile.targetX, y: missile.targetY }, missile.speed * 60 * elapsed);
    if (hit || Math.hypot(missile.x - state.carrier.x, missile.y - state.carrier.y) < 10) {
      missile.life = 0;
      state.resources.hull = clamp(state.resources.hull - 7);
      state.resources.morale = clamp(state.resources.morale - 4);
      state.effects.push({ type: "burst", x: state.carrier.x, y: state.carrier.y, life: 52, max: 52 });
      addLog("근접 방어망 일부 실패. 항모 주변에서 폭발 발생.", "danger");
    }
  });
  state.projectiles = state.projectiles.filter((missile) => missile.life > 0);

  state.effects.forEach((effect) => effect.life -= 1);
  state.effects = state.effects.filter((effect) => effect.life > 0);

  state.mapMessages.forEach((message) => message.life -= 1);
  state.mapMessages = state.mapMessages.filter((message) => message.life > 0);
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawSea();
  drawCoastAndIslands();
  drawControlLanes();
  drawZones();
  drawRoutes();
  drawRadarSweep();
  drawEscorts();
  drawCarrier();
  drawEnemies();
  drawProjectiles();
  drawUnits();
  drawEffects();
  drawMapMessages();
}

function drawSea() {
  const gradient = ctx.createLinearGradient(0, 0, 980, 660);
  gradient.addColorStop(0, "#0d3145");
  gradient.addColorStop(0.55, "#092439");
  gradient.addColorStop(1, "#061522");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 980, 660);
  ctx.strokeStyle = "rgba(79, 215, 255, 0.08)";
  ctx.lineWidth = 1;
  for (let x = 20; x < 980; x += 42) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x - 80, 660);
    ctx.stroke();
  }
  for (let y = 24; y < 660; y += 42) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(980, y - 60);
    ctx.stroke();
  }

  const t = performance.now() / 1000;
  for (let i = 0; i < 34; i += 1) {
    const y = 30 + i * 19;
    const offset = Math.sin(t * 0.7 + i * 0.6) * 18;
    ctx.beginPath();
    for (let x = -40; x <= 1020; x += 44) {
      const waveY = y + Math.sin(x * 0.018 + t + i) * 4;
      if (x === -40) ctx.moveTo(x + offset, waveY);
      else ctx.lineTo(x + offset, waveY);
    }
    ctx.strokeStyle = i % 3 === 0 ? "rgba(95, 204, 255, 0.08)" : "rgba(180, 238, 255, 0.035)";
    ctx.lineWidth = 1;
    ctx.stroke();
  }
}

function drawCoastAndIslands() {
  ctx.save();
  ctx.fillStyle = "rgba(24, 57, 49, 0.84)";
  ctx.strokeStyle = "rgba(126, 224, 131, 0.32)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(875, 0);
  ctx.bezierCurveTo(842, 62, 888, 122, 850, 178);
  ctx.bezierCurveTo(820, 222, 860, 286, 824, 348);
  ctx.bezierCurveTo(790, 406, 838, 488, 802, 660);
  ctx.lineTo(980, 660);
  ctx.lineTo(980, 0);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = "rgba(31, 75, 64, 0.78)";
  [
    [720, 326, 18, 7],
    [674, 390, 12, 5],
    [625, 520, 15, 6],
    [188, 438, 11, 5],
    [132, 272, 8, 4]
  ].forEach(([x, y, rx, ry]) => {
    ctx.beginPath();
    ctx.ellipse(x, y, rx, ry, -0.25, 0, Math.PI * 2);
    ctx.fill();
  });

  ctx.fillStyle = "rgba(234, 248, 255, 0.5)";
  ctx.font = "700 12px Segoe UI, sans-serif";
  ctx.fillText("COAST", 838, 86);
  ctx.fillText("SEA CONTROL GRID", 48, 44);
  ctx.restore();
}

function drawControlLanes() {
  const lanes = [
    [[state.carrier.x, state.carrier.y], [220, 170], "rgba(255, 209, 102, 0.24)"],
    [[state.carrier.x, state.carrier.y], [710, 145], "rgba(66, 230, 216, 0.22)"],
    [[state.carrier.x, state.carrier.y], [785, 430], "rgba(126, 224, 131, 0.2)"],
    [[state.carrier.x, state.carrier.y], [315, 500], "rgba(183, 132, 255, 0.2)"]
  ];
  lanes.forEach(([[x1, y1], [x2, y2], color], index) => {
    const pulse = (performance.now() / 35 + index * 18) % 100;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.quadraticCurveTo((x1 + x2) / 2, Math.min(y1, y2) - 54, x2, y2);
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.setLineDash([10, 10]);
    ctx.stroke();
    ctx.setLineDash([]);

    const px = x1 + (x2 - x1) * (pulse / 100);
    const py = y1 + (y2 - y1) * (pulse / 100);
    ctx.beginPath();
    ctx.arc(px, py, 3, 0, Math.PI * 2);
    ctx.fillStyle = color.replace("0.2", "0.9").replace("0.22", "0.9").replace("0.24", "0.9");
    ctx.fill();
  });
}

function drawRadarSweep() {
  const { x, y } = state.carrier;
  const angle = (performance.now() / 1300) % (Math.PI * 2);
  const radius = 250;
  const sweep = ctx.createRadialGradient(x, y, 0, x, y, radius);
  sweep.addColorStop(0, "rgba(66, 230, 216, 0.16)");
  sweep.addColorStop(1, "rgba(66, 230, 216, 0)");

  ctx.save();
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.arc(x, y, radius, angle - 0.18, angle + 0.18);
  ctx.closePath();
  ctx.fillStyle = sweep;
  ctx.fill();
  ctx.restore();

  [85, 150, 215].forEach((ring) => {
    ctx.beginPath();
    ctx.arc(x, y, ring, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(66, 230, 216, 0.12)";
    ctx.lineWidth = 1;
    ctx.stroke();
  });
}

function drawEscorts() {
  state.escorts.forEach((ship) => {
    ctx.save();
    ctx.translate(ship.x, ship.y);
    ctx.rotate(Math.sin(ship.orbit) * 0.25);
    ctx.fillStyle = ship.color;
    ctx.strokeStyle = "rgba(234, 248, 255, 0.58)";
    ctx.lineWidth = 1.3;
    ctx.beginPath();
    ctx.moveTo(16, 0);
    ctx.lineTo(5, -7);
    ctx.lineTo(-15, -5);
    ctx.lineTo(-18, 0);
    ctx.lineTo(-15, 5);
    ctx.lineTo(5, 7);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    ctx.restore();

    ctx.beginPath();
    ctx.arc(ship.x, ship.y, 38 + Math.sin(performance.now() / 240 + ship.orbit) * 3, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(126, 224, 131, 0.12)";
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.fillStyle = "rgba(234, 248, 255, 0.78)";
    ctx.font = "700 10px Segoe UI, sans-serif";
    ctx.fillText(ship.id, ship.x - 16, ship.y - 22);
  });
}

function drawZones() {
  state.zones.forEach((zone, index) => {
    const selected = index === state.selectedZone;
    const danger = zone.threat >= 72;
    const color = danger ? "255, 93, 93" : zone.threat >= 50 ? "244, 211, 94" : "126, 224, 131";
    ctx.beginPath();
    ctx.arc(zone.x, zone.y, zone.radius, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${color}, ${selected ? 0.16 : 0.08})`;
    ctx.fill();
    ctx.strokeStyle = `rgba(${color}, ${selected ? 0.95 : 0.45})`;
    ctx.setLineDash(danger ? [8, 8] : []);
    ctx.lineWidth = selected ? 3 : 1.5;
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.beginPath();
    ctx.arc(zone.x, zone.y, Math.max(26, zone.radius * 0.54), -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * (zone.control / 100));
    ctx.strokeStyle = "rgba(66, 230, 216, 0.62)";
    ctx.lineWidth = 5;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(zone.x, zone.y, Math.max(34, zone.radius * 0.66), -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * (zone.threat / 100));
    ctx.strokeStyle = `rgba(${color}, 0.72)`;
    ctx.lineWidth = 4;
    ctx.stroke();

    if (danger) {
      ctx.beginPath();
      ctx.arc(zone.x, zone.y, zone.radius + 8 + Math.sin(performance.now() / 180) * 5, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(255, 93, 93, 0.35)";
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    drawZoneIcon(zone);

    ctx.fillStyle = "#eaf8ff";
    ctx.font = "700 16px Segoe UI, sans-serif";
    ctx.fillText(zone.name, zone.x - zone.radius + 12, zone.y - zone.radius + 25);
    ctx.fillStyle = "rgba(234, 248, 255, 0.72)";
    ctx.font = "12px Segoe UI, sans-serif";
    ctx.fillText(zone.detected ? `${zone.enemy} / 위협 ${Math.round(zone.threat)}%` : "정체불명 신호 / 위협 미확정", zone.x - zone.radius + 12, zone.y - zone.radius + 45);

    ctx.fillStyle = "rgba(234, 248, 255, 0.5)";
    ctx.font = "700 10px Segoe UI, sans-serif";
    ctx.fillText(`CTRL ${Math.round(zone.control)}%`, zone.x - 32, zone.y + zone.radius - 18);
  });
}

function drawZoneIcon(zone) {
  ctx.save();
  ctx.translate(zone.x, zone.y);
  ctx.strokeStyle = zone.detected ? "rgba(234, 248, 255, 0.82)" : "rgba(255, 209, 102, 0.86)";
  ctx.fillStyle = zone.detected ? "rgba(234, 248, 255, 0.18)" : "rgba(255, 209, 102, 0.16)";
  ctx.lineWidth = 2;

  if (zone.kind === "air") {
    ctx.beginPath();
    ctx.moveTo(22, 0);
    ctx.lineTo(-16, -12);
    ctx.lineTo(-8, 0);
    ctx.lineTo(-16, 12);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  } else if (zone.kind === "missile") {
    ctx.beginPath();
    ctx.moveTo(0, -24);
    ctx.lineTo(10, 10);
    ctx.lineTo(0, 20);
    ctx.lineTo(-10, 10);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  } else if (zone.kind === "sub" || zone.kind === "unknown") {
    ctx.beginPath();
    ctx.ellipse(0, 0, 25, 10, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(12, -10);
    ctx.lineTo(12, -20);
    ctx.lineTo(24, -20);
    ctx.stroke();
  } else {
    ctx.beginPath();
    ctx.arc(0, 0, 22, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(-24, 0);
    ctx.lineTo(24, 0);
    ctx.moveTo(0, -24);
    ctx.lineTo(0, 24);
    ctx.stroke();
  }
  ctx.restore();
}

function drawRoutes() {
  state.units.forEach((unit) => {
    if (!unit.target) return;
    const zone = state.zones.find((item) => item.id === unit.target);
    ctx.beginPath();
    ctx.moveTo(unit.x, unit.y);
    ctx.lineTo(zone.x, zone.y);
    ctx.strokeStyle = "rgba(66, 230, 216, 0.34)";
    ctx.lineWidth = 1.5;
    ctx.setLineDash([5, 7]);
    ctx.stroke();
    ctx.setLineDash([]);
  });
}

function drawCarrier() {
  const { x, y } = state.carrier;
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(-0.12);
  ctx.fillStyle = "#8ca3ad";
  ctx.strokeStyle = "rgba(234, 248, 255, 0.7)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(-86, -24);
  ctx.lineTo(62, -24);
  ctx.lineTo(92, 0);
  ctx.lineTo(62, 24);
  ctx.lineTo(-86, 24);
  ctx.lineTo(-104, 0);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  ctx.strokeStyle = "rgba(5, 16, 26, 0.8)";
  ctx.lineWidth = 5;
  ctx.beginPath();
  ctx.moveTo(-72, 0);
  ctx.lineTo(60, 0);
  ctx.stroke();
  ctx.fillStyle = "#526c78";
  ctx.fillRect(30, -34, 28, 23);
  ctx.restore();

  ctx.beginPath();
  ctx.arc(x, y, 122 + Math.sin(performance.now() / 320) * 8, 0, Math.PI * 2);
  ctx.strokeStyle = "rgba(66, 230, 216, 0.2)";
  ctx.lineWidth = 2;
  ctx.stroke();
}

function drawUnits() {
  state.units.forEach((unit) => {
    if (unit.scan) {
      ctx.beginPath();
      ctx.arc(unit.x, unit.y, unit.scan + Math.sin(performance.now() / 260) * 7, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(183, 132, 255, 0.22)";
      ctx.lineWidth = 2;
      ctx.stroke();
    }
    ctx.fillStyle = unit.color;
    ctx.strokeStyle = "rgba(255, 255, 255, 0.7)";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    if (unit.type === "heli") ctx.arc(unit.x, unit.y, 9, 0, Math.PI * 2);
    else if (unit.type === "supply") ctx.rect(unit.x - 11, unit.y - 8, 22, 16);
    else {
      ctx.moveTo(unit.x + 14, unit.y);
      ctx.lineTo(unit.x - 10, unit.y - 8);
      ctx.lineTo(unit.x - 5, unit.y);
      ctx.lineTo(unit.x - 10, unit.y + 8);
      ctx.closePath();
    }
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = "#eaf8ff";
    ctx.font = "700 11px Segoe UI, sans-serif";
    ctx.fillText(unit.label, unit.x - 12, unit.y - 15);
  });
}

function drawEnemies() {
  state.enemies.forEach((enemy) => {
    ctx.globalAlpha = enemy.type === "잠수함" ? 0.5 : 0.9;
    ctx.fillStyle = enemy.type === "신호" ? "#b784ff" : "#ff6b57";
    ctx.strokeStyle = "rgba(255, 255, 255, 0.42)";
    ctx.lineWidth = 1.2;
    ctx.beginPath();
    if (enemy.type === "잠수함") ctx.ellipse(enemy.x, enemy.y, 18, 8, 0, 0, Math.PI * 2);
    else if (enemy.type === "미사일") {
      ctx.moveTo(enemy.x + 14, enemy.y);
      ctx.lineTo(enemy.x - 10, enemy.y - 6);
      ctx.lineTo(enemy.x - 10, enemy.y + 6);
      ctx.closePath();
    } else ctx.rect(enemy.x - 9, enemy.y - 9, 18, 18);
    ctx.fill();
    ctx.stroke();
    ctx.globalAlpha = 1;
    ctx.fillStyle = "rgba(255, 235, 220, 0.86)";
    ctx.font = "700 11px Segoe UI, sans-serif";
    ctx.fillText(enemy.type, enemy.x - 18, enemy.y - 16);
  });
}

function drawProjectiles() {
  state.projectiles.forEach((missile) => {
    missile.trail.forEach((point, index) => {
      const alpha = index / Math.max(1, missile.trail.length);
      ctx.beginPath();
      ctx.arc(point.x, point.y, 2 + alpha * 4, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255, 159, 67, ${0.05 + alpha * 0.25})`;
      ctx.fill();
    });

    ctx.beginPath();
    ctx.moveTo(missile.x, missile.y);
    ctx.lineTo(missile.targetX, missile.targetY);
    ctx.strokeStyle = "rgba(255, 93, 93, 0.28)";
    ctx.lineWidth = 2;
    ctx.stroke();

    const warning = 8 + Math.sin(performance.now() / 90) * 3;
    ctx.beginPath();
    ctx.arc(missile.x, missile.y, warning, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(255, 93, 93, 0.52)";
    ctx.lineWidth = 1.5;
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(missile.x, missile.y, 5, 0, Math.PI * 2);
    ctx.fillStyle = "#ff5d5d";
    ctx.fill();
  });
}

function drawEffects() {
  state.effects.forEach((effect) => {
    const progress = 1 - effect.life / effect.max;
    if (effect.type === "burst") {
      ctx.beginPath();
      ctx.arc(effect.x, effect.y, 10 + progress * 42, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255, 159, 67, ${0.28 * (1 - progress)})`;
      ctx.fill();
      ctx.strokeStyle = `rgba(255, 93, 93, ${0.8 * (1 - progress)})`;
      ctx.lineWidth = 2;
      ctx.stroke();
    }
    if (effect.type === "jam") {
      ctx.beginPath();
      ctx.arc(effect.x, effect.y, 80 + progress * 260, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(183, 132, 255, ${0.45 * (1 - progress)})`;
      ctx.lineWidth = 4;
      ctx.stroke();
    }
    if (effect.type === "repair") {
      ctx.beginPath();
      ctx.arc(effect.x, effect.y, 50 + progress * 70, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(126, 224, 131, ${0.5 * (1 - progress)})`;
      ctx.lineWidth = 3;
      ctx.stroke();
    }
  });
}

function drawMapMessages() {
  const visible = state.mapMessages.slice(0, 3);
  if (!visible.length) return;

  ctx.save();
  ctx.font = "700 13px Segoe UI, sans-serif";
  visible.forEach((entry, index) => {
    const progress = entry.life / entry.max;
    const alpha = Math.min(1, progress * 2.4);
    const x = 22;
    const y = 82 + index * 58;
    const width = 360;
    const height = 46;
    const color = entry.type === "danger" ? "#ff5d5d" : entry.type === "warn" ? "#ff9f43" : entry.type === "good" ? "#7ee083" : "#42e6d8";
    const pulse = entry.type === "danger" ? Math.sin(performance.now() / 90) * 0.16 + 0.22 : 0.12;

    ctx.globalAlpha = alpha;
    ctx.fillStyle = "rgba(4, 13, 22, 0.82)";
    roundRect(x, y, width, height, 8);
    ctx.fill();

    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    roundRect(x, y, width, height, 8);
    ctx.stroke();

    ctx.fillStyle = color;
    ctx.globalAlpha = alpha * (0.55 + pulse);
    ctx.fillRect(x, y, 5, height);

    ctx.globalAlpha = alpha;
    ctx.fillStyle = color;
    ctx.font = "900 11px Segoe UI, sans-serif";
    ctx.fillText(entry.type === "danger" ? "ALERT" : entry.type === "warn" ? "CAUTION" : entry.type === "good" ? "CONFIRM" : "AI MSG", x + 14, y + 17);

    ctx.fillStyle = "rgba(234, 248, 255, 0.92)";
    ctx.font = "700 13px Segoe UI, sans-serif";
    ctx.fillText(trimCanvasText(`${entry.time} ${entry.message}`, 42), x + 14, y + 35);
  });
  ctx.restore();
}

function trimCanvasText(text, maxLength) {
  return text.length > maxLength ? `${text.slice(0, maxLength - 1)}...` : text;
}

function roundRect(x, y, width, height, radius) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + width - radius, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
  ctx.lineTo(x + width, y + height - radius);
  ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  ctx.lineTo(x + radius, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();
}

function render() {
  renderStatus();
  renderPriorityCards();
  renderTacticalCards();
  renderZones();
  renderSelectedZone();
  renderCommands();
  renderWeights();
  renderCrewMini();
  renderLog();
  renderPlans();
  renderCrew();
  renderPerformance();
  renderResult();
}

function renderStatus() {
  const items = [["시간", formatTime(state.minute), null], ["단계", `${state.phase}`, null], ...Object.entries(state.resources).map(([key, value]) => [labels[key], `${Math.round(value)}%`, value])];
  document.querySelector("#statusStrip").innerHTML = items.map(([label, value, meter]) => {
    const level = meter !== null && meter < 30 ? "bad" : meter !== null && meter < 55 ? "warn" : "";
    const bar = meter === null ? "" : `<div class="meter"><i style="width:${meter}%"></i></div>`;
    return `<article class="status-card ${level}"><span>${label}</span><b>${value}</b>${bar}</article>`;
  }).join("");
  document.querySelector("#phaseLabel").textContent = state.paused ? "일시 정지" : `작전 단계 ${state.phase}`;
  document.querySelector("#tickLabel").textContent = `다음 전술 계산 ${Math.max(0, state.nextCalcIn).toFixed(1)}초`;
  document.querySelector("#controlScore").textContent = `통제율 ${Math.round(averageControl())}%`;
  document.querySelector("#pauseButton").textContent = state.paused ? "▶" : "II";
}

function renderPriorityCards() {
  const cards = [...state.zones].sort((a, b) => b.threat - a.threat).slice(0, 5);
  document.querySelector("#priorityList").innerHTML = cards.map((zone, index) => `
    <article class="priority-card ${zone.threat > 72 ? "danger" : ""}">
      <h3>${index + 1}. ${zone.enemy}</h3>
      <p>${zone.name} / 위험 ${zone.detected ? Math.round(zone.threat) : "?"}% / 가중치 ${(zone.threat / 100).toFixed(2)}</p>
      <p>예상 피해: ${zone.threat > 70 ? "항모 직접 피해" : zone.threat > 50 ? "작전 지연" : "국지 교란"}<br>권장 대응: ${recommendCommand(zone)}</p>
    </article>
  `).join("");
}

function recommendCommand(zone) {
  if (!zone.detected) return "장거리 정찰";
  if (["air", "missile"].includes(zone.kind)) return "긴급 CAP 또는 타격";
  if (zone.kind === "sub" || zone.kind === "unknown") return "대잠 탐지";
  if (zone.kind === "ew") return "전자전 교란";
  return "보급선 보호";
}

function renderTacticalCards() {
  document.querySelector("#tacticalCardList").innerHTML = commands.slice(0, 5).map((item) => `
    <article class="tactical-card" data-command="${item.id}">
      <h3>${item.name}</h3>
      <p>${item.desc} / 필요 ${item.tags.join(", ")}</p>
    </article>
  `).join("");
}

function renderZones() {
  document.querySelector("#zoneList").innerHTML = state.zones.map((zone, index) => {
    const level = zone.threat >= 72 ? "danger" : zone.threat >= 50 ? "watch" : "";
    return `
      <article class="zone-card ${index === state.selectedZone ? "selected" : ""} ${level === "danger" ? "danger" : ""}" data-zone="${index}">
        <div class="threat-row">
          <h3>${zone.name}</h3>
          <span class="threat-pill ${level}">${zone.detected ? Math.round(zone.threat) : "?"}%</span>
        </div>
        <p>탐지: ${zone.detected ? "확인" : "미확정"} / 적: ${zone.detected ? zone.enemy : "정체불명"}</p>
        <p>작전: ${zone.operation}</p>
        <p>통제율 ${Math.round(zone.control)}%</p>
      </article>
    `;
  }).join("");
  document.querySelectorAll(".zone-card").forEach((card) => {
    card.addEventListener("click", () => {
      state.selectedZone = Number(card.dataset.zone);
      render();
    });
  });
}

function renderSelectedZone() {
  const zone = selectedZone();
  document.querySelector("#selectedZone").innerHTML = `
    <strong>${zone.name}</strong>
    <p>위협도 ${zone.detected ? `${Math.round(zone.threat)}%` : "미확정"} / 통제율 ${Math.round(zone.control)}%</p>
    <p>현재 적: ${zone.detected ? zone.enemy : "정체불명 접촉"}<br>아군 상태: ${zone.operation}</p>
  `;
}

function renderCommands() {
  document.querySelector("#commandGrid").innerHTML = commands.map((item) => {
    const disabled = state.gameOver ? "disabled" : "";
    return `<button type="button" data-command="${item.id}" ${disabled}>${item.name}<small>${item.desc}</small></button>`;
  }).join("");
}

function threatWeights() {
  const weights = { air: 0, missile: 0, sub: 0, ew: 0, unknown: 0 };
  state.zones.forEach((zone) => {
    weights[zone.kind] = Math.max(weights[zone.kind] || 0, zone.threat);
  });
  return weights;
}

function renderWeights() {
  const weights = threatWeights();
  document.querySelector("#weightBars").innerHTML = Object.entries(weights).map(([key, value]) => `
    <div class="weight-row ${value > 70 ? "danger" : value > 50 ? "warn" : ""}">
      <span>${threatLabels[key]}</span>
      <div class="mini-meter"><i style="width:${value}%"></i></div>
      <b>${Math.round(value)}</b>
    </div>
  `).join("");
}

function renderCrewMini() {
  const depts = ["전투정보", "항공운용", "전자전", "정비/무장", "의무/지원"];
  document.querySelector("#crewLinkMini").innerHTML = depts.map((dept) => {
    const members = state.crew.filter((crew) => crew.dept === dept);
    const ready = members.length ? members.reduce((sum, crew) => sum + crew.ready, 0) / members.length : 76;
    return `
      <div class="mini-crew-row ${ready < 55 ? "danger" : ready < 72 ? "warn" : ""}">
        <span>${dept}</span>
        <div class="mini-meter"><i style="width:${ready}%"></i></div>
        <b>${Math.round(ready)}</b>
      </div>
    `;
  }).join("");
}

function renderLog() {
  document.querySelector("#logList").innerHTML = state.logs.map((log) => `<p class="log-entry ${log.type}">${log.time} ${log.message}</p>`).join("");
}

function gameSnapshotForAI() {
  const zone = selectedZone();
  const highestThreats = [...state.zones]
    .sort((a, b) => b.threat - a.threat)
    .slice(0, 3)
    .map((item) => ({
      id: item.id,
      name: item.name,
      kind: item.kind,
      threat: Math.round(item.threat),
      control: Math.round(item.control),
      detected: item.detected,
      enemy: item.enemy
    }));

  return {
    time: formatTime(state.minute),
    phase: state.phase,
    selectedZone: {
      id: zone.id,
      name: zone.name,
      kind: zone.kind,
      threat: Math.round(zone.threat),
      control: Math.round(zone.control),
      detected: zone.detected,
      enemy: zone.enemy
    },
    averageControl: Math.round(averageControl()),
    resources: Object.fromEntries(Object.entries(state.resources).map(([key, value]) => [key, Math.round(value)])),
    crew: {
      ready: Math.round(averageCrew("ready")),
      fatigue: Math.round(averageCrew("fatigue")),
      stress: Math.round(averageCrew("stress"))
    },
    highestThreats,
    availableCommands: commands.map((item) => ({
      id: item.id,
      name: item.name,
      tags: item.tags,
      cost: item.cost
    }))
  };
}

function localTacticalAdvice() {
  const snapshot = gameSnapshotForAI();
  const critical = snapshot.highestThreats[0];
  let commandId = "recon";
  if (critical.kind === "air" || critical.kind === "missile") commandId = snapshot.resources.ammo > 30 ? "strike" : "cap";
  if (critical.kind === "sub" || critical.kind === "unknown") commandId = critical.detected ? "asw" : "recon";
  if (critical.kind === "ew") commandId = "ew";
  if (snapshot.resources.deck < 42 || snapshot.resources.hull < 55) commandId = "repair";

  const commandConfig = commands.find((item) => item.id === commandId);
  return [
    `추천: ${commandConfig ? commandConfig.name : commandId}`,
    `이유: ${critical.name} 위협 ${critical.threat}% / 통제 ${critical.control}%가 가장 급합니다.`,
    `주의: 함체 ${snapshot.resources.hull}%, 갑판 ${snapshot.resources.deck}%, 승무원 피로 ${snapshot.crew.fatigue}%를 함께 관리하세요.`
  ].join("\n");
}

function setAIAdvice(text, status = "") {
  const advice = document.querySelector("#aiAdvice");
  if (!advice) return;
  advice.classList.toggle("loading", status === "loading");
  advice.classList.toggle("error", status === "error");
  advice.textContent = text;
}

async function requestOllamaAdvice() {
  const button = document.querySelector("#aiAdviceButton");
  const modelInput = document.querySelector("#ollamaModelInput");
  const model = (modelInput?.value || "kimi-k2.6:cloud").trim();
  const endpoint = localStorage.getItem("ollamaEndpoint") || "http://127.0.0.1:11434";
  const snapshot = gameSnapshotForAI();

  localStorage.setItem("ollamaModel", model);
  if (button) button.disabled = true;
  setAIAdvice("Ollama Cloud 모델이 전술 상태를 분석 중입니다...", "loading");

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 9000);

  try {
    const response = await fetch(`${endpoint.replace(/\/$/, "")}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      body: JSON.stringify({
        model,
        stream: false,
        options: {
          temperature: 0.25,
          num_predict: 140
        },
        messages: [
          {
            role: "system",
            content: "You are a fast tactical advisor for an arcade carrier command game. Answer in Korean. Keep it under 3 short lines. Recommend exactly one command id and explain why."
          },
          {
            role: "user",
            content: JSON.stringify(snapshot)
          }
        ]
      })
    });

    if (!response.ok) throw new Error(`Ollama 응답 실패: ${response.status}`);

    const data = await response.json();
    const content = data?.message?.content || data?.response || "";
    setAIAdvice(content.trim() || localTacticalAdvice());
    addLog("Ollama Cloud AI 전술 추천을 수신했습니다.", "good");
  } catch (error) {
    console.warn("[requestOllamaAdvice] fallback:", error);
    setAIAdvice(`${localTacticalAdvice()}\n\nOllama 연결 실패: ${error.message}`, "error");
  } finally {
    clearTimeout(timeout);
    if (button) button.disabled = false;
  }
}

function sortedPlans() {
  const key = state.planSort === "success" ? "success" : "weight";
  return [...state.plans].sort((a, b) => b[key] - a[key]);
}

function renderPlans() {
  document.querySelector("#autoSortButton").textContent = state.autoSortPlans ? "재배열 ON" : "재배열 OFF";
  document.querySelector("#planGrid").innerHTML = sortedPlans().map((plan) => `
    <article class="plan-card">
      <div class="threat-row">
        <h3>${plan.id}</h3>
        <span class="tag ${plan.weight > 65 ? "danger" : plan.weight > 45 ? "warn" : "violet"}">${Math.round(plan.weight)}</span>
      </div>
      <p><b>${plan.name}</b><br>${plan.desc}</p>
      <div class="plan-metrics">
        ${metric("성공", plan.success)}
        ${metric("생존", plan.survival)}
        ${metric("피로", plan.fatigue, true)}
      </div>
      <p>소요 ${plan.time}분</p>
      <div class="tag-row">${plan.tags.map((tag) => `<span class="tag">${tag}</span>`).join("")}</div>
    </article>
  `).join("");

  document.querySelector("#planLinks").innerHTML = sortedPlans().slice(0, 6).map((plan) => {
    const linked = linkedCrewForPlan(plan).slice(0, 2).map((crew) => crew.role).join(", ");
    return `<article class="link-card"><h3>${plan.id} ${plan.name}</h3><p>${linked || "대기 인원 없음"} 연결 / 가중치 ${Math.round(plan.weight)}</p></article>`;
  }).join("");
}

function metric(label, value, inverse = false) {
  const level = inverse ? value > 65 ? "danger" : value > 45 ? "warn" : "" : value < 45 ? "danger" : value < 65 ? "warn" : "";
  return `
    <div class="metric-row ${level}">
      <span>${label}</span>
      <div class="mini-meter"><i style="width:${value}%"></i></div>
      <b>${Math.round(value)}</b>
    </div>
  `;
}

function linkedCrewForPlan(plan) {
  const tagDept = { AIR: "항공운용", ASW: "대잠전", EW: "전자전", NAVY: "함교 운영", RECON: "전투정보", UDT: "특수전", INTEL: "전투정보" };
  return state.crew.filter((crew) => plan.tags.some((tag) => tagDept[tag] === crew.dept));
}

function renderCrew() {
  const available = state.crew.filter((crew) => crew.ready >= 70 && crew.fatigue < 55).length;
  const overloaded = state.crew.filter((crew) => crew.fatigue >= 58 || crew.stress >= 58).length;
  const recovery = state.crew.filter((crew) => crew.ready < 62).length;
  document.querySelector("#crewSummary").innerHTML = [
    ["평균 컨디션", `${Math.round((averageCrew("focus") + averageCrew("ready")) / 2)}%`],
    ["가용 인원", `${available}`],
    ["과부하", `${overloaded}`],
    ["회복 필요", `${recovery}`]
  ].map(([label, value]) => `<article class="summary-chip"><span>${label}</span><b>${value}</b></article>`).join("");

  document.querySelector("#crewGrid").innerHTML = state.crew.map((crew) => {
    const level = crew.fatigue > 62 || crew.stress > 62 ? "danger" : crew.fatigue > 48 || crew.stress > 48 ? "warning" : "";
    return `
      <article class="crew-card ${level}">
        <div class="threat-row">
          <h3>${crew.name}</h3>
          <span class="tag ${level === "danger" ? "danger" : level === "warning" ? "warn" : ""}">${crew.status}</span>
        </div>
        <p>${crew.role}<br>${crew.dept} / 연결 플랜 ${crew.plans}</p>
        <div class="crew-metrics">
          ${metric("집중", crew.focus)}
          ${metric("피로", crew.fatigue, true)}
          ${metric("스트", crew.stress, true)}
          ${metric("준비", crew.ready)}
        </div>
      </article>
    `;
  }).join("");

  const departments = [...new Set(state.crew.map((crew) => crew.dept))];
  document.querySelector("#departmentList").innerHTML = departments.map((dept) => {
    const members = state.crew.filter((crew) => crew.dept === dept);
    const ready = members.reduce((sum, crew) => sum + crew.ready, 0) / members.length;
    return `<article class="department-card"><h3>${dept}</h3><p>인원 ${members.length} / 준비도 ${Math.round(ready)}%</p>${metric("준비", ready)}</article>`;
  }).join("");

  const alerts = state.crew.filter((crew) => crew.fatigue > 55 || crew.stress > 55);
  document.querySelector("#crewAlerts").innerHTML = (alerts.length ? alerts : [{ name: "경고 없음", role: "전 부서 안정", fatigue: 0, stress: 0 }]).map((crew) => `
    <article class="alert-card ${crew.fatigue > 62 || crew.stress > 62 ? "danger" : ""}">
      <h3>${crew.name}</h3>
      <p>${crew.role} / 피로 ${Math.round(crew.fatigue)} / 스트레스 ${Math.round(crew.stress)}</p>
    </article>
  `).join("");
}

function renderPerformance() {
  const efficiency = clamp((averageControl() + averageCrew("ready") + state.resources.morale) / 3);
  const overload = state.crew.filter((crew) => crew.fatigue > 58).length;
  const linked = state.plans.reduce((sum, plan) => sum + linkedCrewForPlan(plan).length, 0);
  document.querySelector("#performanceSummary").innerHTML = [
    ["연결 효율", `${Math.round(efficiency)}%`],
    ["연결 인원", linked],
    ["과부하", overload],
    ["대기 편대", state.units.filter((unit) => unit.ready).length]
  ].map(([label, value]) => `<article class="summary-chip"><span>${label}</span><b>${value}</b></article>`).join("");

  const grades = ["S++", "S", "A", "B", "C", "D", "E", "F", "G", "H"];
  document.querySelector("#gradeRow").innerHTML = grades.map((grade, index) => {
    const score = clamp(efficiency + 22 - index * 9);
    return `<article class="grade-card"><strong>${grade}</strong><p>성과 ${Math.round(score)}<br>위험 통제 ${Math.round(clamp(score - averageCrew("stress") / 5))}</p></article>`;
  }).join("");

  const teams = ["함교 운영팀", "전투정보팀", "항공운용팀", "전자전팀", "대잠전팀", "의무팀", "통신팀", "정비팀"];
  document.querySelector("#performanceMatrix").innerHTML = teams.map((team, index) => {
    const grade = grades[Math.min(grades.length - 1, Math.max(0, Math.floor((100 - efficiency + index * 3) / 10)))];
    return `<div class="matrix-line"><b>${team}</b><i></i><span class="tag ${index < 2 ? "gold" : ""}">${grade}</span></div>`;
  }).join("");

  document.querySelector("#teamList").innerHTML = teams.map((team, index) => {
    const load = clamp(42 + index * 5 + averageCrew("fatigue") / 4);
    return `<article class="team-card"><h3>${team}</h3><p>부하율 ${Math.round(load)}% / 연결 카드 ${1 + (index % 4)}</p>${metric("부하", load, true)}</article>`;
  }).join("");
}

function renderResult() {
  const panel = document.querySelector("#resultPanel");
  if (!state.gameOver) {
    panel.classList.add("hidden");
    return;
  }
  panel.classList.remove("hidden");
  document.querySelector("#resultTitle").textContent = `작전 ${state.result.title}`;
  document.querySelector("#resultText").textContent = `${state.result.text} 최종 통제율 ${Math.round(averageControl())}%, 함체 ${Math.round(state.resources.hull)}%.`;
}

function resizeCanvasForDisplay() {
  const rect = canvas.getBoundingClientRect();
  const scale = window.devicePixelRatio || 1;
  const width = Math.round(rect.width * scale);
  const height = Math.round(rect.height * scale);
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
    ctx.setTransform(width / 980, 0, 0, height / 660, 0, 0);
  }
}

function canvasClick(event) {
  const rect = canvas.getBoundingClientRect();
  const x = ((event.clientX - rect.left) / rect.width) * 980;
  const y = ((event.clientY - rect.top) / rect.height) * 660;
  const clicked = state.zones.findIndex((zone) => Math.hypot(zone.x - x, zone.y - y) <= zone.radius);
  if (clicked >= 0) {
    state.selectedZone = clicked;
    render();
  }
}

function showScreen(id) {
  state.activeScreen = id;
  document.querySelectorAll(".screen-tabs button").forEach((button) => button.classList.toggle("active", button.dataset.screen === id));
  document.querySelectorAll(".screen").forEach((screen) => screen.classList.toggle("active", screen.id === id));
  resizeCanvasForDisplay();
}

function loop(now) {
  resizeCanvasForDisplay();
  updateWorld(now);
  if (state.needsRender) {
    render();
    state.needsRender = false;
  }
  draw();
  renderStatus();
  requestAnimationFrame(loop);
}

document.body.addEventListener("click", (event) => {
  const commandButton = event.target.closest("[data-command]");
  if (commandButton) command(commandButton.dataset.command);

  const screenButton = event.target.closest("[data-screen]");
  if (screenButton) showScreen(screenButton.dataset.screen);

  const sortButton = event.target.closest("[data-sort-plans]");
  if (sortButton) {
    state.planSort = sortButton.dataset.sortPlans;
    renderPlans();
  }
});

document.querySelector("#autoSortButton").addEventListener("click", () => {
  state.autoSortPlans = !state.autoSortPlans;
  renderPlans();
});

document.querySelector("#pauseButton").addEventListener("click", () => {
  state.paused = !state.paused;
  state.lastFrame = performance.now();
  render();
});

document.querySelector("#aiAdviceButton")?.addEventListener("click", requestOllamaAdvice);
const savedOllamaModel = localStorage.getItem("ollamaModel");
if (savedOllamaModel) {
  document.querySelector("#ollamaModelInput").value = savedOllamaModel;
}

canvas.addEventListener("click", canvasClick);
window.addEventListener("resize", resizeCanvasForDisplay);

addLog("작전 개시. AI 전술 카드 상황실이 전장 우선순위를 계산합니다.", "good");
addLog("전장 지도 또는 구역 카드를 선택한 뒤 전술 카드를 실행하십시오.");
spawnEnemy();
render();
requestAnimationFrame(loop);
