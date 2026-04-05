(function () {
  const FEED_AI_URL = "./world-monitor-ai.json";

  function escapeHtml(value) {
    const div = document.createElement("div");
    div.textContent = value || "";
    return div.innerHTML;
  }

  function buildList(items, fallbackItems) {
    const source = Array.isArray(items) && items.length ? items : fallbackItems;
    return source
      .map((item) => `<li>${item}</li>`)
      .join("");
  }

  function renderSection(data) {
    const root = document.getElementById("event-layer-root");
    if (!root) return;

    const headline = data && data.headline ? escapeHtml(data.headline) : "핵심 메시지를 보호하는 이중 구조";
    const summary = data && data.summary
      ? escapeHtml(data.summary)
      : "참소식.com은 의미를 선언하고, 이클립스 센츄어리 D.P는 그 의미가 흐트러지지 않도록 구조를 지탱합니다.";

    const signals = buildList(
      (data && data.signals || []).map((item) => `<strong>신호:</strong> ${escapeHtml(item)}`),
      [
        "<strong>메시지:</strong> 속보보다 오래 남는 문장을 먼저 세웁니다.",
        "<strong>본질:</strong> 소음 속에서도 핵심 질문과 방향을 잃지 않습니다.",
        "<strong>좌표:</strong> 사이트 전체를 하나의 의미 체계로 묶는 기준점을 유지합니다."
      ]
    );

    const risks = buildList(
      (data && data.risks || []).map((item) => `<strong>방어:</strong> ${escapeHtml(item)}`),
      [
        "<strong>상위 스킬:</strong> 복잡한 흐름을 정리해 핵심만 남깁니다.",
        "<strong>방어막:</strong> 왜곡, 과잉 반응, 잡음을 흡수해 중심 메시지를 보호합니다.",
        "<strong>질서 유지:</strong> 흩어진 이슈를 세계관과 구조 안으로 다시 정렬합니다."
      ]
    );

    const outlook = data && data.outlook
      ? escapeHtml(data.outlook)
      : "이 구조는 클릭 유도가 아니라, 읽는 순간 세계관과 방어 체계를 함께 보여주기 위한 장치입니다.";

    const qualityNote = data && data.quality_note
      ? escapeHtml(data.quality_note)
      : "월드 모니터 AI 브리핑이 아직 준비되지 않았습니다.";

    root.innerHTML = `
      <div class="event-layer-header">
        <div class="event-layer-eyebrow">Eclipse Centauri D.P</div>
        <h2 class="event-layer-title" id="event-layer-title">참소식.com × 이클립스 센츄어리 D.P</h2>
        <p class="event-layer-summary">
          하나는 의미를 선언하고, 하나는 질서를 유지합니다. 이 섹션은 참소식.com의 메시지와 방어 구조를 함께 보여주는
          이중 코어입니다.
        </p>
      </div>

      <div class="event-layer-grid">
        <article class="event-layer-card declarative">
          <span class="event-layer-label">Mission Layer</span>
          <h4>참소식.com: 메시지 코어와 의미 좌표</h4>
          <p class="event-layer-quote">"${headline}"</p>
          <p>
            ${summary}
          </p>
          <ul class="event-layer-list">
            ${signals}
          </ul>
        </article>

        <article class="event-layer-card functional">
          <span class="event-layer-label">Defense Layer</span>
          <h4>이클립스 센츄어리 D.P: 보호, 정렬, 밀도 유지</h4>
          <p class="event-layer-quote">
            "가치를 지키는 시스템은 앞에 나서지 않아도, 항상 뒤에서 구조를 붙잡고 있어야 합니다."
          </p>
          <p>
            D.P는 충격을 흡수하고, 과장된 반응을 걸러내고, 중심 문장이 끝까지 남도록 시스템의 질서를 유지하는 방어 레이어입니다.
          </p>
          <ul class="event-layer-list">
            ${risks}
          </ul>
        </article>
      </div>

      <div class="event-layer-footer">
        <strong>월드 모니터 연동 메모:</strong> ${outlook}
        <br>
        <span style="opacity:.84;">품질 메모: ${qualityNote}</span>
      </div>
    `;
  }

  async function loadSectionData() {
    try {
      const response = await fetch(`${FEED_AI_URL}?t=${Date.now()}`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      renderSection(data);
    } catch (error) {
      console.warn("eclipse-centauri-dp load failed", error);
      renderSection(null);
    }
  }

  document.addEventListener("DOMContentLoaded", loadSectionData);
})();
