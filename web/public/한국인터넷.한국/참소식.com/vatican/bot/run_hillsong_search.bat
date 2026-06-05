@echo off
chcp 65001 >nul
echo ========================================
echo   Hillsong Worship 영상 검색 봇 실행
echo ========================================
echo.

cd /d "%~dp0"

REM 가상환경 활성화 (프로젝트 루트)
if exist "..\..\..\..\..\..\.venv\Scripts\activate.bat" (
    call ..\..\..\..\..\..\.venv\Scripts\activate.bat
    echo [OK] 가상환경 활성화
) else (
    echo [INFO] 가상환경 없이 실행
)

echo.
echo [실행] Hillsong Worship 영상 검색 중...
python hillsong_search_bot.py

echo.
echo ========================================
echo   완료! 결과는 상위 폴더에 저장됩니다.
echo   - hillsong_videos.json
echo   - hillsong_videos_summary.md
echo ========================================
pause