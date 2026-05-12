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
const constantValueEl = document.getElementById("constantValue");
const constantDetailEl = document.getElementById("constantDetail");
const sampleValueEl = document.getElementById("sampleValue");
const sampleDetailEl = document.getElementById("sampleDetail");
const sceneTitleEl = document.getElementById("sceneTitle");
const sceneStepEl = document.getElementById("sceneStep");
const sceneDescriptionEl = document.getElementById("sceneDescription");
const lessonPointsEl = document.getElementById("lessonPoints");
const formulaBoxEl = document.getElementById("formulaBox");
const processBoxEl = document.getElementById("processBox");
const explanationBoxEl = document.getElementById("explanationBox");
const sceneButtonsEl = document.getElementById("sceneButtons");
const pageEl = document.querySelector(".page");
const widthMinusEl = document.getElementById("widthMinus");
const widthPlusEl = document.getElementById("widthPlus");
const widthValueTextEl = document.getElementById("widthValue");

const width = 900;
const height = 580;
const margin = { top: 28, right: 34, bottom: 58, left: 62 };
const xMin = -0.2;
const xMax = 3.4;
const yMin = -1;
const yMax = 10.5;
const constantC = 3;
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

function F(x) {
  return (x * x * x) / 3;
}

function g(x) {
  return 2 * x;
}

function G(x) {
  return x * x;
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

function functionPath(fn, start = xMin, end = xMax, step = 0.03) {
  let d = "";
  for (let x = start; x <= end + 1e-9; x += step) {
    d += `${x === start ? "M" : "L"} ${mapX(x)} ${mapY(fn(x))} `;
  }
  return d.trim();
}

function areaPath(fn, start, end, step = 0.03) {
  const left = Math.min(start, end);
  const right = Math.max(start, end);
  let d = `M ${mapX(left)} ${mapY(0)} `;
  for (let x = left; x <= right + 1e-9; x += step) {
    d += `L ${mapX(x)} ${mapY(fn(x))} `;
  }
  d += `L ${mapX(right)} ${mapY(0)} Z`;
  return d;
}

function tangentLineAt(x0) {
  const y0 = f(x0);
  const slope = df(x0);
  return {
    yLeft: y0 + slope * (xMin - x0),
    yRight: y0 + slope * (xMax - x0)
  };
}

function tangentSegmentAt(x0, span = 0.45) {
  const leftX = clamp(x0 - span, xMin, xMax);
  const rightX = clamp(x0 + span, xMin, xMax);
  const y0 = f(x0);
  const slope = df(x0);
  return {
    x1: leftX,
    y1: y0 + slope * (leftX - x0),
    x2: rightX,
    y2: y0 + slope * (rightX - x0),
    xMid: (leftX + rightX) / 2,
    yMid: y0 + slope * (((leftX + rightX) / 2) - x0)
  };
}

function secantAt(x0, h) {
  const x1 = clamp(x0, xMin, xMax);
  const x2 = clamp(x0 + h, xMin, xMax);
  return {
    x1,
    y1: f(x1),
    x2,
    y2: f(x2),
    h: x2 - x1
  };
}

function ballRadiusFromY(y) {
  const normalized = clamp(y / yMax, 0, 1);
  return 11 + normalized * 16;
}

function getBallFromX(x) {
  const y = f(x);
  return {
    x,
    y,
    radius: ballRadiusFromY(y),
    tangent: tangentSegmentAt(x, 0.45)
  };
}

const scenes = [
  {
    title: "미분 복습: 접선의 기울기",
    description: "적분으로 가기 전에, 먼저 미분이 접선의 기울기를 구하는 과정이라는 감각을 다시 붙잡습니다.",
    points: [
      "두 점의 기울기는 평균변화율입니다.",
      "점을 더 가까이 보내면 접선의 기울기에 가까워집니다.",
      "적분은 이 미분의 역과정이라는 말을 곧 이어서 보게 됩니다."
    ],
    getDetails(x) {
      const secant = secantAt(x, 0.9);
      const secantSlope = (secant.y2 - secant.y1) / secant.h;
      return {
        formula: [
          "f'(a) = lim h->0 [f(a+h)-f(a)] / h",
          "f(x) = x^2",
          `a = ${fmt(x)}`
        ].join("\n"),
        process: [
          `1. f(${fmt(secant.x1)}) = ${fmt(secant.y1)}`,
          `2. f(${fmt(secant.x2)}) = ${fmt(secant.y2)}`,
          `3. 평균변화율 = (${fmt(secant.y2)} - ${fmt(secant.y1)}) / ${fmt(secant.h)}`,
          `4. 할선의 기울기 = ${fmt(secantSlope)}`,
          `5. 접선의 기울기 f'(${fmt(x)}) = ${fmt(df(x))}`
        ],
        explanation: "지금 장면은 적분의 출발점입니다. 미분이 '순간적인 기울기'를 구하는 과정이어야, 그 반대 방향인 적분을 '원래 함수 복원'으로 느낄 수 있습니다.",
        graph: { kind: "derivative", secant }
      };
    }
  },
  {
    title: "부정적분과 적분상수",
    description: "도함수만 알고 원래 함수를 되돌리면, 마지막 상수항은 알 수 없어서 +C가 남습니다.",
    points: [
      "2x를 미분하기 전 함수는 x^2입니다.",
      "하지만 x^2 + 1, x^2 + 213을 미분해도 모두 2x입니다.",
      "그래서 부정적분은 하나로 정해지지 않고 +C를 붙입니다."
    ],
    getDetails(x) {
      return {
        formula: [
          "Integral 2x dx = x^2 + C",
          "d/dx (x^2 + C) = 2x",
          `예시 C = ${fmt(constantC)}`
        ].join("\n"),
        process: [
          "1. 2x가 나오려면 미분 전 함수의 차수는 1 올라갑니다.",
          "2. x^2를 미분하면 2x가 됩니다.",
          "3. 상수 C를 미분하면 0이 됩니다.",
          "4. 따라서 원래 함수들은 x^2 + C 꼴 전체입니다.",
          `5. 예시 곡선: y = x^2 + ${fmt(constantC)}`
        ],
        explanation: "대본에서 말한 '끄트리를 알 수 없다'는 느낌이 바로 이것입니다. 미분하면 사라지는 상수항 때문에, 적분은 조건 없이는 완전히 하나로 결정되지 않습니다.",
        graph: { kind: "antiderivativeFamily", x }
      };
    }
  },
  {
    title: "정적분: 넓이가 하나의 값으로 정해질 때",
    description: "구간이 주어지면 적분상수는 서로 지워지고, 넓이처럼 딱 하나의 값이 남습니다.",
    points: [
      "정적분은 위끝 대입값에서 아래끝 대입값을 빼는 계산입니다.",
      "Integral 0 to x of t^2 dt = [t^3/3]_0^x = x^3/3 입니다.",
      "이 값은 0부터 x까지 곡선 아래 누적된 양입니다."
    ],
    getDetails(x) {
      const area = F(x);
      return {
        formula: [
          "Integral 0->x t^2 dt = [t^3 / 3]_0^x",
          `= ${fmt(x)}^3 / 3`,
          `= ${fmt(area)}`
        ].join("\n"),
        process: [
          "1. t^2의 한 부정적분은 t^3/3 입니다.",
          `2. 위끝 ${fmt(x)}를 넣으면 ${fmt(area)}`,
          "3. 아래끝 0을 넣으면 0.00",
          `4. 정적분 값 = ${fmt(area)} - 0.00`,
          `5. 최종값 = ${fmt(area)}`
        ],
        explanation: "부정적분에서는 +C가 있었지만, 정적분에서는 위끝과 아래끝을 빼는 순간 C가 사라집니다. 그래서 결과가 하나의 수로 딱 정해집니다.",
        graph: { kind: "area", x }
      };
    }
  },
  {
    title: "미적분의 기본정리",
    description: "0부터 x까지 넓이를 S(x)라 두면, 그 넓이를 미분한 값은 바로 현재 높이 f(x)가 됩니다.",
    points: [
      "S(x) = Integral 0 to x of t^2 dt 라고 둡니다.",
      "아주 조금 오른쪽으로 가면 넓이는 거의 '높이 x 얇은 폭'만큼 늘어납니다.",
      "그래서 S'(x) = f(x) 가 됩니다."
    ],
    getDetails(x) {
      const dx = 0.28;
      const nextX = clamp(x + dx, 0, 3.2);
      const deltaArea = F(nextX) - F(x);
      return {
        formula: [
          "S(x) = Integral 0->x t^2 dt",
          "S'(x) = f(x)",
          `S'(${fmt(x)}) = ${fmt(f(x))}`
        ].join("\n"),
        process: [
          `1. 현재 높이 f(${fmt(x)}) = ${fmt(f(x))}`,
          `2. Delta x = ${fmt(nextX - x)}`,
          `3. 실제 넓이 증가 Delta S = ${fmt(deltaArea)}`,
          `4. Delta S / Delta x = ${fmt(deltaArea / (nextX - x))}`,
          `5. 폭이 더 얇아질수록 ${fmt(f(x))}에 가까워집니다.`
        ],
        explanation: "대본의 핵심 문장인 '넓이를 미분하면 길이가 된다'를 시각화한 장면입니다. 누적 넓이의 순간 변화율은 지금 막 추가되는 세로 길이와 같아집니다.",
        graph: { kind: "fundamental", x, nextX }
      };
    }
  },
  {
    title: "예시: 0에서 3까지 2x를 적분하면",
    description: "직선 y=2x 아래 삼각형 넓이를 적분으로 계산하면, 익숙한 삼각형 넓이 공식과 정확히 같은 값이 나옵니다.",
    points: [
      "정적분은 직선뿐 아니라 곡선 아래 넓이에도 그대로 확장됩니다.",
      "여기서는 가장 익숙한 삼각형 예시를 먼저 확인합니다.",
      "Integral 0 to 3 of 2x dx = [x^2]_0^3 = 9 입니다."
    ],
    getDetails() {
      return {
        formula: [
          "Integral 0->3 2x dx = [x^2]_0^3",
          "= 3^2 - 0^2",
          "= 9"
        ].join("\n"),
        process: [
          "1. 2x의 한 부정적분은 x^2 입니다.",
          "2. 위끝 3 대입: 9",
          "3. 아래끝 0 대입: 0",
          "4. 정적분 값 = 9 - 0",
          "5. 삼각형 넓이 1/2 x 3 x 6 과도 일치합니다."
        ],
        explanation: "이 장면이 대본의 마지막 하이라이트와 맞닿아 있습니다. 적분으로 구한 값이, 이미 알고 있던 도형 넓이 공식과 정확히 같아지면서 감각이 굳어집니다.",
        graph: { kind: "triangleExample" }
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
  processBoxEl.innerHTML = details.process.map((step) => `<li class="fade">${step}</li>`).join("");
  explanationBoxEl.textContent = details.explanation;
}

function drawAxes() {
  for (let gx = 0; gx <= 3; gx += 0.5) {
    svg.appendChild(createSvg("line", {
      x1: mapX(gx),
      y1: mapY(yMin),
      x2: mapX(gx),
      y2: mapY(yMax),
      class: "grid-line"
    }));
  }
  for (let gy = 0; gy <= 10; gy += 1) {
    svg.appendChild(createSvg("line", {
      x1: mapX(xMin),
      y1: mapY(gy),
      x2: mapX(xMax),
      y2: mapY(gy),
      class: "grid-line"
    }));
  }
  svg.appendChild(createSvg("line", {
    x1: mapX(xMin),
    y1: mapY(0),
    x2: mapX(xMax),
    y2: mapY(0),
    class: "axis"
  }));
  svg.appendChild(createSvg("line", {
    x1: mapX(0),
    y1: mapY(yMin),
    x2: mapX(0),
    y2: mapY(yMax),
    class: "axis"
  }));
}

function label(text, x, y, className = "label") {
  const node = createSvg("text", { x, y, class: className });
  node.textContent = text;
  svg.appendChild(node);
}

function drawBallOnTangent(ball, options = {}) {
  const compact = options.compact ?? true;
  const radius = compact ? ball.radius * 0.78 : ball.radius;
  const tangent = compact ? tangentSegmentAt(ball.x, 0.34) : ball.tangent;
  const cx = mapX(tangent.xMid);
  const cy = mapY(tangent.yMid);
  renderedBallHit = { cx, cy, radius };

  svg.appendChild(createSvg("path", {
    d: linePath(tangent.x1, tangent.y1, tangent.x2, tangent.y2),
    class: compact ? "secant" : "tangent"
  }));

  svg.appendChild(createSvg("ellipse", {
    cx,
    cy: cy + radius + 6,
    rx: radius * 0.95,
    ry: compact ? 4.5 : 7,
    class: "ball-shadow"
  }));

  const group = createSvg("g", { transform: `translate(${cx} ${cy}) rotate(${ball.x * 28})` });
  group.appendChild(createSvg("circle", { cx: 0, cy: 0, r: radius + (compact ? 4 : 8), class: "ball-halo" }));
  group.appendChild(createSvg("circle", { cx: 0, cy: 0, r: radius, class: "rolling-ball" }));
  group.appendChild(createSvg("path", {
    d: `M ${-radius * 0.68} ${-radius * 0.2} Q 0 ${-radius * 0.88} ${radius * 0.68} ${-radius * 0.2}`,
    class: "ball-stripe"
  }));
  group.appendChild(createSvg("path", {
    d: `M ${-radius * 0.7} ${radius * 0.18} Q 0 ${radius * 0.84} ${radius * 0.7} ${radius * 0.18}`,
    class: "ball-stripe"
  }));
  group.appendChild(createSvg("circle", {
    cx: -radius * 0.28,
    cy: -radius * 0.34,
    r: Math.max(2.5, radius * 0.18),
    class: "ball-highlight"
  }));
  svg.appendChild(group);
}

function drawDerivativeScene(x, secant) {
  svg.appendChild(createSvg("path", { d: functionPath(f, 0, 3.2), class: "curve" }));
  const tangent = tangentLineAt(x);
  const slope = (secant.y2 - secant.y1) / secant.h;
  svg.appendChild(createSvg("path", {
    d: linePath(0, tangent.yLeft, 3.2, tangent.yRight),
    class: "tangent"
  }));
  svg.appendChild(createSvg("path", {
    d: linePath(secant.x1, secant.y1, secant.x2, secant.y2),
    class: "secant"
  }));
  svg.appendChild(createSvg("circle", { cx: mapX(secant.x1), cy: mapY(secant.y1), r: 8, class: "point-main" }));
  svg.appendChild(createSvg("circle", { cx: mapX(secant.x2), cy: mapY(secant.y2), r: 7, class: "point-helper" }));
  svg.appendChild(createSvg("line", {
    x1: mapX(secant.x2),
    y1: mapY(0),
    x2: mapX(secant.x2),
    y2: mapY(secant.y2),
    class: "helper-line"
  }));
  label("f(x)=x^2", mapX(2.45), mapY(f(2.45)) - 14);
  label("접선", mapX(2.5), mapY(tangent.yRight) - 12, "label-soft");
  label("할선", mapX(secant.x2) + 8, mapY(secant.y2) - 8, "label-soft");
  label(`A(${fmt(secant.x1)}, ${fmt(secant.y1)})`, mapX(secant.x1) + 10, mapY(secant.y1) - 12, "label-soft");
  label(`B(${fmt(secant.x2)}, ${fmt(secant.y2)})`, mapX(secant.x2) + 10, mapY(secant.y2) + 22, "label-soft");
  label(`Δx=${fmt(secant.h)}`, (mapX(secant.x1) + mapX(secant.x2)) / 2 - 18, mapY(0) + 28, "label-soft");
  label(`Δy=${fmt(secant.y2 - secant.y1)}`, mapX(secant.x2) + 10, (mapY(secant.y1) + mapY(secant.y2)) / 2, "label-soft");
  label(`할선 기울기=${fmt(slope)}`, mapX(0.32), mapY(8.8), "label-soft");
  label(`접선 기울기=${fmt(df(x))}`, mapX(0.32), mapY(8.15), "label-soft");
}

function drawAntiderivativeFamily(x) {
  const shifts = [-2, 0, constantC];
  shifts.forEach((shift) => {
    svg.appendChild(createSvg("path", {
      d: functionPath((value) => f(value) + shift, 0, 3.1),
      class: shift === 0 ? "curve" : "family-curve"
    }));
  });
  svg.appendChild(createSvg("circle", {
    cx: mapX(x),
    cy: mapY(f(x) + constantC),
    r: 8,
    class: "point-accent"
  }));
  label("x^2", mapX(2.7), mapY(f(2.7)) - 10, "label-soft");
  label("x^2 + C", mapX(2.2), mapY(f(2.2) + constantC) - 12);
  label("미분하면 모두 2x", mapX(1.5), mapY(9.4), "label-soft");
  label(`x=${fmt(x)}`, mapX(x) + 10, mapY(0) + 28, "label-soft");
  label(`x^2=${fmt(f(x))}`, mapX(x) + 10, mapY(f(x)) - 12, "label-soft");
  label(`x^2+C=${fmt(f(x) + constantC)}`, mapX(x) + 10, mapY(f(x) + constantC) - 12, "label-soft");
  label(`C=${fmt(constantC)}`, mapX(0.4), mapY(9.9), "label-soft");
}

function drawAreaScene(x) {
  svg.appendChild(createSvg("path", { d: functionPath(f, 0, 3.1), class: "curve" }));
  svg.appendChild(createSvg("path", { d: areaPath(f, 0, x), class: "area-fill" }));
  svg.appendChild(createSvg("circle", { cx: mapX(x), cy: mapY(f(x)), r: 8, class: "point-main" }));
  svg.appendChild(createSvg("line", {
    x1: mapX(x),
    y1: mapY(0),
    x2: mapX(x),
    y2: mapY(f(x)),
    class: "helper-line"
  }));
  label(`x=${fmt(x)}`, mapX(x) - 16, mapY(0) + 28, "label-soft");
  label(`f(x)=${fmt(f(x))}`, mapX(x) + 10, mapY(f(x)) - 12, "label-soft");
  label(`넓이=${fmt(F(x))}`, mapX(Math.max(0.35, x * 0.45)), mapY(Math.max(0.9, f(x) * 0.28)));
  label(`[t^3/3]_0^x`, mapX(0.25), mapY(9.3), "label-soft");
  label(`${fmt(x)}^3/3 = ${fmt(F(x))}`, mapX(0.25), mapY(8.65), "label-soft");
}

function drawFundamentalScene(x, nextX) {
  const deltaX = nextX - x;
  const deltaArea = F(nextX) - F(x);
  svg.appendChild(createSvg("path", { d: functionPath(f, 0, 3.1), class: "curve" }));
  svg.appendChild(createSvg("path", { d: areaPath(f, 0, x), class: "area-fill" }));
  svg.appendChild(createSvg("rect", {
    x: mapX(x),
    y: mapY(f(x)),
    width: mapX(nextX) - mapX(x),
    height: mapY(0) - mapY(f(x)),
    class: "rect-fill"
  }));
  svg.appendChild(createSvg("circle", { cx: mapX(x), cy: mapY(f(x)), r: 8, class: "point-main" }));
  svg.appendChild(createSvg("circle", { cx: mapX(nextX), cy: mapY(f(nextX)), r: 7, class: "point-helper" }));
  svg.appendChild(createSvg("line", {
    x1: mapX(x),
    y1: mapY(f(x)),
    x2: mapX(nextX),
    y2: mapY(f(x)),
    class: "helper-line"
  }));
  label("S(x)", mapX(x * 0.42), mapY(Math.max(0.8, f(x) * 0.26)));
  label("추가되는 얇은 넓이", mapX(x) + 8, mapY(f(x)) - 16, "label-soft");
  label("높이 f(x)", mapX(x) + 14, mapY(f(x) / 2), "label-soft");
  label(`f(x)=${fmt(f(x))}`, mapX(x) + 14, mapY(f(x) / 2) + 18, "label-soft");
  label(`Δx=${fmt(deltaX)}`, (mapX(x) + mapX(nextX)) / 2 - 16, mapY(0) + 28, "label-soft");
  label(`ΔS=${fmt(deltaArea)}`, mapX(x) + 12, mapY(f(x)) - 36, "label-soft");
  label(`ΔS/Δx=${fmt(deltaArea / deltaX)}`, mapX(0.25), mapY(9.2), "label-soft");
}

function drawTriangleExample() {
  svg.appendChild(createSvg("path", { d: functionPath(g, 0, 3.1), class: "curve" }));
  svg.appendChild(createSvg("path", { d: areaPath(g, 0, 3), class: "area-fill" }));
  svg.appendChild(createSvg("line", {
    x1: mapX(3),
    y1: mapY(0),
    x2: mapX(3),
    y2: mapY(6),
    class: "helper-line"
  }));
  svg.appendChild(createSvg("circle", { cx: mapX(3), cy: mapY(6), r: 8, class: "point-main" }));
  label("y=2x", mapX(2.2), mapY(g(2.2)) - 14);
  label("밑변 3", mapX(1.35), mapY(0) + 28, "label-soft");
  label("높이 6", mapX(3) + 10, mapY(3), "label-soft");
  label("정적분 = 9", mapX(1.05), mapY(1.35));
  label("(3, 6)", mapX(3) + 10, mapY(6) - 10, "label-soft");
  label("[x^2]_0^3 = 9", mapX(0.28), mapY(9.25), "label-soft");
  label("1/2 × 3 × 6 = 9", mapX(0.28), mapY(8.6), "label-soft");
}

function draw() {
  const sceneIndex = Number(sceneRange.value);
  const x = Number(xRange.value);
  const details = scenes[sceneIndex].getDetails(x);
  const ball = getBallFromX(x);
  const fx = f(x);
  const dfx = df(x);
  const area = F(x);
  const sample = G(3) - G(0);

  xValueEl.textContent = fmt(x);
  fxValueEl.textContent = fmt(fx);
  dfValueEl.textContent = fmt(dfx);
  areaValueEl.textContent = fmt(area);
  constantValueEl.textContent = fmt(constantC);
  sampleValueEl.textContent = fmt(sample);

  if (sceneIndex === 0) {
    const secant = details.graph.secant;
    xDetailEl.textContent = `공식: x = a, x+h = a+h\n대입: a=${fmt(secant.x1)}, a+h=${fmt(secant.x2)}`;
  } else {
    xDetailEl.textContent = `공식: 현재 선택값 = x\n대입: x=${fmt(x)}`;
  }

  fxDetailEl.textContent = `공식: f(x) = x^2\n대입: ${fmt(x)}^2 = ${fmt(fx)}`;
  dfDetailEl.textContent = `공식: f'(x) = 2x\n대입: 2 × ${fmt(x)} = ${fmt(dfx)}`;
  areaDetailEl.textContent = `공식: ∫0→x t^2dt = x^3 / 3\n대입: ${fmt(x)}^3 / 3 = ${fmt(area)}`;
  constantDetailEl.textContent = `공식: ∫2x dx = x^2 + C\n대입: C = ${fmt(constantC)}`;
  sampleDetailEl.textContent = `공식: ∫0→3 2x dx = [x^2]0→3\n대입: 3^2 - 0^2 = ${fmt(sample)}`;

  if (sceneIndex === 0) {
    const secant = details.graph.secant;
    xDetailEl.textContent = `공식: x = a, x+h = a+h\n대입: a=${fmt(secant.x1)}, a+h=${fmt(secant.x2)}\n설명: 접점 근처에 다른 점을 잡아 할선부터 만듭니다.`;
  } else {
    xDetailEl.textContent = `공식: 현재 선택값 = x\n대입: x=${fmt(x)}\n설명: 슬라이더가 현재 보고 있는 위치를 정합니다.`;
  }

  fxDetailEl.textContent = `공식: f(x) = x^2\n대입: ${fmt(x)}^2 = ${fmt(fx)}\n설명: 원래 함수가 현재 점의 높이를 만듭니다.`;
  dfDetailEl.textContent = `공식: f'(x) = 2x\n대입: 2 × ${fmt(x)} = ${fmt(dfx)}\n설명: 도함수로 현재 접선의 기울기를 바로 구합니다.`;
  areaDetailEl.textContent = `공식: ∫0→x t^2dt = x^3 / 3\n대입: ${fmt(x)}^3 / 3 = ${fmt(area)}\n설명: 0부터 x까지 함수 아래에서 누적된 넓이입니다.`;
  constantDetailEl.textContent = `공식: ∫2x dx = x^2 + C\n대입: C = ${fmt(constantC)}\n설명: 상수는 미분하면 0이므로 적분에서는 +C가 남습니다.`;
  sampleDetailEl.textContent = `공식: ∫0→3 2x dx = [x^2]0→3\n대입: 3^2 - 0^2 = ${fmt(sample)}\n설명: 정적분 값이 삼각형 넓이와 같아지는 예시입니다.`;

  if (sceneIndex === 0) {
    const secant = details.graph.secant;
    xDetailEl.textContent = `공식: x = a, x+h = a+h\n대입: a=${fmt(secant.x1)}, a+h=${fmt(secant.x2)}\n계산: ${fmt(secant.x1)} + ${fmt(secant.h)} = ${fmt(secant.x2)}\n설명: 접점 근처에 다른 점을 잡아 할선부터 만듭니다.`;
  } else {
    xDetailEl.textContent = `공식: 현재 선택값 = x\n대입: x=${fmt(x)}\n계산: 슬라이더 값 = ${fmt(x)}\n설명: 슬라이더가 현재 보고 있는 위치를 정합니다.`;
  }

  fxDetailEl.textContent = `공식: f(x) = x^2\n대입: ${fmt(x)}^2 = ${fmt(fx)}\n계산: ${fmt(x)} × ${fmt(x)} = ${fmt(fx)}\n설명: 원래 함수가 현재 점의 높이를 만듭니다.`;
  dfDetailEl.textContent = `공식: f'(x) = 2x\n대입: 2 × ${fmt(x)} = ${fmt(dfx)}\n계산: 2 × ${fmt(x)} = ${fmt(dfx)}\n설명: 도함수로 현재 접선의 기울기를 바로 구합니다.`;
  areaDetailEl.textContent = `공식: ∫0→x t^2dt = x^3 / 3\n대입: ${fmt(x)}^3 / 3 = ${fmt(area)}\n계산: ${fmt(x * x * x)} / 3 = ${fmt(area)}\n설명: 0부터 x까지 함수 아래에서 누적된 넓이입니다.`;
  constantDetailEl.textContent = `공식: ∫2x dx = x^2 + C\n대입: C = ${fmt(constantC)}\n계산: x^2 + ${fmt(constantC)}\n설명: 상수는 미분하면 0이므로 적분에서는 +C가 남습니다.`;
  sampleDetailEl.textContent = `공식: ∫0→3 2x dx = [x^2]0→3\n대입: 3^2 - 0^2 = ${fmt(sample)}\n계산: 9.00 - 0.00 = ${fmt(sample)}\n설명: 정적분 값이 삼각형 넓이와 같아지는 예시입니다.`;

  svg.innerHTML = "";
  renderedBallHit = null;
  drawAxes();

  switch (details.graph.kind) {
    case "derivative":
      drawDerivativeScene(x, details.graph.secant);
      break;
    case "antiderivativeFamily":
      drawAntiderivativeFamily(x);
      break;
    case "area":
      drawAreaScene(details.graph.x);
      break;
    case "fundamental":
      drawFundamentalScene(details.graph.x, details.graph.nextX);
      break;
    case "triangleExample":
      drawTriangleExample();
      break;
    default:
      break;
  }

  if (sceneIndex < 4) {
    drawBallOnTangent(ball, { compact: true });
  }
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
