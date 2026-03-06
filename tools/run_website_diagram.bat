@echo off
chcp 65001 > nul
title 웹사이트 다이어그램 자동 생성 도구

echo ========================================
echo 🌐 웹사이트 구조 다이어그램 생성 도구
echo ========================================
echo.
echo Ollama AI가 웹사이트를 분석하여
echo Mermaid 다이어그램 HTML을 자동 생성합니다.
echo.
echo ========================================
echo.

REM Python 가상환경 활성화
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo ✅ Python 가상환경 활성화됨
) else (
    echo ⚠️  가상환경을 찾을 수 없습니다. 시스템 Python 사용
)

echo.
echo 【기본 사용법】
echo   Enter 키만 누르면 참소식.com을 분석합니다
echo   다른 URL을 입력하면 해당 사이트를 분석합니다
echo.
set /p USER_URL="분석할 웹사이트 URL (기본: https://xn--9l4b4xi9r.com): "

REM 기본값 설정
if "%USER_URL%"=="" (
    set TARGET_URL=https://xn--9l4b4xi9r.com
    echo.
    echo 📍 참소식.com을 분석합니다...
) else (
    set TARGET_URL=%USER_URL%
    echo.
    echo 📍 %TARGET_URL%을 분석합니다...
)

echo.
echo ========================================
echo 🚀 다이어그램 생성 시작
echo ========================================
echo.

REM Python 스크립트 실행
python tools\generate_website_diagram.py "%TARGET_URL%"

echo.
echo ========================================
if %ERRORLEVEL% EQU 0 (
    echo ✅ 다이어그램 생성 완료!
    echo.
    echo 생성된 HTML 파일을 브라우저로 여시겠습니까?
    set /p OPEN_FILE="열기 (Y/N, 기본: Y): "
    
    if /i "!OPEN_FILE!"=="" set OPEN_FILE=Y
    if /i "!OPEN_FILE!"=="Y" (
        echo.
        echo 🌐 브라우저에서 파일을 여는 중...
        for /f "delims=" %%f in ('dir /b /od website_diagram_*.html 2^>nul') do set LAST_FILE=%%f
        if defined LAST_FILE (
            start "" "!LAST_FILE!"
        ) else (
            echo ⚠️  HTML 파일을 찾을 수 없습니다.
        )
    )
) else (
    echo ❌ 다이어그램 생성 실패
    echo.
    echo 문제 해결 방법:
    echo   1. Ollama 서비스가 실행 중인지 확인하세요
    echo   2. 인터넷 연결을 확인하세요
    echo   3. URL이 올바른지 확인하세요
)
echo ========================================
echo.

pause
