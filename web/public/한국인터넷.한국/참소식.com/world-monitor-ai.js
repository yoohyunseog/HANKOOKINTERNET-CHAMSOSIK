(function () {
  const DATA_URL = "world-monitor-ai.json";
  const REFRESH_MS = 60000;

  function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value || "";
    return div.innerHTML;
  }

  function formatTime(value) {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString("ko-KR");
  }

  function formatShortTime(value) {
    if (!value) return "-";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
  }

  function renderList(items, emptyMessage = "아직 분석 데이터가 없습니다.") {
    if (!Array.isArray(items) || !items.length) {
      return `<p class="world-monitor-ai-empty">${escapeHtml(emptyMessage)}</p>`;
    }

    return `<ul class="world-monitor-ai-list">${items
      .map((item) => `<li>${escapeHtml(item)}</li>`)
      .join("")}</ul>`;
  }

  function normalizeFactorLists(weighted) {
    const upper = Array.isArray(weighted?.upper_factors) ? [...weighted.upper_factors] : [];
    const lower = Array.isArray(weighted?.lower_factors) ? [...weighted.lower_factors] : [];
    const basis = Array.isArray(weighted?.basis) ? weighted.basis : [];

    for (const item of basis) {
      const text = String(item || "").trim();
      if (!text) continue;
      if (text.includes("-")) {
        lower.push(text);
      } else {
        upper.push(text);
      }
    }

    return {
      upper: upper.filter(Boolean),
      lower: lower.filter(Boolean),
    };
  }

  function buildSearchUrl(payload) {
    const factors = normalizeFactorLists(payload.weighted_signal || {});
    const queryParts = [
      payload.headline,
      payload.summary,
      ...(Array.isArray(payload.signals) ? payload.signals : []),
      ...(Array.isArray(payload.risks) ? payload.risks : []),
      ...(Array.isArray(payload.market_impact) ? payload.market_impact : []),
      ...factors.upper,
      ...factors.lower,
      payload.outlook,
    ].filter(Boolean);

    const query = queryParts.join(" ").replace(/\s+/g, " ").trim().slice(0, 500);
    return `https://www.google.com/search?q=${encodeURIComponent(query || "이클립스 센츄어리 D.P")}`;
  }

  function renderWeightedSignal(weighted) {
    if (!weighted || typeof weighted !== "object") {
      return "";
    }

    const factors = normalizeFactorLists(weighted);

    return `
      <div class="world-monitor-ai-card">
        <h4>가중치 상한·하한</h4>
        <p><strong>등급:</strong> ${escapeHtml(weighted.grade || "-")}</p>
        <p><strong>종합 가중치:</strong> ${escapeHtml(String(weighted.score ?? "-"))}</p>
        <p><strong>상한치:</strong> ${escapeHtml(String(weighted.upper_bound ?? "-"))}</p>
        <p><strong>하한치:</strong> ${escapeHtml(String(weighted.lower_bound ?? "-"))}</p>
        <p><strong>상한치 요인</strong></p>
        ${renderList(factors.upper, "상한치 요인이 아직 없습니다.")}
        <p><strong>하한치 요인</strong></p>
        ${renderList(factors.lower, "하한치 요인이 아직 없습니다.")}
      </div>
    `;
  }

  function buildCalculusSeries(items) {
    const points = (Array.isArray(items) ? items : [])
      .map((item, index) => {
        const time = new Date(item?.pubDate || item?.published_at || item?.date || "");
        if (Number.isNaN(time.getTime())) return null;
        return {
          index,
          time,
          title: item?.title || `item-${index + 1}`,
        };
      })
      .filter(Boolean)
      .sort((a, b) => a.time - b.time)
      .map((point, index) => ({
        ...point,
        cumulative: index + 1,
      }));

    const derivative = points.map((point, index) => {
      if (index === 0) {
        return {
          ...point,
          deltaMinutes: 0,
          ratePerHour: 0,
        };
      }

      const previous = points[index - 1];
      const deltaMinutes = Math.max((point.time - previous.time) / 60000, 0.01);
      return {
        ...point,
        deltaMinutes,
        ratePerHour: 60 / deltaMinutes,
      };
    });

    return { points, derivative };
  }

  function buildPolyline(points, mapX, mapY, valueKey) {
    return points.map((point) => `${mapX(point.time)} ${mapY(point[valueKey])}`).join(" ");
  }

  function renderCalculusGraph(payload) {
    const { points, derivative } = buildCalculusSeries(payload.items);

    if (points.length < 2) {
      return `
        <div class="world-monitor-ai-graph-card">
          <h4>미분·적분 그래프</h4>
          <p class="world-monitor-ai-empty">pubDate가 2개 이상 있어야 변화율과 누적 그래프를 그릴 수 있습니다.</p>
        </div>
      `;
    }

    const width = 860;
    const height = 330;
    const paddingX = 56;
    const topChartTop = 26;
    const topChartBottom = 142;
    const bottomChartTop = 198;
    const bottomChartBottom = 304;
    const minTime = points[0].time.getTime();
    const maxTime = points[points.length - 1].time.getTime();
    const maxCumulative = Math.max(...points.map((point) => point.cumulative), 1);
    const maxRate = Math.max(...derivative.map((point) => point.ratePerHour), 1);
    const safeTimeSpan = Math.max(maxTime - minTime, 1);

    const mapX = (time) => {
      const value = time instanceof Date ? time.getTime() : time;
      return paddingX + ((value - minTime) / safeTimeSpan) * (width - paddingX * 2);
    };

    const mapTopY = (value) => topChartBottom - (value / maxCumulative) * (topChartBottom - topChartTop);
    const mapBottomY = (value) => bottomChartBottom - (value / maxRate) * (bottomChartBottom - bottomChartTop);

    const cumulativePolyline = buildPolyline(points, mapX, mapTopY, "cumulative");
    const derivativePolyline = buildPolyline(derivative, mapX, mapBottomY, "ratePerHour");

    const guidePoints = [points[0], points[Math.floor((points.length - 1) / 2)], points[points.length - 1]];
    const guides = guidePoints
      .map((point) => {
        const x = mapX(point.time);
        return `
          <line x1="${x}" y1="${topChartTop}" x2="${x}" y2="${bottomChartBottom}" class="world-monitor-ai-guide" />
          <text x="${x}" y="${height - 8}" text-anchor="middle" class="world-monitor-ai-axis-label">${formatShortTime(point.time)}</text>
        `;
      })
      .join("");

    const cumulativeDots = points
      .map((point) => {
        const x = mapX(point.time);
        const y = mapTopY(point.cumulative);
        return `
          <circle cx="${x}" cy="${y}" r="4.5" class="world-monitor-ai-dot world-monitor-ai-dot-cumulative" />
          <text x="${x}" y="${y - 10}" text-anchor="middle" class="world-monitor-ai-point-label">${point.cumulative}</text>
        `;
      })
      .join("");

    const derivativeDots = derivative
      .map((point, index) => {
        const x = mapX(point.time);
        const y = mapBottomY(point.ratePerHour);
        const label = index === 0 ? "0" : point.ratePerHour.toFixed(1);
        return `
          <circle cx="${x}" cy="${y}" r="4.5" class="world-monitor-ai-dot world-monitor-ai-dot-derivative" />
          <text x="${x}" y="${y - 10}" text-anchor="middle" class="world-monitor-ai-point-label">${label}</text>
        `;
      })
      .join("");

    return `
      <div class="world-monitor-ai-graph-card">
        <div class="world-monitor-ai-graph-head">
          <div>
            <h4>미분·적분 그래프</h4>
            <p class="world-monitor-ai-graph-desc">
              기사 발행 시각을 시간축으로 두고, 누적 기사 수는 적분처럼, 발행 속도는 미분처럼 읽도록 정리했습니다.
            </p>
          </div>
          <div class="world-monitor-ai-graph-meta">
            <span>누적 기사 수: ${points.length}</span>
            <span>현재 종합 점수: ${escapeHtml(String(payload?.weighted_signal?.score ?? "-"))}</span>
          </div>
        </div>
        <svg viewBox="0 0 ${width} ${height}" class="world-monitor-ai-graph" aria-label="세계 모니터 AI 미분 적분 그래프">
          <rect x="0" y="0" width="${width}" height="${height}" rx="24" class="world-monitor-ai-graph-bg" />
          <text x="${paddingX}" y="18" class="world-monitor-ai-chart-title">적분 해석: 시간에 따라 쌓인 누적 기사 수</text>
          <text x="${paddingX}" y="190" class="world-monitor-ai-chart-title">미분 해석: 직전 기사 대비 발행 속도(건/시간)</text>

          <line x1="${paddingX}" y1="${topChartBottom}" x2="${width - paddingX}" y2="${topChartBottom}" class="world-monitor-ai-axis-line" />
          <line x1="${paddingX}" y1="${bottomChartBottom}" x2="${width - paddingX}" y2="${bottomChartBottom}" class="world-monitor-ai-axis-line" />
          ${guides}

          <polyline points="${cumulativePolyline}" class="world-monitor-ai-line world-monitor-ai-line-cumulative" />
          ${cumulativeDots}

          <polyline points="${derivativePolyline}" class="world-monitor-ai-line world-monitor-ai-line-derivative" />
          ${derivativeDots}

          <text x="${width - paddingX}" y="${topChartTop + 6}" text-anchor="end" class="world-monitor-ai-axis-label">최대 ${maxCumulative}건</text>
          <text x="${width - paddingX}" y="${bottomChartTop + 6}" text-anchor="end" class="world-monitor-ai-axis-label">최대 ${maxRate.toFixed(1)}건/시간</text>
        </svg>
      </div>
    `;
  }

  function renderPayload(payload) {
    const target = document.getElementById("world-monitor-ai-content");
    const updatedEl = document.getElementById("world-monitor-ai-updated");
    const modelEl = document.getElementById("world-monitor-ai-model");
    if (!target || !updatedEl || !modelEl) return;

    updatedEl.textContent = formatTime(payload.updated_at);
    modelEl.textContent = payload.model || "-";

    const weighted = payload.weighted_signal || {};
    const factors = normalizeFactorLists(weighted);
    const score = Number.isFinite(Number(weighted.score)) ? Number(weighted.score) : "-";
    const upperBound = Number.isFinite(Number(weighted.upper_bound)) ? Number(weighted.upper_bound) : "-";
    const lowerBound = Number.isFinite(Number(weighted.lower_bound)) ? Number(weighted.lower_bound) : "-";
    const grade = weighted.grade || "-";
    const signals = Array.isArray(payload.signals) && payload.signals.length
      ? payload.signals
      : ["아직 핵심 신호 데이터가 없습니다."];
    const risks = Array.isArray(payload.risks) && payload.risks.length
      ? payload.risks
      : ["아직 리스크 데이터가 없습니다."];
    const marketImpact = Array.isArray(payload.market_impact) && payload.market_impact.length
      ? payload.market_impact
      : ["아직 시장 영향 데이터가 없습니다."];
    const splitFactor = (item) => {
      const text = String(item || "").trim();
      const match = text.match(/^(.*?)([+-]\s*\d+(?:\.\d+)?)\s*$/);
      if (!match) return [text, ""];
      return [match[1].trim(), match[2].replace(/\s+/g, "")];
    };
    const upperFactors = factors.upper.length
      ? factors.upper.map(splitFactor)
      : [["상한치 요인이 아직 없습니다.", ""]];
    const lowerFactors = factors.lower.length
      ? factors.lower.map(splitFactor)
      : [["하한치 요인이 아직 없습니다.", ""]];
    const googleSearchText = [
      "이클립스 센츄어리 D.P",
      "핵심 신호",
      ...signals,
      "리스크",
      ...risks,
      "시장 영향",
      ...marketImpact,
      "가중치 상한 하한",
      `등급 ${grade}`,
      `종합 가중치 ${score}`,
      `상한치 ${upperBound}`,
      `하한치 ${lowerBound}`,
      "상한치 요인",
      ...upperFactors.map(([label, value]) => `${label} ${value}`),
      "하한치 요인",
      ...lowerFactors.map(([label, value]) => `${label} ${value}`),
    ].join(" ");
    const googleSearchUrl = `https://www.google.com/search?q=${encodeURIComponent(googleSearchText)}`;
    const cardSearches = [
      ["핵심 신호", ["이클립스 센츄어리 D.P", "핵심 신호", ...signals].join(" ")],
      ["리스크", ["이클립스 센츄어리 D.P", "리스크", ...risks].join(" ")],
      ["시장 영향", ["이클립스 센츄어리 D.P", "시장 영향", ...marketImpact].join(" ")],
      [
        "가중치",
        [
          "이클립스 센츄어리 D.P",
          "가중치 상한 하한",
          `등급 ${grade}`,
          `종합 가중치 ${score}`,
          `상한치 ${upperBound}`,
          `하한치 ${lowerBound}`,
          ...upperFactors.map(([label, value]) => `${label} ${value}`),
          ...lowerFactors.map(([label, value]) => `${label} ${value}`),
        ].join(" "),
      ],
    ];
    const renderPlainList = (items, iconClass) => `
      <ul class="ecdp-list ${iconClass}">
        ${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
      </ul>
    `;
    const renderFactorList = (items, type) => `
      <ul class="ecdp-factor-list ${type}">
        ${items.map(([label, value]) => `<li><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></li>`).join("")}
      </ul>
    `;

    target.innerHTML = `
      <div class="ecdp-layout" aria-label="이클립스 센츄어리 D.P 분석 카드">
        <article class="ecdp-card ecdp-card-signal">
          <div class="ecdp-icon"><i class="bi bi-graph-up-arrow"></i></div>
          <div class="ecdp-content">
            <h3>핵심 신호</h3>
            <span class="ecdp-rule"></span>
            ${renderPlainList(signals, "is-blue")}
          </div>
        </article>
        <article class="ecdp-card ecdp-card-risk">
          <div class="ecdp-icon"><i class="bi bi-shield-exclamation"></i></div>
          <div class="ecdp-content">
            <h3>리스크</h3>
            <span class="ecdp-rule"></span>
            ${renderPlainList(risks, "is-pink")}
          </div>
        </article>
        <article class="ecdp-card ecdp-card-market">
          <div class="ecdp-icon"><i class="bi bi-bar-chart-line"></i></div>
          <div class="ecdp-content">
            <h3>시장 영향</h3>
            <span class="ecdp-rule"></span>
            ${renderPlainList(marketImpact, "is-teal")}
          </div>
        </article>
        <article class="ecdp-card ecdp-card-search">
          <div class="ecdp-icon"><i class="bi bi-google"></i></div>
          <div class="ecdp-content">
            <h3>전체 브리핑 텍스트 검색</h3>
            <span class="ecdp-rule"></span>
            <p class="ecdp-search-desc">핵심 신호, 리스크, 시장 영향, 가중치 요인을 하나의 검색어로 묶었습니다.</p>
            <div class="ecdp-google-actions">
              <a class="ecdp-google-main" href="${googleSearchUrl}" target="_blank" rel="noopener noreferrer">
                <i class="bi bi-google"></i>
                전체 검색
              </a>
              ${cardSearches.map(([label, query]) => `
                <a href="https://www.google.com/search?q=${encodeURIComponent(query)}" target="_blank" rel="noopener noreferrer">
                  ${escapeHtml(label)}
                </a>
              `).join("")}
            </div>
          </div>
        </article>
        <article class="ecdp-card ecdp-card-weight">
          <div class="ecdp-icon"><i class="bi bi-scales"></i></div>
          <div class="ecdp-content">
            <h3>가중치 상한·하한</h3>
            <span class="ecdp-rule"></span>
            <div class="ecdp-score-grid">
              <div><span>등급</span><strong>${escapeHtml(grade)}</strong></div>
              <div><span>종합 가중치</span><strong>${escapeHtml(String(score))}</strong></div>
              <div><span>상한치</span><strong>${escapeHtml(String(upperBound))}</strong></div>
              <div><span>하한치</span><strong>${escapeHtml(String(lowerBound))}</strong></div>
            </div>
            <div class="ecdp-scale">
              <div class="ecdp-scale-track"><span></span><span></span><span></span></div>
              <div class="ecdp-scale-labels"><span>0</span><span>${escapeHtml(String(upperBound))}</span><span>${escapeHtml(String(score))}</span><span>100</span></div>
            </div>
            <div class="ecdp-factor-grid">
              <div class="ecdp-factor-box">
                <h4>상한치 요인 <span>↑</span></h4>
                ${renderFactorList(upperFactors, "upper")}
              </div>
              <div class="ecdp-factor-box">
                <h4>하한치 요인 <span>↓</span></h4>
                ${renderFactorList(lowerFactors, "lower")}
              </div>
            </div>
          </div>
        </article>
      </div>
    `;
    return;

    target.innerHTML = `
      <div class="world-monitor-ai-panel">
        <h3 class="world-monitor-ai-headline">${escapeHtml(payload.headline || "이클립스 센츄어리 D.P 브리핑")}</h3>
        <p class="world-monitor-ai-summary">${escapeHtml(payload.summary || "")}</p>
        ${renderCalculusGraph(payload)}
        <div class="world-monitor-ai-grid">
          <div class="world-monitor-ai-card">
            <h4>핵심 신호</h4>
            ${renderList(payload.signals)}
          </div>
          <div class="world-monitor-ai-card">
            <h4>리스크</h4>
            ${renderList(payload.risks)}
          </div>
          <div class="world-monitor-ai-card">
            <h4>시장 영향</h4>
            ${renderList(payload.market_impact)}
          </div>
          ${renderWeightedSignal(payload.weighted_signal)}
        </div>
        <div class="world-monitor-ai-footer">
          <p class="world-monitor-ai-outlook"><strong>전망:</strong> ${escapeHtml(payload.outlook || "-")}</p>
          <p class="world-monitor-ai-quality"><strong>품질 메모:</strong> ${escapeHtml(payload.quality_note || "-")}</p>
          <p class="world-monitor-ai-more">
            <a href="${buildSearchUrl(payload)}" target="_blank" rel="noopener noreferrer">자세히 찾아보기</a>
          </p>
        </div>
      </div>
    `;
  }

  function renderError(message) {
    const target = document.getElementById("world-monitor-ai-content");
    if (!target) return;

    target.innerHTML = `<div class="world-monitor-ai-panel"><p class="world-monitor-ai-error">${escapeHtml(
      message || "이클립스 센츄어리 D.P 분석을 불러오지 못했습니다."
    )}</p></div>`;
  }

  async function loadWorldMonitorAi() {
    try {
      const response = await fetch(`${DATA_URL}?t=${Date.now()}`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const payload = await response.json();
      renderPayload(payload);
    } catch (error) {
      console.warn("world-monitor-ai.json load failed", error);
      renderError("이클립스 센츄어리 D.P 분석 생성 대기 중입니다.");
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    loadWorldMonitorAi();
    setInterval(loadWorldMonitorAi, REFRESH_MS);
  });
})();
