@echo off
chcp 65001 >nul
echo ========================================
echo   Vatican 봇 전체 실행 (1회)
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
echo [실행 순서]
echo 1. Vatican RSS 봇 (뉴스 수집)
echo 2. 기사 요약 봇 (AI 요약)
echo 3. 유튜브 영상 검색 봇 (관련 영상)
echo 4. Hillsong Worship 영상 검색 봇 (워십 영상)
echo.

pause

echo ========================================
echo   [%date% %time%] 봇 실행 시작
echo ========================================
echo.

REM 1. Vatican RSS 봇 실행
echo [1/4] Vatican RSS 봇 실행 중...
python vatican_rss_bot.py
if %errorlevel% neq 0 (
    echo [ERROR] Vatican RSS 봇 실행 실패
) else (
    echo [OK] Vatican RSS 봇 완료
)
echo.

REM 2. 기사 요약 봇 실행
echo [2/4] 기사 요약 봇 실행 중...
python article_summarizer.py
if %errorlevel% neq 0 (
    echo [ERROR] 기사 요약 봇 실행 실패
) else (
    echo [OK] 기사 요약 봇 완료
)
echo.

REM 3. 유튜브 영상 검색 봇 실행
echo [3/4] 유튜브 영상 검색 봇 실행 중...
python youtube_search_bot.py
if %errorlevel% neq 0 (
    echo [ERROR] 유튜브 영상 검색 봇 실행 실패
) else (
    echo [OK] 유튜브 영상 검색 봇 완료
)
echo.

REM 4. Hillsong Worship 영상 검색 봇 실행
echo [4/4] Hillsong Worship 영상 검색 봇 실행 중...
python hillsong_search_bot.py
if %errorlevel% neq 0 (
    echo [ERROR] Hillsong Worship 영상 검색 봇 실행 실패
) else (
    echo [OK] Hillsong Worship 영상 검색 봇 완료
)
echo.

echo ========================================
echo   [%date% %time%] 모든 봇 실행 완료
echo ========================================
echo.

REM 5. 웹 서버 업로드
echo [5/5] 웹 서버 업로드 중...
echo.

set "VATICAN_DIR=%~dp0.."
set "SERVER_USER=root"
set "SERVER_HOST=211.45.162.155"
set "SERVER_PATH=/var/www/chamsosik/vatican"

echo Local:  %VATICAN_DIR%
echo Remote: %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%
echo.

REM 원격 디렉토리 준비
ssh "%SERVER_USER%@%SERVER_HOST%" "mkdir -p '%SERVER_PATH%'"
if errorlevel 1 (
    echo [ERROR] 원격 디렉토리 준비 실패
) else (
    echo [OK] 원격 디렉토리 준비 완료
)

REM 파일 업로드
scp -r "%VATICAN_DIR%\*.json" "%VATICAN_DIR%\*.md" "%SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/"
if errorlevel 1 (
    echo [ERROR] 업로드 실패
) else (
    echo [OK] 웹 서버 업로드 완료
)

echo.
echo 생성된 파일:
echo - vatican_rss_raw.json
echo - vatican_rss_translated.json
echo - vatican_news_summary.md
echo - article_news.json
echo - article_news_summary.md
echo - youtube_videos.json
echo - youtube_videos_summary.md
echo - hillsong_videos.json
echo - hillsong_videos_summary.md
echo.

pause