/**
 * 설명 노드를 지표별로 그룹화하여 배열로 반환
 * @param {string} mermaidCode - Mermaid 원본 전체 텍스트
 * @returns {Array<{indicator: string, desc: string, id: string, label: string, text: string, importance: string}>}
 */
function parseDescriptionNodesGroupedByIndicator(mermaidCode) {
  const descNodes = parseDescriptionNodesToArray(mermaidCode);
  // indicator: id에서 _설명 제거
  return descNodes.map(node => {
    const indicator = node.id.replace(/_설명$/, '').replace(/_KRW$/, '').replace(/_/g, '').replace(/\:.*/, '');
    return {
      indicator,
      desc: node.text,
      id: node.id,
      label: node.label,
      text: node.text,
      importance: node.importance
    };
  });
}
// (아래로 이동)
/**
 * Mermaid 코드에서 설명 노드만 배열로 추출 (label에 _설명 포함)
 * @param {string} mermaidCode - Mermaid 원본 전체 텍스트
 * @returns {Array<{id: string, label: string, text: string, importance: string}>}
 */
function parseDescriptionNodesToArray(mermaidCode) {
  const allNodes = parseMermaidNodesWithMeta(mermaidCode);
  return allNodes.filter(node => node.label.includes('_설명'));
}
/**
 * Mermaid MMD를 한 줄씩 파싱하여 지표별 value/desc/edges로 그룹화
 * @param {string} mmdText - Mermaid 원본 전체 텍스트
 * @returns {object} indicators - { KOSPI: { value, desc, edges: [] }, ... }
 */
function parseIndicatorsGroupedById(mmdText) {
  const lines = mmdText.split('\n');
  const indicators = {};
  for (const line of lines) {
    // 1. 지표 값 노드 (예: KOSPI[KOSPI: 5,557.11])
    let m = line.match(/^\s*([A-Za-z0-9_]+)\[([A-Za-z0-9_]+):\s*([0-9.,$]+)\]/);
    if (m) {
      const id = m[1];
      const value = m[3];
      if (!indicators[id]) indicators[id] = {};
      indicators[id].value = value;
      continue;
    }
    // 2. 설명 노드 (예: KOSPI_설명[KOSPI_설명: ...])
    m = line.match(/^\s*([A-Za-z0-9_]+_설명)\[([A-Za-z0-9_]+_설명):\s*(.+)\]/);
    if (m) {
      const id = m[1].replace('_설명', '');
      const desc = m[3];
      if (!indicators[id]) indicators[id] = {};
      indicators[id].desc = desc;
      continue;
    }
    // 3. 관계(엣지) (예: KOSPI -- [중요] --> S&P500)
    m = line.match(/^\s*([A-Za-z0-9_]+)\s*--.*?--+>\s*([A-Za-z0-9_]+)/);
    if (m) {
      const from = m[1], to = m[2];
      if (!indicators[from]) indicators[from] = {};
      if (!indicators[from].edges) indicators[from].edges = [];
      indicators[from].edges.push(to);
      continue;
    }
  }
  return indicators;
}

/**
 * Mermaid 코드에서 지수 노드 → 설명 노드 직접 연결만 추출
 * @param {string} mmdText - Mermaid 원본 전체 텍스트
 * @returns {Array<{from: string, to: string}>}
 */
function parseDirectDescriptionEdges(mmdText) {
  const directEdges = [];
  // KOSPI[KOSPI: ...] --> KOSPI_설명[KOSPI_설명: ...] 등만 추출
  const edgeRegex = /([^\s\[\{]+)\s*\[.*?\]\s*--\>\s*([^\s\[\{]+)\s*\[.*?\]/g;
  let match;
  while ((match = edgeRegex.exec(mmdText)) !== null) {
    const from = match[1];
    const to = match[2];
    directEdges.push({ from, to });
  }
  return directEdges;
}

/**
 * website_from_diagram.json에서 JSON 오브젝트만 robust하게 추출/파싱
 * @param {string} fileText - 파일 전체 텍스트
 * @returns {Object} { nodes: [...], edges: [...] }
 */
function parseWebsiteFromDiagramJsonText(fileText) {
  // 첫 번째 { ... } 블록만 추출
  const match = fileText.match(/{[\s\S]*}/);
  if (!match) return { nodes: [], edges: [] };
  try {
    const jsonData = JSON.parse(match[0]);
    if (!Array.isArray(jsonData.nodes) || !Array.isArray(jsonData.edges)) return { nodes: [], edges: [] };
    return { nodes: jsonData.nodes, edges: jsonData.edges };
  } catch (e) {
    return { nodes: [], edges: [] };
  }
}
/**
 * website_from_diagram.json 파싱 (노드/엣지 robust)
 * @param {Object} jsonData - website_from_diagram.json 내용 (nodes, edges 배열 포함)
 * @returns {Object} { nodes: [...], edges: [...] }
// ...existing code...
**/ 
// ESM import 대응: 주요 함수 export
export { parseMermaidToRelations, parseWebsiteFromDiagramJsonText, parseDiagramJsonToGraph, parseDirectDescriptionEdges, parseIndicatorsGroupedById, parseMermaidToGroupedIndicators, parseMermaidNodesWithMeta, parseDescriptionNodesToArray, parseDescriptionNodesGroupedByIndicator };

// 브라우저 환경에서 주요 함수 window에 명시적으로 할당 (동적 import 대응)
// 반드시 모든 함수 선언 이후에 할당해야 함
if (typeof window !== 'undefined') {
  window.parseMermaidToRelations = parseMermaidToRelations;
  window.parseWebsiteFromDiagramJsonText = parseWebsiteFromDiagramJsonText;
  window.parseDiagramJsonToGraph = parseDiagramJsonToGraph;
  window.parseDirectDescriptionEdges = parseDirectDescriptionEdges;
  window.parseIndicatorsGroupedById = parseIndicatorsGroupedById;
  window.parseMermaidToGroupedIndicators = parseMermaidToGroupedIndicators;
  window.parseMermaidNodesWithMeta = parseMermaidNodesWithMeta;
  window.parseDescriptionNodesToArray = parseDescriptionNodesToArray;
  window.parseDescriptionNodesGroupedByIndicator = parseDescriptionNodesGroupedByIndicator;
}
/**
 * Mermaid 코드에서 노드 id, label, text(desc), importance를 모두 추출
 * @param {string} mermaidCode - Mermaid 원본 전체 텍스트
 * @returns {Array<{id: string, label: string, text: string, importance: string}>}
 */
function parseMermaidNodesWithMeta(mermaidCode) {
  const nodeLabelMap = new Map();
  const nodeMetaMap = new Map();
  // 주석에서 노드 설명/중요도 추출
  const commentRegex = /^%%\s*([A-Za-z0-9_]+):\s*(.*?)(?:,\s*(중요|보통|낮음))?$/gm;
  let commentMatch;
  while ((commentMatch = commentRegex.exec(mermaidCode || '')) !== null) {
    const nodeId = (commentMatch[1] || '').trim();
    const desc = (commentMatch[2] || '').trim();
    const importance = (commentMatch[3] || '보통').trim();
    if (nodeId) {
      nodeMetaMap.set(nodeId, { desc, importance });
    }
  }
  const normalized = (mermaidCode || '')
    .replace(/^```.*/gm, '')
    .replace(/%%.*$/gm, '')
    .replace(/\/\/.*$/gm, '')
    .replace(/\r/g, '');
  const nodeDefRegex = /([^\s\[\{]+)\s*([\[{])(.*?)[\]}]/g;
  let nodeMatch;
  while ((nodeMatch = nodeDefRegex.exec(normalized)) !== null) {
    const nodeId = (nodeMatch[1] || '').trim();
    let nodeLabel = (nodeMatch[3] || '').trim();
    let desc = '';
    const descMatch = nodeLabel.match(/^(.*?_설명):\s*(.+)$/);
    if (descMatch) {
      nodeLabel = descMatch[1];
      desc = descMatch[2];
    }
    const meta = nodeMetaMap.get(nodeId) || { desc: '', importance: '보통' };
    if (nodeId && nodeLabel) {
      nodeLabelMap.set(nodeId, { label: nodeLabel, desc: desc || meta.desc, importance: meta.importance });
    }
  }
  return Array.from(nodeLabelMap.entries()).map(([id, node]) => ({
    id,
    label: node.label,
    text: node.desc,
    importance: node.importance
  }));
}
/**
 * Mermaid 코드를 한 줄씩 robust하게 파싱 후, 지표(fromLabel) 단위로 그룹화
 * @param {string} mermaidCode - Mermaid 원본 전체 텍스트
 * @returns {object} groups - { [지표]: { fromLabel, fromDesc, fromImportance, edges: [...] } }
 */
function parseMermaidToGroupedIndicators(mermaidCode) {
  const relations = parseMermaidToRelations(mermaidCode);
  const groups = {};
  relations.forEach(rel => {
    const key = rel.fromLabel;
    if (!groups[key]) {
      groups[key] = {
        fromLabel: rel.fromLabel,
        fromDesc: rel.fromDesc,
        fromImportance: rel.fromImportance,
        edges: []
      };
    }
    groups[key].edges.push({
      toLabel: rel.toLabel,
      toDesc: rel.toDesc,
      toImportance: rel.toImportance,
      edgeLabel: rel.edgeLabel,
      edgeImportance: rel.edgeImportance
    });
  });
  return groups;
}
// .mmd 파일 파싱 전용 JS (중요도 지원)

function parseMermaidToRelations(mermaidCode) {
  if (typeof window !== 'undefined') {
    window.parseMermaidToRelations = parseMermaidToRelations;
  }
  if (typeof window !== 'undefined') {
    window.parseMermaidToRelations = parseMermaidToRelations;
  }
  const relations = [];
  const nodeLabelMap = new Map();
  const nodeMetaMap = new Map();
  try {
    console.log('[Mermaid 파서] 입력 코드 일부:', (mermaidCode || '').slice(0, 200));
    // 주석에서 노드 설명/중요도 추출 (%% A: 설명, 중요)
    const commentRegex = /^%%\s*([A-Za-z0-9_]+):\s*(.*?)(?:,\s*(중요|보통|낮음))?$/gm;
    let commentMatch;
    while ((commentMatch = commentRegex.exec(mermaidCode || '')) !== null) {
      const nodeId = (commentMatch[1] || '').trim();
      const desc = (commentMatch[2] || '').trim();
      const importance = (commentMatch[3] || '보통').trim();
      if (nodeId) {
        nodeMetaMap.set(nodeId, { desc, importance });
      }
    }
    console.log('[Mermaid 파서] 주석 기반 노드 메타:', Array.from(nodeMetaMap.entries()));

    const normalized = (mermaidCode || '')
      .replace(/^```.*$/gm, '')
      .replace(/%%.*$/gm, '')
      .replace(/\/\/.*$/gm, '')
      .replace(/\r/g, '');

    // 노드 정의 추출 (ID[라벨] 또는 ID{라벨}만, ( )는 무시, id에 한글/특수문자/공백도 허용)
    const nodeDefRegex = /([^\s\[\{]+)\s*([\[{])(.*?)[\]}]/g;
    let nodeMatch;
    while ((nodeMatch = nodeDefRegex.exec(normalized)) !== null) {
      const nodeId = (nodeMatch[1] || '').trim();
      let nodeLabel = (nodeMatch[3] || '').trim();
      let desc = '';
      // label이 *_설명: ... 형태면 label/desc 분리
      const descMatch = nodeLabel.match(/^(.*?_설명):\s*(.+)$/);
      if (descMatch) {
        nodeLabel = descMatch[1];
        desc = descMatch[2];
      }
      const meta = nodeMetaMap.get(nodeId) || { desc: '', importance: '보통' };
      if (nodeId && nodeLabel) {
        nodeLabelMap.set(nodeId, { label: nodeLabel, desc: desc || meta.desc, importance: meta.importance });
      }
    }
    // 설명 노드(지표별 그룹화 배열)만 사용하여 출력
    const descArray = parseDescriptionNodesGroupedByIndicator(mermaidCode);
    if (descArray.length > 0) {
      console.log('[Mermaid 파서] 설명 노드(그룹화 배열):', descArray);
    }

    // 각 줄을 순회하며 다양한 Mermaid 에지 표기법 robust 파싱
    const lines = normalized.split('\n');
    for (const line of lines) {
      // 1. A -- [중요] --> B
      let m = line.match(/^\s*([A-Za-z0-9_]+)\s*--\s*\[\s*(중요|보통|낮음)\s*\]\s*--+>\s*([A-Za-z0-9_]+)\s*$/);
      if (m) {
        const fromId = m[1], edgeImportance = m[2], toId = m[3];
        const fromNode = nodeLabelMap.get(fromId) || { label: fromId, desc: '', importance: '보통' };
        const toNode = nodeLabelMap.get(toId) || { label: toId, desc: '', importance: '보통' };
        relations.push({
          fromLabel: fromNode.label,
          fromDesc: fromNode.desc,
          fromImportance: fromNode.importance,
          toLabel: toNode.label,
          toDesc: toNode.desc,
          toImportance: toNode.importance,
          edgeLabel: '',
          edgeImportance: edgeImportance
        });
        continue;
      }
      // 2. A -- [라벨][중요] --> B
      m = line.match(/^\s*([A-Za-z0-9_]+)\s*--\s*\[([^\]]*?)\]\s*\[\s*(중요|보통|낮음)\s*\]\s*--+>\s*([A-Za-z0-9_]+)\s*$/);
      if (m) {
        const fromId = m[1], edgeLabel = m[2], edgeImportance = m[3], toId = m[4];
        const fromNode = nodeLabelMap.get(fromId) || { label: fromId, desc: '', importance: '보통' };
        const toNode = nodeLabelMap.get(toId) || { label: toId, desc: '', importance: '보통' };
        relations.push({
          fromLabel: fromNode.label,
          fromDesc: fromNode.desc,
          fromImportance: fromNode.importance,
          toLabel: toNode.label,
          toDesc: toNode.desc,
          toImportance: toNode.importance,
          edgeLabel: edgeLabel,
          edgeImportance: edgeImportance
        });
        continue;
      }
      // 3. A -- [라벨] --> B
      m = line.match(/^\s*([A-Za-z0-9_]+)\s*--\s*\[([^\]]*?)\]\s*--+>\s*([A-Za-z0-9_]+)\s*$/);
      if (m) {
        const fromId = m[1], edgeLabel = m[2], toId = m[3];
        const fromNode = nodeLabelMap.get(fromId) || { label: fromId, desc: '', importance: '보통' };
        const toNode = nodeLabelMap.get(toId) || { label: toId, desc: '', importance: '보통' };
        relations.push({
          fromLabel: fromNode.label,
          fromDesc: fromNode.desc,
          fromImportance: fromNode.importance,
          toLabel: toNode.label,
          toDesc: toNode.desc,
          toImportance: toNode.importance,
          edgeLabel: edgeLabel,
          edgeImportance: '보통'
        });
        continue;
      }
      // 4. A --> B, A -> B
      m = line.match(/^\s*([A-Za-z0-9_]+)\s*-+>\s*([A-Za-z0-9_]+)\s*$/);
      if (m) {
        const fromId = m[1], toId = m[2];
        const fromNode = nodeLabelMap.get(fromId) || { label: fromId, desc: '', importance: '보통' };
        const toNode = nodeLabelMap.get(toId) || { label: toId, desc: '', importance: '보통' };
        relations.push({
          fromLabel: fromNode.label,
          fromDesc: fromNode.desc,
          fromImportance: fromNode.importance,
          toLabel: toNode.label,
          toDesc: toNode.desc,
          toImportance: toNode.importance,
          edgeLabel: '',
          edgeImportance: '보통'
        });
        continue;
      }
    }
    console.log('[Mermaid 파서] 에지 추출 결과:', relations);
    return relations;
  } catch (err) {
    console.error('[Mermaid 파서] 파싱 중 예외 발생:', err, { mermaidCode });
    return [];
  }
}

/**
 * website_diagram.json 파싱 (노드명이 랜덤/가변이어도 robust)
 * @param {Object} jsonData - website_diagram.json 내용 (edges 배열 포함)
 * @returns {Object} { nodes: [...], edges: [...] }
 */
function parseDiagramJsonToGraph(jsonData) {
  if (!jsonData || !Array.isArray(jsonData.edges)) return { nodes: [], edges: [] };
  // 노드명 집합 만들기
  const nodeSet = new Set();
  jsonData.edges.forEach(edge => {
    nodeSet.add(edge.source);
    nodeSet.add(edge.target);
  });
  const nodes = Array.from(nodeSet).map(name => ({ id: name }));
  // edges 그대로 importance 포함 반환
  const edges = jsonData.edges.map(e => ({
    source: e.source,
    target: e.target,
    importance: e.importance
  }));
  return { nodes, edges };
}
