const crypto = require('crypto');

const COUPANG_DOMAIN = 'https://api-gateway.coupang.com';
const COUPANG_ACCESS_KEY = process.env.COUPANG_ACCESS_KEY || 'a4672c2f-d1e7-4f48-9c34-30535528c8c7';
const COUPANG_SECRET_KEY = process.env.COUPANG_SECRET_KEY || 'ed03dd673ad780db96453e2c869cfc9861584802';
const COUPANG_SUB_ID = process.env.COUPANG_SUB_ID || '';

function createCoupangAuthorization(method, pathWithQuery) {
    // 쿠팡 API 공식 가이드: YYMMDDTHHMMSSZ (UTC 기준)
    const now = new Date();
    const isoString = now.toISOString(); // 2026-05-26T12:34:56.789Z
    
    const year = isoString.slice(2, 4);
    const month = isoString.slice(5, 7);
    const day = isoString.slice(8, 10);
    const hours = isoString.slice(11, 13);
    const minutes = isoString.slice(14, 16);
    const seconds = isoString.slice(17, 19);
    
    const signedDate = `${year}${month}${day}T${hours}${minutes}${seconds}Z`;
    
    // 가이드라인: message = datetime + method + path + query
    const message = signedDate + method.toUpperCase() + pathWithQuery;
    
    const signature = crypto
        .createHmac('sha256', COUPANG_SECRET_KEY)
        .update(message)
        .digest('hex');

    // 공백과 쉼표 위치를 가이드라인과 100% 일치시킴
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
