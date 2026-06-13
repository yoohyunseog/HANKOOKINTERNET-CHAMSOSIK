/**
 * 블로그 포스트 조회수 추적 및 정렬 시스템
 * - 서버 API를 사용하여 조회수 저장 (모든 사용자 공유)
 * - 캐시 없이 항상 최신 데이터 조회
 * - 조회수 기반 정렬 기능 제공
 */

(function() {
  'use strict';

  const SORT_KEY = 'chamsosik_blog_sort';
  const API_BASE = window.location.origin;

  // 메모리 캐시 (페이지 로드 시에만 사용)
  let viewsCache = null;

  /**
   * 서버에서 조회수 데이터 가져오기
   */
  async function fetchViewsFromServer() {
    try {
      const response = await fetch(`${API_BASE}/api/blog/views`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          viewsCache = data.data;
          return viewsCache;
        }
      }
    } catch (e) {
      console.error('서버 조회수 로드 실패:', e);
    }
    return {};
  }

  /**
   * 조회수 데이터 가져오기 (항상 서버에서 최신 데이터)
   */
  async function getViewsData() {
    // 이미 로드된 데이터가 있으면 사용
    if (viewsCache !== null) {
      return viewsCache;
    }
    
    // 서버에서 가져오기
    return await fetchViewsFromServer();
  }

  /**
   * 특정 포스트 조회수 증가 (서버에 저장)
   */
  async function incrementView(postHref) {
    try {
      const response = await fetch(`${API_BASE}/api/blog/views/${encodeURIComponent(postHref)}`, {
        method: 'POST'
      });
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          // 캐시 업데이트
          if (viewsCache) {
            viewsCache[postHref] = data.views;
          }
          return data.views;
        }
      }
    } catch (e) {
      console.error('조회수 증가 실패:', e);
    }
    return 0;
  }

  /**
   * 특정 포스트 조회수 가져오기
   */
  async function getViewCount(postHref) {
    const views = await getViewsData();
    return views[postHref] || 0;
  }

  /**
   * 모든 포스트 조회수 가져오기
   */
  async function getAllViews() {
    return await getViewsData();
  }

  /**
   * 조회수 기준 정렬 (비동기)
   */
  async function sortByViews(posts, order = 'desc') {
    const views = await getViewsData();
    return posts.sort((a, b) => {
      const viewsA = views[a.href] || 0;
      const viewsB = views[b.href] || 0;
      return order === 'desc' ? viewsB - viewsA : viewsA - viewsB;
    });
  }

  /**
   * 날짜 기준 정렬
   */
  function sortByDate(posts, order = 'desc') {
    return posts.sort((a, b) => {
      const dateA = new Date(a.date).getTime();
      const dateB = new Date(b.date).getTime();
      return order === 'desc' ? dateB - dateA : dateA - dateB;
    });
  }

  /**
   * 현재 정렬 방식 가져오기
   */
  function getSortMethod() {
    return localStorage.getItem(SORT_KEY) || 'date';
  }

  /**
   * 정렬 방식 저장
   */
  function setSortMethod(method) {
    localStorage.setItem(SORT_KEY, method);
  }

  /**
   * 조회수 포맷팅 (천 단위 콤마)
   */
  function formatViews(count) {
    if (count >= 1000) {
      return (count / 1000).toFixed(1) + 'K';
    }
    return count.toString();
  }

  /**
   * 조회수 표시 업데이트 (비동기)
   */
  async function updateViewDisplay(postHref, element) {
    const count = await getViewCount(postHref);
    if (element) {
      element.textContent = formatViews(count);
      element.setAttribute('data-views', count);
    }
  }

  /**
   * 포스트 카드에 조회수 표시 추가 (비동기)
   */
  async function addViewCountToCard(card, postHref) {
    const count = await getViewCount(postHref);
    
    // 조회수 표시 요소 찾기 또는 생성
    let viewElement = card.querySelector('.post-views');
    if (!viewElement) {
      const metaContainer = card.querySelector('.post-meta');
      if (metaContainer) {
        viewElement = document.createElement('span');
        viewElement.className = 'post-views';
        viewElement.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg><span class="view-count">${formatViews(count)}</span>`;
        metaContainer.appendChild(viewElement);
      }
    } else {
      // 기존 요소 업데이트
      const countSpan = viewElement.querySelector('.view-count');
      if (countSpan) {
        countSpan.textContent = formatViews(count);
      } else {
        viewElement.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align: middle; margin-right: 4px;"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg><span class="view-count">${formatViews(count)}</span>`;
      }
    }
  }

  /**
   * 전체 포스트 목록 조회수 표시 업데이트 (비동기)
   */
  async function updateAllViewDisplays(posts) {
    const views = await getViewsData();
    posts.forEach(post => {
      const card = document.querySelector(`a[href="${post.href}"]`)?.closest('.post-card');
      if (card) {
        const count = views[post.href] || 0;
        let viewElement = card.querySelector('.post-views');
        if (viewElement) {
          const countSpan = viewElement.querySelector('.view-count');
          if (countSpan) {
            countSpan.textContent = formatViews(count);
          }
        }
      }
    });
  }

  /**
   * 현재 페이지가 포스트 상세 페이지인지 확인
   */
  function isPostPage() {
    const path = window.location.pathname;
    return path.includes('/posts/') && path.endsWith('.html');
  }

  /**
   * 현재 포스트의 href 가져오기
   */
  function getCurrentPostHref() {
    const path = window.location.pathname;
    const match = path.match(/\/posts\/(.+\.html)$/);
    return match ? `posts/${match[1]}` : null;
  }

  /**
   * 포스트 방문 기록 (상세 페이지에서 호출) - 비동기
   */
  async function trackPostVisit() {
    if (isPostPage()) {
      const postHref = getCurrentPostHref();
      if (postHref) {
        // 세션 체크로 중복 카운트 방지
        const sessionKey = `viewed_${postHref}`;
        if (!sessionStorage.getItem(sessionKey)) {
          await incrementView(postHref);
          sessionStorage.setItem(sessionKey, 'true');
        }
        
        // 조회수 표시 업데이트
        const viewCountEl = document.getElementById('view-count');
        if (viewCountEl) {
          const count = await getViewCount(postHref);
          viewCountEl.textContent = formatViews(count);
        }
      }
    }
  }

  // 전역 함수로 노출
  window.BlogViewTracker = {
    incrementView,
    getViewCount,
    getAllViews,
    sortByViews,
    sortByDate,
    getSortMethod,
    setSortMethod,
    formatViews,
    updateViewDisplay,
    addViewCountToCard,
    updateAllViewDisplays,
    trackPostVisit
  };

  // 주의: trackPostVisit()은 포스트 HTML에서 직접 호출됩니다.
  // 여기서 자동 호출하면 중복 카운트가 발생합니다.

})();