function getSimilarity(a, b) {
  a = a.toLowerCase();
  b = b.toLowerCase();
  let match = 0;
  a.split('').forEach(char => {
    if (b.includes(char)) match++;
  });
  return match;
}

const $grid = $('#masonry-grid').masonry({
  itemSelector: '.masonry-item',
  percentPosition: true,
  gutter: 20
});

$('#cardForm').on('submit', function (e) {
  e.preventDefault();
  const title = $('#title').val().trim();
  const tag = $('#tag').val().trim();
  const quote = $('#quote').val().trim();
  const link = $('#link').val().trim();

  const $card = $(`
    <div class="col-sm-6 col-lg-4 masonry-item" data-title="${title}" data-quote="${quote}">
      <div class="card shadow-sm">
        <div class="card-body">
          <h5 class="card-title">${title}</h5>
          <p class="tag">${tag}</p>
          <p class="quote">${quote}</p>
          <a href="${link}" target="_blank" class="btn btn-outline-primary btn-sm mt-2">바로가기</a>
        </div>
      </div>
    </div>
  `);

  $('#title, #tag, #quote, #link').val('');
  $grid.append($card).imagesLoaded(() => {
    $grid.masonry('appended', $card);
  });
});

function updateCardBits() {
  $('.masonry-item').each(function () {
    const $item = $(this);
    const title = $item.data('title');
    const text = `${title}`;

    const bits = wordNbUnicodeFormat(text);
    const bitMax = BIT_MAX_NB(bits);
    const bitMin = BIT_MIN_NB(bits);

    console.log(`카드 ${title}`);
    console.log(`   BIT_MAX: ${bitMax.toFixed(2)}, BIT_MIN: ${bitMin.toFixed(2)}`);

    $item.find('.sort-keyword').val(bitMin.toFixed(10));
    $item.find('.bit-max-input').val(bitMax.toFixed(10));
    $item.find('.bit-min-input').val(bitMin.toFixed(10));
  });
}

function updateCardSimilarityFromCalculatedBits() {
  const keywordString = $('#sortKeywordGlobal').val().toLowerCase().trim();
  const keywordList = keywordString.split(',').map(k => k.trim()).filter(k => k);

  $('.masonry-item').each(function () {
    const $item = $(this);
    const cardBitMax = parseFloat($item.find('.bit-max-input').val());
    const title = ($item.data('title') || '').toLowerCase();

    let baseScore = 0;

    const keywordBitMax = parseFloat($('#bitMaxGlobal').val());
    if (!isNaN(cardBitMax) && !isNaN(keywordBitMax)) {
      const diff = Math.abs(cardBitMax - keywordBitMax);
      baseScore = Math.max(0, 100 - diff);
    }

    let keywordBonus = 0;
    keywordList.forEach(kw => {
      if (title.includes(kw)) keywordBonus += 10;
    });

    const totalScore = (baseScore + keywordBonus).toFixed(10);
    $item.find('.sort-score').val(totalScore);
  });
}

$('#sortKeywordGlobal').on('input', function () {
  const keyword = $(this).val().trim();
  if (keyword) {
    const bits = wordNbUnicodeFormat(keyword);
    const bitMax = BIT_MAX_NB(bits).toFixed(10);
    const bitMin = BIT_MIN_NB(bits).toFixed(10);

    $('#bitMaxGlobal').val(bitMax);
    $('#bitMinGlobal').val(bitMin);
  } else {
    $('#bitMaxGlobal').val('');
    $('#bitMinGlobal').val('');
  }
  currentIndex = 0;
  // updateCardBits();
  // updateCardSimilarityFromCalculatedBits();
  // sortCardsByScoreDescending();
});

let masonryLayoutTimeout = null;

function sortCardsByScoreDescending() {
  const $grid = $('#masonry-grid');
  const $cards = $grid.children('.masonry-item').get();

  $cards.sort((a, b) => {
    const scoreA = parseFloat($(a).find('.sort-score').val()) || 0;
    const scoreB = parseFloat($(b).find('.sort-score').val()) || 0;
    return scoreB - scoreA;
  });

  $cards.forEach(card => $grid.append(card));

  if (masonryLayoutTimeout) {
    clearTimeout(masonryLayoutTimeout);
  }

  masonryLayoutTimeout = setTimeout(() => {
    $grid.masonry('reloadItems').masonry('layout');
  }, 1000);
}

let currentIndex = 0;
let switchStep = 0;

setInterval(() => {
  const $items = $('.masonry-item');
  const totalCards = $items.length;

  $('.switchStep').text(switchStep);
  $('.cardCount').text(currentIndex);
  $('.totalCards').text(totalCards);

  if (totalCards === 0 || switchStep === -1) return;

  switch (switchStep) {
    case 0:
      if (currentIndex >= totalCards) {
        currentIndex = 0;
      }
      switchStep = 1;
      break;

    case 1: {
      const $item = $($items[currentIndex]);
      if (!$item.length) {
        switchStep = 0;
        break;
      }

      const title = $item.data('title') || '';
      const text = `${title}`;

      const bits = wordNbUnicodeFormat(text);
      const bitMax = BIT_MAX_NB(bits);
      const bitMin = BIT_MIN_NB(bits);

      $item.find('.bit-max-input').val(bitMax.toFixed(10));
      $item.find('.bit-min-input').val(bitMin.toFixed(10));
      $item.find('.max').text(bitMax.toFixed(10));
      $item.find('.min').text(bitMin.toFixed(10));

      switchStep = 2;
      break;
    }

    case 2: {
      const $item = $($items[currentIndex]);
      if (!$item.length) {
        switchStep = 0;
        break;
      }

      const keywordString = ($('#sortKeywordGlobal').val() || '').toLowerCase().trim();
      const keywordList = keywordString.split(',').map(k => k.trim()).filter(k => k);

      const keywordBitMax = parseFloat($('#bitMaxGlobal').val());
      const cardBitMax = parseFloat($item.find('.bit-max-input').val());
      const title = ($item.data('title') || '').toLowerCase();

      let baseScore = 0;
      if (!isNaN(cardBitMax) && !isNaN(keywordBitMax)) {
        const diff = Math.abs(cardBitMax - keywordBitMax);
        baseScore = Math.max(0, 100 - diff);
      }

      let keywordBonus = 0;
      keywordList.forEach(kw => {
        if (title.includes(kw)) keywordBonus += 10;
      });

      const totalScore = (baseScore + keywordBonus).toFixed(10);
      $item.find('.sort-score').val(totalScore);
      $item.find('.score').text(totalScore);

      currentIndex++;

      if (currentIndex < totalCards) {
        switchStep = 1;
      } else {
        switchStep = 0;
        sortCardsByScoreDescending();
      }
      break;
    }

    default:
      switchStep = 0;
      break;
  }
}, 100);
