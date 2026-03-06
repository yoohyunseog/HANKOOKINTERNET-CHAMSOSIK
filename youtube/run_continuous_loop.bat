@echo off
chcp 65001 > nul
setlocal

:: ========================================
:: YouTube 모니터링 반복 실행 시스템
:: ========================================

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

set LOOP_COUNT=0

echo.
echo ================================================
echo    YouTube 모니터링 반복 실행 시스템
echo ================================================
echo.
echo [INFO] run_continuous_monitor.bat을 반복 실행합니다.
echo [INFO] 종료하려면 Ctrl+C를 누르세요.
echo.
echo ================================================
echo.

:loop
set /a LOOP_COUNT+=1
set LOOP_MODE=1
echo.
echo ========================================
echo [LOOP #%LOOP_COUNT%] %date% %time%
echo ========================================
echo.

:: run_continuous_monitor.bat 실행
call "%SCRIPT_DIR%run_continuous_monitor.bat"

set EXIT_CODE=%errorlevel%

if %EXIT_CODE% equ 0 (
    echo.
    echo [INFO] 모니터링이 정상 종료되었습니다.
    echo [INFO] 즉시 재시작합니다...
) else (
    echo.
    echo [WARN] 오류로 종료되었습니다 (코드: %EXIT_CODE%)
    echo [INFO] 즉시 재시작합니다...
)

goto loop
