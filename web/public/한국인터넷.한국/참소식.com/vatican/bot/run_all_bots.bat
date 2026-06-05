@echo off
chcp 65001 >nul
echo ========================================
echo   Vatican 봇 자동 실행 (반복 주기)
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
echo [실행 주기 설정]
echo 1. 1시간마다 실행 (기본)
echo 2. 30분마다 실행
echo 3. 2시간마다 실행
echo 4. 6시간마다 실행
echo 5. 12시간마다 실행
echo 6. 24시간마다 실행 (매일)
echo.

set /p interval="선택하세요 (1-6): "

if "%interval%"=="1" set wait_seconds=3600
if "%interval%"=="2" set wait_seconds=1800
if "%interval%"=="3" set wait_seconds=7200
if "%interval%"=="4" set wait_seconds=21600
if "%interval%"=="5" set wait_seconds=43200
if "%interval%"=="6" set wait_seconds=86400

if "%wait_seconds%"=="" set wait_seconds=3600

echo.
echo [선택된 주기] %wait_seconds%초마다 반복 실행
echo.

:loop
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
ssh "%SERVER_USER%@%SERVER_HOST%" "mkdir -p '%SERVER_PATH%'" 2>nul
if errorlevel 1 (
    echo [WARN] 원격 디렉토리 준비 실패 (계속 진행)
) else (
    echo [OK] 원격 디렉토리 준비 완료
)

REM 파일 업로드
scp -r "%VATICAN_DIR%\*.json" "%VATICAN_DIR%\*.md" "%SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/" 2>nul
if errorlevel 1 (
    echo [WARN] 업로드 실패 (계속 진행)
) else (
    echo [OK] 웹 서버 업로드 완료
)

echo.
echo ========================================
echo   [%date% %time%] 업로드 완료
echo ========================================
echo.
echo 다음 실행까지 %wait_seconds%초 대기...
echo 종료하려면 Ctrl+C를 누르세요.
echo.

REM 대기 (Windows에서는 timeout 사용)
timeout /t %wait_seconds% /nobreak >nul

goto loop