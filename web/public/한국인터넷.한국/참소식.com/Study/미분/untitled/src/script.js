const svg = document.getElementById("graph");
const sceneRange = document.getElementById("sceneRange");
const xRange = document.getElementById("xRange");
const xValueEl = document.getElementById("xValue");
const fxValueEl = document.getElementById("fxValue");
const dfValueEl = document.getElementById("dfValue");
const areaValueEl = document.getElementById("areaValue");
const sceneTitleEl = document.getElementById("sceneTitle");
const sceneStepEl = document.getElementById("sceneStep");
const sceneDescriptionEl = document.getElementById("sceneDescription");
const lessonPointsEl = document.getElementById("lessonPoints");
const formulaBoxEl = document.getElementById("formulaBox");
const sceneButtonsEl = document.getElementById("sceneButtons");

const width = 900;
const height = 560;
const margin = { top: 30, right: 32, bottom: 56, left: 56 };
const xMin = -3;
const xMax = 3;
const yMin = -2;
const yMax = 9;

const scenes = [
  {
    title: "Slope Of A Line",
    description: "Start with two points. The slope is change in y divided by change in x.",
    points: [
      "A line's slope is fixed by two points.",
      "Slope = delta y / delta x.",
      "Upward means positive slope, downward means negative slope."
    ],
    formula: "slope = (y2 - y1) / (x2 - x1)\nExample: points (1,1), (2,4) => slope = 3"
  },
  {
    title: "Secant To Tangent",
    description: "On a curve, make a secant with a nearby point and slide that point closer to the target point.",
    points: [
      "A nearby point creates a secant line.",
      "As the point gets closer, the secant slope approaches the tangent slope.",
      "That destination is the limit."
    ],
    formula: "f'(a) = lim (x -> a) [f(x) - f(a)] / [x - a]"
  },
  {
    title: "Derivative As Slope Function",
    description: "For f(x)=x^2, every x has its own tangent slope. Collecting them gives f'(x)=2x.",
    points: [
      "At x=1, slope is 2.",
      "At x=2, slope is 4.",
      "The derivative matches each x with its tangent slope."
    ],
    formula: "f(x) = x^2\nf'(x) = 2x"
  },
  {
    title: "Indefinite Integral",
    description: "Integration reverses differentiation, but the constant term is unknown, so we leave +C.",
    points: [
      "Integrating 2x gives x^2.",
      "x^2, x^2+3, x^2-10 all differentiate to 2x.",
      "That is why the answer includes +C."
    ],
    formula: "Integral of 2x dx = x^2 + C\nIntegral of (2x - 6) dx = x^2 - 6x + C"
  },
  {
    title: "Definite Integral As Area",
    description: "Add many thin vertical slices under the curve and you get area.",
    points: [
      "Function height becomes thin slices.",
      "Adding those slices produces area.",
      "This is the key bridge between differentiation and integration."
    ],
    formula: "Integral from a to b of f(x) dx = F(b) - F(a)\nExample: Integral from 0 to x of t^2 dt = x^3 / 3"
  }
];

function f(x) {
  return x * x;
}

function df(x) {
  return 2 * x;
}

function integralFromZero(x) {
  return (x * x * x) / 3;
}

function mapX(x) {
  return margin.left + ((x - xMin) / (xMax - xMin)) * (width - margin.left - margin.right);
}

function mapY(y) {
  return height - margin.bottom - ((y - yMin) / (yMax - yMin)) * (height - margin.top - margin.bottom);
}

function fmt(value) {
  return Number(value).toFixed(2);
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

function secantLineAt(x0, dx) {
  const x2 = Math.max(xMin, Math.min(xMax, x0 + dx));
  return { x1: x0, y1: f(x0), x2, y2: f(x2) };
}

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
  sceneTitleEl.textContent = scene.title;
  sceneStepEl.textContent = `${sceneIndex + 1} / ${scenes.length}`;
  sceneDescriptionEl.textContent = scene.description;
  lessonPointsEl.innerHTML = scene.points.map((point) => `<li class="fade">${point}</li>`).join("");

  let formula = scene.formula;
  if (sceneIndex === 1) {
    formula += `\n현재 x = ${fmt(x)}\n현재 접선 기울기 ≈ ${fmt(df(x))}`;
  }
  if (sceneIndex === 4) {
    formula += `\n현재 넓이 = ${fmt(integralFromZero(Math.max(0, x)))}`;
  }
  formulaBoxEl.textContent = formula;
}

function draw() {
  const sceneIndex = Number(sceneRange.value);
  const x = Number(xRange.value);
  const y = f(x);
  const slope = df(x);
  const areaX = Math.max(0, x);

  xValueEl.textContent = fmt(x);
  fxValueEl.textContent = fmt(y);
  dfValueEl.textContent = fmt(slope);
  areaValueEl.textContent = fmt(integralFromZero(areaX));

  svg.innerHTML = "";

  for (let gx = Math.ceil(xMin); gx <= Math.floor(xMax); gx += 1) {
    svg.appendChild(createSvg("line", { x1: mapX(gx), y1: mapY(yMin), x2: mapX(gx), y2: mapY(yMax), class: "grid-line" }));
  }
  for (let gy = Math.ceil(yMin); gy <= Math.floor(yMax); gy += 1) {
    svg.appendChild(createSvg("line", { x1: mapX(xMin), y1: mapY(gy), x2: mapX(xMax), y2: mapY(gy), class: "grid-line" }));
  }

  svg.appendChild(createSvg("line", { x1: mapX(xMin), y1: mapY(0), x2: mapX(xMax), y2: mapY(0), class: "axis" }));
  svg.appendChild(createSvg("line", { x1: mapX(0), y1: mapY(yMin), x2: mapX(0), y2: mapY(yMax), class: "axis" }));
  svg.appendChild(createSvg("path", { d: functionPath(), class: "curve" }));

  if (sceneIndex === 0) {
    const x1 = 1;
    const x2 = 2;
    const y1 = f(x1);
    const y2 = f(x2);
    svg.appendChild(createSvg("path", { d: linePath(x1, y1, x2, y2), class: "tangent" }));
    svg.appendChild(createSvg("line", { x1: mapX(x1), y1: mapY(y1), x2: mapX(x2), y2: mapY(y1), class: "helper-line" }));
    svg.appendChild(createSvg("line", { x1: mapX(x2), y1: mapY(y1), x2: mapX(x2), y2: mapY(y2), class: "helper-line" }));
    svg.appendChild(createSvg("circle", { cx: mapX(x1), cy: mapY(y1), r: 8, class: "point-main" }));
    svg.appendChild(createSvg("circle", { cx: mapX(x2), cy: mapY(y2), r: 8, class: "point-helper" }));
    svg.appendChild(createSvg("text", { x: mapX(1.5), y: mapY(y1) + 26, class: "label label-soft" })).textContent = "Δx = 1";
    svg.appendChild(createSvg("text", { x: mapX(x2) + 12, y: mapY(2.5), class: "label label-soft" })).textContent = "Δy = 3";
  }

  if (sceneIndex === 1) {
    const secant = secantLineAt(x, Math.max(0.18, Math.abs(x) * 0.25));
    const tangent = tangentLineAt(x);
    svg.appendChild(createSvg("path", { d: linePath(secant.x1, secant.y1, secant.x2, secant.y2), class: "secant" }));
    svg.appendChild(createSvg("path", { d: linePath(xMin, tangent.yLeft, xMax, tangent.yRight), class: "tangent" }));
    svg.appendChild(createSvg("circle", { cx: mapX(secant.x1), cy: mapY(secant.y1), r: 8, class: "point-main" }));
    svg.appendChild(createSvg("circle", { cx: mapX(secant.x2), cy: mapY(secant.y2), r: 7, class: "point-helper" }));
  }

  if (sceneIndex === 2) {
    const tangent = tangentLineAt(x);
    svg.appendChild(createSvg("path", { d: linePath(xMin, tangent.yLeft, xMax, tangent.yRight), class: "tangent" }));
    svg.appendChild(createSvg("circle", { cx: mapX(x), cy: mapY(y), r: 8, class: "point-main" }));
    svg.appendChild(createSvg("text", { x: mapX(x) + 12, y: mapY(y) - 14, class: "label" })).textContent = `기울기 = ${fmt(slope)}`;
  }

  if (sceneIndex === 3) {
    const tangent = tangentLineAt(x);
    svg.appendChild(createSvg("path", { d: linePath(xMin, tangent.yLeft, xMax, tangent.yRight), class: "tangent" }));
    svg.appendChild(createSvg("circle", { cx: mapX(x), cy: mapY(y), r: 8, class: "point-main" }));

    for (const c of [-2, 0, 2]) {
      const d = `M ${mapX(xMin)} ${mapY(f(xMin) + c)} ` +
        Array.from({ length: 200 }, (_, i) => {
          const px = xMin + (i + 1) * ((xMax - xMin) / 200);
          return `L ${mapX(px)} ${mapY(f(px) + c)} `;
        }).join("");
      svg.appendChild(createSvg("path", { d, class: "secant", opacity: c === 0 ? "0.15" : "0.45" }));
    }
  }

  if (sceneIndex === 4) {
    svg.appendChild(createSvg("path", { d: areaPath(0, areaX), class: "area-fill" }));
    svg.appendChild(createSvg("circle", { cx: mapX(areaX), cy: mapY(f(areaX)), r: 8, class: "point-main" }));
    svg.appendChild(createSvg("line", { x1: mapX(areaX), y1: mapY(0), x2: mapX(areaX), y2: mapY(f(areaX)), class: "helper-line" }));
    svg.appendChild(createSvg("text", { x: mapX(0.25), y: mapY(1.5), class: "label label-soft" })).textContent = "세로 길이를 촘촘히 더하면 넓이";
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

update();
