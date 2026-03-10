// .mmd 파일 파싱 전용 JS (중요도 지원)
// 사용: import { parseMermaidToRelations } from './parseMermaidMmd.js';

export function parseMermaidToRelations(mermaidCode) {
  const relations = [];
  const nodeLabelMap = new Map();

  const normalized = (mermaidCode || '')
    .replace(/^```.*$/gm, '')
    .replace(/%%.*$/gm, '')
    .replace(/\/\/.*$/gm, '')
    .replace(/\r/g, '');

  // 노드 정의 추출 (ID, 라벨, 중요도)
  const nodeDefRegex = /([A-Za-z0-9_]+)\s*\[(.*?)\](\[(중요|보통|낮음)\])?/g;
  let nodeMatch;
  while ((nodeMatch = nodeDefRegex.exec(normalized)) !== null) {
    const nodeId = (nodeMatch[1] || '').trim();
    const nodeLabel = (nodeMatch[2] || '').trim();
    const importance = (nodeMatch[4] || '보통').trim();
    if (nodeId && nodeLabel) {
      nodeLabelMap.set(nodeId, { label: nodeLabel, importance });
    }
  }

  // 필터링에 사용할 불필요한 키워드 목록
  const ignorePatterns = [
    /^\|$/,
    /^키워드[:：]/,
    /^이슈 맵 바로가기[:：]/
  ];
  const isIgnored = (label) => {
    if (!label) return false;
    return ignorePatterns.some((pat) => pat.test(label.trim()));
  };

  // 에지 추출 (A -> B[라벨][중요])
  const edgeRegex = /^([A-Za-z0-9_]+)\s*->\s*([A-Za-z0-9_]+)\s*\[(.*?)\](\[(중요|보통|낮음)\])?/gm;
  let edgeMatch;
  while ((edgeMatch = edgeRegex.exec(normalized)) !== null) {
    const fromId = (edgeMatch[1] || '').trim();
    const toId = (edgeMatch[2] || '').trim();
    const toLabel = (edgeMatch[3] || '').trim();
    const toImportance = (edgeMatch[5] || '보통').trim();
    const fromNode = nodeLabelMap.get(fromId) || { label: fromId, importance: '보통' };
    const toNode = { label: toLabel, importance: toImportance };
    relations.push({
      fromLabel: fromNode.label,
      fromImportance: fromNode.importance,
      toLabel: toNode.label,
      toImportance: toNode.importance
    });
  }
  return relations;
}

/**
 * website_diagram.json 파싱 (노드명이 랜덤/가변이어도 robust)
 * @param {Object} jsonData - website_diagram.json 내용 (edges 배열 포함)
 * @returns {Object} { nodes: [...], edges: [...] }
 */
export function parseDiagramJsonToGraph(jsonData) {
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
