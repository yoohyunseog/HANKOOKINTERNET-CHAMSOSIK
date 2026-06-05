(function () {
  const ADS_CLIENT = "ca-pub-4501795912654667";
  const ADS_SLOT = "3078174225";
  const scriptUrl = new URL(document.currentScript?.src || "./common-site.js", window.location.href);
  const rootUrl = new URL("./", scriptUrl).href;

  function root(path) {
    return new URL(path, rootUrl).href;
  }

  function ensureAdsenseScript() {
    if (document.querySelector('script[src*="pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"]')) return;
    const script = document.createElement("script");
    script.async = true;
    script.crossOrigin = "anonymous";
    script.src = `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${ADS_CLIENT}`;
    document.head.appendChild(script);
  }

  function pushAd(ad) {
    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
      ad.dataset.adInit = "1";
    } catch (error) {
      ad.dataset.adError = "1";
    }
  }

  function createAd(position) {
    const wrap = document.createElement("aside");
    wrap.className = `chamsosik-common-ad chamsosik-common-ad-${position}`;
    wrap.setAttribute("aria-label", "Google AdSense");
    wrap.innerHTML = `
      <ins class="adsbygoogle"
        style="display:block"
        data-ad-client="${ADS_CLIENT}"
        data-ad-slot="${ADS_SLOT}"
        data-ad-format="auto"
        data-full-width-responsive="true"></ins>
    `;
    return wrap;
  }

  function createHeader() {
    const header = document.createElement("header");
    header.className = "chamsosik-common-header";
    header.innerHTML = `
      <div class="chamsosik-common-inner">
        <a class="chamsosik-common-brand" href="${root("./")}">
          <span class="chamsosik-common-mark">AI</span>
          <span>참소식.com</span>
        </a>
        <nav class="chamsosik-common-nav" aria-label="참소식 공통 메뉴">
          <a href="${root("./")}">메인</a>
          <a href="${root("community/")}">컴퓨터 커뮤니티 뉴스</a>
          <a href="${root("robot/")}">로봇 뉴스</a>
          <a href="${root("pc-parts-ai/")}">AI 컴퓨터 부품 분석</a>
          <a href="${root("pc-parts-ai/parts.html")}">부품 분석표</a>
          <a href="${root("server-journal.html")}">서버 일지</a>
          <span class="chamsosik-common-featured" aria-label="지역 및 성당 소식">
            <a class="chamsosik-common-gold" href="https://www.xn--9l4b4xi9r.com/jungnang-volunteer/">중랑구 소식</a>
            <a class="chamsosik-common-gold" href="https://www.xn--9l4b4xi9r.com/vatican/#latest">주요 성당 소식</a>
          </span>
        </nav>
      </div>
    `;
    return header;
  }

  function createFooter() {
    const footer = document.createElement("footer");
    footer.className = "chamsosik-common-footer site-footer";
    footer.innerHTML = `
      <nav class="chamsosik-common-footer-nav" aria-label="참소식 하단 메뉴">
        <a href="${root("./")}">참소식.com 메인</a>
        <a href="${root("server-journal.html")}">서버 일지 공개 페이지</a>
        <a href="${root("robot/")}">로봇 뉴스</a>
        <a href="${root("pc-parts-ai/")}">AI 컴퓨터 부품 분석</a>
        <a href="https://www.icann.org/compliance/complaint" target="_blank" rel="noopener noreferrer">ICANN 제보</a>
      </nav>
      <div>© 2026 참소식.com. All rights reserved.</div>
      <small>본 도메인은 ICANN 규정에 따라 인증된 계정으로 관리됩니다.</small>
    `;
    return footer;
  }

  function initAds() {
    ensureAdsenseScript();
    document.querySelectorAll(".chamsosik-common-ad .adsbygoogle:not([data-ad-init])").forEach(pushAd);
  }

  function boot() {
    if (!document.body || document.body.dataset.commonShellReady === "1") return;
    document.body.dataset.commonShellReady = "1";

    document.querySelectorAll(".chamsosik-common-header, .chamsosik-common-footer, .chamsosik-common-ad").forEach((item) => item.remove());

    const header = createHeader();
    document.body.insertBefore(header, document.body.firstChild);

    const topAd = createAd("top");
    header.insertAdjacentElement("afterend", topAd);

    const bottomAd = createAd("bottom");
    const footer = createFooter();
    document.body.appendChild(bottomAd);
    document.body.appendChild(footer);

    initAds();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
