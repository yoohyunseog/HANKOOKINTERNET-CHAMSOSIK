const crypto = require('crypto');

const COUPANG_DOMAIN = 'https://api-gateway.coupang.com';
const COUPANG_ACCESS_KEY = 'a4672c2f-d1e7-4f48-9c34-30535528c8c7';
const COUPANG_SECRET_KEY = 'ed03dd673ad780db96453e2c869cfc9861584802';
const COUPANG_SUB_ID = '';

function getSignedDate() {
    const now = new Date();

    const year = String(now.getUTCFullYear()).slice(2);
    const month = String(now.getUTCMonth() + 1).padStart(2, '0');
    const day = String(now.getUTCDate()).padStart(2, '0');
    const hours = String(now.getUTCHours()).padStart(2, '0');
    const minutes = String(now.getUTCMinutes()).padStart(2, '0');
    const seconds = String(now.getUTCSeconds()).padStart(2, '0');

    return `${year}${month}${day}T${hours}${minutes}${seconds}Z`;
}

function createCoupangAuthorization(method, uri) {
    if (!COUPANG_ACCESS_KEY || !COUPANG_SECRET_KEY) {
        throw new Error('COUPANG_ACCESS_KEY 또는 COUPANG_SECRET_KEY가 비어 있습니다.');
    }

    const signedDate = getSignedDate();

    const parts = uri.split('?');

    if (parts.length > 2) {
        throw new Error('잘못된 URI 형식입니다.');
    }

    const path = parts[0];
    const query = parts[1] || '';

    const message = signedDate + method.toUpperCase() + path + query;

    const signature = crypto
        .createHmac('sha256', COUPANG_SECRET_KEY)
        .update(message, 'utf8')
        .digest('hex');

    console.log('signedDate:', signedDate);
    console.log('path:', path);
    console.log('query:', query);
    console.log('message:', message);

    return `CEA algorithm=HmacSHA256,access-key=${COUPANG_ACCESS_KEY},signed-date=${signedDate},signature=${signature}`;
}

async function testCoupangApi() {
    const keyword = 'laptop';
    const limit = 4;

    const path = '/v2/providers/affiliate_open_api/apis/openapi/products/search';

    let query = `keyword=${encodeURIComponent(keyword)}&limit=${limit}`;

    if (COUPANG_SUB_ID) {
        query += `&subId=${encodeURIComponent(COUPANG_SUB_ID)}`;
    }

    const uri = `${path}?${query}`;
    const url = `${COUPANG_DOMAIN}${uri}`;

    console.log('--- Coupang API Final Test Start ---');
    console.log('URL:', url);

    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                Authorization: createCoupangAuthorization('GET', uri),
                'Content-Type': 'application/json;charset=UTF-8'
            }
        });

        console.log('Status Code:', response.status);

        const text = await response.text();
        console.log('Raw Response:', text);

        let data = {};
        try {
            data = JSON.parse(text);
        } catch {
            data = { raw: text };
        }

        console.log('Response Body:', JSON.stringify(data, null, 2));

        if (response.ok) {
            console.log('SUCCESS: API is working correctly.');
        } else {
            console.log('FAILED: API returned an error.');
        }
    } catch (error) {
        console.error('CRITICAL ERROR:', error.message);
    }
}

testCoupangApi();