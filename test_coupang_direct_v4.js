const crypto = require('crypto');

const COUPANG_DOMAIN = 'https://api-gateway.coupang.com';
const COUPANG_ACCESS_KEY = process.env.COUPANG_ACCESS_KEY || 'a4672c2f-d1e7-4f48-9c34-30535528c8c7';
const COUPANG_SECRET_KEY = process.env.COUPANG_SECRET_KEY || 'ed03dd673ad780db96453e2c869cfc9861584802';
const COUPANG_SUB_ID = process.env.COUPANG_SUB_ID || '';

function createCoupangAuthorization(method, pathWithQuery) {
    const now = new Date();
    const isoString = now.toISOString(); 
    
    const year = isoString.slice(2, 4);
    const month = isoString.slice(5, 7);
    const day = isoString.slice(8, 10);
    const hours = isoString.slice(11, 13);
    const minutes = isoString.slice(14, 16);
    const seconds = isoString.slice(17, 19);
    
    const signedDate = `${year}${month}${day}T${hours}${minutes}${seconds}Z`;
    
    // 쿠팡 API는 쿼리스트링의 인코딩에 매우 민감합니다.
    // pathWithQuery가 이미 인코딩된 상태라면 그대로 사용합니다.
    const message = signedDate + method.toUpperCase() + pathWithQuery;
    
    const signature = crypto
        .createHmac('sha256', COUPANG_SECRET_KEY)
        .update(message)
        .digest('hex');

    return `CEA algorithm=HmacSHA256, access-key=${COUPANG_ACCESS_KEY}, signed-date=${signedDate}, signature=${signature}`;
}

async function testCoupangApi() {
    // 쿼리스트링을 URLSearchParams 대신 직접 구성하여 인코딩 이슈를 최소화합니다.
    const keyword = '노트북';
    const limit = 4;
    const encodedKeyword = encodeURIComponent(keyword);
    
    let pathWithQuery = `/v2/providers/affiliate_open_api/apis/openapi/products/search?keyword=${encodedKeyword}&limit=${limit}`;
    
    if (COUPANG_SUB_ID) {
        pathWithQuery += `&subId=${encodeURIComponent(COUPANG_SUB_ID)}`;
    }

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
