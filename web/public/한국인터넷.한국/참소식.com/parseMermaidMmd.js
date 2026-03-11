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
 */
function parseWebsiteFromDiagramJsonToGraph(jsonData) {
  if (!jsonData || !Array.isArray(jsonData.nodes) || !Array.isArray(jsonData.edges)) return { nodes: [], edges: [] };
  // nodes: id, type, name, value/text 등 모든 필드 유지
  const nodes = jsonData.nodes.map(node => ({ ...node }));
  // edges: source, target, label 등 모든 필드 유지
  const edges = jsonData.edges.map(edge => ({ ...edge }));
  return { nodes, edges };
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

    // 노드 정의 추출 (ID[라벨] 또는 ID{라벨}만, ( )는 무시)
    const nodeDefRegex = /([A-Za-z0-9_]+)\s*([\[{])(.*?)[\]}]/g;
    let nodeMatch;
    while ((nodeMatch = nodeDefRegex.exec(normalized)) !== null) {
      const nodeId = (nodeMatch[1] || '').trim();
      const nodeLabel = (nodeMatch[3] || '').trim();
      const meta = nodeMetaMap.get(nodeId) || { desc: '', importance: '보통' };
      if (nodeId && nodeLabel) {
        nodeLabelMap.set(nodeId, { label: nodeLabel, desc: meta.desc, importance: meta.importance });
      }
    }
    console.log('[Mermaid 파서] 노드 정의:', Array.from(nodeLabelMap.entries()));

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
