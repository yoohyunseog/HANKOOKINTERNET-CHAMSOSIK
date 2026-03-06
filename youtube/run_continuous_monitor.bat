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
if not defined OLLAMA_MODEL set OLLAMA_MODEL=gemma3:4b

:: 키인드 개수 (기본: 3개)
if not defined KEYWORD_COUNT set KEYWORD_COUNT=3

:: 키워드당 영상 수 (기본: 10개)
if not defined VIDEO_LIMIT set VIDEO_LIMIT=10

:: 모니터링 간격 (기본: 30분)
if not defined MONITOR_INTERVAL set MONITOR_INTERVAL=0

:: 자막 분석 활성화 (기본: 활성화, 비활성화하려면 set ANALYZE_SUBTITLES=0)
if not defined ANALYZE_SUBTITLES set ANALYZE_SUBTITLES=1

:: 분석 소스 (subtitles|google|bing|naver|zum|youtube|auto)
if not defined ANALYSIS_SOURCE set ANALYSIS_SOURCE=youtube

:: ChromeDriver 검색 설정 (ANALYSIS_SOURCE=google|bing|naver|zum|youtube일 때 사용)
if not defined SEARCH_MARKET set SEARCH_MARKET=ko-KR
if not defined SEARCH_COUNT set SEARCH_COUNT=5

:: 검색 화면 표시 (0=화면 보기, 1=백그라운드 모드)
if not defined SHOW_SEARCH_WINDOW set SHOW_SEARCH_WINDOW=0
if %SHOW_SEARCH_WINDOW%==0 (
    set SEARCH_HEADLESS=0
) else (
    set SEARCH_HEADLESS=1
)

:: 선택: 크롬 실행 파일 경로 지정
:: set CHROME_BINARY=C:\Program Files\Google\Chrome\Application\chrome.exe

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
echo - Analysis Source: %ANALYSIS_SOURCE%
if "%ANALYSIS_SOURCE%"=="google" (
    if %SHOW_SEARCH_WINDOW%==0 (
        echo - Google Search: ON (크롬 화면 표시)
    ) else (
        echo - Google Search: OFF (백그라운드 모드)
    )
)
if "%ANALYSIS_SOURCE%"=="bing" (
    if %SHOW_SEARCH_WINDOW%==0 (
        echo - Bing Search: ON (크롬 화면 표시)
    ) else (
        echo - Bing Search: OFF (백그라운드 모드)
    )
)
if "%ANALYSIS_SOURCE%"=="naver" (
    if %SHOW_SEARCH_WINDOW%==0 (
        echo - Naver Search: ON (크롬 화면 표시)
    ) else (
        echo - Naver Search: OFF (백그라운드 모드)
    )
)
if "%ANALYSIS_SOURCE%"=="zum" (
    if %SHOW_SEARCH_WINDOW%==0 (
        echo - Zum Search: ON (크롬 화면 표시)
    ) else (
        echo - Zum Search: OFF (백그라운드 모드)
    )
)
if "%ANALYSIS_SOURCE%"=="youtube" (
    if %SHOW_SEARCH_WINDOW%==0 (
        echo - YouTube Subtitle: ON (크롬 화면 표시)
    ) else (
        echo - YouTube Subtitle: OFF (백그라운드 모드)
    )
)
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
"%PYTHON_EXE%" continuous_youtube_monitor.py ^
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
