@echo off
chcp 65001 > nul
setlocal

:: ========================================
:: YouTube 지속 모니터링 시스템 실행
:: ========================================

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

:: Python 실행 파일 경로 찾기
set PYTHON_EXE=%SCRIPT_DIR%..\..venv\Scripts\python.exe
if exist "%PYTHON_EXE%" goto :python_found

set PYTHON_EXE=E:\Ai project\사이트\.venv\Scripts\python.exe
if exist "%PYTHON_EXE%" goto :python_found

:: 시스템 Python 찾기
where python >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_EXE=python
    echo [INFO] Using system Python
    goto :python_found
)

echo [ERROR] Python not found. Please install Python or check virtual environment path.
echo [INFO] Expected venv location: E:\Ai project\사이트\.venv\Scripts\python.exe
pause
exit /b 1

:python_found
echo [INFO] Python: %PYTHON_EXE%

:: Ollama 모델 설정 (환경변수로 커스터마이징 가능)
if not defined OLLAMA_MODEL set OLLAMA_MODEL=kimi-k2.5:120b-cloud

:: 키인드 개수 (기본: 3개)
if not defined KEYWORD_COUNT set KEYWORD_COUNT=3

:: 키워드당 영상 수 (기본: 10개)
if not defined VIDEO_LIMIT set VIDEO_LIMIT=10

:: 모니터링 간격 (기본: 30분)
if not defined MONITOR_INTERVAL set MONITOR_INTERVAL=0

:: 자막 분석 활성화 (기본: 활성화, 비활성화하려면 set ANALYZE_SUBTITLES=0)
if not defined ANALYZE_SUBTITLES set ANALYZE_SUBTITLES=1
if not defined BLOCK_KOREAN_PERSON_NAMES set BLOCK_KOREAN_PERSON_NAMES=1

:: 분석 소스 (youtube만 사용 - 외부 검색 엔진 제거됨)
if not defined ANALYSIS_SOURCE set ANALYSIS_SOURCE=youtube

:: YouTube 봇 체크 우회용 쿠키 설정 (선택)
:: 예시1) set USE_BROWSER_COOKIES=1
:: 예시2) set YTDLP_BROWSER=edge
:: 예시3) set YTDLP_COOKIES_FILE=E:\cookies\youtube_cookies.txt
if not defined USE_BROWSER_COOKIES set USE_BROWSER_COOKIES=0
if not defined YTDLP_BROWSER set YTDLP_BROWSER=chrome

:: 참소식 DB 저장 설정
if not defined DATABASE_SAVE_ENABLED set DATABASE_SAVE_ENABLED=1
if not defined DATABASE_BASE_URL set DATABASE_BASE_URL=https://xn--9l4b4xi9r.com
if not defined DATABASE_OPEN_PAGE set DATABASE_OPEN_PAGE=1

echo.
echo ================================================
echo    YouTube Continuous Monitoring System
echo ================================================
echo.
echo [Configuration]
echo - Ollama Model: %OLLAMA_MODEL%
echo - Keywords Source: monitor_keywords.txt (all lines + fixed keyword)
echo - Keywords Count Option: %KEYWORD_COUNT% (fallback only)
echo - Video Limit: %VIDEO_LIMIT%/keyword
echo - Subtitle Analysis: %ANALYZE_SUBTITLES%
echo - Block Korean Person Names: %BLOCK_KOREAN_PERSON_NAMES%
echo - Analysis Source: YouTube 자막 추출 (외부 검색 엔진 미사용)
echo - Browser Cookies: %USE_BROWSER_COOKIES% (%YTDLP_BROWSER%)
if defined YTDLP_COOKIES_FILE echo - Cookies File: %YTDLP_COOKIES_FILE%
echo - Database Save: %DATABASE_SAVE_ENABLED% (%DATABASE_BASE_URL%)
echo - Database Open Page: %DATABASE_OPEN_PAGE%
echo - Monitor Interval: %MONITOR_INTERVAL% minutes
echo.
echo [Features]
echo - Manual keyword loading from monitor_keywords.txt
echo - JSON and Markdown reports
echo - Reports saved to: reports/YYYY-MM-DD/
echo - Fixed keyword: "Today's Major News"
echo - Press Ctrl+C to stop
echo.
echo ================================================
echo.

:: 자막 분석 옵션 설정
set SUBTITLE_OPT=--subtitles
if "%ANALYZE_SUBTITLES%"=="0" set SUBTITLE_OPT=--no-subtitles

:: 지속 모니터링 실행
"%PYTHON_EXE%" continuous_youtube_monitor.py --once ^
    --model=%OLLAMA_MODEL% ^
    --keywords=%KEYWORD_COUNT% ^
    --videos=%VIDEO_LIMIT% ^
    --interval=%MONITOR_INTERVAL% ^
    --analysis-source=%ANALYSIS_SOURCE% ^
    %SUBTITLE_OPT%

if errorlevel 1 (
    echo.
    echo [ERROR] 모니터링 실행 중 오류 발생
    echo.
    if "%LOOP_MODE%"=="1" (
        exit /b 1
    ) else (
        pause
        exit /b 1
    )
)

echo.
echo [INFO] 모니터링 종료
if "%LOOP_MODE%"=="1" (
    exit /b 0
)
pause
