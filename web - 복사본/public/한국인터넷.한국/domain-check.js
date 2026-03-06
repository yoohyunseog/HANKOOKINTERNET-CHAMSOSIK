/**
 * domain-check.js
 * 허용된 도메인만 페이지 표시, 아니면 기존 404 페이지로 리다이렉트
 */

(function() {
    // config.json에서 허용된 도메인 로드
    let ALLOWED_DOMAINS = [];
    
    // config.json 로드 (동기 방식 - 페이지 로드 완료 전에 실행)
    const configPath = '../config.json';
    const xhr = new XMLHttpRequest();
    xhr.open('GET', configPath, false); // 동기 방식
    xhr.onload = function() {
        if (xhr.status === 200) {
            try {
                const config = JSON.parse(xhr.responseText);
                ALLOWED_DOMAINS = config.allowedDomains || [];
                console.log('[Domain Check] config.json에서 allowedDomains 로드 성공:', ALLOWED_DOMAINS);
            } catch (e) {
                console.error('[Domain Check] config.json 파싱 오류:', e);
                ALLOWED_DOMAINS = [];
            }
        } else {
            console.warn('[Domain Check] config.json을 찾을 수 없습니다.');
            ALLOWED_DOMAINS = [];
        }
    };
    xhr.onerror = function() {
        console.warn('[Domain Check] config.json 로드 오류');
        ALLOWED_DOMAINS = [];
    };
    xhr.send();

    // 현재 도메인 확인 (포트 제거)
    const currentHost = window.location.hostname.toLowerCase();
    
    console.log(`[Domain Check] 현재 도메인: ${currentHost}`);
    console.log(`[Domain Check] 허용 도메인: ${ALLOWED_DOMAINS.join(', ')}`);

    // www 제거한 버전도 확인
    const hostWithoutWWW = currentHost.replace(/^www\./, '');

    // 도메인 검증
    const isAllowed = ALLOWED_DOMAINS.some(domain => {
        const domainWithoutWWW = domain.toLowerCase().replace(/^www\./, '');
        return currentHost === domain.toLowerCase() || 
               currentHost === 'www.' + domainWithoutWWW ||
               hostWithoutWWW === domainWithoutWWW;
    });

    if (!isAllowed && !isLocalhost()) {
        console.warn(`[Domain Check] 차단됨: ${currentHost}`);
        // 기존 404 페이지로 리다이렉트
        window.location.href = '/xn--9l4b4xi9r.com//ErrPage/404/index.html';
    } else {
        console.log(`[Domain Check] 허용됨: ${currentHost}`);
    }

    /**
     * 로컬호스트 확인
     */
    function isLocalhost() {
        return currentHost === 'localhost' || 
               currentHost === '127.0.0.1' || 
               currentHost === '::1' ||
               currentHost === '[::1]';
    }
})();
