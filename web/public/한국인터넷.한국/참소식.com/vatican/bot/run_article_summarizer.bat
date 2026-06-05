@echo off
chcp 65001 >nul
echo ========================================
echo   최신 기사 요약 AI 실행
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
echo [실행] 기본 모드 (사이트당 3개 기사)...
python article_summarizer.py --max 3

echo.
echo ========================================
echo   완료! 결과는 상위 폴더에 저장됩니다.
echo   - article_news_*.json
echo   - article_news.json (최신)
echo   - article_news_summary.md (마크다운)
echo ========================================
pause