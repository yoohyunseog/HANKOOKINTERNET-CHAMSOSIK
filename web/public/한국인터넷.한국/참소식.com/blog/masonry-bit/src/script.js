(function ($) {
  'use strict';

  const APP_VERSION = '0.1';
  const SORT_DELAY = 260;

  const posts = [
    { title: '자백의 대가 결말', hit: 23, date: '2025-01-15' },
    { title: '친애하는 x 결말', hit: 4, date: '2025-01-14' },
    { title: '자백의 대가', hit: 28, date: '2025-01-13' },
    { title: '자백의대가 기본정보', hit: 8, date: '2025-01-12' },
    { title: '자백의대가 결말', hit: 23, date: '2025-01-11' },
    { title: '친애하는 x', hit: 4, date: '2025-01-10' },
    { title: '프로보노 기본정보', hit: 1, date: '2025-01-09' },
    { title: '프로보노', hit: 1, date: '2025-01-08' },
    { title: '자백의 대가 범인', hit: 90, date: '2025-01-07' },
    { title: '프로보노 뜻', hit: 1, date: '2025-01-06' },
    { title: '이강에는 달이 흐른다', hit: 17, date: '2025-01-05' },
    { title: '김유정, 친애하는X 파격 결말', hit: 1, date: '2025-01-04' },
    { title: '키스는 괜히 해서, 은인 정체 공개', hit: 1, date: '2025-01-03' },
    { title: '김유정 친애하는X 파격 엔딩', hit: 1, date: '2025-01-02' },
    { title: '친애하는x 기본정보', hit: 5, date: '2025-01-01' }
  ];

  let $grid = null;
  let processing = null;

  function normalizeText(value) {
    return String(value || '')
      .toLowerCase()
      .replace(/[^\wㄱ-ㅎ가-힣\s]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function tokenize(value) {
    const compact = normalizeText(value);
    const words = compact.split(' ').filter(Boolean);
    const chars = Array.from(compact.replace(/\s/g, ''));
    return [...new Set([...words, ...chars])];
  }

  function getBitApi() {
    return {
      ready:
        typeof window.wordNbUnicodeFormat === 'function' &&
        typeof window.BIT_MAX_NB === 'function' &&
        typeof window.BIT_MIN_NB === 'function',
      unicode: window.wordNbUnicodeFormat,
      max: window.BIT_MAX_NB,
      min: window.BIT_MIN_NB,
      sim: typeof window.wordSim2 === 'function' ? window.wordSim2 : null,
      pair: typeof window.calculateSimilarity2 === 'function' ? window.calculateSimilarity2 : null
    };
  }

  function fallbackHash(value, salt) {
    const chars = Array.from(normalizeText(value));
    return chars.reduce((total, char, index) => {
      return total + char.codePointAt(0) * (index + 1 + salt);
    }, salt * 997);
  }

  function calculateBits(title) {
    const bitApi = getBitApi();

    if (bitApi.ready) {
      try {
        const unicode = bitApi.unicode(title);
        return {
          bitMax: Number(bitApi.max(unicode)) || 0,
          bitMin: Number(bitApi.min(unicode)) || 0
        };
      } catch (error) {
        console.warn('bitCalculation.v.0.1.js 계산 실패, fallback 사용:', error);
      }
    }

    return {
      bitMax: fallbackHash(title, 11),
      bitMin: fallbackHash(title, 3)
    };
  }

  function levenshteinSimilarity(left, right) {
    const a = normalizeText(left);
    const b = normalizeText(right);
    const longer = a.length > b.length ? a : b;
    const shorter = a.length > b.length ? b : a;

    if (longer.length === 0) return 1;

    const costs = [];
    for (let i = 0; i <= longer.length; i += 1) {
      let previous = i;
      for (let j = 0; j <= shorter.length; j += 1) {
        if (i === 0) {
          costs[j] = j;
        } else if (j > 0) {
          let next = costs[j - 1];
          if (longer.charAt(i - 1) !== shorter.charAt(j - 1)) {
            next = Math.min(next, previous, costs[j]) + 1;
          }
          costs[j - 1] = previous;
          previous = next;
        }
      }
      if (i > 0) costs[shorter.length] = previous;
    }

    return (longer.length - costs[shorter.length]) / longer.length;
  }

  function tokenSimilarity(left, right) {
    const leftTokens = tokenize(left);
    const rightTokens = tokenize(right);
    const union = new Set([...leftTokens, ...rightTokens]);

    if (union.size === 0) return 0;

    const matches = leftTokens.filter((token) => rightTokens.includes(token));
    return matches.length / union.size;
  }

  function bitSimilarity(leftTitle, rightTitle) {
    const bitApi = getBitApi();
    const leftBits = calculateBits(leftTitle);
    const rightBits = calculateBits(rightTitle);

    if (bitApi.sim) {
      try {
        const maxScore = Number(bitApi.sim(leftBits.bitMax, rightBits.bitMax)) || 0;
        const minScore = Number(bitApi.sim(leftBits.bitMin, rightBits.bitMin)) || 0;
        return Math.max(0, Math.min(1, ((maxScore + minScore) / 2) / 100));
      } catch (error) {
        console.warn('wordSim2 계산 실패, fallback 사용:', error);
      }
    }

    const maxDistance = Math.abs(leftBits.bitMax - rightBits.bitMax);
    const minDistance = Math.abs(leftBits.bitMin - rightBits.bitMin);
    return 1 / (1 + ((maxDistance + minDistance) / 20000));
  }

  function calculateScore(baseTitle, targetTitle) {
    if (!baseTitle || !targetTitle) return 0;
    if (normalizeText(baseTitle) === normalizeText(targetTitle)) return 100;

    const textScore = levenshteinSimilarity(baseTitle, targetTitle);
    const wordScore = tokenSimilarity(baseTitle, targetTitle);
    const nbScore = bitSimilarity(baseTitle, targetTitle);

    return Math.round(((textScore * 0.25) + (wordScore * 0.35) + (nbScore * 0.4)) * 10000) / 100;
  }

  function setProgress($item, score) {
    const safeScore = Math.max(0, Math.min(100, score));
    $item.find('.progress-bar-left').css('width', `${safeScore}%`);
    $item.find('.progress-bar-right').css('width', `${100 - safeScore}%`);
  }

  function createPost(post, index) {
    const bits = calculateBits(post.title);

    return `
      <li class="grid-item" data-post-id="${index}" data-title="${post.title}">
        <article class="post-item" tabindex="0">
          <h3 class="post-title">${post.title}</h3>
          <div class="post-meta">
            <div class="post-meta-item">
              <i class="fas fa-eye" aria-hidden="true"></i>
              <span class="hit-count">${post.hit.toLocaleString()}</span>
            </div>
            <div class="post-meta-item">
              <i class="fas fa-calendar" aria-hidden="true"></i>
              <span>${post.date}</span>
            </div>
            <div class="post-meta-item">
              <i class="fas fa-chart-line" aria-hidden="true"></i>
              <span>MAX: ${bits.bitMax.toFixed(6)}</span>
            </div>
            <div class="post-meta-item">
              <i class="fas fa-chart-area" aria-hidden="true"></i>
              <span>MIN: ${bits.bitMin.toFixed(6)}</span>
            </div>
            <div class="post-meta-item similarity-row" hidden>
              <i class="fas fa-code-compare" aria-hidden="true"></i>
              <span class="similarity-value">유사도 0%</span>
            </div>
          </div>
          <div class="progress-box" aria-hidden="true">
            <div class="progress-container">
              <div class="progress-bar">
                <div class="progress-bar-left"></div>
                <div class="progress-bar-right"></div>
              </div>
            </div>
          </div>
        </article>
      </li>
    `;
  }

  function layoutGrid() {
    if ($grid && $grid.data('masonry')) {
      $grid.masonry('reloadItems').masonry('layout');
    }
  }

  function renderPosts() {
    const $postsList = $('#postsList');
    $postsList.html(posts.map(createPost).join(''));

    $postsList.find('.grid-item').each(function () {
      setProgress($(this), 0);
    });
  }

  function initMasonry() {
    if (typeof $.fn.masonry !== 'function') return;

    $grid = $('#postsList').masonry({
      itemSelector: '.grid-item',
      columnWidth: '.grid-item',
      percentPosition: true,
      transitionDuration: '0.45s',
      horizontalOrder: true
    });
  }

  function updateLoadingProgress(percent, status) {
    $('#loadingProgressBar').css('width', `${Math.max(0, Math.min(100, percent))}%`);
    $('#loadingStatus').text(status);
  }

  function showLoading(status) {
    updateLoadingProgress(0, status);
    $('#loadingOverlay').removeClass('hidden');
  }

  function hideLoading() {
    setTimeout(() => {
      $('#loadingOverlay').addClass('hidden');
    }, 250);
  }

  function stopProcessing() {
    if (processing) {
      window.clearTimeout(processing.timer);
      processing = null;
    }
  }

  function increaseHitCount($item) {
    const $hitCount = $item.find('.hit-count');
    const currentHit = Number($hitCount.text().replace(/,/g, '')) || 0;
    $hitCount.text((currentHit + 1).toLocaleString());
  }

  function sortBySimilarity($baseItem) {
    stopProcessing();

    const baseTitle = $baseItem.data('title');
    const $items = $('#postsList .grid-item');
    const scoredItems = $items.toArray().map((element) => {
      const $item = $(element);
      const score = calculateScore(baseTitle, $item.data('title'));
      return { element, score };
    });

    showLoading('유사도 계산 중...');

    scoredItems.forEach(({ element, score }, index) => {
      const $item = $(element);
      $item.attr('data-score', score);
      $item.find('.similarity-row').prop('hidden', false);
      $item.find('.similarity-value').text(`유사도 ${score.toFixed(2)}%`);
      setProgress($item, score);
      updateLoadingProgress(Math.round(((index + 1) / scoredItems.length) * 45), `유사도 계산 중... (${index + 1}/${scoredItems.length})`);
    });

    scoredItems.sort((a, b) => b.score - a.score);

    let index = 0;
    processing = {
      timer: null
    };

    function appendNext() {
      if (index >= scoredItems.length) {
        layoutGrid();
        $('#sortIndicator').prop('hidden', false);
        updateLoadingProgress(100, '재정렬 완료');
        hideLoading();
        processing = null;
        return;
      }

      $('#postsList').append(scoredItems[index].element);
      updateLoadingProgress(45 + Math.round(((index + 1) / scoredItems.length) * 55), `정렬 중... (${index + 1}/${scoredItems.length})`);
      layoutGrid();
      index += 1;
      processing.timer = window.setTimeout(appendNext, SORT_DELAY);
    }

    $('#postsList').empty();
    appendNext();
  }

  function bindEvents() {
    $(document).on('click keydown', '.post-item', function (event) {
      if (event.type === 'keydown' && event.key !== 'Enter' && event.key !== ' ') return;
      event.preventDefault();

      const $card = $(this);
      const $item = $card.closest('.grid-item');

      increaseHitCount($item);
      $('.post-item').removeClass('clicked');
      $card.addClass('clicked');
      sortBySimilarity($item);
    });
  }

  function waitForBitCalculation(callback, attemptsLeft = 30) {
    if (getBitApi().ready || attemptsLeft <= 0) {
      callback();
      return;
    }

    window.setTimeout(() => waitForBitCalculation(callback, attemptsLeft - 1), 100);
  }

  $(function () {
    window.MASONRY_BIT_VERSION = APP_VERSION;
    renderPosts();

    waitForBitCalculation(() => {
      renderPosts();

      if (typeof imagesLoaded === 'function') {
        imagesLoaded('#postsList', initMasonry);
      } else {
        initMasonry();
      }
    });

    bindEvents();
  });
})(jQuery);
