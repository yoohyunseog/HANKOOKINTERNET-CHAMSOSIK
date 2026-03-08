@echo off
setlocal
chcp 65001 >nul
title 다이어그램 생성+동기화 무한 반복

REM 작업 디렉토리를 프로젝트 루트로 이동
set "ROOT_DIR=%~dp0"
set "TOOLS_DIR=%ROOT_DIR%tools\"
cd /d "%ROOT_DIR%"

REM run_website_diagram.bat의 pause/입력 대기 방지
set "AUTO_MODE=1"

REM 사이클 간 대기 시간(초). 필요하면 값 변경: 0 이면 즉시 반복
set "INTERVAL_SECONDS=600"

echo ========================================
echo ♾️  다이어그램 자동 무한 반복 실행
echo ========================================
echo 1) tools\run_website_diagram.bat
echo 2) tools\sync_diagram.bat
echo.
echo 중단: Ctrl+C
echo ========================================
echo.

:loop
echo.
echo ========================================
echo 🔁 사이클 시작 - %date% %time%
echo ========================================
echo.

echo [1/2] 다이어그램 생성 실행...
call "%TOOLS_DIR%run_website_diagram.bat"
if errorlevel 1 (
  echo ⚠️  생성 실패. 다음 단계로 계속 진행합니다.
)
echo.

echo [2/2] 다이어그램 동기화 실행...
call "%TOOLS_DIR%sync_diagram.bat"
if errorlevel 1 (
  echo ⚠️  동기화 실패. 다음 사이클로 계속 진행합니다.
)
echo.

echo ========================================
echo ✅ 사이클 완료 - %date% %time%
echo ========================================

if "%INTERVAL_SECONDS%"=="0" goto loop

echo 다음 사이클까지 %INTERVAL_SECONDS%초 대기...
timeout /t %INTERVAL_SECONDS% /nobreak >nul
goto loop
