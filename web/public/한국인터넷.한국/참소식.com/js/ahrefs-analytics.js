/**
 * Ahrefs Analytics - 자동 로드 스크립트
 * 모든 페이지에 Ahrefs Analytics를 자동으로 추가합니다.
 * 
 * 사용법: <script src="./js/ahrefs-analytics.js"></script>
 * 또는 common-site.js에서 자동으로 로드됩니다.
 */
(function() {
  'use strict';
  
  // Ahrefs Analytics 설정
  const AHREFS_CONFIG = {
    key: 'FB5lEHThbMnrfH2IIMvKaQ',
    src: 'https://analytics.ahrefs.com/analytics.js'
  };
  
  // 이미 로드되었는지 확인
  function isAlreadyLoaded() {
    return document.querySelector('script[src*="analytics.ahrefs.com"]') !== null;
  }
  
  // Ahrefs Analytics 스크립트 로드
  function loadAhrefsAnalytics() {
    if (isAlreadyLoaded()) {
      console.log('[Ahrefs] 이미 로드됨');
      return;
    }
    
    const script = document.createElement('script');
    script.src = AHREFS_CONFIG.src;
    script.setAttribute('data-key', AHREFS_CONFIG.key);
    script.async = true;
    
    script.onload = function() {
      console.log('[Ahrefs] Analytics 로드 완료');
    };
    
    script.onerror = function() {
      console.warn('[Ahrefs] Analytics 로드 실패');
    };
    
    document.head.appendChild(script);
  }
  
  // DOM 준비되면 실행
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadAhrefsAnalytics);
  } else {
    loadAhrefsAnalytics();
  }
  
  // 전역으로 내보내기 (필요시)
  window.AhrefsAnalytics = {
    load: loadAhrefsAnalytics,
    isLoaded: isAlreadyLoaded
  };
})();