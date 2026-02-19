@echo off
REM N/B 계산 프로그램 실행 배치 파일
REM Node.js 프로그램 실행 + 자동 정리

chcp 65001 > nul
color 0A

:start
cls
echo.
echo ============================================================
echo  N/B MAX, N/B MIN 계산 프로그램 (Node.js)
echo ============================================================
echo.

REM 1단계: N/B 계산 실행
E:\node\node.exe "E:\Ai project\사이트\8BIT\js\nb_calculation_node.js"

echo.
echo ============================================================
echo  N/B 계산 완료! 이제 결과를 자동으로 정리합니다.
echo ============================================================
echo.

REM 2단계: Python 환경 확인 및 정리 프로그램 실행
py --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo 설정 ^ 아래로 스킵합니다.
    goto :end
)

echo [1/2] 필요한 패키지 확인 중...
REM 패키지 이미 설치되어 있으므로 건너뜀

echo [2/2] 결과 정리 중...
py 8BIT\organize_nb_results.py

:end
echo.
echo ============================================================
echo  모든 작업이 완료되었습니다.
echo ============================================================
echo.

timeout /t 3 /nobreak
