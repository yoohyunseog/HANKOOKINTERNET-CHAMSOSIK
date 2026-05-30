#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YouTube 자막 추출 함수 수정 스크립트"""

import re

# 파일 읽기
with open('youtube/continuous_youtube_monitor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 새 함수 정의
new_function = '''def analyze_with_youtube(video_id: str, video_title: str, keyword: str, model: str, upload_date: str = "") -> str:
    """YouTube 자막 추출 후 분석 (youtube-transcript-api + yt-dlp 사용, Selenium 없음)"""
    import time

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 업로드일 확인 (오늘 날짜만 허용)
    verified_upload_date = resolve_upload_date_by_video_id(video_id)
    if verified_upload_date:
        if not is_today_only(verified_upload_date):
            log_subtitle_failure(
                video_id,
                video_title,
                "youtube",
                f"스킵: verified_upload_date={verified_upload_date}, now={now_str}, rule=today_only",
                upload_date=verified_upload_date,
            )
            return "오늘 날짜 영상 아님(건너뜀)"
    elif upload_date and not is_today_only(upload_date):
        log_subtitle_failure(
            video_id,
            video_title,
            "youtube",
            f"스킵(검색일자 기준): upload_date={upload_date}, now={now_str}, rule=today_only",
            upload_date=upload_date,
        )
        return "오늘 날짜 영상 아님(건너뜀)"
    
    print(f"            [자막 추출] API 방식으로 시도 (youtube-transcript-api + yt-dlp)")
    
    try:
        # youtube-transcript-api + yt-dlp로 자막 추출
        subtitles_text = get_video_subtitles(video_id)
        
        if subtitles_text and len(subtitles_text) >= 50 and subtitles_text not in {"자막 없음", "자막 요청 제한(429)", "자막 추출 실패"}:
            print(f"            [자막 추출] 성공, 자막 길이: {len(subtitles_text)}자")
            return analyze_subtitles_with_ollama(subtitles_text, model, video_title)
        
        # 실패 시 로그 기록
        fail_reason = "자막 없음 또는 길이 부족"
        if subtitles_text in {"자막 없음", "자막 요청 제한(429)", "자막 추출 실패"}:
            fail_reason = subtitles_text
        
        print(f"            [자막 추출] 실패: {fail_reason}")
        log_subtitle_failure(
            video_id,
            video_title,
            "youtube",
            f"API 방식 실패: {fail_reason}",
            upload_date=verified_upload_date or upload_date,
        )
        return "유튜브 자막 추출 실패"
        
    except Exception as e:
        print(f"            [자막 추출] 예외 발생: {str(e)[:200]}")
        log_subtitle_failure(
            video_id,
            video_title,
            "youtube",
            f"자막 추출 예외: {str(e)[:300]}",
            upload_date=verified_upload_date or upload_date,
        )
        return "유튜브 자막 추출 실패"


'''

# 함수 찾기 및 교체
pattern = r'def analyze_with_youtube\(video_id: str, video_title: str, keyword: str, model: str, upload_date: str = ""\) -> str:.*?(?=\ndef collect_youtube_data\()'
replacement = new_function

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# 파일 쓰기
with open('youtube/continuous_youtube_monitor.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Function replaced successfully')