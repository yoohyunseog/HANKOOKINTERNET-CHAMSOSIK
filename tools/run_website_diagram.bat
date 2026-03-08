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

REM 작업 디렉토리를 프로젝트 루트로 변경
cd /d "%~dp0.."

REM Python 가상환경 활성화
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo ✅ Python 가상환경 활성화됨
) else (
    echo ⚠️  가상환경을 찾을 수 없습니다.
    echo.
    echo Python 가상환경을 생성하려면:
    echo   python -m venv .venv
    echo.
    pause
    exit /b 1
)

REM 항상 자동 실행 (URL 입력 없이 기본 대상 분석)
set TARGET_URL=https://xn--9l4b4xi9r.com
echo 🤖 자동 실행: 참소식.com을 분석합니다...

:start_generation

echo.
echo ========================================
echo 🚀 다이어그램 생성 시작
echo ========================================
echo.

REM Python 스크립트 실행 (이미 루트 디렉토리로 이동함)
python tools\generate_website_diagram.py "%TARGET_URL%"

echo.
echo ========================================
if %ERRORLEVEL% EQU 0 (
    echo ✅ 다이어그램 생성 완료!
    echo.
    echo 생성된 파일이 web/public/한국인터넷.한국/참소식.com/ 에 저장되었습니다.
    echo.
    echo 파일: website_diagram.html
    echo 파일: website_diagram.mmd
) else (
    echo ❌ 다이어그램 생성 실패
    echo.
    echo 문제 해결 방법:
    echo   1. Ollama 서비스가 실행 중인지 확인
    echo   2. 인터넷 연결 확인
    echo   3. URL이 올바른지 확인
)
echo ========================================
echo.

if not "%AUTO_MODE%"=="1" pause
