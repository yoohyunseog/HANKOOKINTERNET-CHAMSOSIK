@echo off
REM N/B 계산 및 정리 관리자
REM 계산, 정리, 보기 등 다양한 옵션 제공

chcp 65001 > nul
color 0A

:menu
cls
echo.
echo ============================================================
echo  N/B 계산 및 정리 프로그램 (관리자)
echo ============================================================
echo.
echo 실행할 작업을 선택하세요:
echo.
echo  1. N/B 계산 실행 + 자동 정리
echo  2. N/B 계산만 실행 (정리 없음)
echo  3. 결과 정리만 실행
echo  4. 최근 결과 보기
echo  5. 모든 작업 종료
echo.
set /p choice="선택 (1-5): "

if "%choice%"=="1" goto :calculate_and_organize
if "%choice%"=="2" goto :calculate_only
if "%choice%"=="3" goto :organize_only
if "%choice%"=="4" goto :view_results
if "%choice%"=="5" goto :exit
if "%choice%"=="" goto :menu

echo ❌ 잘못된 선택입니다.
timeout /t 2 /nobreak
goto :menu

:calculate_and_organize
echo.
echo [1/3] N/B 계산 실행 중...
echo.
E:\node\node.exe "E:\Ai project\사이트\8BIT\js\nb_calculation_node.js"

echo.
echo [2/3] 결과 정리 중...
echo.
py 8BIT\organize_nb_results.py

echo.
echo [3/3] 작업 완료!
echo.
pause
goto :menu

:calculate_only
echo.
echo N/B 계산 실행 중...
echo.
E:\node\node.exe "E:\Ai project\사이트\8BIT\js\nb_calculation_node.js"

echo.
echo 계산 완료!
echo.
pause
goto :menu

:organize_only
echo.
echo 결과 정리 중...
echo.
py 8BIT\organize_nb_results.py

echo.
echo 정리 완료!
echo.
pause
goto :menu

:view_results
echo.
echo 최근 결과를 확인합니다...
echo.

if exist "data\nb_results\latest_results.json" (
    py -c "import json; data=json.load(open('data/nb_results/latest_results.json', 'r', encoding='utf-8')); stats=data.get('statistics', {}); print(f'✅ 총 항목: {stats.get(\"total_count\", 0):,}개'); print(f'📅 정리 시간: {stats.get(\"collection_time\", \"N/A\")}'); print(f'📁 저장 위치: data/nb_results/')"
    
    REM 결과 폴더 열기
    explorer.exe "data\nb_results"
) else (
    echo ⚠️ 결과 파일이 없습니다.
    echo 먼저 계산 및 정리를 실행하세요.
)

echo.
pause
goto :menu

:exit
cls
echo.
echo ============================================================
echo  프로그램을 종료합니다.
echo ============================================================
echo.
timeout /t 2 /nobreak
exit
