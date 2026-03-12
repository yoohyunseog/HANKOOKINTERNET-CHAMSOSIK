// website_diagram_full.json의 노드/엣지 정보를 realtime_finance_data.json에 저장
// 실행: node updateRealtimeFinanceData.js

import fs from 'fs';

const fullJsonPath = './website_diagram_full.json';
const realtimePath = './realtime_finance_data.json';

const fullData = JSON.parse(fs.readFileSync(fullJsonPath, 'utf-8'));
const { nodes, edges } = fullData;

const result = { nodes, edges };
fs.writeFileSync(realtimePath, JSON.stringify(result, null, 2), 'utf-8');
console.log('realtime_finance_data.json에 노드/엣지 모두 반영 완료');
