#!/usr/bin/env python3
"""
블로그 포스트에 view-tracker.js 스크립트와 조회수 표시 요소를 추가합니다.
"""

import os
import re
from pathlib import Path


def find_workspace_root() -> Path:
    for path in [Path(__file__).resolve().parent, *Path(__file__).resolve().parents]:
        if (path / "web").exists() and (path / "search").exists():
            return path
    return Path(__file__).resolve().parents[6]


ROOT = find_workspace_root()
POSTS_DIR = ROOT / "web" / "public" / "한국인터넷.한국" / "참소식.com" / "blog" / "posts"


def add_view_tracker_to_post(file_path: Path) -> bool:
    """포스트 파일에 view-tracker.js와 조회수 표시 요소를 추가합니다."""
    try:
        content = file_path.read_text(encoding="utf-8")
        
        # 이미 view-tracker.js가 있는지 확인
        if "view-tracker.js" in content:
            print(f"  ✓ 이미 view-tracker.js 포함됨: {file_path.name}")
            return False
        
        # 1. </body> 앞에 view-tracker.js 스크립트 추가
        view_tracker_script = '''
  <script src="../js/view-tracker.js"></script>
  <script>
    document.addEventListener('DOMContentLoaded', function() {
      if (typeof BlogViewTracker !== 'undefined') {
        BlogViewTracker.trackPostVisit();
        const viewCountEl = document.getElementById('view-count');
        if (viewCountEl) {
          const postHref = window.location.pathname.split('/').pop();
          const count = BlogViewTracker.getViewCount('posts/' + postHref);
          viewCountEl.textContent = BlogViewTracker.formatViews(count);
        }
      }
    });
  </script>
</body>'''
        
        content = content.replace('</body>', view_tracker_script)
        
        # 2. CSS에 .post-views 스타일 추가 (없는 경우)
        if '.post-views' not in content:
            # .post-meta 스타일 뒤에 .post-views 스타일 추가
            post_views_css = '''
    .post-views {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--muted);
      font-size: 13px;
      padding: 4px 10px;
    }
    .post-views::before {
      content: '👁';
      font-size: 12px;
    }
'''
            # </style> 앞에 추가
            content = content.replace('</style>', post_views_css + '</style>')
        
        # 3. post-meta에 조회수 표시 요소 추가
        # 이미 view-count ID가 있는지 확인
        if 'id="view-count"' not in content:
            # post-meta div 찾기
            meta_pattern = r'(<div class="post-meta"[^>]*>.*?</div>)'
            match = re.search(meta_pattern, content, re.DOTALL)
            
            if match:
                meta_content = match.group(1)
                # 마지막 </span> 뒤에 조회수 추가
                if '</span>' in meta_content:
                    # 닫는 </div> 앞에 추가
                    new_meta = meta_content.replace(
                        '</div>',
                        '        <span class="post-views" id="view-count">조회수 로딩중...</span>\n      </div>'
                    )
                    content = content.replace(meta_content, new_meta)
        
        # 파일 저장
        file_path.write_text(content, encoding="utf-8")
        print(f"  ✓ view-tracker.js 추가됨: {file_path.name}")
        return True
        
    except Exception as e:
        print(f"  ✗ 오류 발생: {file_path.name} - {e}")
        return False


def main():
    """모든 포스트 파일에 view-tracker.js를 추가합니다."""
    print("=" * 60)
    print("블로그 포스트에 view-tracker.js 추가 중...")
    print("=" * 60)
    
    if not POSTS_DIR.exists():
        print(f"✗ 포스트 디렉토리를 찾을 수 없습니다: {POSTS_DIR}")
        return
    
    html_files = list(POSTS_DIR.glob("*.html"))
    
    if not html_files:
        print("✗ HTML 파일을 찾을 수 없습니다.")
        return
    
    print(f"\n총 {len(html_files)}개의 포스트 파일을 처리합니다.\n")
    
    updated_count = 0
    for html_file in sorted(html_files):
        if add_view_tracker_to_post(html_file):
            updated_count += 1
    
    print(f"\n{'=' * 60}")
    print(f"완료! {updated_count}개 파일 업데이트됨")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()