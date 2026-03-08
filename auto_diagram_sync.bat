@echo off
chcp 65001 > nul
title 자동 다이어그램 생성 및 동기화

echo ========================================
echo 🔄 자동 다이어그램 생성 및 동기화 시스템
echo ========================================
echo.
echo 이 스크립트는 다음 작업을 반복 실행합니다:
echo   1. 웹사이트 다이어그램 생성 (참소식.com)
echo   2. 서버에 파일 동기화
echo.
echo 중단하려면 Ctrl+C를 누르세요.
echo ========================================
echo.

REM 자동 모드 활성화
set AUTO_MODE=1

REM 작업 디렉토리를 프로젝트 루트로 변경
cd /d "%~dp0"

:loop
echo.
echo ========================================
echo 🔁 반복 실행 시작 - %date% %time%
echo ========================================
echo.

REM 1단계: 다이어그램 생성
echo [1/2] 웹사이트 다이어그램 생성 중...
echo ----------------------------------------
call tools\run_website_diagram.bat
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  다이어그램 생성 실패. 계속 진행합니다...
)
echo.

REM 2단계: 서버 동기화
echo [2/2] 서버에 다이어그램 파일 업로드 중...
echo ----------------------------------------
call tools\sync_diagram.bat
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  동기화 실패. 계속 진행합니다...
)
echo.

echo ========================================
echo ✅ 1회 사이클 완료 - %date% %time%
echo ========================================
echo.
echo 다음 사이클을 10분 후에 시작합니다...
timeout /t 600 /nobreak >nul
echo.

goto loop
