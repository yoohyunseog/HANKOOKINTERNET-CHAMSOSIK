"""
네이버 크리에이터 트렌드 데이터 뷰어
- 수집된 데이터를 HTML로 표시
- 시계열 그래프 생성
"""

import json
import os
from datetime import datetime
from pathlib import Path
import pandas as pd

def load_latest_data(data_dir="data/naver_creator_trends"):
    """최신 데이터 로드"""
    latest_file = os.path.join(data_dir, "latest_trend_data.json")
    
    if not os.path.exists(latest_file):
        print("❌ 데이터 파일이 없습니다.")
        return None
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_all_data(data_dir="data/naver_creator_trends"):
    """모든 데이터 로드 (시계열 분석용)"""
    data_files = sorted(Path(data_dir).glob("trend_data_*.json"))
    all_data = []
    
    for file in data_files:
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_data.append(data)
    
    return all_data

def generate_html_report(data, output_file="data/naver_creator_trends/report.html"):
    """HTML 리포트 생성"""
    
    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>네이버 크리에이터 트렌드 분석 리포트</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <style>
        body {{
            background: #f8f9fa;
            font-family: 'Noto Sans KR', sans-serif;
        }}
        .header {{
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            color: white;
            padding: 30px 0;
            margin-bottom: 30px;
        }}
        .data-card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .keyword-badge {{
            background: #e0f2fe;
            color: #0284c7;
            padding: 5px 12px;
            border-radius: 20px;
            margin: 5px;
            display: inline-block;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #1e40af;
        }}
        .trend-item {{
            border-left: 4px solid #3b82f6;
            padding: 15px;
            margin: 10px 0;
            background: #f8fafc;
        }}
    </style>
</head>
<body>
    <div class="header text-center">
        <h1><i class="bi bi-graph-up-arrow"></i> 네이버 크리에이터 트렌드 분석</h1>
        <p class="mb-0">수집 시간: {data.get('collection_time', 'N/A')}</p>
    </div>

    <div class="container">
        <!-- 통계 요약 -->
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="data-card text-center">
                    <i class="bi bi-collection text-primary" style="font-size: 2em;"></i>
                    <h3 class="mt-2">총 항목</h3>
                    <div class="metric-value">{data.get('total_items', 0)}</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="data-card text-center">
                    <i class="bi bi-tags text-success" style="font-size: 2em;"></i>
                    <h3 class="mt-2">키워드</h3>
                    <div class="metric-value">{sum(len(item.get('keywords', [])) for item in data.get('trend_data', []))}</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="data-card text-center">
                    <i class="bi bi-clock-history text-warning" style="font-size: 2em;"></i>
                    <h3 class="mt-2">블로그 ID</h3>
                    <div class="metric-value" style="font-size: 1.5em;">{data.get('blog_id', 'N/A')}</div>
                </div>
            </div>
        </div>

        <!-- 트렌드 데이터 -->
        <div class="data-card">
            <h2 class="mb-4"><i class="bi bi-fire"></i> 트렌드 항목</h2>
            
            {"".join(f'''
            <div class="trend-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h4>#{item.get('index', 'N/A')} - {item.get('title', '제목 없음')}</h4>
                        <div class="my-3">
                            {"".join(f'<span class="keyword-badge"><i class="bi bi-hash"></i> {kw}</span>' for kw in item.get('keywords', []))}
                        </div>
                        <div class="small text-muted">
                            <i class="bi bi-clock"></i> {item.get('timestamp', 'N/A')}
                        </div>
                        {"".join(f'<div class="mt-2"><strong>{k}:</strong> {v}</div>' for k, v in item.get('metrics', {}).items())}
                    </div>
                </div>
                <div class="mt-3 p-3 bg-light rounded">
                    <strong>원본 데이터:</strong>
                    <pre class="mb-0 small">{item.get('raw_text', 'N/A')[:500]}</pre>
                </div>
            </div>
            ''' for item in data.get('trend_data', []))}
        </div>

        <!-- 상세 데이터 -->
        {"".join(f'''
        <div class="data-card">
            <h3><i class="bi bi-table"></i> 테이블 데이터 #{idx + 1}</h3>
            <div class="table-responsive">
                <table class="table table-striped">
                    {"".join(f'<tr>{"".join(f"<td>{cell}</td>" for cell in row)}</tr>' for row in table)}
                </table>
            </div>
        </div>
        ''' for idx, table in enumerate(data.get('detailed_data', {}).get('tables', [])))}
        
        {"".join(f'''
        <div class="data-card">
            <h3><i class="bi bi-list-ul"></i> 리스트 데이터 #{idx + 1}</h3>
            <ul class="list-group">
                {"".join(f'<li class="list-group-item">{item}</li>' for item in lst)}
            </ul>
        </div>
        ''' for idx, lst in enumerate(data.get('detailed_data', {}).get('lists', [])))}

        <!-- 푸터 -->
        <div class="text-center my-5">
            <p class="text-muted">
                Generated by Naver Creator Trend Analyzer<br>
                <small>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>
            </p>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML 리포트 생성: {output_file}")
    return output_file

def main():
    """메인 함수"""
    print("\n📊 트렌드 데이터 뷰어\n")
    
    # 데이터 로드
    data = load_latest_data()
    
    if not data:
        print("사용 가능한 데이터가 없습니다. 먼저 데이터를 수집하세요.")
        return
    
    # HTML 리포트 생성
    report_file = generate_html_report(data)
    
    # 브라우저에서 열기
    import webbrowser
    webbrowser.open(f'file:///{os.path.abspath(report_file)}')
    print(f"\n🌐 브라우저에서 리포트를 열었습니다.")

if __name__ == "__main__":
    main()
