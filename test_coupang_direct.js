const crypto = require('crypto');

const COUPANG_DOMAIN = 'https://api-gateway.coupang.com';
const COUPANG_ACCESS_KEY = process.env.COUPANG_ACCESS_KEY || 'a4672c2f-d1e7-4f48-9c34-30535528c8c7';
const COUPANG_SECRET_KEY = process.env.COUPANG_SECRET_KEY || 'ed03dd673ad780db96453e2c869cfc9861584802';
const COUPANG_SUB_ID = process.env.COUPANG_SUB_ID || '';

function createCoupangAuthorization(method, pathWithQuery) {
    const now = new Date();
    const year = String(now.getUTCFullYear()).slice(2);
    const month = String(now.getUTCMonth() + 1).padStart(2, '0');
    const day = String(now.getUTCDate()).padStart(2, '0');
    const hours = String(now.getUTCHours()).padStart(2, '0');
    const minutes = String(now.getUTCMinutes()).padStart(2, '0');
    const seconds = String(now.getUTCSeconds()).padStart(2, '0');
    
    const signedDate = `${year}${month}${day}T${hours}${minutes}${seconds}Z`;
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
