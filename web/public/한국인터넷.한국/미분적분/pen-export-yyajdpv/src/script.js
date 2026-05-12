const svg = document.getElementById("graph");
const sceneRange = document.getElementById("sceneRange");
const xRange = document.getElementById("xRange");
const xValueEl = document.getElementById("xValue");
const xDetailEl = document.getElementById("xDetail");
const fxValueEl = document.getElementById("fxValue");
const fxDetailEl = document.getElementById("fxDetail");
const dfValueEl = document.getElementById("dfValue");
const dfDetailEl = document.getElementById("dfDetail");
const areaValueEl = document.getElementById("areaValue");
const areaDetailEl = document.getElementById("areaDetail");
const circleValueEl = document.getElementById("circleValue");
const circleDetailEl = document.getElementById("circleDetail");
const sceneTitleEl = document.getElementById("sceneTitle");
const sceneStepEl = document.getElementById("sceneStep");
const sceneDescriptionEl = document.getElementById("sceneDescription");
const lessonPointsEl = document.getElementById("lessonPoints");
const formulaBoxEl = document.getElementById("formulaBox");
const processBoxEl = document.getElementById("processBox");
const quickProcessBoxEl = document.getElementById("quickProcessBox");
const explanationBoxEl = document.getElementById("explanationBox");
const sceneButtonsEl = document.getElementById("sceneButtons");
const pageEl = document.querySelector(".page");
const widthMinusEl = document.getElementById("widthMinus");
const widthPlusEl = document.getElementById("widthPlus");
const widthValueTextEl = document.getElementById("widthValue");

const width = 900;
const height = 560;
const margin = { top: 30, right: 32, bottom: 56, left: 56 };
const xMin = -3;
const xMax = 3;
const yMin = -2;
const yMax = 9;
const minPageWidth = 320;
const maxPageWidth = 900;
const pageWidthStep = 20;
const pageWidthStorageKey = "study-layout-width";
let renderedBallHit = null;
let isDraggingBall = false;

function f(x) {
  return x * x;
}

function df(x) {
  return 2 * x;
}

function integralFromZero(x) {
  return (x * x * x) / 3;
}

function fmt(value) {
  if (Math.abs(value) < 1e-9) {
    return "0.00";
  }
  return Number(value).toFixed(2);
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function setPageWidth(nextWidth) {
  const safeWidth = clamp(nextWidth, minPageWidth, maxPageWidth);
  pageEl.style.setProperty("--page-max-width", `${safeWidth}px`);
  widthValueTextEl.textContent = `${safeWidth}px`;
  localStorage.setItem(pageWidthStorageKey, String(safeWidth));
}

function initializePageWidth() {
  const storedWidth = Number(localStorage.getItem(pageWidthStorageKey));
  const initialWidth = Number.isFinite(storedWidth) && storedWidth > 0 ? storedWidth : 430;
  setPageWidth(initialWidth);
}

function mapX(x) {
  return margin.left + ((x - xMin) / (xMax - xMin)) * (width - margin.left - margin.right);
}

function mapY(y) {
  return height - margin.bottom - ((y - yMin) / (yMax - yMin)) * (height - margin.top - margin.bottom);
}

function unmapX(px) {
  const usableWidth = width - margin.left - margin.right;
  return xMin + ((px - margin.left) / usableWidth) * (xMax - xMin);
}

function createSvg(tag, attrs = {}) {
  const el = document.createElementNS("http://www.w3.org/2000/svg", tag);
  Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value));
  return el;
}

function linePath(x1, y1, x2, y2) {
  return `M ${mapX(x1)} ${mapY(y1)} L ${mapX(x2)} ${mapY(y2)}`;
}

function functionPath(start = xMin, end = xMax, step = 0.03) {
  let d = "";
  for (let x = start; x <= end + 1e-9; x += step) {
    d += `${x === start ? "M" : "L"} ${mapX(x)} ${mapY(f(x))} `;
  }
  return d.trim();
}

function areaPath(start, end, step = 0.03) {
  const left = Math.min(start, end);
  const right = Math.max(start, end);
  let d = `M ${mapX(left)} ${mapY(0)} `;
  for (let x = left; x <= right + 1e-9; x += step) {
    d += `L ${mapX(x)} ${mapY(f(x))} `;
  }
  d += `L ${mapX(right)} ${mapY(0)} Z`;
  return d;
}

function tangentLineAt(x0) {
  const y0 = f(x0);
  const m = df(x0);
  return {
    yLeft: y0 + m * (xMin - x0),
    yRight: y0 + m * (xMax - x0)
  };
}

function tangentSegmentAt(x0, span = 0.8) {
  const leftX = clamp(x0 - span, xMin, xMax);
  const rightX = clamp(x0 + span, xMin, xMax);
  const y0 = f(x0);
  const m = df(x0);
  return {
    x1: leftX,
    y1: y0 + m * (leftX - x0),
    x2: rightX,
    y2: y0 + m * (rightX - x0),
    xMid: (leftX + rightX) / 2,
    yMid: y0 + m * (((leftX + rightX) / 2) - x0)
  };
}

function secantLineAt(x0, dx) {
  const x2 = clamp(x0 + dx, xMin, xMax);
  return { x1: x0, y1: f(x0), x2, y2: f(x2), dx: x2 - x0 };
}

function ballRadiusFromY(y) {
  const normalized = clamp(y / yMax, 0, 1);
  return 12 + normalized * 24;
}

function getBallFromX(x) {
  const y = f(x);
  const tangent = tangentSegmentAt(x, 0.72);
  return {
    x,
    y,
    radius: ballRadiusFromY(y),
    tangent
  };
}

const scenes = [
  {
    title: "직선의 기울기",
    description: "두 점의 세로 변화량과 가로 변화량을 비교하면 직선의 기울기를 구할 수 있습니다.",
    points: [
      "기울기는 변화량의 비율입니다.",
      "두 점을 잡으면 평균 변화율이 계산됩니다.",
      "미분의 출발점이 되는 감각입니다."
    ],
    getDetails(x) {
      const x1 = clamp(x, xMin, xMax - 1);
      const x2 = x1 + 1;
      const y1 = f(x1);
      const y2 = f(x2);
      const dy = y2 - y1;
      const slope = dy / (x2 - x1);
      return {
        formula: [
          "기울기 = (y2 - y1) / (x2 - x1)",
          `A = (${fmt(x1)}, ${fmt(y1)})`,
          `B = (${fmt(x2)}, ${fmt(y2)})`
        ].join("\n"),
        process: [
          `1. x1 = ${fmt(x1)}, x2 = ${fmt(x2)}`,
          `2. y1 = (${fmt(x1)})^2 = ${fmt(y1)}`,
          `3. y2 = (${fmt(x2)})^2 = ${fmt(y2)}`,
          `4. Δy = ${fmt(y2)} - ${fmt(y1)} = ${fmt(dy)}`,
          `5. Δx = ${fmt(x2)} - ${fmt(x1)} = 1.00`,
          `6. 기울기 = ${fmt(slope)}`
        ],
        explanation: `두 점 사이 평균 변화율을 먼저 보고, 이후 접선 기울기로 넘어갑니다.`,
        graph: { x1, y1, x2, y2 }
      };
    }
  },
  {
    title: "할선에서 접선으로",
    description: "가까운 두 점을 이은 할선이 점점 접선의 기울기에 가까워지는 장면입니다.",
    points: [
      "할선은 두 점을 잇는 선입니다.",
      "점이 가까워질수록 순간 변화율에 가까워집니다.",
      "극한의 생각이 들어갑니다."
    ],
    getDetails(x) {
      const h = Math.max(0.2, 1.2 - Math.abs(x) * 0.2);
      const secant = secantLineAt(x, h);
      const slope = (secant.y2 - secant.y1) / secant.dx;
      return {
        formula: [
          "f'(a) = lim h→0 [f(a+h) - f(a)] / h",
          `a = ${fmt(x)}, h = ${fmt(secant.dx)}`
        ].join("\n"),
        process: [
          `1. f(a) = ${fmt(secant.y1)}`,
          `2. f(a+h) = ${fmt(secant.y2)}`,
          `3. Δy = ${fmt(secant.y2 - secant.y1)}`,
          `4. Δx = ${fmt(secant.dx)}`,
          `5. 할선 기울기 = ${fmt(slope)}`,
          `6. 접선 기울기 ${fmt(df(x))}에 가까워집니다.`
        ],
        explanation: `두 번째 점이 더 가까워질수록 접선의 기울기에 수렴합니다.`,
        graph: { secant }
      };
    }
  },
  {
    title: "도함수는 기울기 함수",
    description: "x²의 도함수 2x는 각 x에서의 접선 기울기를 바로 알려줍니다.",
    points: [
      "도함수는 변화 속도입니다.",
      "x²의 도함수는 2x입니다.",
      "현재 x에서의 기울기를 즉시 읽을 수 있습니다."
    ],
    getDetails(x) {
      const y = f(x);
      const slope = df(x);
      return {
        formula: ["f(x) = x²", "f'(x) = 2x", `현재 x = ${fmt(x)}`].join("\n"),
        process: [
          "1. 원래 함수는 f(x) = x²",
          "2. x²를 미분하면 2x",
          `3. f'(${fmt(x)}) = 2 × ${fmt(x)}`,
          `4. 결과는 ${fmt(slope)}`,
          `5. 현재 점의 접선 기울기도 ${fmt(slope)}`
        ],
        explanation: `도함수는 현재 위치의 접선 기울기를 빠르게 계산하는 식입니다.`,
        graph: { x, y }
      };
    }
  },
  {
    title: "부정적분과 +C",
    description: "2x를 적분하면 x²가 되고, 상수항은 미분하면 사라지므로 +C가 남습니다.",
    points: [
      "적분은 미분의 반대 방향입니다.",
      "상수는 미분하면 0입니다.",
      "그래서 답은 x² + C 꼴입니다."
    ],
    getDetails(x) {
      const y = f(x);
      const slope = df(x);
      return {
        formula: ["∫ 2x dx = x² + C", "d/dx (x² + C) = 2x"].join("\n"),
        process: [
          "1. 적분하려는 식은 2x",
          "2. 미분 결과가 2x인 대표 함수는 x²",
          "3. 상수 C는 미분하면 0",
          "4. 따라서 ∫ 2x dx = x² + C",
          `5. 현재 x에서 2x = ${fmt(slope)}`,
          `6. x² = ${fmt(y)}`
        ],
        explanation: `같은 도함수를 만드는 함수가 여러 개라서 +C가 필요합니다.`,
        graph: { x, y }
      };
    }
  },
  {
    title: "정적분은 넓이",
    description: "0부터 현재 x까지 곡선 아래의 누적량을 정적분으로 볼 수 있습니다.",
    points: [
      "정적분은 누적량입니다.",
      "x²의 0부터 x까지 적분은 x³/3입니다.",
      "넓이처럼 보이지만 방향도 함께 반영합니다."
    ],
    getDetails(x) {
      const area = integralFromZero(x);
      return {
        formula: ["∫₀ˣ t² dt = [t³ / 3]₀ˣ", "= x³ / 3 - 0"].join("\n"),
        process: [
          "1. 원시함수는 t³ / 3",
          `2. F(${fmt(x)}) = ${fmt(area)}`,
          "3. F(0) = 0.00",
          `4. 정적분 = F(${fmt(x)}) - F(0)`,
          `5. 값 = ${fmt(area)}`
        ],
        explanation: `현재 x까지 쌓인 값이 음영 면적으로 표현됩니다.`,
        graph: { x }
      };
    }
  },
  {
    title: "접선 위 공의 크기 변화",
    description: "x 위치 이동 슬라이더를 움직이면 공이 현재 접선의 가운데에 맞춰 움직이고, y값이 0에 가까우면 작아지고 커질수록 확대됩니다. 원주율처럼 고정된 상수는 정적이지만, 기울기는 x에 따라 바뀌는 동적인 값이라는 대비도 함께 볼 수 있습니다.",
    points: [
      "공의 중심은 현재 x에서 만든 접선의 가운데에 놓입니다.",
      "y = 0이면 가장 작은 크기로 보입니다.",
      "y값이 커질수록 공 반지름도 커집니다.",
      "지금 공 크기는 기울기보다 y값을 기준으로 커지거나 작아지게 연결되어 있습니다.",
      "원주율은 고정된 값이고, 기울기는 계속 변하는 값입니다."
    ],
    getDetails(x) {
      const ball = getBallFromX(x);
      return {
        formula: [
          "공 반지름 = 12 + (y / 9) × 24",
          "y = x²"
        ].join("\n"),
        process: [
          `1. 현재 x = ${fmt(x)}`,
          `2. y = x² = ${fmt(ball.y)}`,
          `3. y가 0이면 공 반지름은 12.00`,
          `4. y가 커질수록 반지름이 선형으로 증가`,
          `5. 현재 공 반지름 = ${fmt(ball.radius)}`,
          `6. 공 중심은 접선 가운데 (${fmt(ball.tangent.xMid)}, ${fmt(ball.tangent.yMid)})`
        ],
        explanation: `지금 공은 현재 x에서 만든 접선의 가운데에 맞춰 놓여 있고, 높이 y가 커질수록 더 크게 보입니다. 여기서 원주율은 변하지 않는 정적인 상수이고, 접선의 기울기는 x에 따라 계속 달라지는 동적인 값입니다.`,
        graph: { ball }
      };
    }
  }
];

function renderButtons() {
  sceneButtonsEl.innerHTML = "";
  scenes.forEach((scene, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `scene-button${index === Number(sceneRange.value) ? " active" : ""}`;
    button.textContent = `${index + 1}. ${scene.title}`;
    button.addEventListener("click", () => {
      sceneRange.value = String(index);
      update();
    });
    sceneButtonsEl.appendChild(button);
  });
}

function updateSide(sceneIndex, x) {
  const scene = scenes[sceneIndex];
  const details = scene.getDetails(x);
  sceneTitleEl.textContent = scene.title;
  sceneStepEl.textContent = `${sceneIndex + 1} / ${scenes.length}`;
  sceneDescriptionEl.textContent = scene.description;
  lessonPointsEl.innerHTML = scene.points.map((point) => `<li class="fade">${point}</li>`).join("");
  formulaBoxEl.textContent = details.formula;
  const processMarkup = details.process.map((step) => `<li class="fade">${step}</li>`).join("");
  processBoxEl.innerHTML = processMarkup;
  quickProcessBoxEl.innerHTML = processMarkup;
  explanationBoxEl.textContent = details.explanation;
}

function drawBaseGraph() {
  for (let gx = Math.ceil(xMin); gx <= Math.floor(xMax); gx += 1) {
    svg.appendChild(createSvg("line", { x1: mapX(gx), y1: mapY(yMin), x2: mapX(gx), y2: mapY(yMax), class: "grid-line" }));
  }
  for (let gy = Math.ceil(yMin); gy <= Math.floor(yMax); gy += 1) {
    svg.appendChild(createSvg("line", { x1: mapX(xMin), y1: mapY(gy), x2: mapX(xMax), y2: mapY(gy), class: "grid-line" }));
  }
  svg.appendChild(createSvg("line", { x1: mapX(xMin), y1: mapY(0), x2: mapX(xMax), y2: mapY(0), class: "axis" }));
  svg.appendChild(createSvg("line", { x1: mapX(0), y1: mapY(yMin), x2: mapX(0), y2: mapY(yMax), class: "axis" }));
  svg.appendChild(createSvg("path", { d: functionPath(), class: "curve" }));
}

function label(text, x, y, className = "label") {
  const node = createSvg("text", { x, y, class: className });
  node.textContent = text;
  svg.appendChild(node);
}

function drawBallOnTangent(ball, options = {}) {
  const compact = options.compact ?? false;
  const radius = compact ? ball.radius * 0.56 : ball.radius;
  const tangent = compact ? tangentSegmentAt(ball.x, 0.42) : ball.tangent;
  const cx = mapX(tangent.xMid);
  const cy = mapY(tangent.yMid);
  renderedBallHit = { cx, cy, radius, compact };

  svg.appendChild(createSvg("path", {
    d: linePath(tangent.x1, tangent.y1, tangent.x2, tangent.y2),
    class: compact ? "secant" : "tangent"
  }));

  svg.appendChild(createSvg("ellipse", {
    cx,
    cy: cy + radius + 8,
    rx: radius * 0.95,
    ry: compact ? 5 : 8,
    class: "ball-shadow"
  }));

  const group = createSvg("g", { transform: `translate(${cx} ${cy}) rotate(${ball.x * 30})` });
  group.appendChild(createSvg("circle", { cx: 0, cy: 0, r: radius + (compact ? 5 : 9), class: "ball-halo" }));
  group.appendChild(createSvg("circle", { cx: 0, cy: 0, r: radius, class: "rolling-ball" }));
  group.appendChild(createSvg("path", {
    d: `M ${-radius * 0.68} ${-radius * 0.2} Q 0 ${-radius * 0.9} ${radius * 0.68} ${-radius * 0.2}`,
    class: "ball-stripe"
  }));
  group.appendChild(createSvg("path", {
    d: `M ${-radius * 0.7} ${radius * 0.18} Q 0 ${radius * 0.88} ${radius * 0.7} ${radius * 0.18}`,
    class: "ball-stripe"
  }));
  group.appendChild(createSvg("circle", {
    cx: -radius * 0.28,
    cy: -radius * 0.34,
    r: Math.max(3, radius * 0.18),
    class: "ball-highlight"
  }));
  svg.appendChild(group);

  if (!compact) {
    const label = createSvg("text", {
      x: cx + 14,
      y: cy - radius - 12,
      class: "label"
    });
    label.textContent = `y=${fmt(ball.y)}, r=${fmt(ball.radius)}`;
    svg.appendChild(label);
  }
}

function draw() {
  const sceneIndex = Number(sceneRange.value);
  const x = Number(xRange.value);
  const y = f(x);
  const slope = df(x);
  const area = integralFromZero(x);
  const ball = getBallFromX(x);
  const details = scenes[sceneIndex].getDetails(x);
  const secant = sceneIndex === 1 ? details.graph.secant : null;
  const x2Scene0 = clamp(x + 1, xMin, xMax);

  xValueEl.textContent = fmt(x);
  fxValueEl.textContent = fmt(y);
  dfValueEl.textContent = fmt(slope);
  areaValueEl.textContent = fmt(area);
  circleValueEl.textContent = fmt(ball.radius);

  if (sceneIndex === 0) {
    xDetailEl.textContent = `공식: x2 = x1 + 1\n대입: x1=${fmt(x)}, x2=${fmt(x2Scene0)}\n설명: 두 점을 잡아 직선의 기울기를 먼저 계산합니다.`;
  } else if (sceneIndex === 1 && secant) {
    xDetailEl.textContent = `공식: x = a + h\n대입: a=${fmt(secant.x1)}, h=${fmt(secant.dx)}\n설명: 접점 a 옆에 a+h를 잡아 할선을 만듭니다.`;
  } else {
    xDetailEl.textContent = `공식: 현재 선택값 = x\n대입: x=${fmt(x)}\n설명: 슬라이더가 현재 보고 있는 위치를 정합니다.`;
  }

  fxDetailEl.textContent = `공식: f(x) = x^2\n대입: ${fmt(x)}^2 = ${fmt(y)}\n설명: 원래 함수가 현재 점의 높이를 만듭니다.`;
  dfDetailEl.textContent = `공식: f'(x) = 2x\n대입: 2 × ${fmt(x)} = ${fmt(slope)}\n설명: 도함수로 현재 접선의 기울기를 바로 구합니다.`;
  areaDetailEl.textContent = `공식: ∫0→x t^2dt = x^3 / 3\n대입: ${fmt(x)}^3 / 3 = ${fmt(area)}\n설명: 0부터 x까지 곡선 아래 누적된 넓이입니다.`;
  circleDetailEl.textContent = `공식: r = 12 + (y / 9) × 24\n대입: 12 + (${fmt(y)} / 9) × 24 = ${fmt(ball.radius)}\n설명: 높이 y가 커질수록 공 반지름도 함께 커집니다.`;

  if (sceneIndex === 0) {
    xDetailEl.textContent = `공식: x2 = x1 + 1\n대입: x1=${fmt(x)}, x2=${fmt(x2Scene0)}\n계산: ${fmt(x)} + 1.00 = ${fmt(x2Scene0)}\n설명: 두 점을 잡아 직선의 기울기를 먼저 계산합니다.`;
  } else if (sceneIndex === 1 && secant) {
    xDetailEl.textContent = `공식: x = a + h\n대입: a=${fmt(secant.x1)}, h=${fmt(secant.dx)}\n계산: ${fmt(secant.x1)} + ${fmt(secant.dx)} = ${fmt(secant.x2)}\n설명: 접점 a 옆에 a+h를 잡아 할선을 만듭니다.`;
  } else {
    xDetailEl.textContent = `공식: 현재 선택값 = x\n대입: x=${fmt(x)}\n계산: 슬라이더 값 = ${fmt(x)}\n설명: 슬라이더가 현재 보고 있는 위치를 정합니다.`;
  }

  fxDetailEl.textContent = `공식: f(x) = x^2\n대입: ${fmt(x)}^2 = ${fmt(y)}\n계산: ${fmt(x)} × ${fmt(x)} = ${fmt(y)}\n설명: 원래 함수가 현재 점의 높이를 만듭니다.`;
  dfDetailEl.textContent = `공식: f'(x) = 2x\n대입: 2 × ${fmt(x)} = ${fmt(slope)}\n계산: 2 × ${fmt(x)} = ${fmt(slope)}\n설명: 도함수로 현재 접선의 기울기를 바로 구합니다.`;
  areaDetailEl.textContent = `공식: ∫0→x t^2dt = x^3 / 3\n대입: ${fmt(x)}^3 / 3 = ${fmt(area)}\n계산: ${fmt(x * x * x)} / 3 = ${fmt(area)}\n설명: 0부터 x까지 곡선 아래 누적된 넓이입니다.`;
  circleDetailEl.textContent = `공식: r = 12 + (y / 9) × 24\n대입: 12 + (${fmt(y)} / 9) × 24 = ${fmt(ball.radius)}\n계산: 12 + ${fmt((y / 9) * 24)} = ${fmt(ball.radius)}\n설명: 높이 y가 커질수록 공 반지름도 함께 커집니다.`;

  svg.innerHTML = "";
  renderedBallHit = null;

  if (sceneIndex === 5) {
    drawBaseGraph();
    drawBallOnTangent(details.graph.ball);
    return;
  }

  drawBaseGraph();

  if (sceneIndex === 0) {
    const { x1, y1, x2, y2 } = details.graph;
    const dx = x2 - x1;
    const dy = y2 - y1;
    const slopeLabel = dy / dx;
    svg.appendChild(createSvg("path", { d: linePath(x1, y1, x2, y2), class: "tangent" }));
    svg.appendChild(createSvg("line", { x1: mapX(x1), y1: mapY(y1), x2: mapX(x2), y2: mapY(y1), class: "helper-line" }));
    svg.appendChild(createSvg("line", { x1: mapX(x2), y1: mapY(y1), x2: mapX(x2), y2: mapY(y2), class: "helper-line" }));
    svg.appendChild(createSvg("circle", { cx: mapX(x1), cy: mapY(y1), r: 8, class: "point-main" }));
    svg.appendChild(createSvg("circle", { cx: mapX(x2), cy: mapY(y2), r: 8, class: "point-helper" }));
    label(`A(${fmt(x1)}, ${fmt(y1)})`, mapX(x1) + 10, mapY(y1) - 12, "label-soft");
    label(`B(${fmt(x2)}, ${fmt(y2)})`, mapX(x2) + 10, mapY(y2) + 20, "label-soft");
    label(`Δx=${fmt(dx)}`, (mapX(x1) + mapX(x2)) / 2 - 18, mapY(y1) + 24, "label-soft");
    label(`Δy=${fmt(dy)}`, mapX(x2) + 10, (mapY(y1) + mapY(y2)) / 2, "label-soft");
    label(`기울기=${fmt(slopeLabel)}`, mapX(-2.65), mapY(8.3), "label-soft");
  }

  if (sceneIndex === 1) {
    const { secant } = details.graph;
    const tangent = tangentLineAt(x);
    const secantSlope = (secant.y2 - secant.y1) / secant.dx;
    svg.appendChild(createSvg("path", { d: linePath(secant.x1, secant.y1, secant.x2, secant.y2), class: "secant" }));
    svg.appendChild(createSvg("path", { d: linePath(xMin, tangent.yLeft, xMax, tangent.yRight), class: "tangent" }));
    svg.appendChild(createSvg("circle", { cx: mapX(secant.x1), cy: mapY(secant.y1), r: 8, class: "point-main" }));
    svg.appendChild(createSvg("circle", { cx: mapX(secant.x2), cy: mapY(secant.y2), r: 7, class: "point-helper" }));
    label(`a=${fmt(secant.x1)}`, mapX(secant.x1) - 18, mapY(0) + 28, "label-soft");
    label(`a+h=${fmt(secant.x2)}`, mapX(secant.x2) - 26, mapY(0) + 28, "label-soft");
    label(`f(a)=${fmt(secant.y1)}`, mapX(secant.x1) + 10, mapY(secant.y1) - 12, "label-soft");
    label(`f(a+h)=${fmt(secant.y2)}`, mapX(secant.x2) + 10, mapY(secant.y2) - 12, "label-soft");
    label(`h=${fmt(secant.dx)}`, (mapX(secant.x1) + mapX(secant.x2)) / 2 - 12, mapY(0) + 46, "label-soft");
    label(`할선=${fmt(secantSlope)}`, mapX(-2.65), mapY(8.35), "label-soft");
    label(`접선≈${fmt(df(x))}`, mapX(-2.65), mapY(7.7), "label-soft");
  }

  if (sceneIndex === 2 || sceneIndex === 3) {
    const tangent = tangentLineAt(x);
    svg.appendChild(createSvg("path", { d: linePath(xMin, tangent.yLeft, xMax, tangent.yRight), class: "tangent" }));
    svg.appendChild(createSvg("circle", { cx: mapX(x), cy: mapY(y), r: 8, class: "point-main" }));
    label(`x=${fmt(x)}`, mapX(x) - 14, mapY(0) + 28, "label-soft");
    label(`f(x)=${fmt(y)}`, mapX(x) + 10, mapY(y) - 12, "label-soft");
    label(`f'(x)=${fmt(slope)}`, mapX(-2.65), mapY(8.25), "label-soft");
    if (sceneIndex === 3) {
      label(`x²+C`, mapX(2.1), mapY(7.8), "label-soft");
      label(`2x=${fmt(slope)}`, mapX(-2.65), mapY(7.55), "label-soft");
    }
  }

  if (sceneIndex === 4) {
    svg.appendChild(createSvg("path", { d: areaPath(0, x), class: "area-fill" }));
    svg.appendChild(createSvg("circle", { cx: mapX(x), cy: mapY(f(x)), r: 8, class: "point-main" }));
    svg.appendChild(createSvg("line", { x1: mapX(x), y1: mapY(0), x2: mapX(x), y2: mapY(f(x)), class: "helper-line" }));
    label(`x=${fmt(x)}`, mapX(x) - 14, mapY(0) + 28, "label-soft");
    label(`f(x)=${fmt(y)}`, mapX(x) + 10, mapY(y) - 12, "label-soft");
    label(`넓이=${fmt(area)}`, mapX(Math.max(0.2, x * 0.45)), mapY(Math.max(0.7, y * 0.3)), "label-soft");
    label(`[t³/3]`, mapX(-2.65), mapY(8.3), "label-soft");
    label(`정적분=${fmt(area)}`, mapX(-2.65), mapY(7.65), "label-soft");
  }

  drawBallOnTangent(ball, { compact: true });
}

function update() {
  const sceneIndex = Number(sceneRange.value);
  const x = Number(xRange.value);
  updateSide(sceneIndex, x);
  renderButtons();
  draw();
}

sceneRange.addEventListener("input", update);
xRange.addEventListener("input", update);

svg.addEventListener("pointerdown", (event) => {
  if (!renderedBallHit) {
    return;
  }

  const rect = svg.getBoundingClientRect();
  const scaleX = width / rect.width;
  const scaleY = height / rect.height;
  const px = (event.clientX - rect.left) * scaleX;
  const py = (event.clientY - rect.top) * scaleY;
  const dx = px - renderedBallHit.cx;
  const dy = py - renderedBallHit.cy;
  const hitRadius = renderedBallHit.radius + 14;

  if ((dx * dx) + (dy * dy) > hitRadius * hitRadius) {
    return;
  }

  isDraggingBall = true;
  svg.setPointerCapture(event.pointerId);
  svg.style.cursor = "grabbing";
});

svg.addEventListener("pointermove", (event) => {
  if (!renderedBallHit) {
    svg.style.cursor = "default";
    return;
  }

  const rect = svg.getBoundingClientRect();
  const scaleX = width / rect.width;
  const scaleY = height / rect.height;
  const px = (event.clientX - rect.left) * scaleX;
  const py = (event.clientY - rect.top) * scaleY;
  const dx = px - renderedBallHit.cx;
  const dy = py - renderedBallHit.cy;
  const hitRadius = renderedBallHit.radius + 14;

  svg.style.cursor = isDraggingBall
    ? "grabbing"
    : ((dx * dx) + (dy * dy) <= hitRadius * hitRadius ? "grab" : "default");

  if (!isDraggingBall) {
    return;
  }

  const nextX = clamp(unmapX(px), Number(xRange.min), Number(xRange.max));
  xRange.value = String(nextX);
  update();
});

function stopDraggingBall(event) {
  if (event && svg.hasPointerCapture(event.pointerId)) {
    svg.releasePointerCapture(event.pointerId);
  }
  isDraggingBall = false;
  svg.style.cursor = "default";
}

svg.addEventListener("pointerup", stopDraggingBall);
svg.addEventListener("pointercancel", stopDraggingBall);

widthMinusEl.addEventListener("click", () => {
  const currentWidth = Number.parseInt(widthValueTextEl.textContent, 10) || 430;
  setPageWidth(currentWidth - pageWidthStep);
});

widthPlusEl.addEventListener("click", () => {
  const currentWidth = Number.parseInt(widthValueTextEl.textContent, 10) || 430;
  setPageWidth(currentWidth + pageWidthStep);
});

initializePageWidth();
update();
