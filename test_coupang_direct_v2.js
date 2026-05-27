const crypto = require('crypto');

const COUPANG_DOMAIN = 'https://api-gateway.coupang.com';
const COUPANG_ACCESS_KEY = process.env.COUPANG_ACCESS_KEY || 'a4672c2f-d1e7-4f48-9c34-30535528c8c7';
const COUPANG_SECRET_KEY = process.env.COUPANG_SECRET_KEY || 'ed03dd673ad780db96453e2c869cfc9861584802';
const COUPANG_SUB_ID = process.env.COUPANG_SUB_ID || '';

function createCoupangAuthorization(method, pathWithQuery) {
    // 쿠팡 API는 정확한 UTC 기반의 YYMMDDTHHMMSSZ 포맷을 요구합니다.
    const now = new Date();
    const utc = new Date(now.getTime() + now.getTimezoneOffset * 60000);
    
    const year = String(utc.getFullYear()).slice(2);
    const month = String(utc.getMonth() + 1).padStart(2, '0');
    const day = String(utc.getDate()).padStart(2, '0');
    const hours = String(utc.getHours()).padStart(2, '0');
    const minutes = String(utc.getMinutes()).padStart(2, '0');
    const seconds = String(utc.getSeconds()).padStart(2, '0');
    
    const signedDate = `${year}${month}${day}T${hours}${minutes}${seconds}Z`;
    
    // 가이드라인: message = datetime + method + path + query
    // pathWithQuery는 이미 /v2/...?keyword=... 형태임
    const message = signedDate + method.toUpperCase() + pathWithQuery;
    
    const signature = crypto
        .createHmac('sha256', COUPANG_SECRET_KEY)
        .update(message)
        .digest('hex');

    return `CEA algorithm=HmacSHA256, access-key=${COUPANG_ACCESS_KEY}, signed-date=${signedDate}, signature=${signature}`;
}

async function testCoupangApi() {
    const keyword = '노트북';
    const limit = 4;
    const query = new URLSearchParams({
        keyword,
        limit: String(limit)
    });
    if (COUPANG_SUB_ID) {
        query.set('subId', COUPANG_SUB_ID);
    }

    const pathWithQuery = `/v2/providers/affiliate_open_api/apis/openapi/products/search?${query.toString()}`;
    const url = `${COUPANG_DOMAIN}${pathWithQuery}`;

    console.log('--- Coupang API Test Start ---');
    console.log('URL:', url);
    
    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Authorization': createCoupangAuthorization('GET', pathWithQuery),
                'Content-Type': 'application/json'
            }
        });

        console.log('Status Code:', response.status);
        const data = await response.json().catch(() => ({}));
        console.log('Response Body:', JSON.stringify(data, null, 2));

        if (response.ok) {
            console.log('\n✅ SUCCESS: API is working correctly!');
        } else {
            console.log('\n❌ FAILED: API returned an error.');
        }
    } catch (error) {
        console.error('\n💥 CRITICAL ERROR:', error.message);
    }
}

testCoupangApi();
